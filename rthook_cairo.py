"""
Runtime hook de PyInstaller: hace que cairocffi encuentre el libcairo empaquetado.

cairocffi no enlaza contra libcairo; lo abre en tiempo de ejecución por nombre,
vía ctypes.util.find_library(). Dentro del .app ese nombre no resuelve a nada,
porque el dylib vive en Contents/Frameworks y no en las rutas que busca dyld.

Aquí interceptamos find_library() para que mire primero en el bundle. Si no lo
encuentra, delegamos en la implementación original (útil al ejecutar sin
congelar, donde el dylib está en /opt/homebrew/lib).
"""
import ctypes.util
import os
import sys

# Nombres de fichero candidatos por biblioteca. cairocffi pide "cairo".
_CANDIDATES = {
    "cairo": ["libcairo.2.dylib", "libcairo.dylib"],
}


def _bundle_dirs():
    """Directorios donde PyInstaller deja los binarios dentro del .app."""
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return []
    # En un .app onedir, _MEIPASS es Contents/Frameworks; en onefile, el tmpdir.
    parent = os.path.dirname(meipass)
    return [
        meipass,
        os.path.join(parent, "Frameworks"),
        os.path.join(parent, "MacOS"),
    ]


def _install():
    original = ctypes.util.find_library

    def find_library(name):
        for filename in _CANDIDATES.get(name, [f"lib{name}.dylib"]):
            for directory in _bundle_dirs():
                path = os.path.join(directory, filename)
                if os.path.exists(path):
                    return path
        return original(name)

    ctypes.util.find_library = find_library


if getattr(sys, "frozen", False):
    _install()
