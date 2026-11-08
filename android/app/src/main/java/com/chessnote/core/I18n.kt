package com.chessnote.core

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

object I18n {
    var lang by mutableStateOf("en")

    fun load(context: Context) {    // Called at startup: restore the last chosen language
        val saved = AppPrefs.language(context)
        if (saved != null && Texts.data.containsKey(saved)) lang = saved
    }

    fun select(context: Context, code: String) {    // Called when the user picks a language: takes effect immediately and is remembered
        lang = code
        AppPrefs.saveLanguage(context, code)
    }

    fun t(key: String, vararg args: Pair<String, Any>): String {
        var text = Texts.data[lang]?.get(key) ?: Texts.data.getValue("en")[key] ?: key
        args.forEach { (name, value) -> text = text.replace("{$name}", value.toString()) }
        return text
    }
}
