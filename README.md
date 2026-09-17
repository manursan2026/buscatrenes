# BuscaTrenes

Buscador de trenes de fichero único (HTML con datos GTFS embebidos) más una
app Android mínima que lo envuelve. Busca trenes directos entre dos
estaciones y, si no los hay, enlaces con 1 o 2 transbordos. Incluye
geolocalización para la estación de origen y botón de compartir itinerario.

Operadores incluidos: RENFE (AV/LD/MD/Cercanías), OUIGO, FGC, Euskotren y
SFM Mallorca. Todo funciona offline una vez generado — no hay backend ni
llamadas de red en tiempo de uso.

## Ficheros

- `gtfs_renfe_extractor.py` — funciones de descarga y categorización de los
  feeds GTFS de RENFE (AV-LD y Cercanías). Lo importa `build_buscador_data.py`.
- `build_buscador_data.py` — descarga los GTFS de los 5 operadores y genera
  `buscador_data.b64` (JSON comprimido en gzip+base64 con estaciones,
  líneas y circulaciones).
- `generar_buscador_html.py` — incrusta `buscador_data.b64` en la plantilla
  HTML/CSS/JS y escribe `buscador_trenes.html` (el buscador en sí).
- `buscador_trenes.html` / `buscador_data.b64` — ya generados, por si no
  quieres regenerarlos de inmediato (los datos actuales caducan según la
  vigencia de los calendarios GTFS, a lo largo de 2026).
- `android_buscador/` — app Android que envuelve el HTML en un WebView.
  **Ver `android_buscador/README.md` para todo lo relativo a compilar la
  app, requisitos, firma del APK y limitaciones conocidas.**
- `Abrir_Emulador.command` — doble clic en el Mac: arranca el emulador de
  Android Studio, instala el `buscador_trenes.apk` de esta carpeta y abre la
  app. Requiere Android Studio con el AVD `Medium_Phone_API_36.1`.
- `manual/` + `docs_manual.py` — capturas del emulador y generador del
  `Manual_BuscaTrenes.pdf` (reportlab).
- `docs_web.py` — genera `Web/` (no versionada): página de descargas
  `index.html` con enlaces relativos y, al lado, el APK, el manual PDF y
  las capturas reducidas; la carpeta se copia entera al alojamiento que se
  quiera.

## Regenerar todo

```bash
python3 build_buscador_data.py        # descarga los GTFS -> buscador_data.b64
python3 generar_buscador_html.py       # genera buscador_trenes.html
android_buscador/build_apk.sh          # genera buscador_trenes.apk (ver requisitos en android_buscador/README.md)
python3 docs_manual.py                 # Manual_BuscaTrenes.pdf a partir de manual/*.png
python3 docs_web.py                    # Web/ autocontenida: index.html + APK + PDF + img/, para subir a cualquier alojamiento
```

Requiere Python 3 con `pandas`, `requests`, `reportlab` y `Pillow`.

Las capturas de `manual/` se toman en el emulador (en español) con
`adb exec-out screencap -p > manual/NN_nombre.png`; si cambia la interfaz,
basta con sustituir la captura correspondiente y volver a ejecutar los dos
scripts de documentación.

## Publicar una versión nueva

El código vive en GitHub (<https://github.com/manursan2026/buscatrenes>);
la página de descargas se aloja aparte, copiando la carpeta `Web/`.

Tras regenerar todo, commit y push, publicar una release con el APK y el
manual, y volver a subir `Web/` al alojamiento:

```bash
gh release create v1.0-$(date +%Y.%m.%d) buscador_trenes.apk Manual_BuscaTrenes.pdf \
  --title "BuscaTrenes · horarios del $(date +%d/%m/%Y)" --notes "Horarios GTFS regenerados."
```

