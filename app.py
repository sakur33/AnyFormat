"""
Conversor de Formatos - Interfaz gráfica (PyQt5).
Dos modos:
  1) Lote: carpeta origen -> carpeta destino, filtrando por formato origen.
  2) Único: un archivo -> carpeta destino.
"""
import os
import sys
import traceback
from collections import Counter

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QTabWidget,
    QProgressBar, QTextEdit, QMessageBox, QDialog,
)
from PyQt5.QtGui import (
    QDesktopServices, QIcon, QStandardItem, QStandardItemModel,
)
from PyQt5.QtCore import QUrl

import converters as cv


# ---------------------------------------------------------------------------
# Desplegables agrupados por categoría
# ---------------------------------------------------------------------------
def fill_grouped(combo, groups):
    """Rellena un QComboBox con cabeceras de categoría no seleccionables."""
    model = QStandardItemModel(combo)
    for label, formats in groups:
        header = QStandardItem(label.upper())
        header.setFlags(Qt.NoItemFlags)
        font = header.font()
        font.setBold(True)
        header.setFont(font)
        model.appendRow(header)
        for fmt in formats:
            model.appendRow(QStandardItem(fmt))
    combo.setModel(model)
    # El índice 0 siempre es una cabecera; el primer formato real es el 1.
    combo.setCurrentIndex(1 if model.rowCount() > 1 else -1)


def select_format(combo, fmt):
    """Selecciona un formato en un combo agrupado. True si existía."""
    idx = combo.findText(fmt, Qt.MatchExactly)
    if idx >= 0:
        combo.setCurrentIndex(idx)
        return True
    return False


