from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QLabel, QToolButton
from PyQt5.QtCore import Qt, pyqtSignal


class TreeRowWidget(QWidget):    # 單一節點的 row，hover 時顯示 ✕ 刪除按鈕
    deleteClicked = pyqtSignal()

    def __init__(self, label, showDelete=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)

        self.nameLabel = QLabel(label)
        layout.addWidget(self.nameLabel)
        layout.addStretch()

        self.deleteButton = QToolButton()
        self.deleteButton.setText("✕")
        self.deleteButton.setVisible(False)
        self.deleteButton.setEnabled(showDelete)
        self.deleteButton.clicked.connect(self.deleteClicked.emit)
        layout.addWidget(self.deleteButton)

    def enterEvent(self, event):    # hover 進入顯示刪除按鈕
        self.deleteButton.setVisible(self.deleteButton.isEnabled())

    def leaveEvent(self, event):    # hover 離開隱藏按鈕
        self.deleteButton.setVisible(False)


class ActionRowButton(QToolButton):    # 「+ 新增 XXX」固定動作列，不屬於任何節點資料
    def __init__(self, text, onClick):
        super().__init__()
        self.setText(text)
        self.setStyleSheet("text-align: left; border: none; color: gray;")
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
        rootRow = TreeRowWidget("開局基本資訊", showDelete=False)
        self.tree.setItemWidget(rootItem, 0, rootRow)

        for variant in opening.variants:
            self.addVariantItem(self.tree, variant)

        self.addActionItem(self.tree, "+ 新增 Variant", self.addVariantRequested.emit)
        self.tree.expandAll()

    def addVariantItem(self, parent, variant):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, variant.id)
        row = TreeRowWidget(f"Variant: {variant.name or '未命名'}")
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("variant", variant.id))
        self.tree.setItemWidget(item, 0, row)

        for sub in variant.subCategories:
            self.addSubCategoryItem(item, sub)
        for line in variant.lines:
            self.addLineItem(item, line)

        self.addActionItem(item, "+ 新增子分類", lambda: self.addSubCategoryRequested.emit(variant.id))
        self.addActionItem(item, "+ 新增 Line", lambda: self.addLineRequested.emit("variant", variant.id))

    def addSubCategoryItem(self, parent, sub):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, sub.id)
        row = TreeRowWidget(sub.name or "未命名子分類")
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("subcategory", sub.id))
        self.tree.setItemWidget(item, 0, row)

        for line in sub.lines:
            self.addLineItem(item, line)

        self.addActionItem(item, "+ 新增 Line", lambda: self.addLineRequested.emit("subcategory", sub.id))

    def addLineItem(self, parent, line):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, line.id)
        row = TreeRowWidget(line.name or "未命名 Line")
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("line", line.id))
        self.tree.setItemWidget(item, 0, row)

    def addActionItem(self, parent, text, onClick):    # 固定的「+ 新增」動作列
        item = QTreeWidgetItem(parent)
        self.tree.setItemWidget(item, 0, ActionRowButton(text, onClick))
