package com.chessnote.core

import android.graphics.BitmapFactory
import android.util.Base64
import org.json.JSONArray
import org.json.JSONObject

class InvalidProjectFile : Exception()    // 非法檔案：格式不符或內容不合格

class LoadedProject(val opening: Opening, val kind: String)    // kind：KIND_JSON（暫存檔）或 KIND_HTML（筆記）

// 讀入暫存檔（.json）或筆記（.html）：用內容判斷類型，並一律當成不可信輸入逐項驗證，不合格丟出 InvalidProjectFile
object ProjectFile {
    const val KIND_JSON = "json"
    const val KIND_HTML = "html"
    private const val SUPPORTED_VERSION = 1
    private const val MAX_FILE_CHARS = 80_000_000
    private const val MAX_TEXT = 1_000_000
    private const val MAX_IMAGE = 30_000_000    // base64 字元數
    private const val MAX_PIXELS = 40_000_000L
    private const val MAX_NODES = 50_000
    private const val MARKER = "data-format=\"chessnote-project\""

    fun parse(text: String): LoadedProject {
        try {
            if (text.length > MAX_FILE_CHARS) throw InvalidProjectFile()
            val trimmed = text.trimStart('\uFEFF', ' ', '\t', '\r', '\n')
            if (trimmed.startsWith("{")) {
                return LoadedProject(validate(JSONObject(trimmed)), KIND_JSON)
            }
            return LoadedProject(validate(JSONObject(extractProjectBlock(trimmed))), KIND_HTML)
        } catch (e: InvalidProjectFile) {
            throw e
        } catch (e: Exception) {
            throw InvalidProjectFile()    // JSON 解析失敗等一律視為非法檔案
        }
    }

    // 只擷取筆記裡的專案資料區塊，不執行網頁中的任何程式碼
    private fun extractProjectBlock(html: String): String {
        val markerPos = html.indexOf(MARKER)
        if (markerPos < 0) throw InvalidProjectFile()
        val tagStart = html.lastIndexOf("<script", markerPos)
        val tagEnd = html.indexOf('>', markerPos)
        if (tagStart < 0 || tagEnd < 0 || html.indexOf('>', tagStart) != tagEnd) throw InvalidProjectFile()
        val tag = html.substring(tagStart, tagEnd)
        val version = Regex("""data-version="(\d+)"""").find(tag)?.groupValues?.get(1)?.toIntOrNull()
        if (version != SUPPORTED_VERSION) throw InvalidProjectFile()
        val end = html.indexOf("</script>", tagEnd)
        if (end < 0) throw InvalidProjectFile()
        return html.substring(tagEnd + 1, end)
    }

    private fun JSONObject.text(key: String, max: Int, required: Boolean): String? {
        if (!has(key) || isNull(key)) {
            if (required) throw InvalidProjectFile()
            return null
        }
        val value = get(key)
        if (value !is String || value.length > max) throw InvalidProjectFile()
        return value
    }

    private fun JSONObject.flag(key: String): Boolean {
        if (!has(key) || isNull(key)) return false
        val value = get(key)
        if (value !is Boolean) throw InvalidProjectFile()
        return value
    }

    private fun JSONObject.objects(key: String): List<JSONObject> {
        if (!has(key) || isNull(key)) return emptyList()
        val value = get(key)
        if (value !is JSONArray) throw InvalidProjectFile()
        return (0 until value.length()).map { (value.get(it) as? JSONObject) ?: throw InvalidProjectFile() }
    }

    // 上傳圖必須是能解碼的圖片，且尺寸不能大到載入時耗盡記憶體
    private fun checkImage(data: String?) {
        if (data == null) return
        val bytes = try {
            Base64.decode(data, Base64.DEFAULT)
        } catch (e: IllegalArgumentException) {
            throw InvalidProjectFile()
        }
        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
        if (bounds.outWidth <= 0 || bounds.outHeight <= 0 || bounds.outWidth.toLong() * bounds.outHeight > MAX_PIXELS) throw InvalidProjectFile()
    }

    private fun validate(root: JSONObject): Opening {
        val usedIds = HashSet<String>()
        var nodes = 0

        fun idOf(o: JSONObject): String {    // 節點計數、id 缺漏或重複就重新產生
            if (++nodes > MAX_NODES) throw InvalidProjectFile()
            val given = o.text("id", 100, false) ?: ""
            val id = if (given.isNotBlank() && !usedIds.contains(given)) given else newId()
            usedIds.add(id)
            return id
        }

        fun line(o: JSONObject): Line {
            val line = Line(o.text("pgn", MAX_TEXT, true)!!, o.text("imagePath", MAX_TEXT, false), o.flag("noImage"))
            line.id = idOf(o)
            line.imageData = o.text("imageData", MAX_IMAGE, false)
            checkImage(line.imageData)
            return line
        }

        val opening = Opening(
            root.text("name", MAX_TEXT, true)!!,
            root.text("description", MAX_TEXT, false) ?: "",
            root.text("startingPgn", MAX_TEXT, true)!!,
        )
        val orientation = root.text("orientation", 20, false) ?: "white"
        if (orientation != "white" && orientation != "black") throw InvalidProjectFile()
        opening.orientation = orientation
        opening.startingImagePath = root.text("startingImagePath", MAX_TEXT, false)
        opening.startingNoImage = root.flag("startingNoImage")
        opening.startingImageData = root.text("startingImageData", MAX_IMAGE, false)
        checkImage(opening.startingImageData)

        for (v in root.objects("variants")) {
            val variant = Variant(v.text("name", MAX_TEXT, true)!!, v.text("description", MAX_TEXT, false) ?: "")
            variant.id = idOf(v)
            for (s in v.objects("subCategories")) {
                val sub = SubCategory(s.text("name", MAX_TEXT, true)!!, s.text("description", MAX_TEXT, false) ?: "")
                sub.id = idOf(s)
                s.objects("lines").forEach { sub.lines.add(line(it)) }
                variant.subCategories.add(sub)
            }
            v.objects("lines").forEach { variant.lines.add(line(it)) }
            opening.variants.add(variant)
        }
        return opening
    }
}