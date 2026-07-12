#!/usr/bin/env bash
# ============================================================
#  Construye AnyFormat.app (macOS), lo firma y lo notariza.
#
#  Requisitos:
#    - macOS con Command Line Tools  (xcode-select --install)
#    - Homebrew con cairo            (brew install cairo)
#    - Python 3.10+
#
#  Firma y notarizacion (opcionales; si no defines las variables,
#  el script construye un .app sin firmar y te avisa):
#
#    export DEV_ID_APP="Developer ID Application: Tu Nombre (TEAMID)"
#    export NOTARY_PROFILE="AnyFormat"
#
#  El perfil de notarizacion se crea UNA vez con:
#    xcrun notarytool store-credentials "AnyFormat" \
#      --apple-id "tu@email.com" --team-id "TEAMID" \
#      --password "clave-especifica-de-app"
#
#  La contraseña es una app-specific password de appleid.apple.com,
#  NO la de tu Apple ID.
# ============================================================
set -euo pipefail

APP="dist/AnyFormat.app"

cd "$(dirname "$0")"

# -- Comprobaciones previas ----------------------------------------------
[[ "$(uname)" == "Darwin" ]] || { echo "Esto solo corre en macOS."; exit 1; }

# -- Arquitectura de destino ---------------------------------------------
# TARGET_ARCH decide para que CPU se compila. Por defecto, la de este Mac.
# PyInstaller lo lee desde el entorno (ver AnyFormat-mac.spec), asi que basta
# con que la variable llegue heredada. El DMG se nombra por arquitectura para
# no pisar builds de otra CPU.
#
#   native / (sin definir)  -> la arquitectura de esta maquina
#   arm64                   -> Apple Silicon
#   x86_64                  -> Intel (corre tambien en Apple Silicon vía Rosetta)
#   universal2              -> binario fat; SOLO si Python y TODAS las deps
#                              (incluido libcairo) son universal2, si no falla.
case "${TARGET_ARCH:-native}" in
  native|"")   ARCH_LABEL="$(uname -m)" ;;
  arm64)       ARCH_LABEL="arm64" ;;
  x86_64)      ARCH_LABEL="x86_64" ;;
  universal2)  ARCH_LABEL="universal2" ;;
  *) echo "TARGET_ARCH invalido: $TARGET_ARCH (usa native, arm64, x86_64 o universal2)"; exit 1 ;;
esac
DMG="dist/AnyFormat-${ARCH_LABEL}.dmg"
echo "Arquitectura de destino: ${TARGET_ARCH:-native} -> $DMG"

if ! brew list --formula cairo &>/dev/null; then
  echo "Falta cairo. Instalalo con:  brew install cairo"
  echo "cairosvg lo carga en tiempo de ejecucion; sin el, convertir SVG falla."
  exit 1
fi

echo "[1/6] Entorno virtual..."
python3 -m venv venv
source venv/bin/activate

echo "[2/6] Dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/6] Icono (assets/AnyFormat.icns)..."
python make_icns.py

echo "[4/6] Empaquetando con PyInstaller..."
pyinstaller --noconfirm --clean AnyFormat-mac.spec

[[ -d "$APP" ]] || { echo "PyInstaller no genero $APP"; exit 1; }

# -- Firma ---------------------------------------------------------------
# codesign --deep es poco fiable y esta desaconsejado por Apple: firma primero
# cada binario anidado (dylibs, .so, el ffmpeg de imageio) y el bundle al final.
if [[ -z "${DEV_ID_APP:-}" ]]; then
  echo
  echo "[5/6] DEV_ID_APP no definida: me salto firma y notarizacion."
  echo "      El .app funciona en tu Mac, pero Gatekeeper lo bloqueara en otras."
  echo "      Listo: $APP"
  exit 0
fi

echo "[5/6] Firmando binarios anidados..."
# Solo Mach-O: firmar un script de shell o un .txt hace fallar a codesign.
while IFS= read -r -d '' candidate; do
  if file --brief "$candidate" | grep -q 'Mach-O'; then
    codesign --force --timestamp --options runtime \
             --sign "$DEV_ID_APP" "$candidate"
  fi
done < <(find "$APP/Contents" -type f -print0)

echo "      Firmando el bundle..."
codesign --force --timestamp --options runtime \
         --entitlements entitlements.plist \
         --sign "$DEV_ID_APP" "$APP"

codesign --verify --deep --strict --verbose=2 "$APP"

# -- Notarizacion --------------------------------------------------------
if [[ -z "${NOTARY_PROFILE:-}" ]]; then
  echo
  echo "[6/6] NOTARY_PROFILE no definida: firmado pero sin notarizar."
  echo "      Al descargarlo de internet, Gatekeeper aun lo bloqueara."
  echo "      Listo: $APP"
  exit 0
fi

echo "[6/6] Notarizando (esto tarda unos minutos)..."
ZIP="dist/AnyFormat-notarize.zip"
# ditto preserva los metadatos de firma; `zip` a secas los destruye.
ditto -c -k --keepParent "$APP" "$ZIP"
xcrun notarytool submit "$ZIP" --keychain-profile "$NOTARY_PROFILE" --wait
rm -f "$ZIP"

# Grapa el ticket al .app para que valide sin conexion.
xcrun stapler staple "$APP"
spctl --assess --type exec --verbose=2 "$APP"

echo "      Creando $DMG..."
rm -f "$DMG"
# Monta el .app junto a un alias de /Applications para que el usuario instale
# arrastrando. hdiutil empaqueta la carpeta entera, no solo el .app.
STAGING="$(mktemp -d)"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "AnyFormat" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
rm -rf "$STAGING"
xcrun stapler staple "$DMG"

echo
echo "============================================================"
echo " Listo:"
echo "   App: $APP"
echo "   DMG: $DMG   (firmado, notarizado y grapado)"
echo "============================================================"
