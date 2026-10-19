from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame, QPushButton
from PyQt5.QtCore import Qt
from ui.line_widget import PgnImageEditor

INDENT_WIDTH = 28    # 每層縮排的像素寬度，呈現 Variant > 子分類 > Line 的從屬關係

COLOR_OPENING = "#6b7280"
COLOR_VARIANT = "#2b6cb0"
COLOR_SUBCATEGORY = "#2f855a"
COLOR_LINE = "#8a6d3b"


class EditorPanel(QScrollArea):
    def __init__(self, onModelChanged):
        super().__init__()
        self.onModelChanged = onModelChanged    # 欄位變動時通知 MainWindow 更新樹狀標籤
        self.setWidgetResizable(True)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignTop)
        self.setWidget(self.container)

        self.nodeWidgets = {}    # nodeId -> 區塊 widget，供樹狀導覽跳轉用

    def rebuild(self, opening):
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.nodeWidgets.clear()

        self.addOpeningSection(opening)

        for variant in opening.variants:
            self.addVariantSection(variant)
            for sub in variant.subCategories:
                self.addSubCategorySection(sub)
                for line in sub.lines:
                    self.addLineSection(line, indentLevel=2)
            for line in variant.lines:
                self.addLineSection(line, indentLevel=1)

        self.layout.addStretch()

    ### 區塊建構 ###
    def addOpeningSection(self, opening):
        frame = self.makeFrame(indentLevel=0, accentColor=COLOR_OPENING)
        layout = frame.layout()
        layout.addWidget(self.makeHeading("📋 開局基本資訊", COLOR_OPENING))

        layout.addWidget(QLabel("開局名稱"))
        nameEdit = QLineEdit(opening.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(opening, "name", text))
        layout.addWidget(nameEdit)

        layout.addWidget(QLabel("開局概述"))
        descEdit = QTextEdit(opening.description)
        descEdit.setMaximumHeight(60)
        descEdit.textChanged.connect(lambda: self.updateField(opening, "description", descEdit.toPlainText()))
        layout.addWidget(descEdit)

        layout.addWidget(QLabel("起始 PGN"))
        pgnEditor = PgnImageEditor(opening.startingPgn, opening.startingImagePath, collapsible=False)
        pgnEditor.changed.connect(lambda: self.updateStartingPgn(opening, pgnEditor))
        layout.addWidget(pgnEditor)

        self.registerSection("opening", frame)

    def addVariantSection(self, variant):
        frame = self.makeFrame(indentLevel=0, accentColor=COLOR_VARIANT)
        layout = frame.layout()
        layout.addWidget(self.makeHeading("VARIANT", COLOR_VARIANT))

        nameEdit = QLineEdit(variant.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(variant, "name", text))
        layout.addWidget(nameEdit)

        self.addDescriptionField(layout, variant)
        self.registerSection(variant.id, frame)

    def addSubCategorySection(self, sub):
        frame = self.makeFrame(indentLevel=1, accentColor=COLOR_SUBCATEGORY)
        layout = frame.layout()
        layout.addWidget(self.makeHeading("子分類", COLOR_SUBCATEGORY))

        nameEdit = QLineEdit(sub.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(sub, "name", text))
        layout.addWidget(nameEdit)

        self.addDescriptionField(layout, sub)
        self.registerSection(sub.id, frame)

    def addLineSection(self, line, indentLevel):
        frame = self.makeFrame(indentLevel=indentLevel, accentColor=COLOR_LINE)
        layout = frame.layout()
        layout.addWidget(self.makeHeading("LINE", COLOR_LINE))

        nameEdit = QLineEdit(line.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(line, "name", text))
        layout.addWidget(nameEdit)

        self.addDescriptionField(layout, line)

        pgnEditor = PgnImageEditor(line.pgn, line.imagePath, collapsible=True)
        pgnEditor.changed.connect(lambda: self.updateLinePgn(line, pgnEditor))
        layout.addWidget(pgnEditor)

        self.registerSection(line.id, frame)

    def addDescriptionField(self, layout, obj):    # Variant / SubCategory / Line 共用的選填說明欄位
        descEdit = QTextEdit(obj.description)
        descEdit.setPlaceholderText("說明（選填）")
        descEdit.setMaximumHeight(50)
        descEdit.textChanged.connect(lambda: self.updateField(obj, "description", descEdit.toPlainText()))
        layout.addWidget(descEdit)

    ### 共用小工具 ###
    def makeFrame(self, indentLevel=0, accentColor="#ccc"):    # indentLevel 呈現 Variant > 子分類 > Line 的從屬層次
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        marginLeft = indentLevel * INDENT_WIDTH
        frame.setStyleSheet(
            f"QFrame {{ border-left: 4px solid {accentColor}; margin-left: {marginLeft}px;"
            f" background: white; border-radius: 3px; }}"
        )
        QVBoxLayout(frame)
        return frame

    def makeHeading(self, text, color):    # 類型徽章，靠左對齊不佔滿整行
        row = QWidget()
        rowLayout = QHBoxLayout(row)
        rowLayout.setContentsMargins(0, 0, 0, 4)
        badge = QLabel(text)
        badge.setStyleSheet(
            f"background: {color}; color: white; padding: 2px 8px;"
            f" border-radius: 3px; font-weight: bold; font-size: 11px;"
        )
        rowLayout.addWidget(badge)
        rowLayout.addStretch()
        return row

    def registerSection(self, nodeId, frame):
        self.layout.addWidget(frame)
        self.nodeWidgets[nodeId] = frame

    ### model 更新 ###
    def updateField(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.onModelChanged()

    def updateStartingPgn(self, opening, pgnEditor):
        opening.startingPgn = pgnEditor.getPgn()
        opening.startingImagePath = pgnEditor.getImagePath()
        self.onModelChanged()

    def updateLinePgn(self, line, pgnEditor):
        line.pgn = pgnEditor.getPgn()
        line.imagePath = pgnEditor.getImagePath()
        self.onModelChanged()

    def scrollToNode(self, nodeId):
        widget = self.nodeWidgets.get(nodeId)
        if widget:
            self.ensureWidgetVisible(widget)