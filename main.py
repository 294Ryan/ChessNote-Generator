import os
import sys

### 修正中文路徑下 Qt 平台外掛找不到的問題，需在 import PyQt5.QtWidgets 之前設定 ###
import PyQt5
pluginPath = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = pluginPath

from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()