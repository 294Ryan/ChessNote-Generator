package com.chessnote.core

import android.content.Context

object AppPrefs {    // Small settings remembered across launches: language, theme, whether the welcome screen was seen
    private fun prefs(context: Context) = context.getSharedPreferences("chessnote_prefs", Context.MODE_PRIVATE)

    fun language(context: Context): String? = prefs(context).getString("lang", null)

    fun saveLanguage(context: Context, code: String) {
        prefs(context).edit().putString("lang", code).apply()
    }

    fun darkTheme(context: Context): Boolean? {    // Chosen theme: true dark, false light, null not chosen yet (follow system)
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