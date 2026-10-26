from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame, QPushButton, QSizePolicy, QApplication, QRadioButton
from PyQt5.QtCore import Qt, QMimeData, QTimer
from PyQt5.QtGui import QDrag, QCursor
from core.models import moveItem
from ui.line_widget import PgnImageEditor

INDENT_WIDTH = 28    # 每層縮排的像素寬度，呈現 Variant > 子分類 > Line 的從屬關係

COLOR_OPENING = "#6b7280"
COLOR_VARIANT = "#2b6cb0"
COLOR_SUBCATEGORY = "#2f855a"
COLOR_LINE = "#8a6d3b"

NODE_MIME = "application/x-chess-node-id"    # 拖曳時攜帶的節點 id
AUTO_SCROLL_EDGE = 40    # 拖曳時游標距可視區上下緣多少像素內開始自動捲動
AUTO_SCROLL_STEP = 20    # 每次自動捲動的像素


class DragHandle(QLabel):    # 區塊右上角的 ☰ 握把，按住拖曳調整順序
    def __init__(self, nodeId, frame):
        super().__init__("☰")
        self.nodeId = nodeId
        self.frame = frame    # 拖曳時拿來截圖當作游標跟隨的縮圖
        self.pressPos = None
        self.setToolTip("拖曳調整順序")
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


