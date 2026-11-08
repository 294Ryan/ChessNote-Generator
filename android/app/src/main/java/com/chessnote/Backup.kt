package com.chessnote

import android.content.Context
import android.net.Uri
import com.chessnote.core.Opening
import org.json.JSONObject
import java.io.File

// App 內部的自動備份：離開 app 時存，下次啟動還原。與使用者自己儲存的 .json 成品檔是兩回事
object Backup {
    private fun file(context: Context) = File(context.filesDir, "autosave.json")

    fun save(context: Context, state: AppState) {
        val o = state.opening ?: return
        try {
            val json = JSONObject()
                .put("opening", o.toJson())
                .put("uri", state.currentUri?.toString() ?: JSONObject.NULL)
                .put("fileName", state.fileName ?: JSONObject.NULL)
                .put("kind", state.currentKind ?: JSONObject.NULL)
                .put("savedSnapshot", state.savedSnapshot)
            val temp = File(context.filesDir, "autosave.tmp")
            temp.writeText(json.toString())
            temp.renameTo(file(context))    // 先寫暫存檔再改名，避免寫到一半被中斷而損毀
        } catch (e: Throwable) {
            // 備份失敗不影響使用
        }
    }

    // 回傳 true 表示已還原；沒有備份或讀取失敗回傳 false
    fun restore(context: Context, state: AppState): Boolean {
        val f = file(context)
        if (!f.exists()) return false
        return try {
            val json = JSONObject(f.readText())
            val o = Opening.fromJson(json.getJSONObject("opening"))
            val uri = if (json.isNull("uri")) null else Uri.parse(json.getString("uri"))
            val name = if (json.isNull("fileName")) null else json.getString("fileName")
            val kind = if (json.has("kind") && !json.isNull("kind")) json.getString("kind") else if (uri != null) "json" else null    // 舊版備份沒有類型欄位，有檔案就視為暫存檔
            state.restore(o, uri, name, kind, json.getString("savedSnapshot"))
            true
        } catch (e: Throwable) {
            false
        }
    }
}