package com.chessnote.core

import android.content.Context

// 需要跨次啟動記住的小設定：介面語言、主題、是否已看過歡迎畫面
object AppPrefs {
    private fun prefs(context: Context) = context.getSharedPreferences("chessnote_prefs", Context.MODE_PRIVATE)

    fun language(context: Context): String? = prefs(context).getString("lang", null)

    fun saveLanguage(context: Context, code: String) {
        prefs(context).edit().putString("lang", code).apply()
    }

    // 使用者選過的主題：true 深色、false 淺色、null 表示還沒選過（跟隨系統）
    fun darkTheme(context: Context): Boolean? {
        val p = prefs(context)
        return if (p.contains("darkTheme")) p.getBoolean("darkTheme", false) else null
    }

    fun saveDarkTheme(context: Context, dark: Boolean) {
        prefs(context).edit().putBoolean("darkTheme", dark).apply()
    }

    fun welcomeDone(context: Context): Boolean = prefs(context).getBoolean("welcomeDone", false)

    fun setWelcomeDone(context: Context) {
        prefs(context).edit().putBoolean("welcomeDone", true).apply()
    }
}