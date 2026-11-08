package com.chessnote

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.RadioButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.chessnote.core.BoardSvg
import com.chessnote.core.Line
import com.chessnote.core.SubCategory
import com.chessnote.core.Variant
import java.util.Collections

// ===== 共用元件（外觀對齊桌面版）=====

// 卡片：左側主色條 + 類型徽章，對應桌面版編輯區的每個區塊
@Composable
fun EditorCard(accent: Color, badge: String, content: @Composable ColumnScope.() -> Unit) {
    val p = LocalPalette.current
    val shape = RoundedCornerShape(8.dp)
    val barWidth = with(LocalDensity.current) { 4.dp.toPx() }
    Column(
        Modifier.fillMaxWidth().clip(shape).background(p.cardBg)
            .drawBehind { drawRect(accent, size = Size(barWidth, size.height)) }
            .border(1.dp, p.cardBorder, shape)
            .padding(start = 18.dp, top = 12.dp, end = 14.dp, bottom = 14.dp),
    ) {
        Text(
            badge, color = Color.White, fontSize = 11.sp, fontWeight = FontWeight.Bold,
            modifier = Modifier.background(accent, RoundedCornerShape(4.dp)).padding(horizontal = 8.dp, vertical = 2.dp),
        )
        content()
    }
}

@Composable
fun CardField(label: String, value: String, accent: Color, onChange: (String) -> Unit, minLines: Int = 1) {
    var text by remember { mutableStateOf(value) }
    OutlinedTextField(
        value = text,
        onValueChange = {
            text = it
            onChange(it)
        },
        label = { Text(label) },
        minLines = minLines,
        textStyle = TextStyle(fontSize = 14.sp),
        shape = RoundedCornerShape(6.dp),
        colors = fieldColors(accent),
        modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
    )
}

@Composable
fun SectionLabel(text: String) {
    Text(
        text, color = LocalPalette.current.inkSoft, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
        modifier = Modifier.padding(top = 20.dp, bottom = 6.dp),
    )
}

@Composable
fun AddButton(text: String, accent: Color, onClick: () -> Unit) {
    val p = LocalPalette.current
    OutlinedButton(
        onClick = onClick,
        shape = RoundedCornerShape(6.dp),
        border = BorderStroke(1.dp, accent.copy(alpha = 0.6f)),
        colors = ButtonDefaults.outlinedButtonColors(contentColor = p.ink, containerColor = accent.copy(alpha = p.chipAlpha / 2)),
        modifier = Modifier.padding(top = 8.dp),
    ) { Text(text, fontSize = 13.sp) }
}

