"""
Genera assets/AnyFormat.icns (multi-resolución) a partir de assets/logo.svg.

Equivalente macOS de make_icon.py, del que reutiliza los rasterizadores.
Se ejecuta en build_mac.sh antes de PyInstaller.

Ruta principal: construye un .iconset y lo empaqueta con `iconutil`, la
herramienta de Apple (incluida en las Command Line Tools). Si no está
disponible, cae al escritor ICNS de Pillow.
"""
import os
import shutil
import subprocess
import sys
import tempfile

from make_icon import render_with_cairosvg, render_fallback

HERE = os.path.dirname(os.path.abspath(__file__))
ICNS = os.path.join(HERE, "assets", "AnyFormat.icns")

# macOS espera cada tamaño en versión normal y @2x (retina).
# icon_16x16@2x.png tiene 32 px, y así sucesivamente.
ICONSET = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def pick_renderer():
    try:
        render_with_cairosvg(32)  # prueba temprana
        print("[make_icns] Usando cairosvg para rasterizar el SVG.")
        return render_with_cairosvg
    except Exception as e:
        print(f"[make_icns] cairosvg no disponible ({e}). Uso respaldo Pillow.")
        return render_fallback


def build_with_iconutil(render):
    tmp = tempfile.mkdtemp()
    iconset = os.path.join(tmp, "AnyFormat.iconset")
    os.makedirs(iconset)
    try:
        for name, size in ICONSET:
            render(size).save(os.path.join(iconset, name), format="PNG")
        subprocess.run(
            ["iconutil", "-c", "icns", iconset, "-o", ICNS], check=True
        )
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_with_pillow(render):
    """Respaldo: Pillow sabe escribir ICNS directamente."""
    sizes = sorted({size for _, size in ICONSET if size <= 512})
    base = render(1024)
    base.save(ICNS, format="ICNS", sizes=[(s, s) for s in sizes])


def main():
    os.makedirs(os.path.dirname(ICNS), exist_ok=True)
    render = pick_renderer()

    if shutil.which("iconutil"):
        build_with_iconutil(render)
    else:
        print("[make_icns] iconutil no encontrado. Uso el escritor de Pillow.")
        build_with_pillow(render)

    print(f"[make_icns] Icono escrito en: {ICNS}")


if __name__ == "__main__":
    sys.exit(main())
