# AnyFormat

**El conversor de archivos que nunca te pedirá la licencia. Gratis para siempre. (Sí, en serio.)**

<!--
  El bloque entre site:start y site:end es la única parte de este README que se
  publica en https://usefulapps.dev/apps/anyformat. Está en inglés porque el sitio
  lo está. Todo lo de fuera (build, desarrollo, notas) se queda en el repo.
  Si borras los marcadores, el build del sitio falla a propósito.
-->

<!-- site:start -->

A Windows desktop app for converting files, one at a time or by the batch. No
installer, no registration, no account. A single self-contained `.exe`.

It is a tribute to the most honest software in the world: that converter you have
been using for fifteen years on a "40-day trial" that never actually expired. We
owe it everything. We changed exactly one thing — we do not insist.

## The model

- **Free for real.** No trial, no clock, no locked feature.
- **Nothing to sign up for.** No registration, no profile, no licence key. If the
  app saved you a bad afternoon, there is a button to buy a coffee. That is the
  whole business model.
- **One reminder.** Every 25 conversions a notice appears, makes the joke, and
  closes itself. It never blocks anything.

## Modes

**Batch mode** — pick a source format, a target format, an input folder and an
output folder. It converts everything of that source format in the folder.

**Single-file mode** — pick one file, a target format, and where to put it.

## Formats

| | |
| --- | --- |
| **Images** | png, jpg, jpeg, bmp, gif, tiff, webp, ico, **heic, heif, avif** |
| **Vector** | **svg** (source only — it gets rasterised) |
| **Documents** | pdf, docx, txt, html, md |
| **Audio** | mp3, wav, ogg, flac, aac, m4a |
| **Video** | mp4, avi, mkv, mov, webm, gif |
| **Data** | csv, xlsx, json, tsv |

It also crosses between categories: image or SVG to PDF, PDF to image (first page),
SVG to any raster format, video to a frame or a GIF, and video to audio.

The app only ever offers you the targets that make sense for the source you picked.

Two notes on the modern web formats. **HEIC/HEIF** is what your iPhone shoots, and
AnyFormat both reads and writes it. **SVG** is source-only: turning a bitmap into a
vector is not a conversion, so it is not offered as a target.

## Requirements

Windows 10 or 11. Nothing else — no runtime to install, no Python on your machine.
The `.exe` bundles its own ffmpeg.

<!-- site:end -->

---

## Configurar la donación

En `app.py`, arriba del todo:

```python
DONATE_URL = "https://ko-fi.com/free_software_solutions"   # tu enlace de Ko-fi / PayPal / Stripe
NAG_EVERY = 25                               # cada cuántas conversiones recordar
```

## La landing

La página de producto vive ahora en [usefulapps.dev](https://usefulapps.dev/apps/anyformat),
que toma su texto del bloque marcado de arriba. `landing.html` se conserva como
la maqueta original de la que salió la estética del sitio.

## Construir el .exe (en Windows)

Doble clic en `build.bat`, o desde una terminal:

```bat
build.bat
```

El resultado queda en `dist\AnyFormat.exe`. Es autónomo: incluye el binario de
ffmpeg, así que no requiere nada instalado en la máquina destino.

> Al publicar un release en GitHub, el asset debe casar con el `assetPattern`
> declarado en `UsefulApps/src/content/apps/anyformat.md`. Si renombras el `.exe`,
> el build del sitio falla antes que publicar un botón de descarga muerto.

## Construir el .dmg (en macOS)

La compilación se hace en un Mac; el repo ya trae todo lo necesario. Desde una
terminal en el Mac:

```bash
brew install cairo        # cairosvg lo carga en tiempo de ejecución
./build_mac.sh
```

El resultado es `dist/AnyFormat.app` y, si firmas, `dist/AnyFormat-<arch>.dmg`
(con el alias de `/Applications` para instalar arrastrando). El `.app` es
*onedir*: no se descomprime en cada arranque, a diferencia del `.exe onefile` de
Windows.

### Arquitecturas (Intel y Apple Silicon)

Por defecto `build_mac.sh` compila para la CPU del Mac que lo ejecuta. La
variable `TARGET_ARCH` cambia el destino:

```bash
TARGET_ARCH=arm64  ./build_mac.sh     # Apple Silicon  -> AnyFormat-arm64.dmg
TARGET_ARCH=x86_64 ./build_mac.sh     # Intel          -> AnyFormat-x86_64.dmg
```

Para cubrir ambas familias, lo fiable es **un DMG por arquitectura**, cada uno
compilado en su toolchain (el `x86_64` en un Intel o bajo Rosetta con un Python y
un Homebrew x86_64). Un build `x86_64` también corre en Apple Silicon vía Rosetta;
uno `arm64` **no** corre en Intel.

`TARGET_ARCH=universal2` existe, pero un binario *fat* exige que Python **y todas
las dependencias binarias** traigan ambos slices. El `libcairo` de Homebrew y el
`ffmpeg` de `imageio-ffmpeg` son *thin*, así que PyInstaller aborta salvo que las
hagas *universal2* a mano (lipo). Por eso el camino recomendado es el DMG por
arquitectura, no `universal2`.

Piezas del empaquetado macOS:

- **`AnyFormat-mac.spec`** — spec de PyInstaller. Genera un `.app`, usa el icono
  `.icns`, desactiva UPX (rompería la firma) y añade `libcairo` a mano.
- **`make_icns.py`** — genera `assets/AnyFormat.icns` desde `assets/logo.svg`.
- **`rthook_cairo.py`** — hace que `cairocffi` encuentre el `libcairo` embebido
  dentro del bundle (lo abre por nombre en tiempo de ejecución).
- **`entitlements.plist`** — permisos del *hardened runtime*, obligatorios para
  notarizar una app de PyInstaller.

### Firma y notarización (opcional)

Sin firmar, el `.dmg` funciona en tu Mac pero Gatekeeper lo bloquea en otras.
Para distribuirlo, define antes de ejecutar `build_mac.sh`:

```bash
export DEV_ID_APP="Developer ID Application: Tu Nombre (TEAMID)"
export NOTARY_PROFILE="AnyFormat"
```

El perfil de notarización se crea **una sola vez** con una *app-specific
password* de [appleid.apple.com](https://appleid.apple.com) (no tu contraseña de
Apple ID):

```bash
xcrun notarytool store-credentials "AnyFormat" \
  --apple-id "tu@email.com" --team-id "TEAMID" \
  --password "clave-especifica-de-app"
```

Ambas variables son opcionales e independientes: sin `DEV_ID_APP` el script salta
firma y notarización; con firma pero sin `NOTARY_PROFILE`, firma sin notarizar.

## Ejecutar en desarrollo

```bash
pip install -r requirements.txt
python app.py 
```

## Notas

- Audio y video usan el ffmpeg embebido en `imageio-ffmpeg`.
- pdf → imagen y pdf → texto usan PyMuPDF.
- El primer arranque del `.exe onefile` tarda unos segundos (se descomprime en temp).
- **SVG en Windows**: `cairosvg` necesita las librerías de Cairo (GTK). El
  empaquetado las incluye, pero si compilas y svg falla, instala
  [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
  antes de ejecutar `build.bat`. El resto de formatos no requieren nada extra. 