// 清單列：同色系淡底 + 左側色條，對應桌面版左側樹的節點
@Composable
private fun ItemRow(title: String, accent: Color, index: Int, count: Int, onClick: () -> Unit, onUp: () -> Unit, onDown: () -> Unit, onDelete: () -> Unit) {
    val p = LocalPalette.current
    val barWidth = with(LocalDensity.current) { 4.dp.toPx() }
    Row(
        Modifier.fillMaxWidth().padding(vertical = 3.dp).clip(RoundedCornerShape(6.dp))
            .background(accent.copy(alpha = p.chipAlpha))
            .drawBehind { drawRect(accent, size = Size(barWidth, size.height)) }
            .clickable(onClick = onClick)
            .padding(start = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(title, Modifier.weight(1f), color = p.ink, fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        val upColor = if (index > 0) p.inkSoft else p.inkFaint.copy(alpha = 0.4f)
        val downColor = if (index < count - 1) p.inkSoft else p.inkFaint.copy(alpha = 0.4f)
        IconButton(onClick = onUp, enabled = index > 0, modifier = Modifier.size(40.dp)) { Text("↑", color = upColor) }
        IconButton(onClick = onDown, enabled = index < count - 1, modifier = Modifier.size(40.dp)) { Text("↓", color = downColor) }
        IconButton(onClick = onDelete, modifier = Modifier.size(40.dp)) { Text("✕", color = p.inkFaint) }
    }
}

// 同層級清單：點擊進入、上下箭頭調序、✕ 刪除（先確認）
@Composable
fun <T> ItemList(items: MutableList<T>, accent: Color, titleOf: (Int, T) -> String, onOpen: (T) -> Unit, onChanged: () -> Unit) {
    val p = LocalPalette.current
    var target by remember { mutableStateOf<T?>(null) }
    items.forEachIndexed { i, item ->
        ItemRow(
            title = titleOf(i, item),
            accent = accent,
            index = i,
            count = items.size,
            onClick = { onOpen(item) },
            onUp = {
                Collections.swap(items, i, i - 1)
                onChanged()
            },
            onDown = {
                Collections.swap(items, i, i + 1)
                onChanged()
            },
            onDelete = { target = item },
        )
    }
    target?.let { item ->
        AlertDialog(
            onDismissRequest = { target = null },
            title = { Text(S.confirmDelete) },
            text = { Text(S.deleteMessage) },
            confirmButton = {
                TextButton(
                    onClick = {
                        items.remove(item)
                        target = null
                        onChanged()
                    },
                    colors = ButtonDefaults.textButtonColors(contentColor = p.danger),
                ) { Text(S.delete) }
            },
            dismissButton = { TextButton(onClick = { target = null }) { Text(S.cancel) } },
        )
    }
}

private fun lineTitle(i: Int, line: Line) = "Line.${i + 1}  " + (if (line.pgn.isBlank()) S.emptyLine else line.pgn.replace("\n", " ").take(40))

private fun isAutoImage(line: Line) = line.imagePath == null && line.imageData == null && !line.noImage

// ===== 各畫面 =====

@Composable
fun RootScreen(state: AppState, boardSvg: BoardSvg) {
    state.observe()
    val o = state.opening ?: return
    val p = LocalPalette.current
    val accent = Accent.opening
    val radioColors = RadioButtonDefaults.colors(selectedColor = accent, unselectedColor = p.radioBorder)
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp)) {
        EditorCard(accent, S.openingInfo) {
            CardField(S.openingName, o.name, accent, {
                o.name = it
                state.touch()
            })
            Text(S.perspective, color = p.inkSoft, fontSize = 12.sp, modifier = Modifier.padding(top = 12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                RadioButton(selected = o.orientation == "white", colors = radioColors, onClick = {
                    o.orientation = "white"
                    state.touch()
                })
                Text(S.whiteLabel, color = p.ink, fontSize = 14.sp)
                Spacer(Modifier.width(16.dp))
                RadioButton(selected = o.orientation == "black", colors = radioColors, onClick = {
                    o.orientation = "black"
                    state.touch()
                })
                Text(S.blackLabel, color = p.ink, fontSize = 14.sp)
            }
            CardField(S.description, o.description, accent, {
                o.description = it
                state.touch()
            }, minLines = 3)
            PgnImageEditor(
                label = S.startingPgn,
                accent = accent,
                pgn = o.startingPgn,
                startingPgn = "",
                imageData = o.startingImageData,
                noImage = o.startingNoImage,
                isAuto = o.startingImagePath == null && o.startingImageData == null && !o.startingNoImage,
                orientation = o.orientation,
                boardSvg = boardSvg,
                collapsible = false,
                onPgnChange = {
                    o.startingPgn = it
                    state.touch()
                },
                onUpload = {
                    o.startingImageData = it
                    o.startingImagePath = null
                    o.startingNoImage = false
                    state.touch()
                },
                onDelete = {
                    o.startingImageData = null
                    o.startingImagePath = null
                    o.startingNoImage = true
                    state.touch()
                },
                onUseDefault = {
                    o.startingImageData = null
                    o.startingImagePath = null
                    o.startingNoImage = false
                    state.touch()
                },
            )
        }

        SectionLabel(S.variants)
        ItemList(o.variants, Accent.variant, { _, v -> v.name.ifBlank { S.unnamedVariant } }, { state.push(Route.VariantEdit(it.id)) }, { state.touch() })
        AddButton(S.addVariant, Accent.variant) {
            val v = Variant()
            o.variants.add(v)
            state.touch()
            state.push(Route.VariantEdit(v.id))
        }
    }
}

@Composable
fun VariantScreen(state: AppState, route: Route.VariantEdit) {
    state.observe()
    val v = state.findVariant(route.vid) ?: return
    val accent = Accent.variant
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp)) {
        EditorCard(accent, "VARIANT") {
            CardField(S.name, v.name, accent, {
                v.name = it
                state.touch()
            })
            CardField(S.note, v.description, accent, {
                v.description = it
                state.touch()
            }, minLines = 3)
        }

        SectionLabel(S.lines)    // Line 排在子分類上方，與桌面版一致
        ItemList(v.lines, Accent.line, ::lineTitle, { state.push(Route.LineEdit(v.id, null, it.id)) }, { state.touch() })
        AddButton(S.addLine, Accent.line) {
            val l = Line()
            v.lines.add(l)
            state.touch()
            state.push(Route.LineEdit(v.id, null, l.id))
        }

        SectionLabel(S.subCategories)
        ItemList(v.subCategories, Accent.sub, { _, s -> s.name.ifBlank { S.unnamedSub } }, { state.push(Route.SubEdit(v.id, it.id)) }, { state.touch() })
        AddButton(S.addSub, Accent.sub) {
            val s = SubCategory()
            v.subCategories.add(s)
            state.touch()
            state.push(Route.SubEdit(v.id, s.id))
        }
    }
}

@Composable
fun SubScreen(state: AppState, route: Route.SubEdit) {
    state.observe()
    val s = state.findSub(route.vid, route.sid) ?: return
    val accent = Accent.sub
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp)) {
        EditorCard(accent, S.subCategories) {
            CardField(S.name, s.name, accent, {
                s.name = it
                state.touch()
            })
            CardField(S.note, s.description, accent, {
                s.description = it
                state.touch()
            }, minLines = 3)
        }

        SectionLabel(S.lines)
        ItemList(s.lines, Accent.line, ::lineTitle, { state.push(Route.LineEdit(route.vid, s.id, it.id)) }, { state.touch() })
        AddButton(S.addLine, Accent.line) {
            val l = Line()
            s.lines.add(l)
            state.touch()
            state.push(Route.LineEdit(route.vid, s.id, l.id))
        }
    }
}

@Composable
fun LineScreen(state: AppState, boardSvg: BoardSvg, route: Route.LineEdit) {
    state.observe()
    val line = state.findLine(route.vid, route.sid, route.lid) ?: return
    val orientation = state.opening?.orientation ?: "white"
    val accent = Accent.line
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp)) {
        EditorCard(accent, "LINE") {
            PgnImageEditor(
                label = S.pgn,
                accent = accent,
                pgn = line.pgn,
                startingPgn = state.opening?.startingPgn ?: "",
                imageData = line.imageData,
                noImage = line.noImage,
                isAuto = isAutoImage(line),
                orientation = orientation,
                boardSvg = boardSvg,
                collapsible = true,
                onPgnChange = {
                    line.pgn = it
                    state.touch()
                },
                onUpload = {
                    line.imageData = it
                    line.imagePath = null
                    line.noImage = false
                    state.touch()
                },
                onDelete = {
                    line.imageData = null
                    line.imagePath = null
                    line.noImage = true
                    state.touch()
                },
                onUseDefault = {
                    line.imageData = null
                    line.imagePath = null
                    line.noImage = false
                    state.touch()
                },
            )
        }
    }
}
