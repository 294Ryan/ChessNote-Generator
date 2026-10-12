from PyQt5.QtWidgets import QMainWindow, QSplitter, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

from core.models import Opening
from core.project_io import saveProject, loadProject
from core.exporter_docx import exportDocx
from core.exporter_html import exportHtml
from ui.tree_panel import TreePanel
from ui.editor_panel import EditorPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Opening Note Generator")
        self.resize(1000, 700)

        self.opening = Opening()
        self.currentProjectPath = None

        self.treePanel = TreePanel()
        self.editorPanel = EditorPanel(self.onModelChanged)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.treePanel)
        splitter.addWidget(self.editorPanel)
        splitter.setStretchFactor(1, 1)    # 右側編輯區優先佔用空間
        self.setCentralWidget(splitter)

        self.buildMenu()
        self.connectSignals()
        self.refreshUI()

    def buildMenu(self):
        fileMenu = self.menuBar().addMenu("檔案")
        fileMenu.addAction("開啟專案", self.onOpenProject)
        fileMenu.addAction("儲存專案", self.onSaveProject)

        exportMenu = self.menuBar().addMenu("匯出")
        exportMenu.addAction("匯出 .docx", self.onExportDocx)
        exportMenu.addAction("匯出 .html", self.onExportHtml)

    def connectSignals(self):
        self.treePanel.nodeSelected.connect(self.editorPanel.scrollToNode)
        self.treePanel.addVariantRequested.connect(self.onAddVariant)
        self.treePanel.addSubCategoryRequested.connect(self.onAddSubCategory)
        self.treePanel.addLineRequested.connect(self.onAddLine)
        self.treePanel.deleteRequested.connect(self.onDeleteNode)

    def refreshUI(self):    # 結構變動（新增/刪除/存讀檔）後重建左右兩側
        self.treePanel.rebuild(self.opening)
        self.editorPanel.rebuild(self.opening)

    def onModelChanged(self):    # 欄位文字變動時，只刷新樹狀標籤，避免編輯區失焦
        self.treePanel.rebuild(self.opening)

    ### 新增節點 ###
    def onAddVariant(self):
        self.opening.addVariant()
        self.refreshUI()

    def onAddSubCategory(self, variantId):
        variant = self.findVariant(variantId)
        if variant:
            variant.addSubCategory()
            self.refreshUI()

    def onAddLine(self, parentType, parentId):
        parent = self.findVariant(parentId) if parentType == "variant" else self.findSubCategory(parentId)
        if parent:
            parent.addLine()
            self.refreshUI()

    ### 刪除節點 ###
    def onDeleteNode(self, nodeType, nodeId):
        confirm = QMessageBox.question(self, "確認刪除", "確定要刪除此項目嗎？此動作無法復原。")
        if confirm != QMessageBox.Yes:
            return

        if nodeType == "variant":
            self.opening.variants = [v for v in self.opening.variants if v.id != nodeId]
        elif nodeType == "subcategory":
            for variant in self.opening.variants:
                variant.subCategories = [s for s in variant.subCategories if s.id != nodeId]
        elif nodeType == "line":
            for variant in self.opening.variants:
                variant.lines = [l for l in variant.lines if l.id != nodeId]
                for sub in variant.subCategories:
                    sub.lines = [l for l in sub.lines if l.id != nodeId]

        self.refreshUI()

    ### 查找節點 ###
    def findVariant(self, variantId):
        for variant in self.opening.variants:
            if variant.id == variantId:
                return variant
        return None

    def findSubCategory(self, subId):
        for variant in self.opening.variants:
            for sub in variant.subCategories:
                if sub.id == subId:
                    return sub
        return None

    ### 存檔 / 載入 ###
    def onSaveProject(self):
        path, _ = QFileDialog.getSaveFileName(self, "儲存專案", "", "JSON Files (*.json)")
        if path:
            saveProject(self.opening, path)
            self.currentProjectPath = path

    def onOpenProject(self):
        path, _ = QFileDialog.getOpenFileName(self, "開啟專案", "", "JSON Files (*.json)")
        if path:
            self.opening = loadProject(path)
            self.currentProjectPath = path
            self.refreshUI()

    ### 匯出 ###
    def onExportDocx(self):
        path, _ = QFileDialog.getSaveFileName(self, "匯出 .docx", "", "Word Files (*.docx)")
        if path:
            exportDocx(self.opening, path)
            QMessageBox.information(self, "完成", "已匯出 .docx")

    def onExportHtml(self):
        path, _ = QFileDialog.getSaveFileName(self, "匯出 .html", "", "HTML Files (*.html)")
        if path:
            exportHtml(self.opening, path)
            QMessageBox.information(self, "完成", "已匯出 .html")
