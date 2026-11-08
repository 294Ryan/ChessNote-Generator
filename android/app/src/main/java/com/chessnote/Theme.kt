package com.chessnote

import androidx.compose.material3.ColorScheme
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.TextFieldColors
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

// 色票取自桌面版 ui/theme.py，兩邊維持同一套外觀
class EditorPalette(
    val dark: Boolean,
    val pageBg: Color,
    val cardBg: Color,
    val cardBorder: Color,
    val inputBg: Color,
    val inputBorder: Color,
    val ink: Color,
    val inkSoft: Color,
    val inkFaint: Color,
    val menuBg: Color,
    val menuBorder: Color,
    val popupBg: Color,
    val danger: Color,
    val radioBorder: Color,
    val chipAlpha: Float,    // 清單列底色的透明度
    val primary: Color,
)

val LightPalette = EditorPalette(
    dark = false,
    pageBg = Color(0xFFFAF8F3), cardBg = Color(0xFFFFFFFF), cardBorder = Color(0xFFE6DFCF),
    inputBg = Color(0xFFFCFBF7), inputBorder = Color(0xFFDDD3BF),
    ink = Color(0xFF2A2520), inkSoft = Color(0xFF655C4E), inkFaint = Color(0xFF9A9080),
    menuBg = Color(0xFFF3EFE4), menuBorder = Color(0xFFDDD3BF), popupBg = Color(0xFFFFFFFF),
    danger = Color(0xFFB91C1C), radioBorder = Color(0xFFB9AE98), chipAlpha = 0.10f,
    primary = Color(0xFF7A2E2E),
)

val DarkPalette = EditorPalette(
    dark = true,
    pageBg = Color(0xFF1A1816), cardBg = Color(0xFF262321), cardBorder = Color(0xFF3A352F),
    inputBg = Color(0xFF1F1C1A), inputBorder = Color(0xFF4A443C),
    ink = Color(0xFFECE6DA), inkSoft = Color(0xFFB8AE98), inkFaint = Color(0xFF857C6C),
    menuBg = Color(0xFF141210), menuBorder = Color(0xFF3A352F), popupBg = Color(0xFF262321),
    danger = Color(0xFFF87171), radioBorder = Color(0xFF6B6354), chipAlpha = 0.20f,
    primary = Color(0xFFE3A8A8),
)

val LocalPalette = staticCompositionLocalOf { LightPalette }

// 四種項目的主色，與桌面版一致
object Accent {
    val opening = Color(0xFF6B7280)
    val variant = Color(0xFF2B6CB0)
    val sub = Color(0xFF2F855A)
    val line = Color(0xFF8A6D3B)
}

fun colorSchemeOf(p: EditorPalette): ColorScheme =
    if (p.dark) {
        darkColorScheme(
            primary = p.primary, onPrimary = p.pageBg,
            background = p.pageBg, onBackground = p.ink,
            surface = p.cardBg, onSurface = p.ink, surfaceVariant = p.inputBg, onSurfaceVariant = p.inkSoft,
            outline = p.inputBorder, outlineVariant = p.cardBorder, error = p.danger,
            surfaceContainer = p.popupBg, surfaceContainerHigh = p.popupBg, surfaceContainerHighest = p.popupBg,
        )
    } else {
        lightColorScheme(
            primary = p.primary, onPrimary = Color.White,
            background = p.pageBg, onBackground = p.ink,
            surface = p.cardBg, onSurface = p.ink, surfaceVariant = p.inputBg, onSurfaceVariant = p.inkSoft,
            outline = p.inputBorder, outlineVariant = p.cardBorder, error = p.danger,
            surfaceContainer = p.popupBg, surfaceContainerHigh = p.popupBg, surfaceContainerHighest = p.popupBg,
        )
    }

// 卡片內輸入框：聚焦時邊框變該卡片主色，PGN 有誤時變紅
@Composable
fun fieldColors(accent: Color): TextFieldColors {
    val p = LocalPalette.current
    return OutlinedTextFieldDefaults.colors(
        focusedBorderColor = accent, unfocusedBorderColor = p.inputBorder, errorBorderColor = p.danger,
        focusedContainerColor = p.cardBg, unfocusedContainerColor = p.inputBg, errorContainerColor = p.inputBg,
        focusedLabelColor = accent, unfocusedLabelColor = p.inkSoft, errorLabelColor = p.danger,
        cursorColor = accent, errorCursorColor = p.danger,
        focusedTextColor = p.ink, unfocusedTextColor = p.ink, errorTextColor = p.ink,
    )
}
