import os
import sys

### 修正中文路徑下 Qt 平台外掛找不到的問題，需在 import PyQt5.QtWidgets 之前設定 ###
import PyQt5
pluginPath = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = pluginPath

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase
from ui.main_window import MainWindow

def loadAppFont(app):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))    # 打包後與原始碼兩種環境
    fontId = QFontDatabase.addApplicationFont(os.path.join(base, "assets", "fonts", "NotoSansTC-Regular.ttf"))
    if fontId == -1:
        return    # 找不到字型檔時沿用系統預設
    font = app.font()    # 只換字型家族，保留原本字級
    font.setFamily(QFontDatabase.applicationFontFamilies(fontId)[0])
    app.setFont(font)

def main():
    app = QApplication(sys.argv)
    loadAppFont(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()