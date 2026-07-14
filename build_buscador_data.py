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

# Provincias (para el filtro de incidencias por provincia/CCAA): polígonos de
# los límites provinciales, asignación por punto-en-polígono a cada estación.
URL_PROVINCIAS = ("https://raw.githubusercontent.com/codeforgermany/click_that_hood/"
                  "main/public/data/spain-provinces.geojson")

CCAA = {
    "Almería": "Andalucía", "Cádiz": "Andalucía", "Córdoba": "Andalucía",
    "Granada": "Andalucía", "Huelva": "Andalucía", "Jaén": "Andalucía",
    "Málaga": "Andalucía", "Sevilla": "Andalucía",
    "Huesca": "Aragón", "Teruel": "Aragón", "Zaragoza": "Aragón",
    "Asturias": "Asturias", "Illes Balears": "Illes Balears",
    "Las Palmas": "Canarias", "Santa Cruz De Tenerife": "Canarias",
    "Cantabria": "Cantabria",
    "Albacete": "Castilla-La Mancha", "Ciudad Real": "Castilla-La Mancha",
    "Cuenca": "Castilla-La Mancha", "Guadalajara": "Castilla-La Mancha",
    "Toledo": "Castilla-La Mancha",
    "Burgos": "Castilla y León", "León": "Castilla y León",
    "Palencia": "Castilla y León", "Salamanca": "Castilla y León",
    "Segovia": "Castilla y León", "Soria": "Castilla y León",
    "Valladolid": "Castilla y León", "Zamora": "Castilla y León",
    "Ávila": "Castilla y León",
    "Barcelona": "Cataluña", "Girona": "Cataluña", "Lleida": "Cataluña",
    "Tarragona": "Cataluña",
    "Alacant/Alicante": "Comunitat Valenciana",
    "Castelló/Castellón": "Comunitat Valenciana",
    "València/Valencia": "Comunitat Valenciana",
    "Badajoz": "Extremadura", "Cáceres": "Extremadura",
    "A Coruña": "Galicia", "Lugo": "Galicia", "Ourense": "Galicia",
    "Pontevedra": "Galicia",
    "La Rioja": "La Rioja", "Madrid": "Madrid", "Murcia": "Murcia",
    "Navarra": "Navarra",
    "Araba/Álava": "País Vasco", "Bizkaia/Vizcaya": "País Vasco",
    "Gipuzkoa/Guipúzcoa": "País Vasco",
    "Ceuta": "Ceuta", "Melilla": "Melilla",
}


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


def punto_en_anillo(lon, lat, anillo):
    dentro = False
    j = len(anillo) - 1
    for i in range(len(anillo)):
        xi, yi = anillo[i][0], anillo[i][1]
        xj, yj = anillo[j][0], anillo[j][1]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def asignar_provincias(estaciones):
    """Añade a cada estación [nombre, lat, lon] un cuarto elemento: índice de
    provincia (o -1 si no tiene coordenadas). Devuelve la lista de provincias
    [[nombre, ccaa], ...]. Si el GeoJSON no se puede descargar, deja -1 en
    todas (el buscador ofrece igualmente "mi zona" y "todas")."""
    try:
        print(f"Descargando {URL_PROVINCIAS} ...")
        gj = requests.get(URL_PROVINCIAS, timeout=120).json()
    except Exception as e:
        print(f"  AVISO: sin provincias ({e})")
        for est in estaciones:
            est.append(-1)
        return []

    provincias, poligonos = [], []
    for f in gj["features"]:
        nombre = f["properties"]["name"]
        # con nombre cooficial doble, mostrar la variante castellana
        visible = nombre.split("/")[-1]
        provincias.append([visible, CCAA.get(nombre, visible)])
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        anillos = [p[0] for p in polys]  # anillo exterior; los huecos no aplican
        cajas = []
        for a in anillos:
            xs = [pt[0] for pt in a]
            ys = [pt[1] for pt in a]
            cajas.append((min(xs), min(ys), max(xs), max(ys)))
        poligonos.append((anillos, cajas))

    sin_asignar = 0
    for est in estaciones:
        lat, lon = est[1], est[2]
        if lat is None:
            est.append(-1)
            continue
        idx = -1
        for i, (anillos, cajas) in enumerate(poligonos):
            for a, (x0, y0, x1, y1) in zip(anillos, cajas):
                if x0 <= lon <= x1 and y0 <= lat <= y1 and punto_en_anillo(lon, lat, a):
                    idx = i
                    break
            if idx >= 0:
                break
        if idx < 0:
            # fuera de todo polígono (redondeos costeros, Cerbère...): la
            # provincia cuyo borde quede más cerca
            mejor_d = None
            for i, (anillos, _) in enumerate(poligonos):
                for a in anillos:
                    for pt in a[::4] or a:
                        d = (pt[0] - lon) ** 2 + (pt[1] - lat) ** 2
                        if mejor_d is None or d < mejor_d:
                            mejor_d, idx = d, i
            sin_asignar += 1
        est.append(idx)

    print(f"  Provincias asignadas ({sin_asignar} por cercanía al borde).")
    return provincias


