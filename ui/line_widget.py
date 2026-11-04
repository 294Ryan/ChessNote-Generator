from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QToolButton, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from core.pgn_renderer import resolveImageBytes, checkPgn
from ui.editor_style import INPUT_RADIUS
from ui.theme import palette
from core.i18n import t

PREVIEW_DEBOUNCE_MS = 300    # 停止輸入多久後才重繪棋盤圖
PREVIEW_WIDTH = 280    # 預覽圖寬度（像素）


class PgnImageEditor(QWidget):    # PGN 輸入 + 圖片預覽，圖片三種狀態：自動產生 / 手動上傳 / 刪除（空白）
    changed = pyqtSignal()

    def __init__(self, pgn="", imagePath=None, noImage=False, orientation="white", collapsible=True, getStartingPgn=None):
        super().__init__()
        self.getStartingPgn = getStartingPgn or (lambda: "")    # Line 取得起始 PGN，用來解析「接續寫法」；起始 PGN 本身不需要
        self.imagePath = imagePath    # 手動上傳的圖片路徑，None 代表用自動生成圖
        self.noImage = noImage    # True 代表刻意不放圖片
        self.orientation = orientation    # 自動生成圖的棋盤視角 white / black
        self.collapsible = collapsible
        self.hadImage = False    # 上一次預覽是否有圖，用來判斷「圖片剛出現」時要自動展開

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        p = palette()

        self.previewTimer = QTimer(self)    # debounce：停止輸入後才重繪棋盤圖
        self.previewTimer.setSingleShot(True)
        self.previewTimer.setInterval(PREVIEW_DEBOUNCE_MS)
        self.previewTimer.timeout.connect(self.refreshPreview)

        self.pgnEdit = QPlainTextEdit(pgn)
        self.pgnEdit.setPlaceholderText(t("pgnPlaceholder"))
        self.pgnEdit.setMaximumHeight(76)
        self.pgnEdit.textChanged.connect(self.onFieldChanged)
        layout.addWidget(self.pgnEdit)

        self.errorLabel = QLabel()    # PGN 有誤時顯示在輸入框下方
        self.errorLabel.setWordWrap(True)
        self.errorLabel.setStyleSheet(f"background: transparent; color: {p.danger}; font-size: 12px;")
        self.errorLabel.hide()
        layout.addWidget(self.errorLabel)

        ### 按鈕列：[▼][上傳圖片] ........ [刪除圖片 / 使用預設] ###
        buttonRow = QHBoxLayout()

        self.toggleArrow = QToolButton(self)    # 預覽圖收合箭頭，只有可收合且有圖時才出現
        self.toggleArrow.setText("▶")
        self.toggleArrow.setCheckable(True)
        self.toggleArrow.setStyleSheet(f"border: none; background: transparent; color: {p.inkSoft};")
        self.toggleArrow.toggled.connect(self.onToggled)
        self.toggleArrow.hide()
        if collapsible:
            sizePolicy = self.toggleArrow.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)    # 隱藏時仍佔位，避免圖片出現時按鈕位移
            self.toggleArrow.setSizePolicy(sizePolicy)
            buttonRow.addWidget(self.toggleArrow)

        uploadButton = QPushButton(t("uploadImage"))
        uploadButton.clicked.connect(self.onUploadImage)
        buttonRow.addWidget(uploadButton)

        buttonRow.addStretch()

        self.rightButton = QPushButton()    # 自動圖狀態 → 刪除圖片；上傳或已刪除狀態 → 使用預設
        self.rightButton.clicked.connect(self.onRightClicked)
        buttonRow.addWidget(self.rightButton)
        layout.addLayout(buttonRow)

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setStyleSheet(    # 預覽圖外框，跟輸入框同一套圓角與邊線
            f"background: {p.inputBg}; border: 1px solid {p.inputBorder}; border-radius: {INPUT_RADIUS}px; padding: 6px;"
        )
        layout.addWidget(self.imageLabel, 0, Qt.AlignLeft)    # 靠左，外框貼著圖片大小

        self.updateRightButton()
        self.refreshPreview()

    def isAutoImage(self):
        return self.imagePath is None and not self.noImage

    def onFieldChanged(self):
        self.changed.emit()
        self.previewTimer.start()    # 每次輸入重新計時

    def onToggled(self, checked):
        self.toggleArrow.setText("▼" if checked else "▶")
        self.updatePreviewVisibility()

    def applyImageState(self, expand):    # 圖片狀態變動的共用收尾
        self.updateRightButton()
        self.changed.emit()
        self.refreshPreview(expand)

    def setAutoImage(self):    # 回到自動生成圖並展開
        self.imagePath = None
        self.noImage = False
        self.applyImageState(expand=True)

    def onUploadImage(self):
        path, _ = QFileDialog.getOpenFileName(self, t("pickImage"), "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.imagePath = path
            self.noImage = False
            self.applyImageState(expand=True)

    def onRightClicked(self):
        if self.isAutoImage():    # 刪除圖片
            self.imagePath = None
            self.noImage = True
            self.applyImageState(expand=False)
        else:    # 使用預設
            self.setAutoImage()

    def updateRightButton(self):
        self.rightButton.setText(t("deleteImage") if self.isAutoImage() else t("useDefault"))
        self.rightButton.setProperty("danger", self.isAutoImage())    # 刪除類按鈕滑過時用紅色
        self.rightButton.style().unpolish(self.rightButton)
        self.rightButton.style().polish(self.rightButton)

    def setOrientation(self, orientation):    # 開局視角變更時由外部呼叫
        self.orientation = orientation
        self.refreshPreview()

    def getPgn(self):
        return self.pgnEdit.toPlainText()

    def getImagePath(self):
        return self.imagePath

    def getNoImage(self):
        return self.noImage

    def refreshPgnError(self):
        message = checkPgn(self.getPgn(), self.getStartingPgn())
        self.errorLabel.setText(message or "")
        self.errorLabel.setVisible(bool(message))
        self.pgnEdit.setProperty("invalid", bool(message))    # 讓輸入框邊框變紅
        self.pgnEdit.style().unpolish(self.pgnEdit)
        self.pgnEdit.style().polish(self.pgnEdit)

    def refreshPreview(self, expand=False):    # expand=True 或圖片剛出現時，自動展開預覽
        self.refreshPgnError()
        rawBytes = resolveImageBytes(self.getPgn(), self.imagePath, self.orientation, self.noImage, self.getStartingPgn())
        pixmap = None
        if rawBytes:
            pixmap = QPixmap()
            pixmap.loadFromData(rawBytes)

        hasImage = pixmap is not None and not pixmap.isNull()
        if hasImage:
            self.imageLabel.setPixmap(pixmap.scaledToWidth(PREVIEW_WIDTH, Qt.SmoothTransformation))
        else:
            self.imageLabel.clear()

        wasImage = self.hadImage
        self.hadImage = hasImage
        if self.collapsible and hasImage and (expand or not wasImage):
            self.toggleArrow.setChecked(True)
        self.updatePreviewVisibility()

    def updatePreviewVisibility(self):
        if self.collapsible:
            self.toggleArrow.setVisible(self.hadImage)
        self.imageLabel.setVisible(self.hadImage and (not self.collapsible or self.toggleArrow.isChecked()))