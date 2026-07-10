@echo off
REM ============================================================
REM  Construye Conversor.exe (un unico archivo, sin consola)
REM  Requisitos: Python 3.9+ instalado y en el PATH
REM ============================================================

echo [1/3] Creando entorno virtual...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/3] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt

echo [3/4] Generando icono (assets\AnyFormat.ico)...
python make_icon.py

echo [4/4] Empaquetando con PyInstaller...
pyinstaller --noconfirm --clean ^
  --name "AnyFormat" ^
  --windowed ^
  --onefile ^
  --icon "assets\AnyFormat.ico" ^
  --add-data "assets\AnyFormat.ico;assets" ^
  --collect-all imageio_ffmpeg ^
  --collect-all fitz ^
  --collect-all pillow_heif ^
  --collect-all cairosvg ^
  --collect-all cairocffi ^
  app.py

echo.
echo ============================================================
echo  Listo. El ejecutable esta en:  dist\AnyFormat.exe
echo ============================================================
pause
