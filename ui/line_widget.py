from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QToolButton, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from core.pgn_renderer import resolveImageBytes

PREVIEW_DEBOUNCE_MS = 300    # 停止輸入多久後才重繪棋盤圖


class CollapsibleImage(QWidget):    # 棋盤圖預覽區，有內容才自動展開（無內容整塊隱藏）
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.toggleButton = QToolButton()
        self.toggleButton.setCheckable(True)
        self.toggleButton.toggled.connect(self.onToggled)
        self.toggleButton.setVisible(False)
        layout.addWidget(self.toggleButton)

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setVisible(False)
        layout.addWidget(self.imageLabel)

    def onToggled(self, checked):
        self.imageLabel.setVisible(checked)
        self.toggleButton.setText("▼ 棋盤預覽" if checked else "▶ 棋盤預覽")

    def setPixmap(self, pixmap):
        hasImage = pixmap is not None and not pixmap.isNull()
        self.toggleButton.setVisible(hasImage)
        if hasImage:
            self.imageLabel.setPixmap(pixmap.scaledToWidth(280, Qt.SmoothTransformation))
            self.toggleButton.setChecked(True)    # 有內容自動展開
        else:
            self.imageLabel.clear()
            self.imageLabel.setVisible(False)


class PgnImageEditor(QWidget):    # PGN 輸入 + 圖片預覽（自動產生或手動上傳覆蓋）
    changed = pyqtSignal()

    def __init__(self, pgn="", imagePath=None, collapsible=True):
        super().__init__()
        self.imagePath = imagePath
        self.collapsible = collapsible

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.previewTimer = QTimer(self)    # debounce：停止輸入後才重繪棋盤圖
        self.previewTimer.setSingleShot(True)
        self.previewTimer.setInterval(PREVIEW_DEBOUNCE_MS)
        self.previewTimer.timeout.connect(self.refreshPreview)

        self.pgnEdit = QPlainTextEdit(pgn)
        self.pgnEdit.setPlaceholderText("輸入 PGN，例如 1. e4 e5 2. Nf3 Nc6")
        self.pgnEdit.setMaximumHeight(70)
        self.pgnEdit.textChanged.connect(self.onFieldChanged)
        layout.addWidget(self.pgnEdit)

        buttonRow = QHBoxLayout()
        uploadButton = QPushButton("上傳圖片覆蓋")
        uploadButton.clicked.connect(self.onUploadImage)
        buttonRow.addWidget(uploadButton)

        self.clearButton = QPushButton("改回自動產生")
        self.clearButton.setVisible(imagePath is not None)
        self.clearButton.clicked.connect(self.onClearOverride)
        buttonRow.addWidget(self.clearButton)
        buttonRow.addStretch()
        layout.addLayout(buttonRow)

        if collapsible:
            self.previewWidget = CollapsibleImage()
        else:
            self.previewWidget = QLabel()
            self.previewWidget.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.previewWidget)

        self.refreshPreview()

    def onFieldChanged(self):
        self.changed.emit()
        self.previewTimer.start()    # 每次輸入重新計時

    def onUploadImage(self):
        path, _ = QFileDialog.getOpenFileName(self, "選擇圖片", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.imagePath = path
            self.clearButton.setVisible(True)
            self.changed.emit()
            self.refreshPreview()

    def onClearOverride(self):
        self.imagePath = None
        self.clearButton.setVisible(False)
        self.changed.emit()
        self.refreshPreview()

    def getPgn(self):
        return self.pgnEdit.toPlainText()

    def getImagePath(self):
        return self.imagePath

    def refreshPreview(self):
        rawBytes = resolveImageBytes(self.getPgn(), self.imagePath)
        pixmap = None
        if rawBytes:
            pixmap = QPixmap()
            pixmap.loadFromData(rawBytes)

        if self.collapsible:
            self.previewWidget.setPixmap(pixmap)
        elif pixmap and not pixmap.isNull():
            self.previewWidget.setPixmap(pixmap.scaledToWidth(280, Qt.SmoothTransformation))
        else:
            self.previewWidget.clear()