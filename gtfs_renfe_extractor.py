#!/usr/bin/env python3
"""
Extractor GTFS de RENFE -> Excel.

Descarga los feeds GTFS públicos de RENFE y genera un único fichero Excel con
dos hojas (AV-LD y Cercanías). Cada fila es una circulación (trip), sin
deduplicar: un mismo número de tren aparece en tantas filas como periodos de
vigencia (service_id) tiene en el calendario.

Columnas base:
    Numero_tren, Estacion_salida, Hora_salida, Estacion_llegada, Hora_llegada
más columnas adicionales derivadas de cada número de tren: producto/núcleo/línea,
nº de paradas, duración, días de circulación y vigencia.

Feeds:
  - AV-LD     : https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip
  - Cercanías : https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip
"""

import io
import re
import zipfile

import pandas as pd
import requests

URL_AVLD = "https://ssl.renfe.com/gtransit/Fichero_AV_LD/google_transit.zip"
URL_CER = "https://ssl.renfe.com/ftransit/Fichero_CER_FOMENTO/fomento_transit.zip"
OUT_XLSX = "RENFE_GTFS_trenes.xlsx"

DIAS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
DIAS_ES = ["L", "M", "X", "J", "V", "S", "D"]

# Categoría comercial a partir del producto (route_short_name) del feed AV-LD
CATEGORIA = {
    "AVE": "AV", "AVLO": "AV", "AVE INT": "AV",
    "ALVIA": "LD", "Intercity": "LD", "EUROMED": "LD", "TRENCELTA": "LD",
    "AVANT": "MD", "AVANT EXP": "MD", "MD": "MD",
    "REG.EXP.": "MD", "REGIONAL": "MD", "PROXIMDAD": "MD",
}

# Núcleo de Cercanías según los 2 primeros dígitos del route_id (inferido del feed)
NUCLEOS = {
    "10": "Madrid", "20": "Asturias", "30": "Sevilla", "31": "Cádiz",
    "32": "Málaga", "40": "València", "41": "Murcia/Alacant",
    "45": "Murcia (Cartagena-Los Nietos)", "46": "Ferrol", "47": "León",
    "51": "Barcelona", "60": "Bilbao", "61": "San Sebastián",
    "62": "Cantabria", "70": "Zaragoza", "90": "Madrid (C9 Guadarrama)",
}


def leer_feed(url):
    print(f"Descargando {url} ...")
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    tablas = {}
    for nombre in ["routes", "trips", "stop_times", "stops", "calendar"]:
        df = pd.read_csv(z.open(f"{nombre}.txt"), dtype=str)
        df.columns = [c.strip() for c in df.columns]              # cabeceras con espacios
        df = df.apply(lambda s: s.str.strip() if s.dtype == "object" else s)
        tablas[nombre] = df
    print("  Leído.")
    return tablas


def hhmm(t):
    if pd.isna(t):
        return ""
    p = str(t).split(":")
    return f"{int(p[0]):02d}:{p[1]}"


def minutos(t):
    if pd.isna(t):
        return None
    p = [int(x) for x in str(t).split(":")]
    return p[0] * 60 + p[1] + (p[2] / 60 if len(p) > 2 else 0)


def patron_dias(fila):
    activos = [DIAS_ES[i] for i, d in enumerate(DIAS) if str(fila[d]) == "1"]
    if len(activos) == 7:
        return "Diario"
    return "-".join(activos) if activos else ""


def fmt_fecha(s):
    if pd.isna(s) or not str(s).strip():
        return ""
    s = str(s)
    return f"{s[6:8]}/{s[4:6]}/{s[0:4]}"


