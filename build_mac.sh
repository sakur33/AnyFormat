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

# Envia un artefacto a notarizar y espera el veredicto tolerando cortes de red.
# `notarytool submit --wait` aborta si la conexion se cae a mitad del sondeo
# (nos paso: NSLocalizedDescription=The Internet connection appears to be
# offline). En su lugar enviamos con --no-wait y sondeamos con `info`, que
# reintentamos: un fallo puntual de red no tumba el build.
notarize_wait() {
  local artifact="$1" sub status
  sub="$(xcrun notarytool submit "$artifact" \
           --keychain-profile "$NOTARY_PROFILE" --no-wait 2>&1 \
         | awk '$1=="id:"{print $2; exit}')"
  [[ -n "$sub" ]] || { echo "      No se obtuvo id de envio para $artifact"; return 1; }
  echo "      Envio $sub ($artifact); esperando veredicto de Apple..."
  # 120 sondeos * 15 s = 30 min de margen; la cola de Apple suele tardar minutos.
  for _ in $(seq 1 120); do
    # 2>/dev/null: un corte de red hace fallar `info`; reintentamos sin abortar.
    status="$(xcrun notarytool info "$sub" \
                --keychain-profile "$NOTARY_PROFILE" 2>/dev/null \
              | awk '/status:/{print $2}')"
    case "$status" in
      Accepted) echo "      Notarizacion aceptada."; return 0 ;;
      Invalid|Rejected)
        echo "      Notarizacion RECHAZADA. Registro de Apple:"
        xcrun notarytool log "$sub" --keychain-profile "$NOTARY_PROFILE" 2>&1 | head -60
        return 1 ;;
    esac
    sleep 15
  done
  echo "      Tiempo de espera agotado (30 min) para $sub."
  return 1
}

echo "[6/6] Notarizando (esto tarda unos minutos)..."

# 1) Notariza y grapa el .app para que valide SIN CONEXION cuando el usuario lo
#    arrastre fuera del DMG. Grapar el DMG solo no marca el .app extraido.
ZIP="dist/AnyFormat-notarize.zip"
# ditto preserva los metadatos de firma; `zip` a secas los destruye.
ditto -c -k --keepParent "$APP" "$ZIP"
notarize_wait "$ZIP"
rm -f "$ZIP"
xcrun stapler staple "$APP"
spctl --assess --type exec --verbose=2 "$APP"

echo "      Creando $DMG..."
rm -f "$DMG"
# Monta el .app (ya grapado) junto a un alias de /Applications para que el
# usuario instale arrastrando. hdiutil empaqueta la carpeta entera.
STAGING="$(mktemp -d)"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "AnyFormat" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
rm -rf "$STAGING"

# 2) El propio DMG debe notarizarse para poder graparlo: `stapler` falla con
#    "Record not found" (Error 65) sobre un DMG que Apple nunca ha visto.
#    Notarizar el .app por separado NO registra un ticket para el contenedor.
notarize_wait "$DMG"
xcrun stapler staple "$DMG"

echo
echo "============================================================"
echo " Listo:"
echo "   App: $APP"
echo "   DMG: $DMG   (firmado, notarizado y grapado)"
echo "============================================================"
