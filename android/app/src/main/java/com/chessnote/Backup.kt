package com.chessnote

import android.content.Context
import android.net.Uri
import com.chessnote.core.Opening
import org.json.JSONObject
import java.io.File

object Backup {    // Internal automatic backup: saved when leaving the app, restored on next launch. Not the same as the user's own saved .json files
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
            temp.renameTo(file(context))    // Write a temp file then rename, so an interrupted write can't corrupt the backup
        } catch (e: Throwable) {    // A failed backup doesn't affect usage
        }
    }

    fun restore(context: Context, state: AppState): Boolean {    // Returns true if restored; false if there is no backup or reading failed
        val f = file(context)
        if (!f.exists()) return false
        return try {
            val json = JSONObject(f.readText())
            val o = Opening.fromJson(json.getJSONObject("opening"))
            val uri = if (json.isNull("uri")) null else Uri.parse(json.getString("uri"))
            val name = if (json.isNull("fileName")) null else json.getString("fileName")
            val kind = if (json.has("kind") && !json.isNull("kind")) json.getString("kind") else if (uri != null) "json" else null    // Old backups have no kind field; a file means a draft
            state.restore(o, uri, name, kind, json.getString("savedSnapshot"))
            true
        } catch (e: Throwable) {
            false
        }
    }
}