class DragSortContainer(QWidget):    # 接收拖曳事件，判斷邏輯交給 EditorPanel
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
        self.onModelChanged = onModelChanged    # 欄位變動時通知 MainWindow 更新樹狀標籤
        self.onStructureChanged = onStructureChanged    # 拖曳調序後通知 MainWindow 重建左右兩側
        self.setWidgetResizable(True)

        self.container = DragSortContainer(self)
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignTop)
        self.setWidget(self.container)

        self.nodeWidgets = {}    # nodeId -> 區塊 widget，供樹狀導覽跳轉用
        self.blocks = {}    # nodeId -> 該節點與所有子孫的 frame（由上到下），拖曳時用來算整塊範圍
        self.siblingLists = {}    # nodeId -> 該節點所在的 model list，只能在同一個 list 內調序
        self.imageEditors = []    # 所有圖片編輯器，棋盤視角變更時統一刷新預覽

        self.draggingId = None
        self.dropIndicator = QFrame(self.container)    # 拖曳時的插入位置指示線
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

        self.currentOrientation = opening.orientation    # Line 編輯器建立時取用
        self.addOpeningSection(opening)

        for variant in opening.variants:
            self.addVariantSection(variant, opening.variants)
            for line in variant.lines:    # Line 預設排在子分類上方
                self.addLineSection(line, 1, variant.lines, (variant.id,))
            for sub in variant.subCategories:
                self.addSubCategorySection(sub, variant.subCategories, (variant.id,))
                for line in sub.lines:
                    self.addLineSection(line, 2, sub.lines, (variant.id, sub.id))

        self.layout.addStretch()

    ### 區塊建構 ###
    def addOpeningSection(self, opening):
        frame = self.makeFrame(indentLevel=0, accentColor=COLOR_OPENING)
        layout = frame.contentLayout
        layout.addWidget(self.makeHeading("開局基本資訊", COLOR_OPENING))

        layout.addWidget(QLabel("開局名稱"))
        nameEdit = QLineEdit(opening.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(opening, "name", text))
        layout.addWidget(nameEdit)

        orientationRow = QHBoxLayout()    # 棋盤視角:  • White  ◦ Black
        orientationRow.addWidget(QLabel("棋盤視角:"))
        whiteRadio = QRadioButton("White")
        blackRadio = QRadioButton("Black")
        whiteRadio.setChecked(opening.orientation == "white")
        blackRadio.setChecked(opening.orientation == "black")
        whiteRadio.toggled.connect(lambda checked: self.onOrientationChanged(opening, "white" if checked else "black"))
        orientationRow.addWidget(whiteRadio)
        orientationRow.addWidget(blackRadio)
        orientationRow.addStretch()
        layout.addLayout(orientationRow)

        layout.addWidget(QLabel("開局概述"))
        descEdit = QTextEdit(opening.description)
        descEdit.setMaximumHeight(60)
        descEdit.textChanged.connect(lambda: self.updateField(opening, "description", descEdit.toPlainText()))
        layout.addWidget(descEdit)

        layout.addWidget(QLabel("起始 PGN"))
        pgnEditor = PgnImageEditor(opening.startingPgn, opening.startingImagePath, opening.startingNoImage, opening.orientation, collapsible=False)
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
        layout.addWidget(self.makeHeading("子分類", COLOR_SUBCATEGORY, DragHandle(sub.id, frame)))

        nameEdit = QLineEdit(sub.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(sub, "name", text))
        layout.addWidget(nameEdit)

        self.addDescriptionField(layout, sub)
        self.registerSection(sub.id, frame, siblings, ancestorIds)

    def addLineSection(self, line, indentLevel, siblings, ancestorIds):
        frame = self.makeFrame(indentLevel=indentLevel, accentColor=COLOR_LINE)
        layout = frame.contentLayout
        layout.addWidget(self.makeHeading("LINE", COLOR_LINE, DragHandle(line.id, frame)))

        pgnEditor = PgnImageEditor(line.pgn, line.imagePath, line.noImage, self.currentOrientation, collapsible=True)
        pgnEditor.changed.connect(lambda: self.updateLinePgn(line, pgnEditor))
        self.imageEditors.append(pgnEditor)
        layout.addWidget(pgnEditor)

        self.registerSection(line.id, frame, siblings, ancestorIds)

    def addDescriptionField(self, layout, obj):    # Variant / SubCategory 共用的選填說明欄位
        descEdit = QTextEdit(obj.description)
        descEdit.setPlaceholderText("說明（選填）")
        descEdit.setMaximumHeight(50)
        descEdit.textChanged.connect(lambda: self.updateField(obj, "description", descEdit.toPlainText()))
        layout.addWidget(descEdit)

    ### 共用小工具 ###
    def makeFrame(self, indentLevel=0, accentColor="#ccc"):    # indentLevel 呈現 Variant > 子分類 > Line 的從屬層次
        outer = QWidget()
        outerLayout = QHBoxLayout(outer)
        outerLayout.setContentsMargins(indentLevel * INDENT_WIDTH, 0, 0, 0)
        outerLayout.setSpacing(0)

        bar = QFrame()    # 實體色塊取代 CSS border-left，避免樣式引擎在子元件邊界產生瑕疵線
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {accentColor};")
        outerLayout.addWidget(bar)

        content = QFrame()
        content.setStyleSheet("QFrame { background: white; }")
        contentLayout = QVBoxLayout(content)
        contentLayout.setContentsMargins(12, 10, 12, 10)
        contentLayout.setSpacing(6)
        outerLayout.addWidget(content, 1)

        outer.contentLayout = contentLayout    # 呼叫端透過這個加入欄位
        return outer

    def makeHeading(self, text, color, handle=None):    # 類型徽章，靠左對齊不佔滿整行，handle 為右側拖曳握把
        row = QWidget()
        row.setFixedHeight(22)    # 明確鎖死整個 row 的高度，不讓它依賴內部元件的 sizeHint 計算
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

    ### model 更新 ###
    def updateField(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.onModelChanged()

    def onOrientationChanged(self, opening, orientation):
        opening.orientation = orientation
        self.currentOrientation = orientation
        for editor in self.imageEditors:
            editor.setOrientation(orientation)

    def updateStartingPgn(self, opening, pgnEditor):
        opening.startingPgn = pgnEditor.getPgn()
        opening.startingImagePath = pgnEditor.getImagePath()
        opening.startingNoImage = pgnEditor.getNoImage()
        self.onModelChanged()

    def updateLinePgn(self, line, pgnEditor):
        line.pgn = pgnEditor.getPgn()
        line.imagePath = pgnEditor.getImagePath()
        line.noImage = pgnEditor.getNoImage()
        self.onModelChanged()

    def scrollToNode(self, nodeId):
        widget = self.nodeWidgets.get(nodeId)
        if widget:
            self.ensureWidgetVisible(widget)

    ### 拖曳排序 ###
    def findDropPosition(self, draggedId, y):    # 回傳 (插入索引, 指示線 y)；只比較同一個 list 的兄弟，所以不會跨層級
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
        if self.draggingId != nodeId:    # 剛進入拖曳，啟動邊緣自動捲動
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
            QTimer.singleShot(0, lambda: self.verticalScrollBar().setValue(scrollValue))    # 重建後維持原捲動位置

    def endDrag(self):
        self.draggingId = None
        self.autoScrollTimer.stop()
        self.dropIndicator.hide()

    def autoScrollStep(self):    # 游標靠近可視區上下緣時自動捲動，並同步更新指示線
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