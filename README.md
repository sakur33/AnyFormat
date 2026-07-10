# AnyFormat

**El conversor de archivos que nunca te pedirá la licencia. Gratis para siempre. (Sí, en serio.)**

Aplicación de escritorio (Windows) para convertir archivos por lotes o de uno en
uno. Sin instalación, sin registro, sin cuenta. Un único `.exe` autónomo.

Inspirado en el software más honesto del mundo: ese conversor/compresor que llevas
15 años usando con su "prueba de 40 días" que nunca caducó. Le debemos todo. Solo
cambiamos una cosa: no insistimos.

## El modelo

- **Gratis de verdad.** Sin prueba, sin reloj, sin función bloqueada.
- **La "cuenta" es bancaria, no de usuario.** No hay registro ni perfil. Si la app
  te ahorró un mal rato, hay un botón para donar un café. Eso es todo.
- **Un solo recordatorio.** Cada 25 conversiones aparece un aviso que hace el
  chiste y se cierra solo. Nunca bloquea nada. Configurable en `app.py`
  (`NAG_EVERY`, `DONATE_URL`).

### Configurar la donación

En `app.py`, arriba del todo:

```python
DONATE_URL = "https://ko-fi.com/free_software_solutions"   # tu enlace de Ko-fi / PayPal / Stripe
NAG_EVERY = 25                               # cada cuántas conversiones recordar
```

### La landing

`landing.html` es la página de producto lista para publicar (estética de diálogo
de instalador retro, con el banner de donación funcionando como demo). Cambia el
IBAN/enlace y súbela a cualquier hosting estático.

---

## Modos

1. **Modo lote**: eliges formato origen, formato destino, carpeta origen y carpeta
   destino. Convierte todos los archivos del formato origen de esa carpeta.
2. **Modo único**: eliges un archivo, formato destino y carpeta destino.

## Formatos soportados

- **Imagen**: png, jpg, jpeg, bmp, gif, tiff, webp, ico, **heic, heif, avif**
- **Vectorial**: **svg** (solo como origen; se rasteriza)
- **Documentos**: pdf, docx, txt, html, md
- **Audio**: mp3, wav, ogg, flac, aac, m4a
- **Video**: mp4, avi, mkv, mov, webm, gif
- **Datos**: csv, xlsx, json, tsv

### Conversiones entre categorías
- imagen / svg → pdf
- pdf → imagen (primera página)
- svg → cualquier imagen raster (png, jpg, webp, heic...)
- video → imagen (frame/gif) y video → audio (extracción)

La aplicación solo ofrece los destinos válidos para cada origen.

### Notas sobre formatos web
- **heic/heif**: formato por defecto de fotos de iPhone. Lectura y escritura.
- **avif**: formato web moderno, lectura y escritura.
- **svg**: solo origen. Convertir un bitmap a SVG no es una conversión real,
  así que no se ofrece como destino.

## Construir el .exe (en Windows)

Doble clic en `build.bat`, o desde una terminal:

```bat
build.bat
```

El resultado queda en `dist\Conversor.exe`. Es autónomo: incluye el binario de
ffmpeg, así que no requiere nada instalado en la máquina destino.

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
