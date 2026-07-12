# -*- mode: python ; coding: utf-8 -*-
"""
Spec de PyInstaller para macOS. Produce dist/AnyFormat.app (onedir).

Diferencias frente a AnyFormat.spec (Windows):
  - onedir en vez de onefile: un .app onefile se descomprime en cada arranque
    (aquí son ~130 MB) y complica la firma.
  - icono .icns, que es lo unico que macOS entiende.
  - upx desactivado: comprimir los binarios invalida la firma de codesign.
  - libcairo se añade a mano. cairocffi lo carga por nombre en tiempo de
    ejecucion, asi que PyInstaller no puede descubrirlo solo (ver rthook_cairo.py).
"""
import glob
import os
import subprocess

from PyInstaller.utils.hooks import collect_all


def find_libcairo():
    """Ruta al libcairo de Homebrew. Sus dependencias (pixman, freetype,
    fontconfig, libpng) las arrastra PyInstaller al analizar el dylib."""
    candidates = []

    try:
        prefix = subprocess.check_output(
            ["brew", "--prefix", "cairo"], text=True
        ).strip()
        candidates.append(os.path.join(prefix, "lib", "libcairo.2.dylib"))
    except Exception:
        pass  # sin brew en el PATH: probamos rutas conocidas

    candidates += [
        "/opt/homebrew/lib/libcairo.2.dylib",   # Apple Silicon
        "/usr/local/lib/libcairo.2.dylib",      # Intel
    ]
    candidates += glob.glob("/opt/homebrew/Cellar/cairo/*/lib/libcairo.2.dylib")

    for path in candidates:
        if os.path.exists(path):
            return path

    raise SystemExit(
        "No encuentro libcairo.2.dylib. Instalalo con:  brew install cairo\n"
        "Sin el, la conversion de SVG falla en el .app aunque el build pase."
    )


# El .icns es el icono del bundle (Dock, Finder). El .ico lo carga app.py en
# tiempo de ejecucion para el icono de la ventana (Qt lee ICO en cualquier SO).
datas = [
    (os.path.join('assets', 'AnyFormat.icns'), 'assets'),
    (os.path.join('assets', 'AnyFormat.ico'), 'assets'),
]
binaries = [(find_libcairo(), '.')]
hiddenimports = []

for pkg in ('imageio_ffmpeg', 'fitz', 'pillow_heif', 'cairosvg', 'cairocffi'):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['rthook_cairo.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Arquitectura de destino. Sin TARGET_ARCH (o "native") se usa la de la maquina
# que compila. build_mac.sh puede fijar arm64, x86_64 o universal2.
#   universal2 exige que Python Y TODAS las dependencias binarias traigan ambos
#   slices. El libcairo de Homebrew y el ffmpeg de imageio-ffmpeg son thin, asi
#   que universal2 aborta aqui salvo que las hayas hecho fat a mano. Lo fiable
#   es compilar un DMG por arquitectura. Ver README.
target_arch = os.environ.get("TARGET_ARCH") or None
if target_arch == "native":
    target_arch = None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AnyFormat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,   # None = arquitectura de la maquina que compila
    codesign_identity=None,    # la firma la hace build_mac.sh
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AnyFormat',
)

app = BUNDLE(
    coll,
    name='AnyFormat.app',
    icon=os.path.join('assets', 'AnyFormat.icns'),
    bundle_identifier='com.freesoftwaresolutions.anyformat',
    info_plist={
        'CFBundleName': 'AnyFormat',
        'CFBundleDisplayName': 'AnyFormat',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Gratis para siempre. Sin cuenta, sin trucos.',
    },
)
