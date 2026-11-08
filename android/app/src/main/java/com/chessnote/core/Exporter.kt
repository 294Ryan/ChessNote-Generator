package com.chessnote.core

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject
import java.io.ByteArrayOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

private object T {    // 匯出檔固定文字，跟隨目前選的語言
    val lang get() = I18n.lang
    val perspective get() = I18n.t("perspective")
    val eyebrow get() = I18n.t("eyebrow")
    val startingPosition get() = I18n.t("startingPosition")
    val basePosition get() = I18n.t("basePosition")
    val expand get() = I18n.t("expand")
    val collapse get() = I18n.t("collapse")
    val altStarting get() = I18n.t("altStarting")
    val altLine get() = I18n.t("altLine")

    val eastAsiaFont get() = when (I18n.lang) {    // Word 中日韓文字的襯線字型
        "zh-CN" -> "SimSun"
        "ja" -> "MS Mincho"
        "ko" -> "Batang"
        else -> "PMingLiU"
    }
}

private fun esc(s: String) = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&#34;").replace("'", "&#39;")    // 等同 Jinja 的 autoescape

// 內嵌在筆記裡的專案資料：與暫存檔（.json）格式相同，但不帶本機圖片路徑；手動上傳的圖已是 imageData
private fun embeddedProjectJson(o: Opening): String {
    val json = o.toJson()
    json.put("startingImagePath", JSONObject.NULL)
    val variants = json.getJSONArray("variants")
    for (i in 0 until variants.length()) {
        val variant = variants.getJSONObject(i)
        stripImagePaths(variant.getJSONArray("lines"))
        val subs = variant.getJSONArray("subCategories")
        for (j in 0 until subs.length()) stripImagePaths(subs.getJSONObject(j).getJSONArray("lines"))
    }
    return json.toString().replace("<", "\\u003c")    // 避免資料中出現 </script> 提早結束區塊
}

private fun stripImagePaths(lines: JSONArray) {
    for (k in 0 until lines.length()) lines.getJSONObject(k).put("imagePath", JSONObject.NULL)
}

private fun orientationLabel(o: Opening) = I18n.t(if (o.orientation == "black") "black" else "white")

private class LineEntry(val fen: String, val moves: String, val skip: Int, val cut: Int)    // 互動棋盤用：起始 FEN、UCI 著法、與起始 PGN 相同的手數、是否截斷顯示文字

class Exporter(private val boardSvg: BoardSvg) {

    // 圖片三態：刪除 -> null；手動上傳 -> 直接用；否則依 PGN 自動生成（桌面版上傳圖的路徑手機讀不到，一律退回自動生成）
    private fun imageBytes(pgn: String, startingPgn: String, imageData: String?, noImage: Boolean, orientation: String): ByteArray? {
        if (noImage) return null
        if (imageData != null) return Base64.decode(imageData, Base64.DEFAULT)
        if (pgn.isBlank()) return null
        val result = PgnService.play(resolvePgn(pgn, startingPgn))
        val bitmap = boardSvg.render(result.board, orientation, 600, result.lastMove)
        val out = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
        return out.toByteArray()
    }

    // ===== HTML（移植自桌面版 exporter_html.py 與 opening_note.html.j2）=====

