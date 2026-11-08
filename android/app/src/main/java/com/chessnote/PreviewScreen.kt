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

@Composable
fun PreviewScreen(state: AppState, exporter: Exporter) {    // Full view: WebView shows the same content as the .html export
    val version = state.observe()
    val o = state.opening ?: return
    val html by produceState<String?>(null, version) {
        val copy = Opening.parse(o.toJson().toString())    // Copy first, then generate on a background thread to avoid conflicts with editing
        value = withContext(Dispatchers.Default) { exporter.html(copy) }
    }
    val content = html
    if (content == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text(S.generating) }
    } else {
        AndroidView(
            factory = { context ->
                WebView(context).apply {
                    settings.javaScriptEnabled = true    // Interactive board needs JavaScript; all content is generated locally
                    webViewClient = WebViewClient()
                }
            },
            update = {
                if (it.tag != content) {    // Avoid reloading on every recomposition
                    it.tag = content
                    it.loadDataWithBaseURL(null, content, "text/html", "utf-8", null)
                }
            },
            modifier = Modifier.fillMaxSize(),
        )
    }
}
