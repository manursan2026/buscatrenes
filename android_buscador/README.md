# BuscaTrenes — app Android

Envoltorio WebView mínimo que muestra `buscador_trenes.html` (buscador de
trenes con datos GTFS embebidos: RENFE AV/LD/MD/Cercanías, OUIGO, FGC,
Euskotren y SFM Mallorca). La app funciona 100% offline; el único permiso
que pide es de ubicación, para el botón "Usar mi ubicación" del buscador.

## Pipeline completo (por este orden)

```bash
cd ..                                  # raíz del proyecto (BuscaTrenes)
python3 build_buscador_data.py         # descarga los GTFS -> buscador_data.b64
python3 generar_buscador_html.py       # incrusta el .b64 en buscador_trenes.html
android_buscador/build_apk.sh          # empaqueta y firma buscador_trenes.apk
```

- `build_buscador_data.py` tarda ~40 s (Cercanías es lo más pesado, ~1,7M paradas).
- `build_apk.sh` tarda unos segundos; no usa Gradle, invoca directamente
  aapt2/javac/d8/zipalign/apksigner del SDK de Android.

## Requisitos en la máquina donde se compile

- **Android Studio instalado** (basta con que exista; no hace falta abrirlo).
  De ahí salen:
  - el SDK, en `~/Library/Android/sdk`
  - el JDK embebido, en `Android Studio.app/Contents/jbr`
- Dentro del SDK: **build-tools 36.1.0** y **platform android-35**. Las rutas
  están fijas en `build_apk.sh` (no se autodetectan) — si la versión
  instalada es otra, hay que editar las variables `BT` y `PLATFORM` al
  principio del script.
- Python 3 con `pandas` y `requests` (para los scripts de datos).

## Firma del APK — importante

El APK se firma con la **clave de depuración local** (`~/.android/debug.keystore`,
contraseña `android`). Esa clave es distinta en cada máquina: si otra persona
compila el proyecto, Android/el SDK le generan su propia clave de depuración
automáticamente la primera vez (no hay que hacer nada especial).

**Consecuencia**: un APK compilado en otra máquina tendrá una firma distinta
al que ya está instalado en un móvil, así que Android **rechazará
instalarlo encima** — hay que desinstalar la versión anterior primero.

Si el proyecto va a tener varias personas compilando y hay que poder
actualizar el mismo móvil desde cualquiera de las dos máquinas, lo correcto
es generar una clave de "release" propia del proyecto (no la de depuración
de nadie en particular) y compartirla entre todos, guardándola con cuidado
(si se pierde, no se puede volver a actualizar la app en los móviles que ya
la tengan instalada). Avisar antes de hacer este cambio si se llega a ese
punto.

## Decisiones de diseño y limitaciones conocidas

- **IRYO no está incluido**: no publica horarios en ningún formato abierto
  (confirmado en datos.gob.es a fecha de julio de 2026, pendiente en el NAP).
  En cuanto lo publique, añadir su URL en `build_buscador_data.py` siguiendo
  el mismo patrón que OUIGO/FGC/Euskotren.
- **Metros, tranvías y funiculares urbanos excluidos a propósito** (Metro
  Madrid, TMB, tranvías de Barcelona/Murcia/Sevilla, funicular de Artxanda,
  transbordador de Bizkaia...): el NAP los publica, pero encajan mal en una
  herramienta pensada para trayectos interurbanos y dispararían el tamaño
  del dataset sin aportar al caso de uso.
- **FGC no tiene `calendar.txt`**, solo `calendar_dates.txt` (fechas exactas
  de servicio en vez de patrón semanal). Se sintetiza un calendario
  equivalente (bitmask semanal + rango de vigencia) en
  `calendario_desde_calendar_dates()`, ignorando bajas puntuales por
  festivos concretos — la misma simplificación que ya se aplica a RENFE,
  que tampoco tiene en cuenta sus propias excepciones de calendario.
- **FGC/Euskotren/SFM Mallorca no publican número de tren** de cara al
  viajero (a diferencia de RENFE/OUIGO); en la UI se muestra "Servicio" en
  vez de "Tren X" para esos operadores (función JS `trenLabel()` en
  `generar_buscador_html.py`).
- **Fusión de estaciones entre operadores**: cuando dos operadores nombran
  distinto la misma estación física (p. ej. "MADRID-PUERTA DE ATOCHA" de
  OUIGO vs "Madrid-Puerta de Atocha-Almudena Grandes" de RENFE), se
  fusionan automáticamente si están a menos de 350 m
  (`FUSION_KM`/`fusionar_cercanas=True` en `build_buscador_data.py`).
- **Búsqueda con transbordos**: si no hay tren directo, se buscan
  automáticamente enlaces con 1 y, si tampoco hay, con 2 transbordos
  (lógica en `generar_buscador_html.py`, funciones `buscarEnlaces`/
  `expandirTransbordo`/`cerrarEnDestino`). Un tercer nivel de transbordo
  no está implementado (rendimiento/utilidad marginal), pero el código
  está preparado para encadenar un nivel más si hiciera falta.
- **OJO al editar la plantilla JS** en `generar_buscador_html.py`: los
  saltos de línea dentro de las cadenas JS deben escribirse `\\n` (con
  doble barra), porque el fichero es una plantilla Python — un `\n` sin
  escapar se convierte en salto de línea real y rompe la sintaxis del
  JavaScript generado. Ya pasó una vez.

## Dónde vienen los datos

- RENFE (AV/LD/MD/Cercanías): feeds públicos en `ssl.renfe.com` — ver
  `gtfs_renfe_extractor.py` en la raíz del proyecto.
- OUIGO, Euskotren, SFM Mallorca: réplicas públicas sin autenticación en
  Mobility Database (`files.mobilitydatabase.org`) de los feeds que estos
  operadores publican en el NAP (`nap.transportes.gob.es`, que exige
  ApiKey para descarga directa).
- FGC: feed propio y abierto en `fgc.cat`, sin autenticación.

## Probar cambios antes de compilar

El HTML se puede abrir directamente en un navegador (funciona igual que en
la app, salvo el puente de "Compartir" nativo). Para probar la app en un
emulador Android:

```bash
~/Library/Android/sdk/emulator/emulator -avd <nombre_avd> -no-window -no-audio -no-boot-anim
~/Library/Android/sdk/platform-tools/adb install -r ../buscador_trenes.apk
~/Library/Android/sdk/platform-tools/adb shell am start -n com.manursan.buscadortrenes/.MainActivity
```

(`~/Library/Android/sdk/emulator/emulator -list-avds` para ver los AVD
disponibles.)
