#!/bin/zsh
# Arranca el emulador Android, instala el último buscador_trenes.apk de esta carpeta y abre BuscaTrenes.
SDK="$HOME/Library/Android/sdk"
ADB="$SDK/platform-tools/adb"
AVD="Medium_Phone_API_36.1"
APK="$(dirname "$0")/buscador_trenes.apk"

if ! "$ADB" devices | grep -q "emulator-.*device"; then
  echo "Arrancando el emulador $AVD..."
  nohup "$SDK/emulator/emulator" -avd "$AVD" -no-boot-anim -gpu auto >/dev/null 2>&1 &
  until [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do sleep 2; done
  sleep 3
else
  echo "El emulador ya estaba encendido."
fi

if [ -f "$APK" ]; then
  echo "Instalando $(basename "$APK")..."
  "$ADB" install -r "$APK" | tail -1
fi
"$ADB" shell am start -n com.manursan.buscadortrenes/.MainActivity >/dev/null 2>&1
echo "Listo. Puedes cerrar esta ventana de Terminal."
