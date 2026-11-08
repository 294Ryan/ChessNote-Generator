@file:OptIn(ExperimentalMaterial3Api::class)

package com.chessnote

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.print.PrintAttributes
import android.print.PrintManager
import android.provider.OpenableColumns
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextOverflow
import com.chessnote.core.AppPrefs
import com.chessnote.core.BoardSvg
import androidx.core.view.WindowCompat
import com.chessnote.core.Exporter
import com.chessnote.core.I18n
import com.chessnote.core.InvalidProjectFile
import com.chessnote.core.Texts
import com.chessnote.core.Opening
import com.chessnote.core.ProjectFile
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    private val state = AppState()    // manifest 已設定 configChanges，旋轉螢幕不會重建 Activity，狀態不會遺失
    private var printWebView: WebView? = null    // 列印期間要保留參照，避免被回收

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val boardSvg = BoardSvg(assets.open("pieces.json").bufferedReader().use { it.readText() })
        val exporter = Exporter(boardSvg)
        I18n.load(this)    // 還原上次選的語言（第一次啟動預設英文）
        if (!Backup.restore(this, state)) state.load(Opening(), null, null, null)    // 還原上次編輯到一半的筆記；沒有就開空白筆記
        setContent {
            val systemDark = isSystemInDarkTheme()
            var showWelcome by remember { mutableStateOf(!AppPrefs.welcomeDone(this)) }    // 只有第一次啟動會顯示歡迎畫面
            var dark by remember { mutableStateOf(AppPrefs.darkTheme(this) ?: systemDark) }    // 用過的主題會記住；還沒選過就跟隨系統
            val palette = if (dark) DarkPalette else LightPalette
            MaterialTheme(colorScheme = colorSchemeOf(palette)) {
                CompositionLocalProvider(LocalPalette provides palette) {
                    SideEffect {
                        window.statusBarColor = palette.menuBg.toArgb()
                        window.decorView.setBackgroundColor(palette.pageBg.toArgb())
                        WindowCompat.getInsetsController(window, window.decorView).isAppearanceLightStatusBars = !dark
                    }
                    AppContent(this, state, boardSvg, exporter, dark, showWelcome, {
                        AppPrefs.setWelcomeDone(this)
                        showWelcome = false
                    }) {
                        val next = !dark
                        dark = next
                        AppPrefs.saveDarkTheme(this, next)    // 記住主題，下次啟動沿用
                    }
                }
            }
        }
    }

    override fun onStop() {
        super.onStop()
        Backup.save(this, state)    // 跳離或關閉 app 前自動備份，下次啟動還原
    }

    fun readText(uri: Uri): String = contentResolver.openInputStream(uri)!!.bufferedReader().use { it.readText() }

    fun writeText(uri: Uri, text: String) = writeBytes(uri, text.toByteArray(Charsets.UTF_8))

    fun writeBytes(uri: Uri, bytes: ByteArray) {
        contentResolver.openOutputStream(uri, "wt")!!.use { it.write(bytes) }    // "wt" 會先清空舊內容
    }

    fun displayName(uri: Uri): String? =
        contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { if (it.moveToFirst()) it.getString(0) else null }

    // PDF：用 WebView 列印，在系統列印畫面選「儲存為 PDF」並指定位置
    fun printAsPdf(html: String, jobName: String) {
        val webView = WebView(this)
        webView.settings.javaScriptEnabled = true    // 棋盤由 JavaScript 繪製，要等它跑完才列印
        var started = false
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView, url: String?) {
                if (started) return
                started = true
                val attributes = PrintAttributes.Builder()
                    .setMediaSize(PrintAttributes.MediaSize.ISO_A4)
                    .setMinMargins(PrintAttributes.Margins(0, 0, 0, 0))    // 邊距改由 HTML 的 @page 控制（8mm）
                    .build()
                (getSystemService(Context.PRINT_SERVICE) as PrintManager).print(jobName, view.createPrintDocumentAdapter(jobName), attributes)
            }
        }
        printWebView = webView
        webView.loadDataWithBaseURL(null, html, "text/html", "utf-8", null)
    }
}