# ---------------------------------------------------------------------------
# Localización de recursos (funciona en desarrollo y en el .exe onefile)
# ---------------------------------------------------------------------------
def resource_path(rel):
    """Ruta a un recurso, tanto ejecutando con Python como desde el .exe.
    PyInstaller onefile descomprime los datos en sys._MEIPASS."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


APP_ICON = resource_path(os.path.join("assets", "AnyFormat.ico"))


# ---------------------------------------------------------------------------
# Configuración de la donación (homenaje al nagware honesto)
# ---------------------------------------------------------------------------
DONATE_URL = "https://ko-fi.com/free_software_solutions"
NAG_EVERY = 25   # mostrar el recordatorio cada N conversiones acumuladas


class NagDialog(QDialog):
    """Recordatorio de donación: aparece, hace el chiste, se cierra solo.
    Nunca bloquea ninguna función de la app. Ese es justo el punto."""

    def __init__(self, total_conversions, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Recordatorio")
        self.setModal(False)  # NO modal: no bloquea nada
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        title = QLabel(f"Llevas {total_conversions} conversiones.")
        title.setStyleSheet("font-size:16px;font-weight:700;")
        layout.addWidget(title)

        body = QLabel(
            "El otro conversor te habría recordado comprar la licencia unas "
            f"{total_conversions} veces.\n\n"
            "Nosotros, una. Esta. Y se cierra sola.\n\n"
            "AnyFormat seguirá siendo gratis, dones o no."
        )
        body.setWordWrap(True)
        layout.addWidget(body)

        btns = QHBoxLayout()
        donate = QPushButton("Vale, invito al café")
        donate.clicked.connect(self._open_donate)
        later = QPushButton("Ahora no, gracias")
        later.clicked.connect(self.accept)
        btns.addWidget(donate)
        btns.addWidget(later)
        layout.addLayout(btns)

    def _open_donate(self):
        QDesktopServices.openUrl(QUrl(DONATE_URL))
        self.accept()


# ---------------------------------------------------------------------------
# Hilo de trabajo para no bloquear la UI durante la conversión
# ---------------------------------------------------------------------------
class WorkerThread(QThread):
    progress = pyqtSignal(int, int)       # (hechos, total)
    log = pyqtSignal(str)
    finished_all = pyqtSignal(int, int)   # (ok, fallos)

    def __init__(self, jobs):
        super().__init__()
        # jobs: lista de tuplas (src, dst, src_fmt, dst_fmt)
        self.jobs = jobs

    def run(self):
        ok = fallos = 0
        total = len(self.jobs)
        for i, (src, dst, sf, df) in enumerate(self.jobs, 1):
            name = os.path.basename(src)
            try:
                os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
                cv.convert_file(src, dst, sf, df)
                ok += 1
                self.log.emit(f"✓ {name} -> {os.path.basename(dst)}")
            except Exception as e:
                fallos += 1
                self.log.emit(f"✗ {name}: {e}")
            self.progress.emit(i, total)
        self.finished_all.emit(ok, fallos)


# ---------------------------------------------------------------------------
# Ventana principal
# ---------------------------------------------------------------------------
class ConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.settings = QSettings("AnyFormat", "Converter")
        self.total_conversions = int(self.settings.value("total_conversions", 0))
        self.setWindowTitle("AnyFormat — gratis para siempre")
        if os.path.exists(APP_ICON):
            self.setWindowIcon(QIcon(APP_ICON))
        self.setMinimumSize(640, 560)
        self._build_ui()

    # -- Construcción de la interfaz ---------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_batch_tab(), "Modo lote (carpeta)")
        tabs.addTab(self._build_single_tab(), "Modo único (archivo)")
        root.addWidget(tabs)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        root.addWidget(self.progress)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Registro de conversiones...")
        root.addWidget(self.console)

        # Barra inferior: lema + botón de donar discreto (sin presión)
        bottom = QHBoxLayout()
        tagline = QLabel("Gratis para siempre. Sin cuenta, sin trucos.")
        tagline.setStyleSheet("color:#777;font-size:12px;")
        bottom.addWidget(tagline)
        bottom.addStretch()
        donate_btn = QPushButton("☕ Donar un café")
        donate_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        bottom.addWidget(donate_btn)
        root.addLayout(bottom)

    # -- Pestaña 1: lote por carpeta ---------------------------------------
    def _build_batch_tab(self):
        w = QWidget()
        g = QGridLayout(w)

        self.b_src_fmt = QComboBox()
        fill_grouped(self.b_src_fmt, cv.all_formats_by_category())
        self.b_src_fmt.currentTextChanged.connect(self._update_batch_targets)

        self.b_dst_fmt = QComboBox()

        self.b_src_dir = QLineEdit()
        self.b_src_dir.textChanged.connect(self._detect_batch_format)
        self.b_dst_dir = QLineEdit()

        g.addWidget(QLabel("Formato origen:"), 0, 0)
        g.addWidget(self.b_src_fmt, 0, 1)
        g.addWidget(QLabel("Formato destino:"), 1, 0)
        g.addWidget(self.b_dst_fmt, 1, 1)

        g.addWidget(QLabel("Carpeta origen:"), 2, 0)
        g.addWidget(self.b_src_dir, 2, 1)
        b1 = QPushButton("Examinar...")
        b1.clicked.connect(lambda: self._pick_dir(self.b_src_dir))
        g.addWidget(b1, 2, 2)

        g.addWidget(QLabel("Carpeta destino:"), 3, 0)
        g.addWidget(self.b_dst_dir, 3, 1)
        b2 = QPushButton("Examinar...")
        b2.clicked.connect(lambda: self._pick_dir(self.b_dst_dir))
        g.addWidget(b2, 3, 2)

        run = QPushButton("Convertir carpeta")
        run.clicked.connect(self._run_batch)
        g.addWidget(run, 4, 0, 1, 3)

        self._update_batch_targets(self.b_src_fmt.currentText())
        return w

    # -- Pestaña 2: archivo único ------------------------------------------
    def _build_single_tab(self):
        w = QWidget()
        g = QGridLayout(w)

        self.s_src_file = QLineEdit()
        self.s_src_file.textChanged.connect(self._detect_single_format)
        self.s_detected = QLabel("—")
        self.s_detected.setStyleSheet("color:#777;")
        self.s_dst_fmt = QComboBox()
        self.s_dst_dir = QLineEdit()

        g.addWidget(QLabel("Archivo origen:"), 0, 0)
        g.addWidget(self.s_src_file, 0, 1)
        bf = QPushButton("Examinar...")
        bf.clicked.connect(self._pick_file)
        g.addWidget(bf, 0, 2)

        g.addWidget(QLabel("Formato detectado:"), 1, 0)
        g.addWidget(self.s_detected, 1, 1)

        g.addWidget(QLabel("Formato destino:"), 2, 0)
        g.addWidget(self.s_dst_fmt, 2, 1)

        g.addWidget(QLabel("Carpeta destino:"), 3, 0)
        g.addWidget(self.s_dst_dir, 3, 1)
        bd = QPushButton("Examinar...")
        bd.clicked.connect(lambda: self._pick_dir(self.s_dst_dir))
        g.addWidget(bd, 3, 2)

        run = QPushButton("Convertir archivo")
        run.clicked.connect(self._run_single)
        g.addWidget(run, 4, 0, 1, 3)
        return w

    # -- Helpers de UI -----------------------------------------------------
    def _update_batch_targets(self, src_fmt):
        fill_grouped(self.b_dst_fmt, cv.targets_by_category(src_fmt))

    def _detect_batch_format(self, src_dir):
        """Elige como formato origen el más frecuente entre los archivos
        soportados de la carpeta. El usuario siempre puede cambiarlo."""
        if not os.path.isdir(src_dir):
            return
        try:
            names = os.listdir(src_dir)
        except OSError:
            return
        counts = Counter(
            fmt for fmt in (cv.detect_format(n) for n in names) if fmt
        )
        if counts:
            select_format(self.b_src_fmt, counts.most_common(1)[0][0])

    def _pick_dir(self, line_edit):
        d = QFileDialog.getExistingDirectory(self, "Selecciona carpeta")
        if d:
            line_edit.setText(d)

    def _pick_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Selecciona archivo")
        if f:
            self.s_src_file.setText(f)

    def _detect_single_format(self, path):
        fmt = cv.detect_format(path)
        if not path.strip():
            self.s_detected.setText("—")
            self.s_detected.setStyleSheet("color:#777;")
        elif fmt:
            self.s_detected.setText(fmt)
            self.s_detected.setStyleSheet("color:#2e7d32;font-weight:600;")
        else:
            ext = os.path.splitext(path)[1].lstrip(".").lower()
            self.s_detected.setText(f"{ext or 'sin extensión'} — no soportado")
            self.s_detected.setStyleSheet("color:#c62828;")
        fill_grouped(self.s_dst_fmt, cv.targets_by_category(fmt) if fmt else [])

    def _log(self, msg):
        self.console.append(msg)

    def _busy(self, busy):
        self.setEnabled(not busy)

    # -- Lanzar modo lote --------------------------------------------------
    def _run_batch(self):
        src_fmt = self.b_src_fmt.currentText()
        dst_fmt = self.b_dst_fmt.currentText()
        src_dir = self.b_src_dir.text().strip()
        dst_dir = self.b_dst_dir.text().strip()

        if not (src_dir and dst_dir and dst_fmt):
            QMessageBox.warning(self, "Faltan datos",
                                "Completa formatos y carpetas.")
            return
        if not os.path.isdir(src_dir):
            QMessageBox.warning(self, "Error", "La carpeta origen no existe.")
            return

        files = [
            os.path.join(src_dir, f) for f in os.listdir(src_dir)
            if f.lower().endswith("." + src_fmt)
        ]
        if not files:
            QMessageBox.information(self, "Sin archivos",
                                    f"No hay archivos .{src_fmt} en la carpeta.")
            return

        jobs = []
        for src in files:
            base = os.path.splitext(os.path.basename(src))[0]
            dst = os.path.join(dst_dir, f"{base}.{dst_fmt}")
            jobs.append((src, dst, src_fmt, dst_fmt))

        self._start(jobs)

    # -- Lanzar modo único -------------------------------------------------
    def _run_single(self):
        src = self.s_src_file.text().strip()
        dst_fmt = self.s_dst_fmt.currentText()
        dst_dir = self.s_dst_dir.text().strip()

        if not src:
            QMessageBox.warning(self, "Faltan datos", "Selecciona un archivo.")
            return
        if not os.path.isfile(src):
            QMessageBox.warning(self, "Error", "El archivo origen no existe.")
            return

        src_fmt = cv.detect_format(src)
        if not src_fmt:
            QMessageBox.warning(self, "Formato no soportado",
                                "No se reconoce la extensión del archivo.")
            return
        if not (dst_fmt and dst_dir):
            QMessageBox.warning(self, "Faltan datos",
                                "Completa formato destino y carpeta.")
            return

        base = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(dst_dir, f"{base}.{dst_fmt}")
        self._start([(src, dst, src_fmt, dst_fmt)])

    # -- Arranque del hilo -------------------------------------------------
    def _start(self, jobs):
        self.console.clear()
        self.progress.setValue(0)
        self._busy(True)
        self.worker = WorkerThread(jobs)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._log)
        self.worker.finished_all.connect(self._on_done)
        self.worker.start()

    def _on_progress(self, done, total):
        self.progress.setMaximum(total)
        self.progress.setValue(done)

    def _on_done(self, ok, fallos):
        self._busy(False)
        self._log(f"\nTerminado: {ok} correctos, {fallos} fallidos.")

        # Actualiza el contador persistente con las conversiones exitosas
        prev = self.total_conversions
        self.total_conversions += ok
        self.settings.setValue("total_conversions", self.total_conversions)

        # ¿Cruzamos un múltiplo de NAG_EVERY en este lote? Mostrar recordatorio.
        crossed = (prev // NAG_EVERY) != (self.total_conversions // NAG_EVERY)
        if ok > 0 and crossed:
            QMessageBox.information(self, "Hecho",
                                    f"{ok} correctos, {fallos} fallidos.")
            QTimer.singleShot(300, self._show_nag)
        else:
            QMessageBox.information(self, "Hecho",
                                    f"{ok} correctos, {fallos} fallidos.")

    def _show_nag(self):
        dlg = NagDialog(self.total_conversions, self)
        dlg.show()  # show() no bloquea; exec_() bloquearía. Usamos show a propósito.


def main():
    app = QApplication(sys.argv)
    if os.path.exists(APP_ICON):
        app.setWindowIcon(QIcon(APP_ICON))
    win = ConverterApp()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
