"""
Genera assets/AnyFormat.ico (multi-resolución) a partir de assets/logo.svg.

Se ejecuta en build.bat antes de PyInstaller para embeber el icono en el .exe.
Usa cairosvg (rasteriza el SVG) + Pillow (empaqueta el .ico). Ambos ya son
dependencias del proyecto.

Si cairosvg no está disponible (p. ej. Cairo/GTK no instalado), cae a un dibujo
de respaldo hecho directamente con Pillow para no romper el build.
"""
import io
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SVG = os.path.join(HERE, "assets", "logo.svg")
ICO = os.path.join(HERE, "assets", "AnyFormat.ico")

# Tamaños estándar para un icono de Windows nítido a cualquier escala.
SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_with_cairosvg(size):
    import cairosvg
    png_bytes = cairosvg.svg2png(
        url=SVG, output_width=size, output_height=size
    )
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def render_fallback(size):
    """Respaldo: badge con gradiente aproximado y doble flecha, dibujado a mano."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    r = int(s * 0.20)
    # Fondo (color sólido aproximando el gradiente del SVG)
    d.rounded_rectangle([s * 0.06, s * 0.06, s * 0.94, s * 0.94],
                        radius=r, fill=(59, 130, 246, 255))

    def arrow(y, head_right, opacity):
        col = (255, 255, 255, opacity)
        x0, x1 = s * 0.27, s * 0.73
        h = s * 0.085          # mitad del grosor del cuerpo
        head = s * 0.13        # largo de la punta
        if head_right:
            d.rectangle([x0, y - h, x1 - head, y + h], fill=col)
            d.polygon([(x1 - head, y - head), (x1, y), (x1 - head, y + head)],
                      fill=col)
        else:
            d.rectangle([x0 + head, y - h, x1, y + h], fill=col)
            d.polygon([(x0 + head, y - head), (x0, y), (x0 + head, y + head)],
                      fill=col)

    arrow(s * 0.40, head_right=True, opacity=255)
    arrow(s * 0.62, head_right=False, opacity=230)
    return img


def main():
    os.makedirs(os.path.dirname(ICO), exist_ok=True)
    try:
        render = render_with_cairosvg
        render(32)  # prueba temprana
        print("[make_icon] Usando cairosvg para rasterizar el SVG.")
    except Exception as e:
        render = render_fallback
        print(f"[make_icon] cairosvg no disponible ({e}). Uso respaldo Pillow.")

    base = render(256)
    images = [render(sz) for sz in SIZES]
    base.save(ICO, format="ICO", sizes=[(i.width, i.height) for i in images])
    print(f"[make_icon] Icono escrito en: {ICO}")


if __name__ == "__main__":
    main()
