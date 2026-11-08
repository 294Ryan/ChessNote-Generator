from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame, QPushButton, QSizePolicy, QApplication, QRadioButton
from PyQt5.QtCore import Qt, QMimeData, QTimer
from PyQt5.QtGui import QDrag, QCursor
from core.models import moveItem
from core.i18n import t
from ui.editor_style import editorStyle, CARD_RADIUS, cardStyle
from ui.line_widget import PgnImageEditor

INDENT_WIDTH = 28    # Indent per level (px): Variant > SubCategory > Line

COLOR_OPENING = "#6b7280"
COLOR_VARIANT = "#2b6cb0"
COLOR_SUBCATEGORY = "#2f855a"
COLOR_LINE = "#8a6d3b"

NODE_MIME = "application/x-chess-node-id"    # Node id carried while dragging
AUTO_SCROLL_EDGE = 40    # Distance (px) from the viewport top/bottom edge where auto-scroll starts during a drag
AUTO_SCROLL_STEP = 20    # Pixels per auto-scroll step


class DragHandle(QLabel):    # ☰ handle at the block's top right; press and drag to reorder
    def __init__(self, nodeId, frame):
        super().__init__("☰")
        self.nodeId = nodeId
        self.frame = frame    # Screenshot used as the drag thumbnail following the cursor
        self.pressPos = None
        self.setToolTip(t("dragTip"))
        self.setCursor(Qt.SizeAllCursor)
        self.setStyleSheet("background: transparent; color: #9ca3af; font-size: 14px; padding: 0 4px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressPos = event.pos()

    def mouseMoveEvent(self, event):
        if self.pressPos is None or not (event.buttons() & Qt.LeftButton):
            return
        if (event.pos() - self.pressPos).manhattanLength() < QApplication.startDragDistance():
            return
        self.pressPos = None
        mime = QMimeData()
        mime.setData(NODE_MIME, self.nodeId.encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(self.frame.grab().scaledToWidth(300, Qt.SmoothTransformation))
        drag.exec_(Qt.MoveAction)


class DragSortContainer(QWidget):    # Receives drag events; the logic is delegated to EditorPanel
    def __init__(self, panel):
        super().__init__()
        self.panel = panel
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        self.panel.onDragMove(event)

    def dragMoveEvent(self, event):
        self.panel.onDragMove(event)

    def dragLeaveEvent(self, event):
        self.panel.endDrag()

    def dropEvent(self, event):
        self.panel.onDrop(event)


class EditorPanel(QScrollArea):
    def __init__(self, onModelChanged, onStructureChanged):
        super().__init__()
        self.onModelChanged = onModelChanged    # Notifies MainWindow to update tree labels on field changes
        self.onStructureChanged = onStructureChanged    # Notifies MainWindow to rebuild both sides after reordering
        self.setWidgetResizable(True)
        self.applyTheme()

        self.container = DragSortContainer(self)
        self.container.setObjectName("editorContainer")
        self.container.setAttribute(Qt.WA_StyledBackground, True)    # Custom QWidget doesn't paint stylesheet backgrounds by default
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)
        self.setWidget(self.container)

        self.nodeWidgets = {}    # nodeId -> block widget, for tree navigation jumps
        self.blocks = {}    # nodeId -> frames of the node and all descendants (top to bottom), used to compute the whole block's extent while dragging
        self.siblingLists = {}    # nodeId -> model list containing the node; reordering only within the same list
        self.imageEditors = []    # All image editors, refreshed together when orientation changes

        self.draggingId = None
        self.dropIndicator = QFrame(self.container)
        self.dropIndicator.setStyleSheet("background: #e53e3e;")
        self.dropIndicator.hide()
        self.autoScrollTimer = QTimer(self)
        self.autoScrollTimer.setInterval(40)
        self.autoScrollTimer.timeout.connect(self.autoScrollStep)

    def rebuild(self, opening):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.nodeWidgets.clear()
        self.blocks.clear()
        self.siblingLists.clear()
        self.imageEditors.clear()

        self.opening = opening    # Line editors always read the latest starting PGN
        self.currentOrientation = opening.orientation    # Used when a Line editor is created
        self.addOpeningSection(opening)

        for variant in opening.variants:
            self.addVariantSection(variant, opening.variants)
            for line in variant.lines:    # Lines are placed above subcategories by default
                self.addLineSection(line, 1, variant.lines, (variant.id,))
            for sub in variant.subCategories:
                self.addSubCategorySection(sub, variant.subCategories, (variant.id,))
                for line in sub.lines:
                    self.addLineSection(line, 2, sub.lines, (variant.id, sub.id))

        self.layout.addStretch()

    def applyTheme(self):    # On theme switch reset the panel style; card styles are applied on rebuild
        self.setStyleSheet(editorStyle())

    ### Block construction ###
    def addOpeningSection(self, opening):
        frame = self.makeFrame(indentLevel=0, accentColor=COLOR_OPENING)
        layout = frame.contentLayout
        layout.addWidget(self.makeHeading(t("openingInfo"), COLOR_OPENING))

        layout.addWidget(QLabel(t("openingName")))
        nameEdit = QLineEdit(opening.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(opening, "name", text))
        layout.addWidget(nameEdit)

        orientationRow = QHBoxLayout()    # Board orientation:  • White  ◦ Black
        orientationRow.addWidget(QLabel(t("orientationLabel")))
        whiteRadio = QRadioButton(t("white"))
        blackRadio = QRadioButton(t("black"))
        whiteRadio.setChecked(opening.orientation == "white")
        blackRadio.setChecked(opening.orientation == "black")
        whiteRadio.toggled.connect(lambda checked: self.onOrientationChanged(opening, "white" if checked else "black"))
        orientationRow.addWidget(whiteRadio)
        orientationRow.addWidget(blackRadio)
        orientationRow.addStretch()
        layout.addLayout(orientationRow)

        layout.addWidget(QLabel(t("openingDesc")))
        descEdit = QTextEdit(opening.description)
        descEdit.setMaximumHeight(76)
        descEdit.textChanged.connect(lambda: self.updateField(opening, "description", descEdit.toPlainText()))
        layout.addWidget(descEdit)

        layout.addWidget(QLabel(t("startingPgn")))
        pgnEditor = PgnImageEditor(opening.startingPgn, opening.startingImagePath, opening.startingImageData, opening.startingNoImage, opening.orientation, collapsible=False)
        pgnEditor.changed.connect(lambda: self.updateStartingPgn(opening, pgnEditor))
        self.imageEditors.append(pgnEditor)
        layout.addWidget(pgnEditor)

        self.registerSection("opening", frame)

    def addVariantSection(self, variant, siblings):
        frame = self.makeFrame(indentLevel=0, accentColor=COLOR_VARIANT)
        layout = frame.contentLayout
        layout.addWidget(self.makeHeading("VARIANT", COLOR_VARIANT, DragHandle(variant.id, frame)))

        nameEdit = QLineEdit(variant.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(variant, "name", text))
        layout.addWidget(nameEdit)

        self.addDescriptionField(layout, variant)
        self.registerSection(variant.id, frame, siblings)

    def addSubCategorySection(self, sub, siblings, ancestorIds):
        frame = self.makeFrame(indentLevel=1, accentColor=COLOR_SUBCATEGORY)
        layout = frame.contentLayout
        layout.addWidget(self.makeHeading(t("subcategory"), COLOR_SUBCATEGORY, DragHandle(sub.id, frame)))

        nameEdit = QLineEdit(sub.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(sub, "name", text))
        layout.addWidget(nameEdit)

        self.addDescriptionField(layout, sub)
        self.registerSection(sub.id, frame, siblings, ancestorIds)

    def addLineSection(self, line, indentLevel, siblings, ancestorIds):
        frame = self.makeFrame(indentLevel=indentLevel, accentColor=COLOR_LINE)
        layout = frame.contentLayout
        layout.addWidget(self.makeHeading("LINE", COLOR_LINE, DragHandle(line.id, frame)))

        pgnEditor = PgnImageEditor(line.pgn, line.imagePath, line.imageData, line.noImage, self.currentOrientation, collapsible=True, getStartingPgn=lambda: self.opening.startingPgn)
        pgnEditor.changed.connect(lambda: self.updateLinePgn(line, pgnEditor))
        self.imageEditors.append(pgnEditor)
        layout.addWidget(pgnEditor)

        self.registerSection(line.id, frame, siblings, ancestorIds)

    def addDescriptionField(self, layout, obj):    # Optional description field shared by Variant / SubCategory
        descEdit = QTextEdit(obj.description)
        descEdit.setPlaceholderText(t("descPlaceholder"))
        descEdit.setMaximumHeight(64)
        descEdit.textChanged.connect(lambda: self.updateField(obj, "description", descEdit.toPlainText()))
        layout.addWidget(descEdit)

    ### Shared helpers ###
    def makeFrame(self, indentLevel=0, accentColor="#ccc"):
        outer = QWidget()
        outerLayout = QHBoxLayout(outer)
        outerLayout.setContentsMargins(indentLevel * INDENT_WIDTH, 0, 0, 0)
        outerLayout.setSpacing(0)

        bar = QFrame()    # Real color block instead of CSS border-left, which leaves artifact lines at child widget borders
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {accentColor}; border-top-left-radius: {CARD_RADIUS}px; border-bottom-left-radius: {CARD_RADIUS}px;")
        outerLayout.addWidget(bar)

        content = QFrame()
        content.setObjectName("card")
        content.setStyleSheet(cardStyle(accentColor))
        contentLayout = QVBoxLayout(content)
        contentLayout.setContentsMargins(12, 10, 12, 10)
        contentLayout.setSpacing(6)
        outerLayout.addWidget(content, 1)

        outer.contentLayout = contentLayout    # Callers add their fields here
        return outer

    def makeHeading(self, text, color, handle=None):    # Type badge, left-aligned (not full width); handle is the drag grip on the right
        row = QWidget()
        row.setFixedHeight(22)    # Fix the row height explicitly instead of relying on child sizeHint
        row.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        rowLayout = QHBoxLayout(row)
        rowLayout.setContentsMargins(0, 0, 0, 0)
        badge = QLabel(text)
        badge.setStyleSheet(
            f"background: {color}; color: white; padding: 2px 8px;"
            f" border-radius: 3px; font-weight: bold; font-size: 11px;"
        )
        badge.setFixedHeight(20)
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        rowLayout.addWidget(badge)
        rowLayout.addStretch()
        if handle:
            rowLayout.addWidget(handle)
        return row

    def registerSection(self, nodeId, frame, siblings=None, ancestorIds=()):
        self.layout.addWidget(frame)
        self.nodeWidgets[nodeId] = frame
        if siblings is not None:
            self.siblingLists[nodeId] = siblings
        for blockId in (*ancestorIds, nodeId):
            self.blocks.setdefault(blockId, []).append(frame)

    ### Model updates ###
    def updateField(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.onModelChanged()

    def onOrientationChanged(self, opening, orientation):
        opening.orientation = orientation
        self.currentOrientation = orientation
        for editor in self.imageEditors:
            editor.setOrientation(orientation)
        self.onModelChanged()    # Orientation is saved content, so mark as modified

    def updateStartingPgn(self, opening, pgnEditor):
        opening.startingPgn = pgnEditor.getPgn()
        opening.startingImagePath = pgnEditor.getImagePath()
        opening.startingImageData = pgnEditor.getImageData()
        opening.startingNoImage = pgnEditor.getNoImage()
        for editor in self.imageEditors:
            if editor is not pgnEditor:
                editor.previewTimer.start()    # Continuation-style Lines re-check and re-preview against the new starting position
        self.onModelChanged()

    def updateLinePgn(self, line, pgnEditor):
        line.pgn = pgnEditor.getPgn()
        line.imagePath = pgnEditor.getImagePath()
        line.imageData = pgnEditor.getImageData()
        line.noImage = pgnEditor.getNoImage()
        self.onModelChanged()

    def scrollToNode(self, nodeId):
        widget = self.nodeWidgets.get(nodeId)
        if widget:
            self.ensureWidgetVisible(widget)

    ### Drag reorder ###
    def findDropPosition(self, draggedId, y):    # Returns (insert index, indicator y); compares siblings in the same list only, so it never crosses levels
        siblings = self.siblingLists[draggedId]
        for index, node in enumerate(siblings):
            headRect = self.blocks[node.id][0].geometry()
            if y < headRect.center().y():
                return index, headRect.top()
        return len(siblings), self.blocks[siblings[-1].id][-1].geometry().bottom()

    def showIndicator(self, y):
        self.dropIndicator.setGeometry(0, max(y - 1, 0), self.container.width(), 3)
        self.dropIndicator.raise_()
        self.dropIndicator.show()

    def readDraggedId(self, event):
        if not event.mimeData().hasFormat(NODE_MIME):
            return None
        return bytes(event.mimeData().data(NODE_MIME)).decode("utf-8")

    def onDragMove(self, event):
        nodeId = self.readDraggedId(event)
        if nodeId not in self.siblingLists:
            event.ignore()
            return
        if self.draggingId != nodeId:    # Drag just started: start edge auto-scroll
            self.draggingId = nodeId
            self.autoScrollTimer.start()
        self.showIndicator(self.findDropPosition(nodeId, event.pos().y())[1])
        event.acceptProposedAction()

    def onDrop(self, event):
        nodeId = self.readDraggedId(event)
        self.endDrag()
        if nodeId not in self.siblingLists:
            return
        index, _ = self.findDropPosition(nodeId, event.pos().y())
        event.acceptProposedAction()
        if moveItem(self.siblingLists[nodeId], nodeId, index):
            scrollValue = self.verticalScrollBar().value()
            self.onStructureChanged()
            QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(scrollValue))    # Keep the scroll position after rebuild

    def endDrag(self):
        self.draggingId = None
        self.autoScrollTimer.stop()
        self.dropIndicator.hide()

    def autoScrollStep(self):    # Auto-scroll near the viewport edges and update the indicator line
        y = self.viewport().mapFromGlobal(QCursor.pos()).y()
        bar = self.verticalScrollBar()
        if y < AUTO_SCROLL_EDGE:
            bar.setValue(bar.value() - AUTO_SCROLL_STEP)
        elif y > self.viewport().height() - AUTO_SCROLL_EDGE:
            bar.setValue(bar.value() + AUTO_SCROLL_STEP)
        else:
            return
        containerY = self.container.mapFromGlobal(QCursor.pos()).y()
        self.showIndicator(self.findDropPosition(self.draggingId, containerY)[1])