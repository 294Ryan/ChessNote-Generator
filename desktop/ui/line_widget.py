from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QToolButton, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from core.pgn_renderer import resolveImageBytes, checkPgn
from core.image_utils import loadScaledBase64
from ui.editor_style import INPUT_RADIUS
from ui.theme import palette
from core.i18n import t

PREVIEW_DEBOUNCE_MS = 300    # Delay after typing stops before redrawing the board image
PREVIEW_WIDTH = 280


class PgnImageEditor(QWidget):    # PGN input + image preview; image has three states: auto-generated / uploaded / deleted (blank)
    changed = pyqtSignal()

    def __init__(self, pgn="", imagePath=None, imageData=None, noImage=False, orientation="white", collapsible=True, getStartingPgn=None):
        super().__init__()
        self.getStartingPgn = getStartingPgn or (lambda: "")    # Lines receive the starting PGN to resolve continuation notation; not needed for the starting position itself
        self.imagePath = imagePath    # Legacy local image path from old saves; preserved as-is, cleared once the user touches the image
        self.imageData = imageData    # Base64 of the uploaded image; None means auto-generated
        self.noImage = noImage    # True means no image on purpose
        self.orientation = orientation    # Board orientation of the auto-generated image: white / black
        self.collapsible = collapsible
        self.hadImage = False    # Whether the last preview had an image; auto-expands when one first appears

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        p = palette()

        self.previewTimer = QTimer(self)
        self.previewTimer.setSingleShot(True)
        self.previewTimer.setInterval(PREVIEW_DEBOUNCE_MS)
        self.previewTimer.timeout.connect(self.refreshPreview)

        self.pgnEdit = QPlainTextEdit(pgn)
        self.pgnEdit.setPlaceholderText(t("pgnPlaceholder"))
        self.pgnEdit.setMaximumHeight(76)
        self.pgnEdit.textChanged.connect(self.onFieldChanged)
        layout.addWidget(self.pgnEdit)

        self.errorLabel = QLabel()
        self.errorLabel.setWordWrap(True)
        self.errorLabel.setStyleSheet(f"background: transparent; color: {p.danger}; font-size: 12px;")
        self.errorLabel.hide()
        layout.addWidget(self.errorLabel)

        ### Button row: [▼][Upload image] ........ [Delete image / Use default] ###
        buttonRow = QHBoxLayout()

        self.toggleArrow = QToolButton(self)    # Collapse arrow; shown only when collapsible and an image exists
        self.toggleArrow.setText("▶")
        self.toggleArrow.setCheckable(True)
        self.toggleArrow.setStyleSheet(f"border: none; background: transparent; color: {p.inkSoft};")
        self.toggleArrow.toggled.connect(self.onToggled)
        self.toggleArrow.hide()
        if collapsible:
            sizePolicy = self.toggleArrow.sizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)    # Keeps its space when hidden so buttons don't shift when the image appears
            self.toggleArrow.setSizePolicy(sizePolicy)
            buttonRow.addWidget(self.toggleArrow)

        uploadButton = QPushButton(t("uploadImage"))
        uploadButton.clicked.connect(self.onUploadImage)
        buttonRow.addWidget(uploadButton)

        buttonRow.addStretch()

        self.rightButton = QPushButton()    # Auto image -> Delete image; uploaded or deleted -> Use default
        self.rightButton.clicked.connect(self.onRightClicked)
        buttonRow.addWidget(self.rightButton)
        layout.addLayout(buttonRow)

        self.imageLabel = QLabel()
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.imageLabel.setStyleSheet(
            f"background: {p.inputBg}; border: 1px solid {p.inputBorder}; border-radius: {INPUT_RADIUS}px; padding: 6px;"
        )
        layout.addWidget(self.imageLabel, 0, Qt.AlignLeft)

        self.updateRightButton()
        self.refreshPreview()

    def isAutoImage(self):
        return self.imageData is None and not self.noImage

    def onFieldChanged(self):
        self.changed.emit()
        self.previewTimer.start()

    def onToggled(self, checked):
        self.toggleArrow.setText("▼" if checked else "▶")
        self.updatePreviewVisibility()

    def applyImageState(self, expand):    # Shared wrap-up after any image state change
        self.updateRightButton()
        self.changed.emit()
        self.refreshPreview(expand)

    def setAutoImage(self):    # Back to the auto-generated image and expand
        self.imagePath = None
        self.imageData = None
        self.noImage = False
        self.applyImageState(expand=True)

    def onUploadImage(self):
        path, _ = QFileDialog.getOpenFileName(self, t("pickImage"), "", "Images (*.png *.jpg *.jpeg)")
        data = loadScaledBase64(path) if path else None
        if data:
            self.imagePath = None
            self.imageData = data
            self.noImage = False
            self.applyImageState(expand=True)

    def onRightClicked(self):
        if self.isAutoImage():
            self.imagePath = None
            self.imageData = None
            self.noImage = True
            self.applyImageState(expand=False)
        else:
            self.setAutoImage()

    def updateRightButton(self):
        self.rightButton.setText(t("deleteImage") if self.isAutoImage() else t("useDefault"))
        self.rightButton.setProperty("danger", self.isAutoImage())
        self.rightButton.style().unpolish(self.rightButton)
        self.rightButton.style().polish(self.rightButton)

    def setOrientation(self, orientation):    # Called externally when the opening orientation changes
        self.orientation = orientation
        self.refreshPreview()

    def getPgn(self):
        return self.pgnEdit.toPlainText()

    def getImagePath(self):
        return self.imagePath

    def getImageData(self):
        return self.imageData

    def getNoImage(self):
        return self.noImage

    def refreshPgnError(self):
        message = checkPgn(self.getPgn(), self.getStartingPgn())
        self.errorLabel.setText(message or "")
        self.errorLabel.setVisible(bool(message))
        self.pgnEdit.setProperty("invalid", bool(message))
        self.pgnEdit.style().unpolish(self.pgnEdit)
        self.pgnEdit.style().polish(self.pgnEdit)

    def refreshPreview(self, expand=False):
        self.refreshPgnError()
        rawBytes = resolveImageBytes(self.getPgn(), self.imageData, self.orientation, self.noImage, self.getStartingPgn(), htmlStyle=True)
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