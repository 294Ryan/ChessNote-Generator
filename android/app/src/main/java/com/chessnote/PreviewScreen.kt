package com.chessnote

import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import com.chessnote.core.Exporter
import com.chessnote.core.Opening
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

// 完整檢視：用 WebView 顯示與 .html 匯出相同的內容
@Composable
fun PreviewScreen(state: AppState, exporter: Exporter) {
    val version = state.observe()
    val o = state.opening ?: return
    val html by produceState<String?>(null, version) {
        val copy = Opening.parse(o.toJson().toString())    // 複製一份再到背景執行緒產生，避免與編輯衝突
        value = withContext(Dispatchers.Default) { exporter.html(copy) }
    }
    val content = html
    if (content == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text(S.generating) }
    } else {
        AndroidView(
            factory = { context ->
                WebView(context).apply {
                    settings.javaScriptEnabled = true    // 互動棋盤需要 JavaScript，內容全由本機產生
                    webViewClient = WebViewClient()
                }
            },
            update = {
                if (it.tag != content) {    // 避免每次重組都重新載入
                    it.tag = content
                    it.loadDataWithBaseURL(null, content, "text/html", "utf-8", null)
                }
            },
            modifier = Modifier.fillMaxSize(),
        )
    }
}