@Composable
private fun AppContent(
    activity: MainActivity,
    state: AppState,
    boardSvg: BoardSvg,
    exporter: Exporter,
    dark: Boolean,
    showWelcome: Boolean,
    onStart: () -> Unit,
    onToggleTheme: () -> Unit,
) {
    val context = LocalContext.current
    val palette = LocalPalette.current
    val scope = rememberCoroutineScope()
    var menuOpen by remember { mutableStateOf(false) }
    var showUnsaved by remember { mutableStateOf(false) }
    var showLanguage by remember { mutableStateOf(false) }
    var pendingAction by remember { mutableStateOf<(() -> Unit)?>(null) }    // 「尚未儲存」詢問後要接著做的事
    var afterSave by remember { mutableStateOf<(() -> Unit)?>(null) }    // 另存新檔成功後要接著做的事

    fun toast(message: String) = Toast.makeText(context, message, Toast.LENGTH_SHORT).show()

    val openLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            try {
                val loaded = ProjectFile.parse(activity.readText(uri))    // 先驗證；不合格就不動目前的內容
                runCatching {
                    context.contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                }
                state.load(loaded.opening, uri, activity.displayName(uri), loaded.kind)
            } catch (e: InvalidProjectFile) {
                toast(S.invalidFile)
            } catch (e: Throwable) {
                toast(S.openFailed + e)
            }
        }
    }

    val saveAsLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri ->
        val o = state.opening
        if (uri == null || o == null) {
            afterSave = null    // 使用者取消另存，連同後續動作一併取消
        } else {
            try {
                activity.writeText(uri, o.toJson().toString(2))
                runCatching {
                    context.contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION)
                }    // 讓下次啟動還原備份後仍能直接儲存到同一個檔案
                state.currentUri = uri
                state.currentKind = ProjectFile.KIND_JSON
                state.fileName = activity.displayName(uri)
                state.markSaved()
                toast(S.saved)
                afterSave?.invoke()
            } catch (e: Throwable) {
                toast(S.saveFailed + e)
            }
            afterSave = null
        }
    }

    // 匯出：先複製一份資料，到背景執行緒產生檔案，避免與編輯衝突
    fun exportTo(uri: Uri, build: (Opening) -> ByteArray) {
        val o = state.opening ?: return
        val copy = Opening.parse(o.toJson().toString())
        toast(S.exporting)
        scope.launch {
            try {
                val bytes = withContext(Dispatchers.Default) { build(copy) }
                withContext(Dispatchers.IO) { activity.writeBytes(uri, bytes) }
                toast(S.exportDone)
            } catch (e: Throwable) {
                toast(S.exportFailed + e)
            }
        }
    }

    val htmlLauncher = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("text/html")) { uri ->
        if (uri != null) exportTo(uri) { exporter.html(it, embedProject = true).toByteArray(Charsets.UTF_8) }    // 內嵌專案資料，之後可開回編輯器
    }
    val docxLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    ) { uri ->
        if (uri != null) exportTo(uri) { exporter.docx(it) }
    }

    fun baseName() = state.opening?.name?.ifBlank { null } ?: "opening"

    fun exportPdf() {
        val o = state.opening ?: return
        val copy = Opening.parse(o.toJson().toString())
        toast(S.exporting)
        scope.launch {
            val html = withContext(Dispatchers.Default) { exporter.html(copy, forPdf = true) }    // PDF 一律展開所有 Line
            activity.printAsPdf(html, baseName())
        }
    }

    fun doSaveAs(next: (() -> Unit)?) {
        afterSave = next
        saveAsLauncher.launch(baseName() + ".json")
    }

    // 儲存變更：目前檔案是暫存檔就寫回 json，是筆記就重新產生並覆寫 html；還沒存過的新筆記則走「另存暫存檔」
    fun saveChanges(next: (() -> Unit)?) {
        val o = state.opening ?: return
        val uri = state.currentUri
        if (uri == null) {
            doSaveAs(next)
            return
        }
        val snapshot = o.toJson().toString()
        if (state.currentKind == ProjectFile.KIND_HTML) {
            val copy = Opening.parse(snapshot)
            scope.launch {
                try {
                    val bytes = withContext(Dispatchers.Default) { exporter.html(copy, embedProject = true).toByteArray(Charsets.UTF_8) }
                    withContext(Dispatchers.IO) { activity.writeBytes(uri, bytes) }
                    state.markSaved(snapshot)
                    toast(S.saved)
                    next?.invoke()
                } catch (e: Throwable) {
                    toast(S.saveFailed + e)
                }
            }
        } else {
            try {
                activity.writeText(uri, o.toJson().toString(2))
                state.markSaved(snapshot)
                toast(S.saved)
                next?.invoke()
            } catch (e: Throwable) {
                toast(S.saveFailed + e)
            }
        }
    }

    fun guardUnsaved(action: () -> Unit) {
        if (state.isDirty) {
            pendingAction = action
            showUnsaved = true
        } else {
            action()
        }
    }

    BackHandler {
        if (!showWelcome && state.backStack.size > 1) state.pop() else activity.finish()    // 離開不再詢問，未存成檔案的修改由自動備份保留
    }

    val route = state.backStack.last()
    val opening = state.opening
    val title = when {
        opening == null -> S.appName
        route is Route.Root -> (if (state.isDirty) "*" else "") + (state.fileName ?: S.untitled)
        route is Route.Preview -> S.menuPreview
        route is Route.VariantEdit -> state.findVariant(route.vid)?.name?.ifBlank { S.unnamedVariant } ?: ""
        route is Route.SubEdit -> state.findSub(route.vid, route.sid)?.name?.ifBlank { S.unnamedSub } ?: ""
        else -> S.lines
    }

    if (showWelcome) {
        WelcomeScreen(onLanguage = { showLanguage = true }, onStart = onStart)
    } else Scaffold(containerColor = palette.pageBg, topBar = {
        Column {
            TopAppBar(
                title = { Text(title, maxLines = 1, overflow = TextOverflow.Ellipsis, fontSize = 17.sp) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = palette.menuBg,
                    titleContentColor = palette.ink,
                    navigationIconContentColor = palette.ink,
                    actionIconContentColor = palette.ink,
                ),
                navigationIcon = {
                    if (state.backStack.size > 1) {
                        IconButton(onClick = { state.pop() }) { Text("←") }
                    }
                },
                actions = {
                    Box {
                        IconButton(onClick = { menuOpen = true }) { Text("⋮") }
                        DropdownMenu(expanded = menuOpen, onDismissRequest = { menuOpen = false }) {
                            DropdownMenuItem(text = { Text(S.menuNewNote) }, onClick = {
                                menuOpen = false
                                guardUnsaved { state.load(Opening(), null, null, null) }
                            })
                            DropdownMenuItem(text = { Text(S.menuOpen) }, onClick = {
                                menuOpen = false
                                guardUnsaved { openLauncher.launch(arrayOf("application/json", "text/html", "*/*")) }
                            })
                            if (state.currentUri != null) {    // 新筆記還沒有檔案，不顯示
                                DropdownMenuItem(text = { Text(S.menuSaveChanges) }, onClick = {
                                    menuOpen = false
                                    saveChanges(null)
                                })
                            }
                            DropdownMenuItem(text = { Text(S.menuSaveAsDraft) }, onClick = {
                                menuOpen = false
                                doSaveAs(null)
                            })
                            HorizontalDivider()
                            DropdownMenuItem(text = { Text(S.menuPreview) }, enabled = route !is Route.Preview, onClick = {
                                menuOpen = false
                                state.push(Route.Preview)
                            })
                            DropdownMenuItem(text = { Text(S.menuExportHtml) }, onClick = {
                                menuOpen = false
                                htmlLauncher.launch(baseName() + ".html")
                            })
                            DropdownMenuItem(text = { Text(S.menuExportDocx) }, onClick = {
                                menuOpen = false
                                docxLauncher.launch(baseName() + ".docx")
                            })
                            DropdownMenuItem(text = { Text(S.menuExportPdf) }, onClick = {
                                menuOpen = false
                                exportPdf()
                            })
                            HorizontalDivider()
                            DropdownMenuItem(text = { Text(S.language) }, onClick = {
                                menuOpen = false
                                showLanguage = true
                            })
                            DropdownMenuItem(text = { Text(if (dark) S.themeToLight else S.themeToDark) }, onClick = {
                                menuOpen = false
                                onToggleTheme()
                            })
                        }
                    }
                },
            )
            HorizontalDivider(color = palette.menuBorder)
        }
    }) { padding ->
        Box(Modifier.padding(padding)) {
            // 進入下一層：新畫面從右側滑入、舊畫面往左退；返回則反向
            AnimatedContent(
                targetState = route,
                transitionSpec = {
                    val duration = 260
                    if (state.navForward) {
                        (slideInHorizontally(tween(duration)) { it / 3 } + fadeIn(tween(duration))) togetherWith
                                (slideOutHorizontally(tween(duration)) { -it / 3 } + fadeOut(tween(duration / 2)))
                    } else {
                        (slideInHorizontally(tween(duration)) { -it / 3 } + fadeIn(tween(duration))) togetherWith
                                (slideOutHorizontally(tween(duration)) { it / 3 } + fadeOut(tween(duration / 2)))
                    }
                },
                label = "screen",
            ) { target ->
                key(target, opening) {    // 換頁或換筆記時重置各輸入框的暫存文字
                    if (opening != null) {
                        when (target) {
                            is Route.Root -> RootScreen(state, boardSvg)
                            is Route.Preview -> PreviewScreen(state, exporter)
                            is Route.VariantEdit -> VariantScreen(state, target)
                            is Route.SubEdit -> SubScreen(state, target)
                            is Route.LineEdit -> LineScreen(state, boardSvg, target)
                        }
                    }
                }
            }
        }
    }

    if (showUnsaved) {
        AlertDialog(
            onDismissRequest = {
                showUnsaved = false
                pendingAction = null
            },
            title = { Text(S.unsavedTitle) },
            text = { Text(S.unsavedOther) },
            confirmButton = {
                Row {
                    TextButton(onClick = {
                        val action = pendingAction
                        showUnsaved = false
                        pendingAction = null
                        action?.invoke()
                    }) { Text(S.dontSave) }
                    TextButton(onClick = {
                        val action = pendingAction
                        showUnsaved = false
                        pendingAction = null
                        saveChanges(action)
                    }) { Text(S.saveButton) }
                }
            },
            dismissButton = {
                TextButton(onClick = {
                    showUnsaved = false
                    pendingAction = null
                }) { Text(S.cancel) }
            },
        )
    }

    if (showLanguage) {
        AlertDialog(
            onDismissRequest = { showLanguage = false },
            title = { Text(S.language) },
            text = {
                Column(Modifier.verticalScroll(rememberScrollState())) {
                    Texts.languages.forEach { (code, label) ->
                        Row(
                            Modifier.fillMaxWidth().clickable {
                                I18n.select(context, code)
                                showLanguage = false
                            },
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            RadioButton(selected = I18n.lang == code, onClick = {
                                I18n.select(context, code)
                                showLanguage = false
                            })
                            Text(label)
                        }
                    }
                }
            },
            confirmButton = {},
            dismissButton = { TextButton(onClick = { showLanguage = false }) { Text(S.cancel) } },
        )
    }
}