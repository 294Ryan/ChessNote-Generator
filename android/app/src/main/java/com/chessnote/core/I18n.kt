package com.chessnote.core

import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

object I18n {
    var lang by mutableStateOf("en")    // 第一次啟動預設英文

    // 啟動時呼叫：還原上次選的語言
    fun load(context: Context) {
        val saved = AppPrefs.language(context)
        if (saved != null && Texts.data.containsKey(saved)) lang = saved
    }

    // 使用者選語言：立即生效並記住
    fun select(context: Context, code: String) {
        lang = code
        AppPrefs.saveLanguage(context, code)
    }

    fun t(key: String, vararg args: Pair<String, Any>): String {
        var text = Texts.data[lang]?.get(key) ?: Texts.data.getValue("en")[key] ?: key
        args.forEach { (name, value) -> text = text.replace("{$name}", value.toString()) }
        return text
    }
}