    // forPdf = true：Line 卡片全部展開、頁面邊距 8mm、不顯示最上方的 eyebrow 文字與卡片外框
    // embedProject = true：內嵌專案資料，之後可在編輯器開啟這份筆記繼續編輯（預覽與 PDF 不需要）
    fun html(o: Opening, forPdf: Boolean = false, embedProject: Boolean = false): String {
        val entries = mutableListOf<LineEntry>()
        var startingFen = ""
        var startingMoves = emptyList<String>()

        fun register(pgn: String, isStarting: Boolean): Int? {    // 回傳在 entries 中的索引；空白回傳 null
            if (pgn.isBlank()) return null
            val resolved = resolvePgn(pgn, if (isStarting) "" else o.startingPgn)
            val parsed = PgnService.play(resolved)
            val fen = if (parsed.startFen == STANDARD_FEN) "" else parsed.startFen
            val moves = parsed.uci
            var skip = startingMoves.size
            if (!(skip > 0 && fen == startingFen && moves.size > skip && moves.subList(0, skip) == startingMoves)) {
                skip = 0    // 沒有以起始 PGN 開頭（或沒有多出新著法）就不截斷
            }
            val cut = if (skip > 0 && resolved == pgn) 1 else 0    // 完整寫法才需要截掉文字；接續寫法本來就從起始 PGN 之後開始
            entries.add(LineEntry(fen, moves.joinToString(" "), skip, cut))
            return entries.size - 1
        }

        fun imageUri(data: String?, noImage: Boolean) = if (!noImage && data != null) "data:image/png;base64,$data" else null

        fun lineCard(line: Line): String {
            val index = register(line.pgn, false)    // 每條 Line 都登記，即使用了手動圖也要讓起始局面棋盤看得到它的分支
            val board = if (!line.noImage && line.imageData == null) index else null
            val image = imageUri(line.imageData, line.noImage)
            val pgn = esc(line.pgn)
            val sb = StringBuilder()
            sb.append("<details class=\"line-card\"")
            if (forPdf) sb.append(" open")
            if (index != null) sb.append(" id=\"line-$index\" data-idx=\"$index\"")
            sb.append("><summary><span class=\"line-pgn\">")
            sb.append("<span class=\"collapsed\"><span class=\"pgn-mark\">&nbsp;<span class=\"pgn-text\">$pgn</span>&nbsp;</span><span class=\"pgn-dots\">.....</span></span>")
            sb.append("<span class=\"expanded\"><span class=\"pgn-mark\">&nbsp;<span class=\"pgn-text\">$pgn</span>&nbsp;</span></span>")
            sb.append("</span><span class=\"line-toggle\"></span></summary>")
            if (board != null) {
                sb.append("<div class=\"line-board\"><div class=\"cb cb-line\" data-own=\"$board\" aria-label=\"${esc(T.altLine)}\"></div></div>")
            } else if (image != null) {
                sb.append("<div class=\"line-board\"><img src=\"$image\" alt=\"${esc(T.altLine)}\"></div>")
            }
            sb.append("</details>")
            return sb.toString()
        }

        val body = StringBuilder()
        body.append("<div class=\"page\"><header class=\"masthead\">")
        if (!forPdf) body.append("<p class=\"eyebrow\">${esc(T.eyebrow)}</p>")
        body.append("<h1 class=\"opening-title\">${esc(o.name)}</h1>")
        body.append("<p class=\"opening-orient\">${esc(T.perspective)}: ${esc(orientationLabel(o))}</p>")
        if (o.description.isNotEmpty()) body.append("<p class=\"opening-desc\">${esc(o.description)}</p>")
        body.append("</header>")

        val startingIndex = register(o.startingPgn, true)
        if (startingIndex != null) {
            startingFen = entries[0].fen
            startingMoves = entries[0].moves.split(" ").filter { it.isNotEmpty() }
        }
        val startingBoard = if (!o.startingNoImage && o.startingImageData == null) startingIndex else null
        val startingImage = imageUri(o.startingImageData, o.startingNoImage)
        body.append("<section class=\"starting-section\"><h2 class=\"variant-title\">${esc(T.startingPosition)}</h2>")
        body.append("<div class=\"pgn-block\"")
        if (startingIndex != null) body.append(" data-idx=\"$startingIndex\"")
        body.append("><span class=\"pgn-text\">${esc(o.startingPgn)}</span></div>")
        if (startingBoard != null) {
            body.append("<figure class=\"board-figure\"><div class=\"cb cb-start\" data-own=\"$startingBoard\" data-scope=\"all\" aria-label=\"${esc(T.altStarting)}\"></div></figure>")
        } else if (startingImage != null) {
            body.append("<figure class=\"board-figure\"><img src=\"$startingImage\" alt=\"${esc(T.altStarting)}\"></figure>")
        }
        body.append("</section>")

        for (v in o.variants) {
            body.append("<section class=\"variant\"><h2 class=\"variant-title\">${esc(v.name)}</h2>")
            if (v.description.isNotEmpty()) body.append("<p class=\"section-desc\">${esc(v.description)}</p>")
            body.append("<div class=\"variant-body\">")
            if (v.lines.isNotEmpty()) {
                body.append("<div class=\"direct-lines\">")
                v.lines.forEach { body.append(lineCard(it)) }    // Line 排在子分類之前，登記順序與桌面版一致
                body.append("</div>")
            }
            for (s in v.subCategories) {
                body.append("<div class=\"subcategory\"><h3 class=\"subcategory-title\">${esc(s.name)}</h3>")
                if (s.description.isNotEmpty()) body.append("<p class=\"section-desc\">${esc(s.description)}</p>")
                body.append("<div class=\"subcategory-body\">")
                s.lines.forEach { body.append(lineCard(it)) }
                body.append("</div></div>")
            }
            body.append("</div></section>")
        }
        body.append("</div>")

        val data = JSONObject()
            .put("o", o.orientation)
            .put("l", JSONArray().also { arr -> entries.forEach { arr.put(JSONArray().put(it.fen).put(it.moves).put(it.skip).put(it.cut)) } })
            .put("t", JSONObject().put("viewAll", I18n.t("boardViewAll", "n" to "{n}")).put("collapse", I18n.t("collapse")))    // {n} 由 JS 代入符合的 Line 數
        val boardJson = data.toString().replace("<", "\\u003c")    // 避免資料中出現 </script> 破壞頁面

        val sb = StringBuilder()
        sb.append("<!DOCTYPE html><html lang=\"${esc(T.lang)}\"><head><meta charset=\"utf-8\">")
        sb.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
        sb.append("<title>${esc(o.name)}</title><style>")
        sb.append(exportCss.replace("__EXPAND__", T.expand).replace("__COLLAPSE__", T.collapse))
        if (forPdf) sb.append("@page { size: A4; margin: 8mm; } .line-card { border: none; }")    // PDF 邊距由 @page 控制，並拿掉卡片外框
        sb.append("</style></head><body>")
        if (entries.isNotEmpty()) {
            sb.append("<svg width=\"0\" height=\"0\" style=\"position:absolute\" aria-hidden=\"true\"><defs>${boardSvg.pieceSymbols()}</defs></svg>")
        }
        sb.append(body)
        if (embedProject) {
            sb.append("<script type=\"application/json\" id=\"chessnote-project\" data-format=\"chessnote-project\" data-version=\"1\">${embeddedProjectJson(o)}</script>")
        }
        sb.append("<script type=\"application/json\" id=\"boardData\">$boardJson</script><script>\n$boardJs\n</script></body></html>")
        return sb.toString()
    }

