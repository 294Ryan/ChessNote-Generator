package com.chessnote

import com.chessnote.core.I18n
import com.chessnote.core.PgnError
import com.github.bhlangonijr.chesslib.Side

object S {    // UI strings: all come from I18n; screens recompose when the language changes
    const val appName = "ChessNote Generator"
    const val pgn = "PGN"
    const val variants = "Variant"
    const val lines = "Line"

    val untitled get() = I18n.t("untitledNote")
    val unnamedVariant get() = I18n.t("treeUnnamedVariant")
    val unnamedSub get() = I18n.t("treeUnnamedSub")
    val emptyLine get() = I18n.t("treeEmptyLine")

    val menuNewNote get() = I18n.t("menuNewNote")
    val menuOpen get() = I18n.t("menuOpen")
    val menuSaveChanges get() = I18n.t("menuSaveChanges")
    val menuSaveAsDraft get() = I18n.t("menuSaveAsDraft")
    val menuPreview get() = I18n.t("menuPreview")
    val menuExportHtml get() = I18n.t("menuExportHtml")
    val menuExportDocx get() = I18n.t("menuExportDocx")
    val menuExportPdf get() = I18n.t("menuExportPdf")
    val language get() = I18n.t("menuLanguage")
    val themeToDark get() = I18n.t("themeToDark")
    val themeToLight get() = I18n.t("themeToLight")

    val saveButton get() = I18n.t("save")
    val saved get() = I18n.t("saved")
    val saveFailed get() = I18n.t("saveFailed")
    val openFailed get() = I18n.t("openFailed")
    val invalidFile get() = I18n.t("invalidFile")
    val tagline get() = I18n.t("tagline")
    val getStarted get() = I18n.t("getStarted")

    val name get() = I18n.t("nameLabel")
    val openingName get() = I18n.t("openingName")
    val description get() = I18n.t("openingDesc")
    val note get() = I18n.t("descPlaceholder")
    val perspective get() = I18n.t("orientationLabel")
    val whiteLabel get() = I18n.t("white")
    val blackLabel get() = I18n.t("black")
    val startingPosition get() = I18n.t("startingPosition")
    val openingInfo get() = I18n.t("openingInfo")
    val startingPgn get() = I18n.t("startingPgn")
    val pgnPlaceholder get() = I18n.t("pgnPlaceholder")
    val uploadImage get() = I18n.t("uploadImage")
    val deleteImage get() = I18n.t("deleteImage")
    val useDefault get() = I18n.t("useDefault")

    val subCategories get() = I18n.t("subcategory")
    val addVariant get() = I18n.t("treeAddVariant")
    val addSub get() = I18n.t("treeAddSub")
    val addLine get() = I18n.t("treeAddLine")

    val confirmDelete get() = I18n.t("deleteTitle")
    val deleteMessage get() = I18n.t("deleteMessage")
    val delete get() = I18n.t("deleteConfirm")
    val cancel get() = I18n.t("cancel")

    val unsavedTitle get() = I18n.t("unsavedTitle")
    val unsavedOther get() = I18n.t("unsavedOther")
    val dontSave get() = I18n.t("discard")

    val exporting get() = I18n.t("exporting")
    val exportDone get() = I18n.t("exportDone")
    val exportFailed get() = I18n.t("exportFailed")
    val generating get() = I18n.t("generating")

    fun pgnError(e: PgnError): String {
        val side = I18n.t(if (e.side == Side.WHITE) "sideWhite" else "sideBlack")
        return I18n.t("pgnErrorMove", "n" to e.fullMove, "side" to side, "move" to e.move)
    }
}