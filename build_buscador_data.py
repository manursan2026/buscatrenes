#!/usr/bin/env python3
"""
build_buscador_data.py
=======================
Genera el payload de datos (JSON comprimido en gzip+base64) para el buscador
de trenes RENFE (buscador_trenes.html). A diferencia de gtfs_renfe_extractor.py
(que produce el Excel con paradas intermedias en columnas), aquí se conserva
la secuencia COMPLETA de paradas por trip (incluye origen y destino) junto con
las coordenadas de las estaciones, necesarias para:
  - la búsqueda de trenes directos origen -> destino en cualquier punto de la
    circulación (no solo extremos),
  - la geolocalización de la estación de origen más cercana en el navegador.

Reutiliza la descarga y el mapeo de categorías de gtfs_renfe_extractor.py.

Salida: escribe `buscador_data.b64` (texto base64 de un gzip de un JSON) que
`generar_buscador_html.py` incrusta en el HTML final.
"""
import base64
import gzip
import io
import json
import math
import re
import zipfile

import pandas as pd
import requests

from gtfs_renfe_extractor import CATEGORIA, DIAS, NUCLEOS, URL_AVLD, URL_CER, leer_feed, minutos

# OUIGO, Euskotren y Mallorca publican su GTFS en el NAP (nap.transportes.gob.es,
# requiere ApiKey); FGC lo publica sin autenticación en su propio portal.
# Mobility Database mantiene una réplica pública diaria sin autenticación de
# los feeds del NAP, que es lo que usamos aquí para no depender de una ApiKey.
URL_OUIGO = "https://files.mobilitydatabase.org/mdb-2785/latest.zip"
URL_FGC = "https://www.fgc.cat/google/google_transit.zip"
URL_EUSKOTREN = "https://files.mobilitydatabase.org/mdb-2715/latest.zip"
# El feed de Mallorca (Consorci de Transports/TIB) mezcla bus, metro y tren en
# un único fichero; nos quedamos solo con route_type=2 (las 3 líneas de SFM).
URL_MALLORCA = "https://files.mobilitydatabase.org/mdb-2766/latest.zip"
# IRYO no publica GTFS a fecha de julio de 2026 (pendiente en el NAP según
# datos.gob.es). Cuando lo haga, añadir aquí su URL y una llamada más en main().

OUT_B64 = "buscador_data.b64"

FUSION_KM = 0.35  # estaciones de otros operadores a <350 m de una de RENFE = la misma


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * r * math.asin(math.sqrt(a))


def calendario_desde_calendar_dates(calendar_dates):
    """Sintetiza un calendar.txt (bitmask semanal + rango de vigencia) a partir
    de calendar_dates.txt, para feeds (p. ej. FGC) que solo listan fechas
    exactas de servicio. Se ignoran las bajas puntuales (exception_type=2,
    festivos concretos): misma simplificación que ya se aplica a RENFE, que
    tampoco tiene en cuenta calendar_dates.txt."""
    cd = calendar_dates[calendar_dates["exception_type"] == "1"].copy()
    cd["date_int"] = cd["date"].astype(int)
    cd["weekday"] = pd.to_datetime(cd["date"], format="%Y%m%d").dt.weekday  # 0=lunes

    filas = []
    for sid, g in cd.groupby("service_id"):
        dias_presentes = set(g["weekday"].unique().tolist())
        fila = {"service_id": sid, "start_date": int(g["date_int"].min()),
                "end_date": int(g["date_int"].max())}
        for i, d in enumerate(DIAS):
            fila[d] = "1" if i in dias_presentes else "0"
        filas.append(fila)
    return pd.DataFrame(filas)


