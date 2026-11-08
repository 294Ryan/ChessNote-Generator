import json
import os

from PyQt5.QtWidgets import QMainWindow, QSplitter, QFileDialog, QToolButton, QActionGroup
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence

from core.models import Opening, moveItem
from core.i18n import t, setLanguage, getLanguage, LANGUAGES
from core.project_io import saveProject, loadProject, InvalidProjectFile, KIND_JSON, KIND_HTML
from core.exporter_docx import exportDocx
from core.exporter_html import exportHtml
from core.exporter_pdf import exportPdf
from ui.tree_panel import TreePanel
from ui.editor_panel import EditorPanel
from ui.theme import setTheme, isDark, windowStyle
from ui.dialogs import showInfo, showConfirm, showSaveChoice


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Opening Note Generator")
        self.resize(1000, 700)

        self.opening = Opening()
        self.currentProjectPath = None
        self.currentKind = None    # 目前檔案類型：json（暫存檔）、html（筆記）；尚未存檔的新內容為 None
        self.savedSnapshot = self.snapshot()    # 最後一次存檔（或開啟）時的內容，用來判斷有沒有未存的修改

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
        self.fileMenu = self.menuBar().addMenu("")    # 文字由 retranslateMenu 依語言設定
        self.openAction = self.fileMenu.addAction("", self.onOpenProject)
        self.saveAction = self.fileMenu.addAction("", self.onSaveProject)
        self.saveAsAction = self.fileMenu.addAction("", self.onSaveProjectAs)
        self.openAction.setShortcut(QKeySequence("Ctrl+O"))
        self.saveAction.setShortcut(QKeySequence("Ctrl+S"))
        self.saveAsAction.setShortcut(QKeySequence("Ctrl+Shift+S"))

        self.exportMenu = self.menuBar().addMenu("")
        self.exportActions = {}
        for ext, handler in (("docx", self.onExportDocx), ("html", self.onExportHtml), ("pdf", self.onExportPdf)):
            self.exportActions[ext] = self.exportMenu.addAction("", handler)

        self.languageMenu = self.menuBar().addMenu("")
        self.languageActions = {}
        languageGroup = QActionGroup(self)    # 互斥，選單內只會有一個打勾
        for code, name in LANGUAGES:
            action = self.languageMenu.addAction(name)    # 語言名稱一律用該語言自己的寫法
            action.setCheckable(True)
            action.setActionGroup(languageGroup)
            action.triggered.connect(lambda checked, c=code: self.onLanguageSelected(c))
            self.languageActions[code] = action
        self.retranslateMenu()

        self.themeButton = QToolButton()    # 選單列右側的主題切換鈕
        self.themeButton.setObjectName("themeToggle")
        self.themeButton.setCursor(Qt.PointingHandCursor)
        self.themeButton.clicked.connect(self.onToggleTheme)
        self.menuBar().setCornerWidget(self.themeButton, Qt.TopRightCorner)

    ### 語言 ###
    def retranslateMenu(self):
        self.fileMenu.setTitle(t("menuFile"))
        self.openAction.setText(t("menuOpenProject"))
        self.saveAction.setText(t("menuSaveProject"))
        self.saveAsAction.setText(t("menuSaveAsProject"))
        self.exportMenu.setTitle(t("menuExport"))
        for ext, action in self.exportActions.items():
            action.setText(t("exportAs", ext=ext))
        title = t("menuLanguage")
        self.languageMenu.setTitle(title if getLanguage() == "en" else f"{title} / Language")    # 附英文，方便看不懂當前語言的人找到
        self.languageActions[getLanguage()].setChecked(True)
        self.updateTitle()    # 「未命名專案」也要跟著語言換

    def onLanguageSelected(self, code):
        setLanguage(code)
        self.retranslateMenu()
        self.applyTheme()    # 主題鈕文字也要換語言
        scrollBar = self.editorPanel.verticalScrollBar()
        scrollValue = scrollBar.value()
        self.refreshUI()    # 重建兩側，標籤與提示文字才會換語言
        QTimer.singleShot(0, lambda: scrollBar.setValue(scrollValue))

    ### 主題 ###
    def applyTheme(self):
        self.setStyleSheet(windowStyle())
        self.treePanel.applyTheme()
        self.editorPanel.applyTheme()
        self.themeButton.setText(t("themeLight") if isDark() else t("themeDark"))    # 顯示點擊後會切換成的主題
        self.themeButton.setToolTip(t("themeToLight") if isDark() else t("themeToDark"))

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
        self.updateTitle()

    def onModelChanged(self):    # 欄位文字變動時，只刷新樹狀標籤，避免編輯區失焦
        self.treePanel.rebuild(self.opening)
        self.updateTitle()

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
        if not showConfirm(self, t("deleteTitle"), t("deleteMessage"), t("deleteConfirm"), danger=True):
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
    def snapshot(self):
        return json.dumps(self.opening.toDict(), sort_keys=True)

    def isDirty(self):    # 以內容快照比對，切換主題與語言不會被當成修改
        return self.snapshot() != self.savedSnapshot

    def updateTitle(self):    # 有未存修改時標題前加 *
        name = os.path.basename(self.currentProjectPath) if self.currentProjectPath else t("untitledProject")
        self.setWindowTitle(f"{'*' if self.isDirty() else ''}{name} - Chess Opening Note Generator")

    def saveTo(self, path, kind):    # kind 為 json（暫存檔）或 html（筆記，重新產生並覆寫）；失敗時提示並回傳 False
        try:
            if kind == KIND_HTML:
                exportHtml(self.opening, path)
            else:
                saveProject(self.opening, path)
        except Exception as e:
            showInfo(self, t("menuSaveProject"), t("saveFailed") + str(e))
            return False
        self.currentProjectPath = path
        self.currentKind = kind
        self.savedSnapshot = self.snapshot()
        self.updateTitle()
        return True

    def doSave(self):    # 不再確認：已有路徑就依目前檔案類型寫回，否則選位置；回傳 True 代表真的存了
        if self.currentProjectPath:
            return self.saveTo(self.currentProjectPath, self.currentKind)
        return self.chooseSavePath()

    def chooseSavePath(self):    # 另存一律是暫存檔（.json）
        path, _ = QFileDialog.getSaveFileName(self, t("menuSaveAsProject"), "", "JSON Files (*.json)")
        return self.saveTo(path, KIND_JSON) if path else False

    def onSaveProject(self):    # 選單 / Ctrl+S：先確認再存；未命名專案沒有檔案可覆蓋，直接走另存
        if not self.currentProjectPath:
            return self.onSaveProjectAs()
        message = t("saveMessage", file=os.path.basename(self.currentProjectPath))
        if not showConfirm(self, t("menuSaveProject"), message, t("save"), kind="check"):
            return False
        return self.doSave()

    def onSaveProjectAs(self):
        message = t("saveAsMessageKeep" if self.currentProjectPath else "saveAsMessage")
        if not showConfirm(self, t("menuSaveAsProject"), message, t("chooseLocation"), kind="check"):
            return False
        return self.chooseSavePath()

    def confirmDiscardChanges(self, messageKey):    # 有未存修改時詢問；messageKey 為 unsavedClosing / unsavedOpening；回傳 True 代表可以繼續
        if not self.isDirty():
            return True
        choice = showSaveChoice(self, t("unsavedTitle"), t(messageKey), t("save"), t("discard"))
        if choice == "save":
            return self.doSave()    # 使用者已選擇要存，不再跳第二次確認；選位置被取消時回傳 False
        return choice == "discard"

    def closeEvent(self, event):
        if self.confirmDiscardChanges("unsavedClosing"):
            event.accept()
        else:
            event.ignore()

    def onOpenProject(self):
        if not self.confirmDiscardChanges("unsavedOpening"):
            return
        path, _ = QFileDialog.getOpenFileName(self, t("menuOpenProject"), "", "Notes and Drafts (*.html *.json)")
        if not path:
            return
        try:
            opening, kind = loadProject(path)    # 先驗證；不合格就不動目前的內容
        except InvalidProjectFile:
            showInfo(self, t("menuOpenProject"), t("invalidFile"))
            return
        except Exception as e:
            showInfo(self, t("menuOpenProject"), t("openFailed") + str(e))
            return
        self.opening = opening
        self.currentProjectPath = path
        self.currentKind = kind
        self.savedSnapshot = self.snapshot()
        self.refreshUI()

    ### 匯出 ###
    def onExportDocx(self):
        path, _ = QFileDialog.getSaveFileName(self, t("exportAs", ext="docx"), "", "Word Files (*.docx)")
        if path:
            exportDocx(self.opening, path)
            showInfo(self, t("exportDone"), t("exportDoneMsg", ext="docx"))

    def onExportHtml(self):
        path, _ = QFileDialog.getSaveFileName(self, t("exportAs", ext="html"), "", "HTML Files (*.html)")
        if path:
            exportHtml(self.opening, path)
            showInfo(self, t("exportDone"), t("exportDoneMsg", ext="html"))

    def onExportPdf(self):
        path, _ = QFileDialog.getSaveFileName(self, t("exportAs", ext="pdf"), "", "PDF Files (*.pdf)")
        if path:
            exportPdf(self.opening, path)
            showInfo(self, t("exportDone"), t("exportDoneMsg", ext="pdf"))