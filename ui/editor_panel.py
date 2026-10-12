from PyQt5.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QFrame, QPushButton
from PyQt5.QtCore import Qt
from ui.line_widget import PgnImageEditor


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
                    self.addLineSection(line)
            for line in variant.lines:
                self.addLineSection(line)

        self.layout.addStretch()

    ### 區塊建構 ###
    def addOpeningSection(self, opening):
        frame = self.makeFrame()
        layout = frame.layout()

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
        frame = self.makeFrame()
        layout = frame.layout()
        layout.addWidget(self.makeHeading(f"Variant"))

        nameEdit = QLineEdit(variant.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(variant, "name", text))
        layout.addWidget(nameEdit)

        self.registerSection(variant.id, frame)

    def addSubCategorySection(self, sub):
        frame = self.makeFrame()
        layout = frame.layout()
        layout.addWidget(self.makeHeading("子分類"))

        nameEdit = QLineEdit(sub.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(sub, "name", text))
        layout.addWidget(nameEdit)

        self.registerSection(sub.id, frame)

    def addLineSection(self, line):
        frame = self.makeFrame()
        layout = frame.layout()
        layout.addWidget(self.makeHeading("Line"))

        nameEdit = QLineEdit(line.name)
        nameEdit.textChanged.connect(lambda text: self.updateField(line, "name", text))
        layout.addWidget(nameEdit)

        pgnEditor = PgnImageEditor(line.pgn, line.imagePath, collapsible=True)
        pgnEditor.changed.connect(lambda: self.updateLinePgn(line, pgnEditor))
        layout.addWidget(pgnEditor)

        self.registerSection(line.id, frame)

    ### 共用小工具 ###
    def makeFrame(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        QVBoxLayout(frame)
        return frame

    def makeHeading(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold;")
        return label

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