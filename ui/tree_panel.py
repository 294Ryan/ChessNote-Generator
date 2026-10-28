from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QLabel, QToolButton, QFrame, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
import textwrap
from ui.theme import palette, scrollbarStyle
from core.i18n import t

TYPE_ROLE = Qt.UserRole + 2    # item 資料：節點類型 variant / subcategory / line（節點 id 在 Qt.UserRole + 1）
INDENT_WIDTH = 18    # 每層縮排的像素寬度，需與 editor_panel 的視覺比例一致（樹狀面板較窄，用較小值）

COLOR_OPENING = "#6b7280"
COLOR_VARIANT = "#2b6cb0"
COLOR_SUBCATEGORY = "#2f855a"
COLOR_LINE = "#8a6d3b"

ROW_HEIGHT = 30    # 每列高度（像素），item widget 的高度由這裡決定
ACTION_ROW_HEIGHT = 24    # 「+ 新增」列高度
CHIP_PADDING = 6    # 色塊內左側留白，「+ 新增」列的 + 也對齊這個位置
TOOLTIP_WIDTH = 48    # tooltip 內 PGN 每行字數


def tint(hexColor, alpha):    # #rrggbb 轉成帶透明度的 rgba，用來做同色系淡底
    r, g, b = (int(hexColor[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


class TreeRowWidget(QWidget):    # 單一節點的 row，縮排/色條由參數明確指定，不依賴 Qt 原生箭頭機制
    deleteClicked = pyqtSignal()
    toggleClicked = pyqtSignal()
    hovered = pyqtSignal(object)    # 滑鼠進入時送出 scopeIds，用來決定要顯示哪些「+ 新增」列

    def __init__(self, label, indentLevel=0, accentColor="#ccc", showDelete=True, hasToggle=False, expanded=True, scopeIds=()):
        super().__init__()
        self.scopeIds = tuple(scopeIds)    # 此列所屬的區塊 id（由外到內）
        outer = QHBoxLayout(self)
        outer.setContentsMargins(4 + indentLevel * INDENT_WIDTH, 2, 4, 2)

        chip = QFrame()    # 整列色塊：節點同色系的淡底，滑過加深
        chip.setObjectName("chip")
        p = palette()
        chip.setStyleSheet(    # 底色與滑過底色的透明度在 ui/theme.py（chipAlpha / chipHoverAlpha）
            f"#chip {{ background: {tint(accentColor, p.chipAlpha)}; border-radius: 4px; }}"
            f"#chip:hover {{ background: {tint(accentColor, p.chipHoverAlpha)}; }}"
        )
        outer.addWidget(chip)

        layout = QHBoxLayout(chip)
        layout.setContentsMargins(CHIP_PADDING, 0, 4, 0)
        layout.setSpacing(6)

        bar = QFrame()    # 左側色條，標示節點類型
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background: {accentColor}; border-radius: 2px;")
        layout.addWidget(bar)

        self.toggleButton = None
        if hasToggle:
            self.toggleButton = QToolButton()
            self.toggleButton.setText("▼" if expanded else "▶")
            self.toggleButton.setStyleSheet(f"border: none; background: transparent; color: {p.ink};")
            self.toggleButton.clicked.connect(self.toggleClicked.emit)
            layout.addWidget(self.toggleButton)
        else:
            spacer = QWidget()
            spacer.setFixedWidth(20)    # 沒有展開箭頭的行也佔同樣寬度，確保文字對齊
            layout.addWidget(spacer)

        self.nameLabel = QLabel(label)
        self.nameLabel.setStyleSheet(f"background: transparent; color: {p.ink};")
        layout.addWidget(self.nameLabel)
        layout.addStretch()

        self.deleteButton = QToolButton()    # 無框的 ✕，平常淡灰，滑過變紅
        self.deleteButton.setText("✕")
        self.deleteButton.setCursor(Qt.PointingHandCursor)
        self.deleteButton.setStyleSheet(
            "QToolButton { border: none; background: transparent; color: #9ca3af; font-size: 12px; padding: 0 4px; }"
            "QToolButton:hover { color: #e53e3e; }"
        )
        self.deleteButton.setVisible(False)
        self.deleteButton.setEnabled(showDelete)
        self.deleteButton.clicked.connect(self.deleteClicked.emit)
        layout.addWidget(self.deleteButton)

    def setToggleIcon(self, expanded):
        if self.toggleButton:
            self.toggleButton.setText("▼" if expanded else "▶")

    def enterEvent(self, event):    # hover 進入顯示刪除按鈕
        self.deleteButton.setVisible(self.deleteButton.isEnabled())
        self.hovered.emit(self.scopeIds)

    def leaveEvent(self, event):    # hover 離開隱藏按鈕
        self.deleteButton.setVisible(False)


class ActionRow(QWidget):    # 「+ 新增 XXX」固定動作列，不屬於任何節點資料；永遠靠左，+ 對齊新增後節點的色條
    hovered = pyqtSignal(object)

    def __init__(self, text, onClick, indentLevel, accentColor, ownerId, scopeIds, excludeIds=()):
        super().__init__()
        self.onClick = onClick
        self.ownerId = ownerId    # 滑鼠位於此區塊內時才顯示本列
        self.scopeIds = tuple(scopeIds)
        self.excludeIds = frozenset(excludeIds)    # 滑鼠位於這些區塊內時隱藏本列（避免本列在游標上方展開把內容往下推）
        self.item = None    # 對應的 QTreeWidgetItem，顯示/隱藏靠它
        self.setCursor(Qt.PointingHandCursor)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4 + indentLevel * INDENT_WIDTH, 2, 4, 2)

        chip = QFrame()    # 平常透明，滑過顯示新增項目的同色系淡底
        chip.setObjectName("chip")
        chip.setStyleSheet(
            "#chip { background: transparent; border-radius: 4px; }"
            f"#chip:hover {{ background: {tint(accentColor, palette().chipAlpha)}; }}"
            "#chip QLabel { color: #9ca3af; background: transparent; }"
            f"#chip:hover QLabel {{ color: {accentColor}; }}"
        )
        outer.addWidget(chip)

        layout = QHBoxLayout(chip)
        layout.setContentsMargins(CHIP_PADDING, 0, 4, 0)
        layout.addWidget(QLabel(text))
        layout.addStretch()

    def enterEvent(self, event):
        self.hovered.emit(self.scopeIds)

    def mousePressEvent(self, event):
        event.accept()    # 接住按下事件，後續的放開事件才會送到這裡

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.onClick()


class DragSortTree(QTreeWidget):    # 只允許同父層、同類型的節點互換順序，實際調序交給外部改 model 後重建
    reorderRequested = pyqtSignal(str, str, bool)    # (draggedId, targetId, insertAfter)
    mouseLeft = pyqtSignal()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.mouseLeft.emit()

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDropIndicatorShown(True)

    def parentIdOf(self, item):
        parent = item.parent()
        return parent.data(0, Qt.UserRole + 1) if parent else ""

    def isSameGroup(self, source, target):    # 同類型且同父層（含自己）才算可放置區域
        if source is None or target is None:
            return False
        sourceType = source.data(0, TYPE_ROLE)
        return bool(sourceType) and sourceType == target.data(0, TYPE_ROLE) and self.parentIdOf(source) == self.parentIdOf(target)

    def findDropTarget(self, event):    # 合法回傳 (draggedId, targetId, insertAfter)，否則 None
        source = self.currentItem()
        target = self.itemAt(event.pos())
        if target is source or not self.isSameGroup(source, target):
            return None
        insertAfter = event.pos().y() > self.visualItemRect(target).center().y()
        return source.data(0, Qt.UserRole + 1), target.data(0, Qt.UserRole + 1), insertAfter

    def dragMoveEvent(self, event):
        if not self.isSameGroup(self.currentItem(), self.itemAt(event.pos())):
            event.ignore()    # 不同層級或類型：顯示禁止游標
            return
        super().dragMoveEvent(event)    # 讓 Qt 更新插入指示線
        event.setDropAction(Qt.MoveAction)
        event.accept()    # Qt 自己會因 InternalMove 規則拒絕，這裡強制接受以免游標顯示禁止

    def dropEvent(self, event):
        result = self.findDropTarget(event)
        event.setDropAction(Qt.IgnoreAction)    # 不讓 Qt 自己搬動項目，避免原項目被移除
        event.accept()
        if result:
            QTimer.singleShot(0, lambda: self.reorderRequested.emit(*result))    # 等拖曳結束後再重建樹


class TreePanel(QWidget):
    nodeSelected = pyqtSignal(str)    # nodeId
    addVariantRequested = pyqtSignal()
    addSubCategoryRequested = pyqtSignal(str)    # variantId
    addLineRequested = pyqtSignal(str, str)    # (parentType, parentId)  parentType: variant | subcategory
    deleteRequested = pyqtSignal(str, str)    # (nodeType, nodeId)
    reorderRequested = pyqtSignal(str, str, bool)    # (draggedId, targetId, insertAfter)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = DragSortTree()
        self.tree.reorderRequested.connect(self.reorderRequested)
        self.tree.mouseLeft.connect(lambda: self.onRowHovered(()))
        self.activeScopes = set()    # 目前滑鼠所在的區塊 id，重建樹後沿用
        self.actionRows = []
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(0)    # 關閉 Qt 原生縮排，改由 TreeRowWidget 自行控制
        self.tree.setRootIsDecorated(False)    # 關閉原生展開箭頭，改用自製 toggle 按鈕
        self.applyTheme()
        self.tree.itemClicked.connect(self.onItemClicked)
        layout.addWidget(self.tree)

    def applyTheme(self):    # 拿掉預設的選取/滑過底色與外框，色塊完全由 row 自己負責；主題切換後需重建樹讓 row 吃到新色票
        self.tree.setStyleSheet(
            f"QTreeWidget {{ border: none; outline: 0; background: {palette().treeBg}; }}"
            "QTreeWidget::item, QTreeWidget::item:hover, QTreeWidget::item:selected { background: transparent; }"
            + scrollbarStyle()
        )

    def onRowHovered(self, scopeIds):    # 滑鼠進入某列：只顯示所屬區塊的「+ 新增」列
        if set(scopeIds) != self.activeScopes:
            self.activeScopes = set(scopeIds)
            self.applyActiveScopes()

    def applyActiveScopes(self):    # 沒顯示的「+」列直接隱藏整列（不佔空間），滑到所屬區塊才展開
        for row in self.actionRows:
            revealed = row.ownerId in self.activeScopes and not (self.activeScopes & row.excludeIds)
            row.item.setHidden(not revealed)

    def onItemClicked(self, item, column):
        nodeId = item.data(0, Qt.UserRole + 1)
        if nodeId:
            self.nodeSelected.emit(nodeId)

    ### 根據 Opening 模型重建整個樹 ###
    def rebuild(self, opening):
        self.tree.clear()
        self.actionRows = []

        rootItem = QTreeWidgetItem(self.tree)
        rootItem.setData(0, Qt.UserRole + 1, "opening")
        rootItem.setFlags(rootItem.flags() & ~Qt.ItemIsDragEnabled)
        rootItem.setSizeHint(0, QSize(0, ROW_HEIGHT))
        rootRow = TreeRowWidget(t("openingInfo"), indentLevel=0, accentColor=COLOR_OPENING, showDelete=False, scopeIds=() if opening.variants else ("tail",))
        rootRow.hovered.connect(self.onRowHovered)
        self.tree.setItemWidget(rootItem, 0, rootRow)

        for index, variant in enumerate(opening.variants):
            self.addVariantItem(self.tree, variant, isLast=(index == len(opening.variants) - 1))

        self.addActionItem(self.tree, t("treeAddVariant"), self.addVariantRequested.emit, indentLevel=0, accentColor=COLOR_VARIANT, ownerId="tail", scopeIds=("tail",))    # 滑到最後一個 Variant 區塊或本列時顯示
        self.tree.expandAll()
        self.applyActiveScopes()

    def addVariantItem(self, parent, variant, isLast):
        scope = (variant.id, "tail") if isLast else (variant.id,)
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, variant.id)
        item.setData(0, TYPE_ROLE, "variant")
        item.setSizeHint(0, QSize(0, ROW_HEIGHT))
        row = TreeRowWidget(variant.name or t("treeUnnamedVariant"), indentLevel=0, accentColor=COLOR_VARIANT, hasToggle=True, scopeIds=scope)
        row.hovered.connect(self.onRowHovered)
        row.setToolTip(variant.name)
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("variant", variant.id))
        row.toggleClicked.connect(lambda: self.toggleItem(item, row))
        self.tree.setItemWidget(item, 0, row)

        for number, line in enumerate(variant.lines, 1):    # Line 排在子分類之前
            self.addLineItem(item, line, indentLevel=1, number=number, scope=scope)
        self.addActionItem(item, t("treeAddLine"), lambda: self.addLineRequested.emit("variant", variant.id), indentLevel=1, accentColor=COLOR_LINE, ownerId=variant.id, scopeIds=scope, excludeIds=[sub.id for sub in variant.subCategories])    # 在子分類內時隱藏，因為它位於子分類上方    # 新增的 Line 會接在最後一條 Line 後面
        for sub in variant.subCategories:
            self.addSubCategoryItem(item, sub, scope)
        self.addActionItem(item, t("treeAddSub"), lambda: self.addSubCategoryRequested.emit(variant.id), indentLevel=1, accentColor=COLOR_SUBCATEGORY, ownerId=variant.id, scopeIds=scope)    # 新增的子分類會接在最後一個子分類後面

    def addSubCategoryItem(self, parent, sub, parentScope):
        scope = parentScope + (sub.id,)
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, sub.id)
        item.setData(0, TYPE_ROLE, "subcategory")
        item.setSizeHint(0, QSize(0, ROW_HEIGHT))
        row = TreeRowWidget(sub.name or t("treeUnnamedSub"), indentLevel=1, accentColor=COLOR_SUBCATEGORY, hasToggle=True, scopeIds=scope)
        row.hovered.connect(self.onRowHovered)
        row.setToolTip(sub.name)
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("subcategory", sub.id))
        row.toggleClicked.connect(lambda: self.toggleItem(item, row))
        self.tree.setItemWidget(item, 0, row)

        for number, line in enumerate(sub.lines, 1):
            self.addLineItem(item, line, indentLevel=2, number=number, scope=scope)

        self.addActionItem(item, t("treeAddLine"), lambda: self.addLineRequested.emit("subcategory", sub.id), indentLevel=2, accentColor=COLOR_LINE, ownerId=sub.id, scopeIds=scope)

    def addLineItem(self, parent, line, indentLevel, number, scope):
        item = QTreeWidgetItem(parent)
        item.setData(0, Qt.UserRole + 1, line.id)
        item.setData(0, TYPE_ROLE, "line")
        item.setSizeHint(0, QSize(0, ROW_HEIGHT))
        row = TreeRowWidget(f"Line.{number}", indentLevel=indentLevel, accentColor=COLOR_LINE, scopeIds=scope)
        row.hovered.connect(self.onRowHovered)
        row.setToolTip(textwrap.fill(line.pgn, TOOLTIP_WIDTH) if line.pgn.strip() else t("treeEmptyLine"))    # 滑過顯示完整 PGN
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("line", line.id))
        self.tree.setItemWidget(item, 0, row)

    def addActionItem(self, parent, text, onClick, indentLevel, accentColor, ownerId, scopeIds, excludeIds=()):    # 固定的「+ 新增」動作列
        item = QTreeWidgetItem(parent)
        item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
        item.setSizeHint(0, QSize(0, ACTION_ROW_HEIGHT))
        row = ActionRow(text, onClick, indentLevel, accentColor, ownerId, scopeIds, excludeIds)
        row.item = item
        row.hovered.connect(self.onRowHovered)
        self.actionRows.append(row)
        self.tree.setItemWidget(item, 0, row)

    def toggleItem(self, item, row):    # 自製展開/折疊，取代 Qt 原生箭頭
        expanded = not item.isExpanded()
        item.setExpanded(expanded)
        row.setToggleIcon(expanded)