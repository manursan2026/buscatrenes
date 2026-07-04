#!/bin/bash
# Construye buscador_trenes.apk sin Gradle, usando directamente las
# herramientas del SDK de Android (aapt2, javac, d8, zipalign, apksigner).
#
# Requiere: Android Studio instalado (SDK en ~/Library/Android/sdk) y el
# buscador_trenes.html generado en el directorio padre.
#
# Uso:  ./build_apk.sh
# Salida: ../buscador_trenes.apk (firmado con la clave debug, lista para
#         instalar por sideload en cualquier Android 7.0+)
set -euo pipefail
cd "$(dirname "$0")"

SDK="$HOME/Library/Android/sdk"
BT="$SDK/build-tools/36.1.0"
PLATFORM="$SDK/platforms/android-35/android.jar"
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
JAVAC="$JAVA_HOME/bin/javac"
OUT="../buscador_trenes.apk"
WORK="build"

rm -rf "$WORK" && mkdir -p "$WORK/classes" "$WORK/assets" "$WORK/res-compiled"

echo "== Asset HTML =="
cp ../buscador_trenes.html "$WORK/assets/"

echo "== Compilando recursos (iconos) =="
"$BT/aapt2" compile --dir res -o "$WORK/res-compiled/res.zip"

echo "== Compilando Java =="
"$JAVAC" -source 11 -target 11 -nowarn -classpath "$PLATFORM" \
    -d "$WORK/classes" MainActivity.java

echo "== DEX =="
"$BT/d8" --release --lib "$PLATFORM" --min-api 24 \
    --output "$WORK" "$WORK/classes/com/manursan/buscadortrenes/"*.class

echo "== Empaquetando =="
"$BT/aapt2" link -o "$WORK/base.apk" -I "$PLATFORM" \
    --manifest AndroidManifest.xml \
    --min-sdk-version 24 --target-sdk-version 35 \
    -A "$WORK/assets" \
    "$WORK/res-compiled/res.zip"
(cd "$WORK" && zip -q -j base.apk classes.dex)

echo "== Alineando y firmando (clave debug) =="
"$BT/zipalign" -f 4 "$WORK/base.apk" "$WORK/aligned.apk"
"$BT/apksigner" sign --ks "$HOME/.android/debug.keystore" \
    --ks-pass pass:android --key-pass pass:android \
    --out "$OUT" "$WORK/aligned.apk"
"$BT/apksigner" verify "$OUT"

rm -rf "$WORK"
echo
ls -lh "$OUT"
echo "APK generado correctamente."
