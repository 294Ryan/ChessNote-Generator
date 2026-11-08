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
    var currentKind by mutableStateOf<String?>(null)    // 目前檔案類型："json"（暫存檔）、"html"（筆記）；尚未存檔的新筆記為 null
    var fileName by mutableStateOf<String?>(null)
    var savedSnapshot by mutableStateOf("")
    private var tick by mutableIntStateOf(0)    // 資料物件不是 Compose 狀態，每次修改靠它通知畫面重繪
    val backStack = mutableStateListOf<Route>(Route.Root)
    var navForward = true    // 最近一次換頁是進入下一層（true）還是返回（false），決定轉場動畫的方向

    fun touch() {
        tick++
    }

    fun observe(): Int = tick    // 畫面讀取它即訂閱資料變動

    val isDirty: Boolean
        get() {
            val o = opening ?: return false
            return tick >= 0 && o.toJson().toString() != savedSnapshot    // 以內容快照比對，跟桌面版一致
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

    // 還原自動備份：連「尚未儲存成檔案」的狀態一起還原
    fun restore(o: Opening, uri: Uri?, name: String?, kind: String?, snapshot: String) {
        load(o, uri, name, kind)
        savedSnapshot = snapshot
    }

    // snapshot：存檔當下的內容快照；非同步存檔時要傳入，才不會把存檔期間的新修改誤判為已存
    fun markSaved(snapshot: String? = null) {
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