    // ===== DOCX（手寫 OOXML，不依賴 Apache POI）=====

    private fun x(s: String) = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    private fun textRun(text: String, rPr: String = ""): String {
        val inner = text.replace("\r", "").split("\n").joinToString("<w:br/>") { "<w:t xml:space=\"preserve\">${x(it)}</w:t>" }
        return "<w:r>" + (if (rPr.isNotEmpty()) "<w:rPr>$rPr</w:rPr>" else "") + inner + "</w:r>"
    }

    private fun paragraph(style: String?, runs: String) =
        "<w:p>" + (if (style != null) "<w:pPr><w:pStyle w:val=\"$style\"/></w:pPr>" else "") + runs + "</w:p>"

    fun docx(o: Opening): ByteArray {
        val images = mutableListOf<ByteArray>()
        val body = StringBuilder()
        val pgnRPr = "<w:rFonts w:ascii=\"Consolas\" w:hAnsi=\"Consolas\" w:eastAsia=\"Consolas\" w:cs=\"Consolas\"/>" +
                "<w:color w:val=\"8A3535\"/><w:sz w:val=\"24\"/><w:szCs w:val=\"24\"/><w:shd w:val=\"clear\" w:color=\"auto\" w:fill=\"F6E3E3\"/>"

        fun heading(level: Int, text: String) = body.append(paragraph("Heading$level", textRun(text)))

        fun description(text: String) {
            if (text.isNotEmpty()) body.append(paragraph(null, textRun(text)))
        }

        fun rule() {
            body.append("<w:p><w:pPr><w:pBdr><w:bottom w:val=\"single\" w:sz=\"6\" w:space=\"1\" w:color=\"CCCCCC\"/></w:pBdr></w:pPr></w:p>")
        }

        fun pgnParagraph(pgn: String) {
            body.append(paragraph(null, textRun("\u00A0$pgn\u00A0", pgnRPr)))    // 前後用不換行空白，底色不會貼著文字
        }

        fun imageParagraph(bytes: ByteArray) {
            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
            if (bounds.outWidth <= 0) return
            images.add(bytes)
            val n = images.size
            val cx = 5029200L    // 5.5 吋，與桌面版一致
            val cy = cx * bounds.outHeight / bounds.outWidth
            body.append(
                "<w:p><w:r><w:drawing><wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">" +
                        "<wp:extent cx=\"$cx\" cy=\"$cy\"/><wp:docPr id=\"$n\" name=\"Picture $n\"/>" +
                        "<a:graphic><a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/picture\">" +
                        "<pic:pic><pic:nvPicPr><pic:cNvPr id=\"$n\" name=\"image$n.png\"/><pic:cNvPicPr/></pic:nvPicPr>" +
                        "<pic:blipFill><a:blip r:embed=\"rIdImg$n\"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>" +
                        "<pic:spPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"$cx\" cy=\"$cy\"/></a:xfrm>" +
                        "<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>" +
                        "</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>"
            )
        }

        fun lineSection(line: Line) {
            pgnParagraph(line.pgn)
            imageBytes(line.pgn, o.startingPgn, line.imageData, line.noImage, o.orientation)?.let { imageParagraph(it) }
        }

        heading(1, o.name)
        body.append(paragraph(null, textRun("${T.perspective}: ${orientationLabel(o)}")))
        description(o.description)
        heading(2, T.basePosition)
        pgnParagraph(o.startingPgn)
        imageBytes(o.startingPgn, "", o.startingImageData, o.startingNoImage, o.orientation)?.let { imageParagraph(it) }

        for (v in o.variants) {
            rule()
            heading(2, v.name)
            description(v.description)
            v.lines.forEach { lineSection(it) }    // Line 排在子分類之前
            for (s in v.subCategories) {
                heading(3, s.name)
                description(s.description)
                s.lines.forEach { lineSection(it) }
            }
        }

        val xmlHead = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        val wNs = "xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\""
        val document = xmlHead + "<w:document $wNs xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\" " +
                "xmlns:wp=\"http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing\" " +
                "xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" " +
                "xmlns:pic=\"http://schemas.openxmlformats.org/drawingml/2006/picture\"><w:body>$body" +
                "<w:sectPr><w:pgSz w:w=\"11906\" w:h=\"16838\"/><w:pgMar w:top=\"1080\" w:right=\"1800\" w:bottom=\"1440\" w:left=\"1800\" w:header=\"720\" w:footer=\"720\" w:gutter=\"0\"/></w:sectPr>" +
                "</w:body></w:document>"

        fun headingStyle(level: Int, size: Int, color: String, before: Int) =
            "<w:style w:type=\"paragraph\" w:styleId=\"Heading$level\"><w:name w:val=\"heading $level\"/><w:basedOn w:val=\"Normal\"/><w:next w:val=\"Normal\"/><w:qFormat/>" +
                    "<w:pPr><w:keepNext/><w:spacing w:before=\"$before\" w:after=\"120\"/><w:outlineLvl w:val=\"${level - 1}\"/></w:pPr>" +
                    "<w:rPr><w:b/><w:bCs/><w:color w:val=\"$color\"/><w:sz w:val=\"${size * 2}\"/><w:szCs w:val=\"${size * 2}\"/></w:rPr></w:style>"

        val styles = xmlHead + "<w:styles $wNs><w:docDefaults><w:rPrDefault><w:rPr>" +
                "<w:rFonts w:ascii=\"Cambria\" w:hAnsi=\"Cambria\" w:eastAsia=\"${T.eastAsiaFont}\" w:cs=\"Cambria\"/>" +
                "<w:color w:val=\"1A1A1A\"/><w:sz w:val=\"25\"/><w:szCs w:val=\"25\"/></w:rPr></w:rPrDefault>" +
                "<w:pPrDefault><w:pPr><w:spacing w:after=\"120\" w:line=\"276\" w:lineRule=\"auto\"/></w:pPr></w:pPrDefault></w:docDefaults>" +
                "<w:style w:type=\"paragraph\" w:default=\"1\" w:styleId=\"Normal\"><w:name w:val=\"Normal\"/><w:qFormat/></w:style>" +
                headingStyle(1, 26, "1A1A1A", 0) + headingStyle(2, 20, "1A1A1A", 240) + headingStyle(3, 16, "4A4A4A", 200) +
                "</w:styles>"

        val contentTypes = xmlHead + "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">" +
                "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>" +
                "<Default Extension=\"xml\" ContentType=\"application/xml\"/><Default Extension=\"png\" ContentType=\"image/png\"/>" +
                "<Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>" +
                "<Override PartName=\"/word/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml\"/></Types>"

        val rootRels = xmlHead + "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
                "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/></Relationships>"

        val docRels = StringBuilder(xmlHead + "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">" +
                "<Relationship Id=\"rIdStyles\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>")
        images.indices.forEach { i ->
            docRels.append("<Relationship Id=\"rIdImg${i + 1}\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/image\" Target=\"media/image${i + 1}.png\"/>")
        }
        docRels.append("</Relationships>")

        val out = ByteArrayOutputStream()
        ZipOutputStream(out).use { zip ->
            fun put(name: String, data: ByteArray) {
                zip.putNextEntry(ZipEntry(name))
                zip.write(data)
                zip.closeEntry()
            }
            put("[Content_Types].xml", contentTypes.toByteArray(Charsets.UTF_8))
            put("_rels/.rels", rootRels.toByteArray(Charsets.UTF_8))
            put("word/document.xml", document.toByteArray(Charsets.UTF_8))
            put("word/styles.xml", styles.toByteArray(Charsets.UTF_8))
            put("word/_rels/document.xml.rels", docRels.toString().toByteArray(Charsets.UTF_8))
            images.forEachIndexed { i, bytes -> put("word/media/image${i + 1}.png", bytes) }
        }
        return out.toByteArray()
    }
}