def leer_feed_generico(url, route_types=None):
    """Como leer_feed pero tolera feeds sin calendar.txt (lo sintetiza desde
    calendar_dates.txt) y permite quedarse solo con ciertos route_type, para
    feeds de un operador que mezclan tren con metro/tranvía/autobús."""
    print(f"Descargando {url} ...")
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))

    def leer(nombre):
        df = pd.read_csv(z.open(f"{nombre}.txt"), dtype=str)
        df.columns = [c.strip() for c in df.columns]
        return df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)

    routes, trips, stop_times, stops = leer("routes"), leer("trips"), leer("stop_times"), leer("stops")

    if route_types is not None:
        routes = routes[routes["route_type"].isin(route_types)]
        trips = trips[trips["route_id"].isin(routes["route_id"])]
        stop_times = stop_times[stop_times["trip_id"].isin(trips["trip_id"])]
        stops = stops[stops["stop_id"].isin(set(stop_times["stop_id"]))]

    if "calendar.txt" in z.namelist():
        calendar = leer("calendar")
    else:
        calendar = calendario_desde_calendar_dates(leer("calendar_dates"))

    print("  Leído.")
    return {"routes": routes, "trips": trips, "stop_times": stop_times,
            "stops": stops, "calendar": calendar}


def numero_de_trip(row):
    t = row["trip_id"]
    if isinstance(row["service_id"], str) and t.startswith(row["service_id"]):
        t = t[len(row["service_id"]):]
    m = re.match(r"(\d+)", t)
    return m.group(1) if m else t


def construir_trips(tablas, ambito, estaciones, idx_estacion, lineas, idx_linea,
                    fusionar_cercanas=False):
    routes, trips, stop_times, stops, calendar = (
        tablas["routes"], tablas["trips"], tablas["stop_times"],
        tablas["stops"], tablas["calendar"],
    )
    print(f"  {ambito}: {len(trips)} trips, {len(stop_times)} paradas...")

    # Estaciones: registrar nombre -> indice (dedup por nombre). Para feeds de
    # otros operadores (fusionar_cercanas), una estación a <FUSION_KM de una ya
    # registrada se considera la misma aunque el nombre difiera (p. ej.
    # "MADRID-PUERTA DE ATOCHA" de OUIGO = "Madrid-Puerta de Atocha-Almudena
    # Grandes" de RENFE), para que las búsquedas mezclen operadores.
    for _, s in stops.iterrows():
        nombre = s["stop_name"]
        if nombre in idx_estacion:
            continue
        try:
            lat, lon = float(s["stop_lat"]), float(s["stop_lon"])
        except (TypeError, ValueError):
            lat, lon = None, None
        if fusionar_cercanas and lat is not None:
            mejor, mejor_d = None, FUSION_KM
            for i, (n2, la2, lo2) in enumerate(estaciones):
                if la2 is None:
                    continue
                d = haversine_km(lat, lon, la2, lo2)
                if d < mejor_d:
                    mejor, mejor_d = i, d
            if mejor is not None:
                idx_estacion[nombre] = mejor
                print(f"    fusionada: {nombre} -> {estaciones[mejor][0]} ({mejor_d*1000:.0f} m)")
                continue
        idx_estacion[nombre] = len(estaciones)
        estaciones.append([nombre, round(lat, 5) if lat is not None else None,
                            round(lon, 5) if lon is not None else None])

    nombres_stop = stops.set_index("stop_id")["stop_name"]

    st = stop_times.copy()
    st["seq"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "seq"])
    st["arr_min"] = st["arrival_time"].map(minutos)
    st["dep_min"] = st["departure_time"].map(minutos)
    st["st_idx"] = st["stop_id"].map(nombres_stop).map(idx_estacion)

    # Agrupar paradas por trip_id preservando el orden
    paradas_por_trip = {}
    for trip_id, grp in st.groupby("trip_id", sort=False):
        flat = []
        for _, r in grp.iterrows():
            flat.append(int(r["st_idx"]))
            flat.append(int(round(r["arr_min"])) if pd.notna(r["arr_min"]) else -1)
            flat.append(int(round(r["dep_min"])) if pd.notna(r["dep_min"]) else -1)
        paradas_por_trip[trip_id] = flat

    df = trips.merge(calendar[["service_id", "start_date", "end_date"] + DIAS],
                      on="service_id", how="left")
    rcols = ["route_id", "route_short_name"]
    df = df.merge(routes[rcols], on="route_id", how="left")

    sin_numero_publico = ambito in ("FGC", "Euskotren", "Mallorca-SFM")
    if sin_numero_publico:
        # Estos operadores no publican un número de tren de cara al viajero
        # (a diferencia de RENFE/OUIGO); el trip_id es un identificador interno
        # sin valor informativo, así que se deja en blanco.
        df["numero_tren"] = ""
    elif "trip_short_name" in df.columns and df["trip_short_name"].notna().any():
        df["numero_tren"] = df["trip_short_name"]
        if ambito == "OUIGO":                       # "TGV 6477" -> "6477"
            df["numero_tren"] = df["numero_tren"].str.replace(
                r"^TGV\s+", "", regex=True)
    else:
        df["numero_tren"] = df.apply(numero_de_trip, axis=1)

    salida = []
    for _, r in df.iterrows():
        flat = paradas_por_trip.get(r["trip_id"])
        if not flat or len(flat) < 6:
            continue  # trip con <2 paradas, no sirve para buscar trayecto

        if ambito == "Cercanías":
            nucleo = NUCLEOS.get(str(r["route_id"])[:2], str(r["route_id"])[:2])
            etiqueta = f"{nucleo} {r['route_short_name']}".strip()
            cat = "CER"
        elif ambito == "OUIGO":
            cat = "OUIGO"
            etiqueta = "OUIGO"
        elif ambito == "FGC":
            cat = "FGC"
            etiqueta = f"FGC {r['route_short_name']}".strip()
        elif ambito == "Euskotren":
            cat = "EUS"
            etiqueta = f"Euskotren {r['route_short_name']}".strip()
        elif ambito == "Mallorca-SFM":
            cat = "SFM"
            etiqueta = f"SFM {r['route_short_name']}".strip()
        else:
            cat = CATEGORIA.get(r["route_short_name"], "LD")
            etiqueta = r["route_short_name"]

        if etiqueta not in idx_linea:
            idx_linea[etiqueta] = len(lineas)
            lineas.append(etiqueta)

        dias_bitmask = 0
        for i, d in enumerate(DIAS):
            if str(r[d]) == "1":
                dias_bitmask |= (1 << i)

        try:
            sd = int(r["start_date"])
            ed = int(r["end_date"])
        except (TypeError, ValueError):
            continue

        salida.append([
            cat,
            idx_linea[etiqueta],
            str(r["numero_tren"]),
            dias_bitmask,
            sd,
            ed,
            flat,
        ])

    print(f"    -> {len(salida)} circulaciones válidas")
    return salida


