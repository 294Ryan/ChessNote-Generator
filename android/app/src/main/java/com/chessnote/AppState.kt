package com.chessnote

import android.net.Uri
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.chessnote.core.Line
import com.chessnote.core.Opening
import com.chessnote.core.SubCategory
import com.chessnote.core.Variant

sealed class Route {
    object Root : Route()
    object Preview : Route()
    data class VariantEdit(val vid: String) : Route()
    data class SubEdit(val vid: String, val sid: String) : Route()
    data class LineEdit(val vid: String, val sid: String?, val lid: String) : Route()
}

class AppState {
    var opening by mutableStateOf<Opening?>(null)
    var currentUri by mutableStateOf<Uri?>(null)
    var currentKind by mutableStateOf<String?>(null)    // Current file kind: "json" (draft) or "html" (note); null for a new unsaved note
    var fileName by mutableStateOf<String?>(null)
    var savedSnapshot by mutableStateOf("")
    private var tick by mutableIntStateOf(0)    // Data objects aren't Compose state; this triggers a redraw on every change
    val backStack = mutableStateListOf<Route>(Route.Root)
    var navForward = true    // Whether the last navigation went deeper (true) or back (false); decides the transition direction

    fun touch() {
        tick++
    }

    fun observe(): Int = tick    // Reading it in a screen subscribes to data changes

    val isDirty: Boolean
        get() {
            val o = opening ?: return false
            return tick >= 0 && o.toJson().toString() != savedSnapshot    // Compare content snapshots, same as desktop
        }

    fun load(o: Opening, uri: Uri?, name: String?, kind: String?) {
        opening = o
        currentUri = uri
        currentKind = kind
        fileName = name
        savedSnapshot = o.toJson().toString()
        navForward = false
        backStack.clear()
        backStack.add(Route.Root)
    }

    fun restore(o: Opening, uri: Uri?, name: String?, kind: String?, snapshot: String) {    // Restore the automatic backup, including the 'not yet saved to a file' state
        load(o, uri, name, kind)
        savedSnapshot = snapshot
    }

    fun markSaved(snapshot: String? = null) {    // snapshot: content at save time; pass it for async saves so edits made during saving aren't treated as saved
        savedSnapshot = snapshot ?: opening?.toJson()?.toString() ?: ""
        tick++
    }

    fun push(route: Route) {
        navForward = true
        backStack.add(route)
    }

    fun pop() {
        if (backStack.size > 1) {
            navForward = false
            backStack.removeAt(backStack.lastIndex)
        }
    }

    fun findVariant(id: String): Variant? = opening?.variants?.firstOrNull { it.id == id }

    fun findSub(vid: String, sid: String): SubCategory? = findVariant(vid)?.subCategories?.firstOrNull { it.id == sid }

    fun findLine(vid: String, sid: String?, lid: String): Line? {
        val list = if (sid == null) findVariant(vid)?.lines else findSub(vid, sid)?.lines
        return list?.firstOrNull { it.id == lid }
    }
}