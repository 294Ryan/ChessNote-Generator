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
        self.setWindowTitle("ChessNote Generator")
        self.resize(1000, 700)

        self.opening = Opening()
        self.currentProjectPath = None
        self.currentKind = None    # Current file kind: json (draft) or html (note); None for new unsaved content
        self.savedSnapshot = self.snapshot()    # Content at last save/open, used to detect unsaved changes

        self.treePanel = TreePanel()
        self.editorPanel = EditorPanel(self.onModelChanged, self.refreshUI)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.treePanel)
        splitter.addWidget(self.editorPanel)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self.buildMenu()
        self.connectSignals()
        self.applyTheme()
        self.refreshUI()

    def buildMenu(self):
        self.fileMenu = self.menuBar().addMenu("")    # Text is set by retranslateMenu per language
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
        languageGroup = QActionGroup(self)
        for code, name in LANGUAGES:
            action = self.languageMenu.addAction(name)    # Language names are shown in their own language
            action.setCheckable(True)
            action.setActionGroup(languageGroup)
            action.triggered.connect(lambda checked, c=code: self.onLanguageSelected(c))
            self.languageActions[code] = action
        self.retranslateMenu()

        self.themeButton = QToolButton()
        self.themeButton.setObjectName("themeToggle")
        self.themeButton.setCursor(Qt.PointingHandCursor)
        self.themeButton.clicked.connect(self.onToggleTheme)
        self.menuBar().setCornerWidget(self.themeButton, Qt.TopRightCorner)

    ### Language ###
    def retranslateMenu(self):
        self.fileMenu.setTitle(t("menuFile"))
        self.openAction.setText(t("menuOpenProject"))
        self.saveAction.setText(t("menuSaveProject"))
        self.saveAsAction.setText(t("menuSaveAsProject"))
        self.exportMenu.setTitle(t("menuExport"))
        for ext, action in self.exportActions.items():
            action.setText(t("exportAs", ext=ext))
        title = t("menuLanguage")
        self.languageMenu.setTitle(title if getLanguage() == "en" else f"{title} / Language")    # English added so users who can't read the current language can find it
        self.languageActions[getLanguage()].setChecked(True)
        self.updateTitle()    # 'Untitled project' also follows the language

    def onLanguageSelected(self, code):
        setLanguage(code)
        self.retranslateMenu()
        self.applyTheme()
        scrollBar = self.editorPanel.verticalScrollBar()
        scrollValue = scrollBar.value()
        self.refreshUI()    # Rebuild both sides so labels and tooltips change language
        QTimer.singleShot(0, lambda: scrollBar.setValue(scrollValue))

    ### Theme ###
    def applyTheme(self):
        self.setStyleSheet(windowStyle())
        self.treePanel.applyTheme()
        self.editorPanel.applyTheme()
        self.themeButton.setText(t("themeLight") if isDark() else t("themeDark"))    # Shows the theme it will switch to when clicked
        self.themeButton.setToolTip(t("themeToLight") if isDark() else t("themeToDark"))

    def onToggleTheme(self):
        setTheme("light" if isDark() else "dark")
        self.applyTheme()
        scrollBar = self.editorPanel.verticalScrollBar()
        scrollValue = scrollBar.value()
        self.refreshUI()    # Rebuild both sides so nodes and cards pick up the new palette
        QTimer.singleShot(0, lambda: scrollBar.setValue(scrollValue))

    def connectSignals(self):
        self.treePanel.nodeSelected.connect(self.editorPanel.scrollToNode)
        self.treePanel.addVariantRequested.connect(self.onAddVariant)
        self.treePanel.addSubCategoryRequested.connect(self.onAddSubCategory)
        self.treePanel.addLineRequested.connect(self.onAddLine)
        self.treePanel.deleteRequested.connect(self.onDeleteNode)
        self.treePanel.reorderRequested.connect(self.onReorder)

    def refreshUI(self):    # Rebuild both sides after structural changes (add/delete/save/load)
        self.treePanel.rebuild(self.opening)
        self.editorPanel.rebuild(self.opening)
        self.updateTitle()

    def onModelChanged(self):    # On field text changes refresh only the tree labels, so the editor keeps focus
        self.treePanel.rebuild(self.opening)
        self.updateTitle()

    ### Add node ###
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

    ### Delete node ###
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

    ### Tree drag reorder ###
    def allSiblingLists(self):    # Every list whose items can be reordered
        yield self.opening.variants
        for variant in self.opening.variants:
            yield variant.lines
            yield variant.subCategories
            for sub in variant.subCategories:
                yield sub.lines

    def onReorder(self, draggedId, targetId, insertAfter):
        for siblings in self.allSiblingLists():
            ids = [n.id for n in siblings]
            if draggedId in ids and targetId in ids:    # Both must be in the same list; otherwise it crosses levels, so ignore
                targetIndex = ids.index(targetId) + (1 if insertAfter else 0)
                if moveItem(siblings, draggedId, targetIndex):
                    self.refreshUI()
                return

    ### Find node ###
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

    ### Save / Load ###
    def snapshot(self):
        return json.dumps(self.opening.toDict(), sort_keys=True)

    def isDirty(self):    # Compare content snapshots so theme/language changes don't count as edits
        return self.snapshot() != self.savedSnapshot

    def updateTitle(self):
        name = os.path.basename(self.currentProjectPath) if self.currentProjectPath else t("untitledProject")
        self.setWindowTitle(f"{'*' if self.isDirty() else ''}{name} - ChessNote Generator")

    def saveTo(self, path, kind):    # kind is json (draft) or html (note, regenerated and overwritten); on failure show a message and return False
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

    def doSave(self):    # No confirmation: write back by current file kind if a path exists, else ask for a location; True if actually saved
        if self.currentProjectPath:
            return self.saveTo(self.currentProjectPath, self.currentKind)
        return self.chooseSavePath()

    def chooseSavePath(self):    # Save As always writes a draft (.json)
        path, _ = QFileDialog.getSaveFileName(self, t("menuSaveAsProject"), "", "JSON Files (*.json)")
        return self.saveTo(path, KIND_JSON) if path else False

    def onSaveProject(self):    # Menu / Ctrl+S: confirm then save; an untitled project has no file to overwrite, so go to Save As
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

    def confirmDiscardChanges(self, messageKey):    # Ask when there are unsaved changes; messageKey is unsavedClosing / unsavedOpening; True means continue
        if not self.isDirty():
            return True
        choice = showSaveChoice(self, t("unsavedTitle"), t(messageKey), t("save"), t("discard"))
        if choice == "save":
            return self.doSave()    # User already chose to save, so no second confirmation; False if the location picker is cancelled
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
            opening, kind = loadProject(path)    # Validate first; don't touch the current content if invalid
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

    ### Export ###
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