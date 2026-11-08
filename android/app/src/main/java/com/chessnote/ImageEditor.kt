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
    val result = if (pgn.isBlank()) null else PgnService.play(resolvePgn(pgn, startingPgn))    // Continuation form must be joined with the starting PGN first
    val bitmap = when {
        noImage -> null
        imageData != null -> {
            val bytes = Base64.decode(imageData, Base64.DEFAULT)
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
        }
        result != null -> boardSvg.render(result.board, orientation, 600, result.lastMove)    // Desktop upload paths are unreadable on mobile; always fall back to the auto-generated image
        else -> null
    }
    return Preview(bitmap, result?.error)
}

fun loadScaledBase64(context: Context, uri: Uri, maxSide: Int = 1200): String? {    // Uploads are shrunk to a 1200px longest side then base64'd to keep .json small
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

@Composable
fun PgnImageEditor(    // PGN input + image preview; image has three states: auto-generated / uploaded / deleted (blank)
    label: String,
    accent: Color,
    pgn: String,
    startingPgn: String,    // Used by Lines to resolve continuation form; pass an empty string for the starting position
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
        delay(300)    // Redraw only after a 300ms typing pause, same as desktop
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
            isError = preview?.error != null,
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
