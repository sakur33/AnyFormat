# AnyFormat

**El conversor de archivos que nunca te pedirá la licencia. Gratis para siempre. (Sí, en serio.)**

<!--
  El bloque entre site:start y site:end es la única parte de este README que se
  publica en https://usefulapps.dev/apps/anyformat. Está en inglés porque el sitio
  lo está. Todo lo de fuera (build, desarrollo, notas) se queda en el repo.
  Si borras los marcadores, el build del sitio falla a propósito.
-->

<!-- site:start -->

AnyFormat is a **free, offline file converter for Windows and macOS**. It converts
images, audio, video, documents and data files right on your own computer — no
upload, no registration, no account, no licence key. Everything it needs is inside
the download.

## What it does

AnyFormat turns one file format into another **without sending anything to the
cloud**. Convert HEIC to JPG the moment you copy photos off an iPhone, WebM to MP4
so a clip plays anywhere, PNG to WebP to shrink a page, a folder of TIFFs to PDF,
or the audio track out of a video into MP3 — all locally, in seconds. Because the
conversion runs on your machine, your files never leave it: there is nothing to
upload and nothing waiting on a stranger's server.

It handles both the everyday formats and the awkward modern ones. **HEIC and HEIF**
(what your iPhone shoots) are read *and* written, not just imported. It reaches
across categories too — image or SVG to PDF, PDF to image, a video to a single
frame or a looping GIF, a video to just its audio. And it works on whole folders,
so converting three hundred files is the same two clicks as converting one.

## Modes

**Batch mode** — pick a source format, a target format, an input folder and an
output folder. It converts everything of that source format in the folder.

**Single-file mode** — pick one file, a target format, and where to put it.

## Supported formats

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

## Why not just use an online converter?

Sites like CloudConvert and Zamzar are fine for one quick file. The catch is what
you give up: you **upload your files to someone else's server**, and the free tier
runs out fast.

| | AnyFormat | Online converters |
| --- | --- | --- |
| Your files | Stay on your PC, never uploaded | Uploaded to their server |
| Account | None | Often required past a few files |
| Free tier | Everything, forever | Daily / size caps, then paid |
| File size limit | None | Common on free plans |
| Watermark | Never | Sometimes on media |
| Works offline | Yes | No — needs a connection |
| Cost | Free | Subscription for regular use |

If the files are private — a scan of your passport, a client's video, family
photos — "it never leaves my computer" is not a nice-to-have. That is the whole
reason AnyFormat exists as an app you install rather than a website you visit.

## The model

- **Free for real.** No trial, no clock, no locked feature.
- **Nothing to sign up for.** No registration, no profile, no licence key. If the
  app saved you a bad afternoon, there is a button to buy a coffee. That is the
  whole business model.
- **One reminder.** Every 25 conversions a notice appears, makes the joke, and
  closes itself. It never blocks anything.

It is a tribute to the most honest software in the world: that converter you have
been using for fifteen years on a "40-day trial" that never actually expired. We
owe it everything. We changed exactly one thing — we do not insist.

## Download

**Windows 10 or 11.** Two ways, same app:

- `AnyFormat.exe` — a single portable file. Download it, double-click it, done.
  Nothing gets installed.
- `AnyFormat-<version>.msi` — a normal installer, if you would rather have a Start
  Menu entry and a clean uninstall.

**macOS 11 Big Sur or later.** `AnyFormat-<arch>.dmg`, signed and notarised: open
it and drag the app into Applications. Take `arm64` for Apple Silicon and `x86_64`
for Intel Macs.

No runtime to install and no Python on your machine either way — the download
bundles its own ffmpeg.

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

## Construir en Windows

Hay **dos artefactos** y cada uno sale de un empaquetado distinto. Son
independientes: puedes construir solo uno.

### El `.exe` portable (onefile)

Doble clic en `build.bat`, o desde una terminal:

```bat
build.bat
```

`build.bat` no usa el `.spec`: pasa los flags a PyInstaller a mano, entre ellos
`--onefile`. El resultado queda en `dist\AnyFormat.exe`, autónomo (incluye ffmpeg)
y sin nada que instalar en la máquina destino.

