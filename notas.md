Conversor de archivos para Windows. Sin instalación, sin registro, sin cuenta.
Un único `.exe` autónomo: descárgalo y ejecútalo.

Gratis de verdad — sin prueba, sin reloj, sin funciones bloqueadas.

## Descarga

**[AnyFormat.exe](https://github.com/sakur33/AnyFormat/releases/download/v1.0.0/AnyFormat.exe)** (~131 MB)

No requiere nada instalado en la máquina destino: ffmpeg viene embebido.
El primer arranque tarda unos segundos, porque el ejecutable `onefile` se
descomprime en una carpeta temporal.

## Modos

- **Lote** — eliges formato origen, formato destino, carpeta origen y carpeta
  destino; convierte todos los archivos de ese formato en la carpeta.
- **Único** — eliges un archivo, formato destino y carpeta destino.

## Formatos soportados

| Categoría | Formatos |
|---|---|
| Imagen | png, jpg, jpeg, bmp, gif, tiff, webp, ico, heic, heif, avif |
| Vectorial | svg (solo como origen; se rasteriza) |
| Documentos | pdf, docx, txt, html, md |
| Audio | mp3, wav, ogg, flac, aac, m4a |
| Video | mp4, avi, mkv, mov, webm, gif |
| Datos | csv, xlsx, json, tsv |

También convierte entre categorías: imagen o svg → pdf, pdf → imagen (primera
página), svg → cualquier raster, video → imagen (frame/gif) y video → audio.

La aplicación solo ofrece los destinos válidos para cada origen.

## Notas

- **heic/heif** (formato por defecto de las fotos de iPhone) y **avif**: lectura
  y escritura.
- **svg** solo como origen. Convertir un bitmap a SVG no es una conversión real,
  así que no se ofrece como destino.
- Cada 25 conversiones aparece un recordatorio que hace el chiste y se cierra
  solo. Nunca bloquea nada.

Windows puede avisar de que el ejecutable no está firmado (SmartScreen): el
binario no lleva firma de código. Puedes construirlo tú mismo con `build.bat`.
