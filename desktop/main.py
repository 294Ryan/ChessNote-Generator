import os
import sys
import ctypes
### Fix Qt plugin lookup on non-ASCII paths (set before importing PyQt5.QtWidgets) ###
import PyQt5
pluginPath = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = pluginPath

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase, QIcon
from ui.main_window import MainWindow
from core.i18n import setLanguage

def loadAppFont(app):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    # Works both frozen and from source
    fontId = QFontDatabase.addApplicationFont(os.path.join(base, "assets", "fonts", "NotoSansTC-Regular.ttf"))
    if fontId == -1:
        return    # Fall back to the system default font if the file is missing
    font = app.font()    # Change the family only; keep the original size
    font.setFamily(QFontDatabase.applicationFontFamilies(fontId)[0])
    app.setFont(font)

def setAppIcon(app):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    # Works both frozen and from source
    app.setWindowIcon(QIcon(os.path.join(base, "assets", "icons", "window_icon.ico")))

def main():
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChessNoteGenerator")    # Keep the taskbar icon separate from python.exe
    app = QApplication(sys.argv)
    setAppIcon(app)    # Used for both the title bar and the taskbar
    loadAppFont(app)
    setLanguage("en")    # Always start in English; the last choice is not remembered
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()