### El `.msi` (onedir + WiX)

El MSI necesita una carpeta, no un archivo único, así que aquí **sí** se usa
`AnyFormat.spec`, que está en modo *onedir* (`EXE` + `COLLECT`). Con
[WiX v4+](https://wixtoolset.org/) instalado (`dotnet tool install --global wix`):

```bat
pyinstaller --noconfirm --clean AnyFormat.spec
wix build AnyFormat.wxs -arch x64 -o dist\AnyFormat-1.0.0.msi
```

El primer comando deja `dist\AnyFormat\` (exe + `_internal\`); `AnyFormat.wxs`
harvestea esa carpeta entera con `<Files Include="dist\AnyFormat\**" />`, instala
en *Archivos de programa* (perMachine), crea acceso directo en el menú Inicio y se
desinstala limpio.

El `UpgradeCode` del `.wxs` debe permanecer **fijo** entre versiones para que un
MSI nuevo reemplace al viejo en vez de instalarse en paralelo. Al sacar versión se
sube solo `Version` (y el nombre del `-o`).

> Al publicar un release en GitHub, el nombre del asset debe casar con el
> `assetPattern` declarado en `UsefulApps/src/content/apps/anyformat.md`. Si
> renombras el `.exe` o el `.msi`, el build del sitio falla antes que publicar un
> botón de descarga muerto.

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

## Publicar el release

Los binarios se compilan en su propia máquina (el `.exe` y el `.msi` en Windows,
el `.dmg` en el Mac) y se suben todos al **mismo release**. La versión del release
es la de la app, no la del sistema operativo: un único `v1.0.0` con los tres
assets colgando.

Con el [GitHub CLI](https://cli.github.com/):

```bash
gh release upload v1.0.0 dist/AnyFormat.exe
gh release upload v1.0.0 dist/AnyFormat-1.0.0.msi
gh release upload v1.0.0 dist/AnyFormat-arm64.dmg
```

Añade `--clobber` para reemplazar un asset que ya exista con ese nombre.

> El nombre del asset debe casar con el `assetPattern` de
> `UsefulApps/src/content/apps/anyformat.md`. Si lo renombras, el build del sitio
> falla antes que publicar un botón de descarga muerto.

### `gh` no se encuentra en la terminal de VS Code

El instalador de `gh` añade `C:\Program Files\GitHub CLI\` al PATH del sistema,
pero **un proceso solo lee el PATH al arrancar**. Si VS Code estaba abierto cuando
instalaste `gh`, su terminal integrada hereda el PATH viejo — sin `gh` — mientras
que una PowerShell nueva lo encuentra sin problema. No es cosa de la shell: es un
entorno rancio.

La solución es **reiniciar VS Code** (cerrarlo del todo, no solo la terminal).
Para salir del paso sin reiniciar, llama al binario por su ruta completa:

```bash
"/c/Program Files/GitHub CLI/gh.exe" release list     # Git Bash
& "C:\Program Files\GitHub CLI\gh.exe" release list   # PowerShell
```

## Ejecutar en desarrollo

Igual en Windows y en macOS:

```bash
pip install -r requirements.txt
python app.py
```

En macOS, además, `brew install cairo` (`cairosvg` lo carga en tiempo de
ejecución; el bundle lo lleva dentro, pero en desarrollo no).

## Notas

- Audio y video usan el ffmpeg embebido en `imageio-ffmpeg`, en las dos
  plataformas.
- pdf → imagen y pdf → texto usan PyMuPDF.
- El `.exe` portable es *onefile*: el primer arranque tarda unos segundos porque se
  descomprime en temp. El `.app` de macOS y el MSI son *onedir* y no pagan ese
  peaje.
- **SVG en Windows**: `cairosvg` necesita las librerías de Cairo (GTK). El
  empaquetado las incluye, pero si compilas y svg falla, instala el
  [GTK3 runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
  antes de construir. El resto de formatos no requieren nada extra.
- **SVG en macOS**: lo resuelve `rthook_cairo.py`, que apunta a `cairocffi` al
  `libcairo` embebido en el bundle. El resto de formatos, tampoco requieren nada.