def numero_de_trip(row):
    t = row["trip_id"]
    if isinstance(row["service_id"], str) and t.startswith(row["service_id"]):
        t = t[len(row["service_id"]):]
    m = re.match(r"(\d+)", t)
    return m.group(1) if m else t


def construir_trips(tablas, ambito, estaciones, idx_estacion, lineas, idx_linea,
                    fusionar_cercanas=False, rutas=None, codigos=None):
    """rutas/codigos: dicts opcionales que se rellenan con route_id -> índice
    de línea y stop_id -> índice de estación. Solo se piden para los operadores
    con feed de incidencias GTFS-RT (Cercanías y FGC), cuyas alertas referencian
    esos identificadores del feed estático."""
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

    if codigos is not None:
        for sid, nombre in nombres_stop.items():
            if nombre in idx_estacion:
                codigos[str(sid)] = idx_estacion[nombre]

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
        if rutas is not None:
            rutas[str(r["route_id"])] = idx_linea[etiqueta]
            if ambito == "Cercanías":
                # RENFE rota los route_id entre versiones del feed (10T0095C4 ->
                # 10T0096C4), pero núcleo (2 primeros chars) y nombre corto de
                # línea son estables: clave alternativa "10|C4" para casar
                # alertas GTFS-RT cuyo route_id exacto ya no exista.
                rutas[str(r["route_id"])[:2] + "|" + str(r["route_short_name"])] = idx_linea[etiqueta]

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

    rutas = {}    # route_id -> índice de línea (Cercanías y FGC, para cruzar alertas GTFS-RT)
    codigos = {}  # stop_id -> índice de estación (ídem)

    trips = []
    trips += construir_trips(leer_feed(URL_AVLD), "AV-LD", estaciones, idx_estacion, lineas, idx_linea)
    trips += construir_trips(leer_feed(URL_CER), "Cercanías", estaciones, idx_estacion, lineas, idx_linea,
                              rutas=rutas, codigos=codigos)
    trips += construir_trips(leer_feed(URL_OUIGO), "OUIGO", estaciones, idx_estacion,
                              lineas, idx_linea, fusionar_cercanas=True)
    trips += construir_trips(leer_feed_generico(URL_FGC, route_types={"2"}), "FGC",
                              estaciones, idx_estacion, lineas, idx_linea, fusionar_cercanas=True,
                              rutas=rutas, codigos=codigos)
    trips += construir_trips(leer_feed_generico(URL_EUSKOTREN, route_types={"2"}), "Euskotren",
                              estaciones, idx_estacion, lineas, idx_linea, fusionar_cercanas=True)
    trips += construir_trips(leer_feed_generico(URL_MALLORCA, route_types={"2"}), "Mallorca-SFM",
                              estaciones, idx_estacion, lineas, idx_linea, fusionar_cercanas=True)

    provincias = asignar_provincias(estaciones)

    payload = {"estaciones": estaciones, "lineas": lineas, "trips": trips,
               "rutas": rutas, "codigos": codigos, "provincias": provincias}
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