def main():
    estaciones = []
    idx_estacion = {}
    lineas = []
    idx_linea = {}

    trips = []
    trips += construir_trips(leer_feed(URL_AVLD), "AV-LD", estaciones, idx_estacion, lineas, idx_linea)
    trips += construir_trips(leer_feed(URL_CER), "Cercanías", estaciones, idx_estacion, lineas, idx_linea)
    trips += construir_trips(leer_feed(URL_OUIGO), "OUIGO", estaciones, idx_estacion,
                              lineas, idx_linea, fusionar_cercanas=True)
    trips += construir_trips(leer_feed_generico(URL_FGC, route_types={"2"}), "FGC",
                              estaciones, idx_estacion, lineas, idx_linea, fusionar_cercanas=True)
    trips += construir_trips(leer_feed_generico(URL_EUSKOTREN, route_types={"2"}), "Euskotren",
                              estaciones, idx_estacion, lineas, idx_linea, fusionar_cercanas=True)
    trips += construir_trips(leer_feed_generico(URL_MALLORCA, route_types={"2"}), "Mallorca-SFM",
                              estaciones, idx_estacion, lineas, idx_linea, fusionar_cercanas=True)

    payload = {"estaciones": estaciones, "lineas": lineas, "trips": trips}
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    print(f"\nJSON crudo: {len(raw) / 1e6:.1f} MB")

    comp = gzip.compress(raw, compresslevel=9)
    print(f"Gzip: {len(comp) / 1e6:.1f} MB")

    b64 = base64.b64encode(comp).decode("ascii")
    print(f"Base64: {len(b64) / 1e6:.1f} MB")

    with open(OUT_B64, "w") as f:
        f.write(b64)
    print(f"\nEstaciones: {len(estaciones)} | Líneas: {len(lineas)} | Trips: {len(trips)}")
    print(f"Generado: {OUT_B64}")


if __name__ == "__main__":
    main()
