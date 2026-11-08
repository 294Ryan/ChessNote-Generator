package com.chessnote

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chessnote.core.I18n
import com.chessnote.core.Texts

@Composable
private fun GlobeIcon(color: Color) {
    Canvas(Modifier.size(20.dp)) {
        val strokeWidth = 1.8f.dp.toPx()
        val stroke = Stroke(width = strokeWidth)
        val half = strokeWidth / 2
        drawCircle(color, radius = size.minDimension / 2 - half, style = stroke)
        drawLine(color, Offset(half, size.height / 2), Offset(size.width - half, size.height / 2), strokeWidth = strokeWidth)
        drawOval(color, topLeft = Offset(size.width * 0.32f, half), size = Size(size.width * 0.36f, size.height - strokeWidth), style = stroke)
    }
}

// 第一次啟動才會出現：app 圖示 + 標語 + 選語言 + 開始使用
@Composable
fun WelcomeScreen(onLanguage: () -> Unit, onStart: () -> Unit) {
    val p = LocalPalette.current
    val languageName = Texts.languages.firstOrNull { it.first == I18n.lang }?.second ?: "English"
    Column(Modifier.fillMaxSize().background(p.pageBg).padding(start = 24.dp, end = 24.dp, bottom = 36.dp)) {
        Column(Modifier.weight(1f).fillMaxWidth(), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
            Image(
                painterResource(R.drawable.ic_launcher_art), contentDescription = null,
                modifier = Modifier.size(132.dp).shadow(10.dp, RoundedCornerShape(30.dp), clip = false),
            )
            Spacer(Modifier.height(32.dp))
            Text(
                S.appName,
                modifier = Modifier.fillMaxWidth(),    // 撐滿寬度，換行時每一行才會置中
                textAlign = TextAlign.Center,
                fontFamily = FontFamily.Serif,
                fontSize = 36.sp,
                lineHeight = 48.sp,
                fontWeight = FontWeight.Bold,
                color = p.ink,
            )
            Spacer(Modifier.height(16.dp))
            Text(S.tagline, fontSize = 16.sp, lineHeight = 24.sp, color = p.inkSoft, textAlign = TextAlign.Center, modifier = Modifier.widthIn(max = 280.dp))
        }
        OutlinedButton(
            onClick = onLanguage,
            shape = RoundedCornerShape(10.dp),
            border = BorderStroke(1.dp, p.inputBorder),
            colors = ButtonDefaults.outlinedButtonColors(containerColor = p.inputBg, contentColor = p.ink),
            contentPadding = PaddingValues(horizontal = 16.dp),
            modifier = Modifier.fillMaxWidth().height(52.dp),
        ) {
            GlobeIcon(p.inkSoft)
            Spacer(Modifier.width(10.dp))
            Text(languageName, fontSize = 16.sp, modifier = Modifier.weight(1f))
            Text("▾", color = p.inkSoft)
        }
        Spacer(Modifier.height(12.dp))
        Button(
            onClick = onStart,
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.buttonColors(containerColor = p.primary, contentColor = if (p.dark) p.pageBg else Color.White),
            modifier = Modifier.fillMaxWidth().height(54.dp),
        ) { Text(S.getStarted, fontSize = 17.sp, fontWeight = FontWeight.SemiBold) }
    }
}