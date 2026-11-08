package com.chessnote

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Base64
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chessnote.core.BoardSvg
import com.chessnote.core.PgnError
import com.chessnote.core.PgnService
import com.chessnote.core.resolvePgn
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream

class Preview(val bitmap: Bitmap?, val error: PgnError?)

private fun buildPreview(pgn: String, startingPgn: String, imageData: String?, noImage: Boolean, orientation: String, boardSvg: BoardSvg): Preview {
    val result = if (pgn.isBlank()) null else PgnService.play(resolvePgn(pgn, startingPgn))    // 接續寫法要先接上起始 PGN
    val bitmap = when {
        noImage -> null    // 使用者刻意刪除圖片
        imageData != null -> {
            val bytes = Base64.decode(imageData, Base64.DEFAULT)
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        }
        result != null -> boardSvg.render(result.board, orientation, 600, result.lastMove)    // 桌面版上傳圖的路徑手機讀不到，一律退回自動生成圖
        else -> null
    }
    return Preview(bitmap, result?.error)
}

// 上傳的圖縮到最長邊 1200px 再轉 base64，避免 .json 過大
fun loadScaledBase64(context: Context, uri: Uri, maxSide: Int = 1200): String? {
    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() } ?: return null
    val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
    BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
    var sample = 1
    while (bounds.outWidth / sample > maxSide * 2 || bounds.outHeight / sample > maxSide * 2) {
        sample *= 2
    }
    var bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size, BitmapFactory.Options().apply { inSampleSize = sample }) ?: return null
    val scale = maxSide.toFloat() / maxOf(bitmap.width, bitmap.height)
    if (scale < 1f) {
        bitmap = Bitmap.createScaledBitmap(bitmap, (bitmap.width * scale).toInt(), (bitmap.height * scale).toInt(), true)
    }
    val out = ByteArrayOutputStream()
    bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
    return Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP)
}

@Composable
private fun SmallButton(text: String, onClick: () -> Unit) {
    val p = LocalPalette.current
    OutlinedButton(
        onClick = onClick,
        shape = RoundedCornerShape(6.dp),
        border = BorderStroke(1.dp, p.inputBorder),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = p.inkSoft),
        contentPadding = PaddingValues(horizontal = 14.dp, vertical = 4.dp),
        modifier = Modifier.height(36.dp),
    ) { Text(text, fontSize = 12.sp) }
}

// PGN 輸入 + 圖片預覽，圖片三種狀態：自動生成 / 手動上傳 / 刪除（空白）
@Composable
fun PgnImageEditor(
    label: String,
    accent: Color,
    pgn: String,
    startingPgn: String,    // Line 用來解析接續寫法；起始局面本身傳空字串
    imageData: String?,
    noImage: Boolean,
    isAuto: Boolean,
    orientation: String,
    boardSvg: BoardSvg,
    collapsible: Boolean,
    onPgnChange: (String) -> Unit,
    onUpload: (String) -> Unit,
    onDelete: () -> Unit,
    onUseDefault: () -> Unit,
) {
    val p = LocalPalette.current
    val context = LocalContext.current
    var text by remember { mutableStateOf(pgn) }
    var expanded by remember { mutableStateOf(true) }
    val picker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            val data = loadScaledBase64(context, uri)
            if (data != null) {
                expanded = true
                onUpload(data)
            }
        }
    }
    val preview by produceState<Preview?>(null, text, startingPgn, imageData, noImage, orientation) {
        delay(300)    // 輸入停頓 300ms 才重繪，跟桌面版一致
        value = withContext(Dispatchers.Default) { buildPreview(text, startingPgn, imageData, noImage, orientation, boardSvg) }
    }

    Column(Modifier.padding(top = 10.dp)) {
        OutlinedTextField(
            value = text,
            onValueChange = {
                text = it
                onPgnChange(it)
            },
            label = { Text(label) },
            placeholder = { Text(S.pgnPlaceholder, color = p.inkFaint) },
            isError = preview?.error != null,    // 與桌面版一致：PGN 有誤時邊框變紅
            minLines = 3,
            textStyle = TextStyle(fontFamily = FontFamily.Monospace, fontSize = 13.sp),
            shape = RoundedCornerShape(6.dp),
            colors = fieldColors(accent),
            modifier = Modifier.fillMaxWidth(),
        )
        preview?.error?.let {
            Text(S.pgnError(it), color = p.danger, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))
        }
        Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
            if (collapsible && preview?.bitmap != null) {
                TextButton(onClick = { expanded = !expanded }) { Text(if (expanded) "▼" else "▶", color = p.inkFaint) }
            }
            SmallButton(S.uploadImage) { picker.launch("image/*") }
            Spacer(Modifier.weight(1f))
            SmallButton(if (isAuto) S.deleteImage else S.useDefault) {
                if (isAuto) {
                    onDelete()
                } else {
                    expanded = true
                    onUseDefault()
                }
            }
        }
        val bitmap = preview?.bitmap
        if (bitmap != null && (expanded || !collapsible)) {
            val frame = RoundedCornerShape(4.dp)
            Box(
                Modifier.padding(top = 10.dp).widthIn(max = 360.dp).fillMaxWidth()
                    .clip(frame).background(p.cardBg).border(1.dp, p.cardBorder, frame).padding(4.dp),
            ) {
                Image(bitmap.asImageBitmap(), contentDescription = null, modifier = Modifier.fillMaxWidth())
            }
        }
    }
}