def recorrido_por_trip(stop_times, stops):
    """Origen/destino, nº de paradas y duración por trip (vectorizado)."""
    st = stop_times.copy()
    st["seq"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "seq"])
    nombres = stops.set_index("stop_id")["stop_name"]

    prim = st.drop_duplicates("trip_id", keep="first")
    ult = st.drop_duplicates("trip_id", keep="last")
    n_par = st.groupby("trip_id").size().rename("num_paradas")

    rec = pd.DataFrame({"trip_id": prim["trip_id"].values})
    rec["estacion_salida"] = prim["stop_id"].map(nombres).fillna(prim["stop_id"]).values
    rec["hora_salida"] = prim["departure_time"].map(hhmm).values
    rec["estacion_llegada"] = ult["stop_id"].map(nombres).fillna(ult["stop_id"]).values
    rec["hora_llegada"] = ult["arrival_time"].map(hhmm).values
    dep = prim["departure_time"].map(minutos).values
    arr = ult["arrival_time"].map(minutos).values
    rec["duracion_min"] = [
        int(round(a - d)) if (a is not None and d is not None) else None
        for d, a in zip(dep, arr)
    ]
    rec = rec.merge(n_par, on="trip_id", how="left")
    return rec


def paradas_intermedias_wide(stop_times, stops):
    """Expande las paradas intermedias (sin origen ni destino) a formato ancho:
    Estacion_1, Llegada_1, Salida_1, Estacion_2, ... por trip."""
    st = stop_times.copy()
    st["seq"] = st["stop_sequence"].astype(int)
    st = st.sort_values(["trip_id", "seq"])
    nombres = stops.set_index("stop_id")["stop_name"]

    st["rk"] = st.groupby("trip_id").cumcount()              # 0 = origen
    st["n"] = st.groupby("trip_id")["rk"].transform("size")
    inter = st[(st["rk"] >= 1) & (st["rk"] < st["n"] - 1)].copy()
    inter["idx"] = inter["rk"]                                # 1 = 1ª intermedia
    inter["Estacion"] = inter["stop_id"].map(nombres).fillna(inter["stop_id"])
    inter["Llegada"] = inter["arrival_time"].map(hhmm)
    inter["Salida"] = inter["departure_time"].map(hhmm)

    piezas = []
    for campo in ("Estacion", "Llegada", "Salida"):
        p = inter.pivot(index="trip_id", columns="idx", values=campo)
        p.columns = [f"{campo}_Intermedia_{c}" for c in p.columns]
        piezas.append(p)
    wide = pd.concat(piezas, axis=1)

    # Intercalar: Estacion_Intermedia_1, Llegada_Intermedia_1, Salida_Intermedia_1, ...
    max_i = inter["idx"].max() if len(inter) else 0
    orden = []
    for i in range(1, int(max_i) + 1):
        orden += [f"Estacion_Intermedia_{i}", f"Llegada_Intermedia_{i}",
                  f"Salida_Intermedia_{i}"]
    wide = wide.reindex(columns=orden)
    return wide.reset_index()


