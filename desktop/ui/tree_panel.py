from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QLabel, QToolButton, QFrame, QAbstractItemView
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
import textwrap
from ui.theme import palette, scrollbarStyle
from core.i18n import t

TYPE_ROLE = Qt.UserRole + 2    # Item data: node type (variant / subcategory / line); node id is at Qt.UserRole + 1
INDENT_WIDTH = 18    # Indent width per level (px); keep proportional to editor_panel (narrower here)

COLOR_OPENING = "#6b7280"
COLOR_VARIANT = "#2b6cb0"
COLOR_SUBCATEGORY = "#2f855a"
COLOR_LINE = "#8a6d3b"

ROW_HEIGHT = 30    # Row height (px); sets the item widget height
ACTION_ROW_HEIGHT = 24    # Height of the '+ Add' row
CHIP_PADDING = 6    # Left padding inside the chip; the '+' of add rows aligns here
TOOLTIP_WIDTH = 48    # Characters per PGN line in the tooltip


def tint(hexColor, alpha):    # Convert #rrggbb to rgba with alpha, for tinted backgrounds
    r, g, b = (int(hexColor[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


class TreeRowWidget(QWidget):    # One node row; indent and color bar come from parameters, not Qt's native arrows
    deleteClicked = pyqtSignal()
    toggleClicked = pyqtSignal()
    hovered = pyqtSignal(object)    # Emits scopeIds on mouse enter to decide which '+ Add' rows to show

    def __init__(self, label, indentLevel=0, accentColor="#ccc", showDelete=True, hasToggle=False, expanded=True, scopeIds=()):
        super().__init__()
        self.scopeIds = tuple(scopeIds)    # Ids of the blocks this row belongs to (outer to inner)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(4 + indentLevel * INDENT_WIDTH, 2, 4, 2)

        chip = QFrame()    # Row chip: tinted node color, darker on hover
        chip.setObjectName("chip")
        p = palette()
        chip.setStyleSheet(    # Background alphas live in ui/theme.py (chipAlpha / chipHoverAlpha)
            f"#chip {{ background: {tint(accentColor, p.chipAlpha)}; border-radius: 4px; }}"
            f"#chip:hover {{ background: {tint(accentColor, p.chipHoverAlpha)}; }}"
        )
        outer.addWidget(chip)

        layout = QHBoxLayout(chip)
        layout.setContentsMargins(CHIP_PADDING, 0, 4, 0)
        layout.setSpacing(6)

        bar = QFrame()
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
            spacer.setFixedWidth(20)    # Rows without a toggle arrow reserve the same width to keep text aligned
            layout.addWidget(spacer)

        self.nameLabel = QLabel(label)
        self.nameLabel.setStyleSheet(f"background: transparent; color: {p.ink};")
        layout.addWidget(self.nameLabel)
        layout.addStretch()

        self.deleteButton = QToolButton()
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

    def enterEvent(self, event):
        self.deleteButton.setVisible(self.deleteButton.isEnabled())
        self.hovered.emit(self.scopeIds)

    def leaveEvent(self, event):
        self.deleteButton.setVisible(False)


class ActionRow(QWidget):    # Fixed '+ Add XXX' action row; not tied to any node data; always left-aligned, '+' aligns with the new node's color bar
    hovered = pyqtSignal(object)

    def __init__(self, text, onClick, indentLevel, accentColor, ownerId, scopeIds, excludeIds=()):
        super().__init__()
        self.onClick = onClick
        self.ownerId = ownerId    # Shown only while the mouse is inside this block
        self.scopeIds = tuple(scopeIds)
        self.excludeIds = frozenset(excludeIds)    # Hidden while the mouse is inside these blocks (avoids content jumping when this row expands above the cursor)
        self.item = None    # Matching QTreeWidgetItem, used to show/hide the row
        self.setCursor(Qt.PointingHandCursor)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(4 + indentLevel * INDENT_WIDTH, 2, 4, 2)

        chip = QFrame()
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
        event.accept()    # Accept the press so the release event reaches this widget

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.onClick()


class DragSortTree(QTreeWidget):    # Only same-parent, same-type nodes may be reordered; the model is changed externally and the tree rebuilt
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

    def isSameGroup(self, source, target):    # Same type and same parent (including itself) is a valid drop area
        if source is None or target is None:
            return False
        sourceType = source.data(0, TYPE_ROLE)
        return bool(sourceType) and sourceType == target.data(0, TYPE_ROLE) and self.parentIdOf(source) == self.parentIdOf(target)

    def findDropTarget(self, event):    # Returns (draggedId, targetId, insertAfter) if valid, else None
        source = self.currentItem()
        target = self.itemAt(event.pos())
        if target is source or not self.isSameGroup(source, target):
            return None
        insertAfter = event.pos().y() > self.visualItemRect(target).center().y()
        return source.data(0, Qt.UserRole + 1), target.data(0, Qt.UserRole + 1), insertAfter

    def dragMoveEvent(self, event):
        if not self.isSameGroup(self.currentItem(), self.itemAt(event.pos())):
            event.ignore()
            return
        super().dragMoveEvent(event)    # Let Qt update the drop indicator line
        event.setDropAction(Qt.MoveAction)
        event.accept()    # Qt would reject this under InternalMove rules; force accept so the cursor isn't forbidden

    def dropEvent(self, event):
        result = self.findDropTarget(event)
        event.setDropAction(Qt.IgnoreAction)    # Don't let Qt move the item, otherwise the original is removed
        event.accept()
        if result:
            QTimer.singleShot(0, lambda: self.reorderRequested.emit(*result))    # Defer the rebuild until the drag finishes


class TreePanel(QWidget):
    nodeSelected = pyqtSignal(str)    # nodeId
    addVariantRequested = pyqtSignal()
    addSubCategoryRequested = pyqtSignal(str)    # variantId
    addLineRequested = pyqtSignal(str, str)    # (parentType, parentId); parentType: variant | subcategory
    deleteRequested = pyqtSignal(str, str)    # (nodeType, nodeId)
    reorderRequested = pyqtSignal(str, str, bool)    # (draggedId, targetId, insertAfter)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = DragSortTree()
        self.tree.reorderRequested.connect(self.reorderRequested)
        self.tree.mouseLeft.connect(lambda: self.onRowHovered(()))
        self.activeScopes = set()    # Id of the block under the mouse; kept across tree rebuilds
        self.actionRows = []
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(0)    # Disable Qt's native indent; TreeRowWidget handles it
        self.tree.setRootIsDecorated(False)    # Disable native expand arrows; custom toggle buttons are used
        self.applyTheme()
        self.tree.itemClicked.connect(self.onItemClicked)
        layout.addWidget(self.tree)

    def applyTheme(self):    # Remove default selection/hover background and frame; rows paint their own chips. Rebuild the tree after a theme switch to apply new colors
        self.tree.setStyleSheet(
            f"QTreeWidget {{ border: none; outline: 0; background: {palette().treeBg}; }}"
            "QTreeWidget::item, QTreeWidget::item:hover, QTreeWidget::item:selected { background: transparent; }"
            + scrollbarStyle()
        )

    def onRowHovered(self, scopeIds):    # Mouse entered a row: show only the '+ Add' rows of its block
        if set(scopeIds) != self.activeScopes:
            self.activeScopes = set(scopeIds)
            self.applyActiveScopes()

    def applyActiveScopes(self):    # Hidden '+' rows are fully hidden (no space); they expand only when the mouse reaches their block
        for row in self.actionRows:
            revealed = row.ownerId in self.activeScopes and not (self.activeScopes & row.excludeIds)
            row.item.setHidden(not revealed)

    def onItemClicked(self, item, column):
        nodeId = item.data(0, Qt.UserRole + 1)
        if nodeId:
            self.nodeSelected.emit(nodeId)

    ### Rebuild the whole tree from the Opening model ###
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

        self.addActionItem(self.tree, t("treeAddVariant"), self.addVariantRequested.emit, indentLevel=0, accentColor=COLOR_VARIANT, ownerId="tail", scopeIds=("tail",))    # Shown when the mouse is over the last Variant block or this row
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

        for number, line in enumerate(variant.lines, 1):    # Lines come before subcategories
            self.addLineItem(item, line, indentLevel=1, number=number, scope=scope)
        self.addActionItem(item, t("treeAddLine"), lambda: self.addLineRequested.emit("variant", variant.id), indentLevel=1, accentColor=COLOR_LINE, ownerId=variant.id, scopeIds=scope, excludeIds=[sub.id for sub in variant.subCategories])    # Hidden inside a subcategory (it sits above them); a new Line goes after the last Line
        for sub in variant.subCategories:
            self.addSubCategoryItem(item, sub, scope)
        self.addActionItem(item, t("treeAddSub"), lambda: self.addSubCategoryRequested.emit(variant.id), indentLevel=1, accentColor=COLOR_SUBCATEGORY, ownerId=variant.id, scopeIds=scope)    # A new subcategory goes after the last subcategory

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
        row.setToolTip(textwrap.fill(line.pgn, TOOLTIP_WIDTH) if line.pgn.strip() else t("treeEmptyLine"))
        row.deleteClicked.connect(lambda: self.deleteRequested.emit("line", line.id))
        self.tree.setItemWidget(item, 0, row)

    def addActionItem(self, parent, text, onClick, indentLevel, accentColor, ownerId, scopeIds, excludeIds=()):
        item = QTreeWidgetItem(parent)
        item.setFlags(item.flags() & ~Qt.ItemIsDragEnabled)
        item.setSizeHint(0, QSize(0, ACTION_ROW_HEIGHT))
        row = ActionRow(text, onClick, indentLevel, accentColor, ownerId, scopeIds, excludeIds)
        row.item = item
        row.hovered.connect(self.onRowHovered)
        self.actionRows.append(row)
        self.tree.setItemWidget(item, 0, row)

    def toggleItem(self, item, row):
        expanded = not item.isExpanded()
        item.setExpanded(expanded)
        row.setToggleIcon(expanded)