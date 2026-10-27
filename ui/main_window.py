from PyQt5.QtWidgets import QMainWindow, QSplitter, QFileDialog, QMessageBox, QToolButton
from PyQt5.QtCore import Qt, QTimer

from core.models import Opening, moveItem
from core.project_io import saveProject, loadProject
from core.exporter_docx import exportDocx
from core.exporter_html import exportHtml
from core.exporter_pdf import exportPdf
from ui.tree_panel import TreePanel
from ui.editor_panel import EditorPanel
from ui.theme import setTheme, isDark, windowStyle


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Opening Note Generator")
        self.resize(1000, 700)

        self.opening = Opening()
        self.currentProjectPath = None

        self.treePanel = TreePanel()
        self.editorPanel = EditorPanel(self.onModelChanged, self.refreshUI)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.treePanel)
        splitter.addWidget(self.editorPanel)
        splitter.setStretchFactor(1, 1)    # 右側編輯區優先佔用空間
        self.setCentralWidget(splitter)

        self.buildMenu()
        self.connectSignals()
        self.applyTheme()
        self.refreshUI()

    def buildMenu(self):
        fileMenu = self.menuBar().addMenu("檔案")
        fileMenu.addAction("開啟專案", self.onOpenProject)
        fileMenu.addAction("儲存專案", self.onSaveProject)

        exportMenu = self.menuBar().addMenu("匯出")
        exportMenu.addAction("匯出 .docx", self.onExportDocx)
        exportMenu.addAction("匯出 .html", self.onExportHtml)
        exportMenu.addAction("匯出 .pdf", self.onExportPdf)

        self.themeButton = QToolButton()    # 選單列右側的主題切換鈕
        self.themeButton.setObjectName("themeToggle")
        self.themeButton.setCursor(Qt.PointingHandCursor)
        self.themeButton.clicked.connect(self.onToggleTheme)
        self.menuBar().setCornerWidget(self.themeButton, Qt.TopRightCorner)

    ### 主題 ###
    def applyTheme(self):
        self.setStyleSheet(windowStyle())
        self.treePanel.applyTheme()
        self.editorPanel.applyTheme()
        self.themeButton.setText("☀  淺色" if isDark() else "☾  深色")    # 顯示點擊後會切換成的主題
        self.themeButton.setToolTip("切換為淺色主題" if isDark() else "切換為深色主題")

    def onToggleTheme(self):
        setTheme("light" if isDark() else "dark")
        self.applyTheme()
        scrollBar = self.editorPanel.verticalScrollBar()
        scrollValue = scrollBar.value()
        self.refreshUI()    # 重建兩側，節點與卡片才會吃到新色票
        QTimer.singleShot(0, lambda: scrollBar.setValue(scrollValue))

    def connectSignals(self):
        self.treePanel.nodeSelected.connect(self.editorPanel.scrollToNode)
        self.treePanel.addVariantRequested.connect(self.onAddVariant)
        self.treePanel.addSubCategoryRequested.connect(self.onAddSubCategory)
        self.treePanel.addLineRequested.connect(self.onAddLine)
        self.treePanel.deleteRequested.connect(self.onDeleteNode)
        self.treePanel.reorderRequested.connect(self.onReorder)

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

    ### 左側樹拖曳調序 ###
    def allSiblingLists(self):    # 所有「可互相調序」的 list
        yield self.opening.variants
        for variant in self.opening.variants:
            yield variant.lines
            yield variant.subCategories
            for sub in variant.subCategories:
                yield sub.lines

    def onReorder(self, draggedId, targetId, insertAfter):
        for siblings in self.allSiblingLists():
            ids = [n.id for n in siblings]
            if draggedId in ids and targetId in ids:    # 兩者必須在同一個 list，否則是跨層級，忽略
                targetIndex = ids.index(targetId) + (1 if insertAfter else 0)
                if moveItem(siblings, draggedId, targetIndex):
                    self.refreshUI()
                return

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

    def onExportPdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "匯出 .pdf", "", "PDF Files (*.pdf)")
        if path:
            exportPdf(self.opening, path)
            QMessageBox.information(self, "完成", "已匯出 .pdf")