def procesar(tablas, ambito):
    routes, trips, stop_times, stops, calendar = (
        tablas["routes"], tablas["trips"], tablas["stop_times"],
        tablas["stops"], tablas["calendar"],
    )
    print(f"  {ambito}: {len(trips)} trips, {len(stop_times)} paradas...")
    rec = recorrido_por_trip(stop_times, stops)

    df = trips.merge(rec, on="trip_id", how="left")
    rcols = ["route_id", "route_short_name"]
    if "route_long_name" in routes.columns:
        rcols.append("route_long_name")
    df = df.merge(routes[rcols], on="route_id", how="left")
    df = df.merge(calendar[["service_id", "start_date", "end_date"] + DIAS],
                  on="service_id", how="left")
    df["dias_circulacion"] = df.apply(patron_dias, axis=1)

    # Número de tren
    if "trip_short_name" in df.columns and df["trip_short_name"].notna().any():
        numero = df["trip_short_name"]
    else:
        def num_de_trip(row):
            t = row["trip_id"]
            if isinstance(row["service_id"], str) and t.startswith(row["service_id"]):
                t = t[len(row["service_id"]):]
            m = re.match(r"(\d+)", t)
            return m.group(1) if m else ""
        numero = df.apply(num_de_trip, axis=1)

    out = pd.DataFrame({
        "Numero_tren": numero,
        "Estacion_salida": df["estacion_salida"],
        "Hora_salida": df["hora_salida"],
        "Estacion_llegada": df["estacion_llegada"],
        "Hora_llegada": df["hora_llegada"],
        "Ambito": ambito,
    })

    if ambito == "Cercanías":
        out["Nucleo"] = df["route_id"].str[:2].map(NUCLEOS).fillna(df["route_id"].str[:2])
        out["Linea"] = df["route_short_name"]
        out["Recorrido_linea"] = df.get("route_long_name", "")
    else:
        out["Producto"] = df["route_short_name"]
        out["Categoria"] = df["route_short_name"].map(CATEGORIA).fillna("LD")

    out["Num_paradas"] = df["num_paradas"]
    out["Duracion_min"] = df["duracion_min"]
    out["Dias_circulacion"] = df["dias_circulacion"]
    out["Vigencia_desde"] = df["start_date"].map(fmt_fecha)
    out["Vigencia_hasta"] = df["end_date"].map(fmt_fecha)
    out["Service_id"] = df["service_id"]
    out["Trip_id"] = df["trip_id"]
    out["Route_id"] = df["route_id"]

    # Paradas intermedias en columnas (Estacion_1, Llegada_1, Salida_1, ...)
    wide = paradas_intermedias_wide(tablas["stop_times"], tablas["stops"])
    out = out.merge(wide, left_on="Trip_id", right_on="trip_id", how="left")
    out = out.drop(columns=["trip_id"])

    out = out.sort_values(["Numero_tren", "Vigencia_desde"],
                          na_position="last").reset_index(drop=True)
    return out


def escribir_hoja(xw, df, hoja):
    from xlsxwriter.utility import xl_col_to_name

    df.to_excel(xw, index=False, sheet_name=hoja, header=False, startrow=1)
    book, ws = xw.book, xw.sheets[hoja]

    centro = book.add_format({"align": "center", "valign": "vcenter"})
    texto = book.add_format({"align": "center", "valign": "vcenter", "num_format": "@"})
    cab = book.add_format({"align": "center", "valign": "vcenter", "bold": True,
                           "bg_color": "#D9E1F2", "border": 1})

    n = len(df)
    for i, col in enumerate(df.columns):
        ws.write(0, i, col, cab)                                   # cabecera centrada
        vals = df[col].dropna().astype(str)
        ancho = max([len(str(col))] + ([vals.map(len).max()] if len(vals) else [0]))
        fmt = texto if col == "Numero_tren" else centro
        ws.set_column(i, i, ancho + 2, fmt)                        # ancho + formato columna

    # Número de tren en modo texto sin el aviso "número almacenado como texto"
    c = xl_col_to_name(list(df.columns).index("Numero_tren"))
    ws.ignore_errors({"number_stored_as_text": f"{c}2:{c}{n + 1}"})

    ws.freeze_panes(1, 0)


def recortar_intermedias(df):
    """Elimina columnas Intermedia_N totalmente vacías (tras filtrar por categoría)."""
    vacias = [c for c in df.columns if "Intermedia" in c and df[c].isna().all()]
    return df.drop(columns=vacias)


def main():
    avld = procesar(leer_feed(URL_AVLD), "AV-LD")
    cer = procesar(leer_feed(URL_CER), "Cercanías")

    with pd.ExcelWriter(OUT_XLSX, engine="xlsxwriter") as xw:
        for cat in ("AV", "LD", "MD"):
            sub = avld[avld["Categoria"] == cat].drop(columns=["Ambito"]).copy()
            sub = recortar_intermedias(sub).reset_index(drop=True)
            escribir_hoja(xw, sub, cat)
            print(f"  {cat:9}: {len(sub):>7} circulaciones | "
                  f"{sub.Numero_tren.nunique()} nº de tren")
        cer_out = recortar_intermedias(cer.drop(columns=["Ambito"]))
        escribir_hoja(xw, cer_out, "Cercanías")
        print(f"  {'Cercanías':9}: {len(cer_out):>7} circulaciones | "
              f"{cer_out.Numero_tren.nunique()} nº de tren")

    print(f"\nGenerado: {OUT_XLSX}")


if __name__ == "__main__":
    main()
