from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QLabel, QToolButton, QFrame
from PyQt5.QtCore import Qt, pyqtSignal

INDENT_WIDTH = 18    # 每層縮排的像素寬度，需與 editor_panel 的視覺比例一致（樹狀面板較窄，用較小值）

COLOR_OPENING = "#6b7280"
COLOR_VARIANT = "#2b6cb0"
COLOR_SUBCATEGORY = "#2f855a"
COLOR_LINE = "#8a6d3b"


class TreeRowWidget(QWidget):    # 單一節點的 row，縮排/色條由參數明確指定，不依賴 Qt 原生箭頭機制
    deleteClicked = pyqtSignal()
    toggleClicked = pyqtSignal()

    def __init__(self, label, indentLevel=0, accentColor="#ccc", showDelete=True, hasToggle=False, expanded=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4 + indentLevel * INDENT_WIDTH, 2, 4, 2)
        layout.setSpacing(6)

        bar = QFrame()    # 左側色條，標示節點類型
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {accentColor}; border-radius: 2px;")
        layout.addWidget(bar)

        self.toggleButton = None
        if hasToggle:
            self.toggleButton = QToolButton()
            self.toggleButton.setText("▼" if expanded else "▶")
            self.toggleButton.setStyleSheet("border: none;")
            self.toggleButton.clicked.connect(self.toggleClicked.emit)
            layout.addWidget(self.toggleButton)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(20)    # 沒有展開箭頭的行也佔同樣寬度，確保文字對齊
            layout.addWidget(spacer)

        self.nameLabel = QLabel(label)
        layout.addWidget(self.nameLabel)
        layout.addStretch()

        self.deleteButton = QToolButton()
        self.deleteButton.setText("✕")
        self.deleteButton.setVisible(False)
        self.deleteButton.setEnabled(showDelete)
        self.deleteButton.clicked.connect(self.deleteClicked.emit)
        layout.addWidget(self.deleteButton)

    def setToggleIcon(self, expanded):
        if self.toggleButton:
            self.toggleButton.setText("▼" if expanded else "▶")

    def enterEvent(self, event):    # hover 進入顯示刪除按鈕
        self.deleteButton.setVisible(self.deleteButton.isEnabled())

    def leaveEvent(self, event):    # hover 離開隱藏按鈕
        self.deleteButton.setVisible(False)


class ActionRowButton(QToolButton):    # 「+ 新增 XXX」固定動作列，不屬於任何節點資料
    def __init__(self, text, onClick, indentLevel=0):
        super().__init__()
        self.setText(text)
        leftPadding = 4 + indentLevel * INDENT_WIDTH + 30    # 30 約為色條+展開箭頭區域寬度，對齊同層節點文字
        self.setStyleSheet(f"text-align: left; border: none; color: gray; padding-left: {leftPadding}px;")
        self.clicked.connect(onClick)


class TreePanel(QWidget):
    nodeSelected = pyqtSignal(str)    # nodeId
    addVariantRequested = pyqtSignal()
    addSubCategoryRequested = pyqtSignal(str)    # variantId
    addLineRequested = pyqtSignal(str, str)    # (parentType, parentId)  parentType: variant | subcategory
    deleteRequested = pyqtSignal(str, str)    # (nodeType, nodeId)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(0)    # 關閉 Qt 原生縮排，改由 TreeRowWidget 自行控制
        self.tree.setRootIsDecorated(False)    # 關閉原生展開箭頭，改用自製 toggle 按鈕
        self.tree.itemClicked.connect(self.onItemClicked)
        layout.addWidget(self.tree)

    def onItemClicked(self, item, column):
        nodeId = item.data(0, Qt.UserRole + 1)
        if nodeId:
            self.nodeSelected.emit(nodeId)

    ### 根據 Opening 模型重建整個樹 ###
    def rebuild(self, opening):
        self.tree.clear()

        rootItem = QTreeWidgetItem(self.tree)
        rootItem.setData(0, Qt.UserRole + 1, "opening")
        rootRow = TreeRowWidget("開局基本資訊", indentLevel=0, accentColor=COLOR_OPENING, showDelete=False)
        self.tree.setItemWidget(rootItem, 0, rootRow)

        for variant in opening.variants:
            self.addVariantItem(self.tree, variant)

        self.addActionItem(self.tree, "+ 新增 Variant", self.addVariantRequested.emit, indentLevel=0)
        self.tree.expandAll()

    def addVariantItem(self, parent, variant):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, variant.id)
        row = TreeRowWidget(variant.name or "未命名 Variant", indentLevel=0, accentColor=COLOR_VARIANT, hasToggle=True)
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("variant", variant.id))
        row.toggleClicked.connect(lambda: self.toggleItem(item, row))
        self.tree.setItemWidget(item, 0, row)

        for sub in variant.subCategories:
            self.addSubCategoryItem(item, sub)
        for line in variant.lines:
            self.addLineItem(item, line, indentLevel=1)

        self.addActionItem(item, "+ 新增子分類", lambda: self.addSubCategoryRequested.emit(variant.id), indentLevel=1)
        self.addActionItem(item, "+ 新增 Line", lambda: self.addLineRequested.emit("variant", variant.id), indentLevel=1)

    def addSubCategoryItem(self, parent, sub):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, sub.id)
        row = TreeRowWidget(sub.name or "未命名子分類", indentLevel=1, accentColor=COLOR_SUBCATEGORY, hasToggle=True)
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("subcategory", sub.id))
        row.toggleClicked.connect(lambda: self.toggleItem(item, row))
        self.tree.setItemWidget(item, 0, row)

        for line in sub.lines:
            self.addLineItem(item, line, indentLevel=2)

        self.addActionItem(item, "+ 新增 Line", lambda: self.addLineRequested.emit("subcategory", sub.id), indentLevel=2)

    def addLineItem(self, parent, line, indentLevel):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, line.id)
        row = TreeRowWidget(line.name or "未命名 Line", indentLevel=indentLevel, accentColor=COLOR_LINE)
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("line", line.id))
        self.tree.setItemWidget(item, 0, row)

    def addActionItem(self, parent, text, onClick, indentLevel):    # 固定的「+ 新增」動作列
        item = QTreeWidgetItem(parent)
        self.tree.setItemWidget(item, 0, ActionRowButton(text, onClick, indentLevel))

    def toggleItem(self, item, row):    # 自製展開/折疊，取代 Qt 原生箭頭
        expanded = not item.isExpanded()
        item.setExpanded(expanded)
        row.setToggleIcon(expanded)