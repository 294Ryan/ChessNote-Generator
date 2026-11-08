package com.chessnote.core

import android.graphics.Bitmap
import android.graphics.Canvas
import android.util.Base64
import com.caverock.androidsvg.SVG
import com.github.bhlangonijr.chesslib.Board
import com.github.bhlangonijr.chesslib.File
import com.github.bhlangonijr.chesslib.Rank
import com.github.bhlangonijr.chesslib.Square
import org.json.JSONObject

// 棋盤樣式與桌面版 buildHtmlStyleSvg、html 互動棋盤一致
private const val LIGHT_SQUARE = "#f0e9d6"
private const val DARK_SQUARE = "#c8b595"
private const val LAST_MOVE_COLOR = "#a9664a"
private const val COORD_ON_LIGHT = "#9a8460"
private const val COORD_ON_DARK = "#f7f0df"
private const val BOARD_BORDER = "#ddd3bf"

class BoardSvg(piecesJson: String) {
    private val pieceDefs = JSONObject(piecesJson).let { o -> o.keys().asSequence().associateWith { o.getString(it) } }    // 棋子符號 -> <g id=...> 片段
    private val idRe = Regex("""id="([^"]+)"""")
    private val pieceIds = pieceDefs.mapValues { idRe.find(it.value)!!.groupValues[1] }

    // 給 html 互動棋盤用的 <symbol> 清單，與桌面版 buildPieceDefs 相同
    fun pieceSymbols(): String = pieceDefs.entries.joinToString("") { """<symbol id="pc-${it.key}" viewBox="0 0 45 45">${it.value}</symbol>""" }

    // lastMove：UCI 字串（如 "e2e4"），兩格以淡色底標示
    private fun buildSvg(board: Board, orientation: String, lastMove: String?): String {
        val flipped = orientation == "black"
        val lastSquares = mutableSetOf<Int>()
        if (lastMove != null && lastMove.length >= 4) {
            lastSquares.add((lastMove[1] - '1') * 8 + (lastMove[0] - 'a'))
            lastSquares.add((lastMove[3] - '1') * 8 + (lastMove[2] - 'a'))
        }
        val sb = StringBuilder()
        sb.append("""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 360 360">""")
        sb.append("<defs>").append(pieceDefs.values.joinToString("")).append("</defs>")
        for (sq in 0..63) {
            val file = sq % 8
            val rank = sq / 8
            val col = if (flipped) 7 - file else file
            val row = if (flipped) rank else 7 - rank
            val x = col * 45
            val y = row * 45
            val dark = (file + rank) % 2 == 0
            sb.append("""<rect x="$x" y="$y" width="45" height="45" fill="${if (dark) DARK_SQUARE else LIGHT_SQUARE}"/>""")
            if (sq in lastSquares) {
                sb.append("""<rect x="$x" y="$y" width="45" height="45" fill="$LAST_MOVE_COLOR" fill-opacity="0.35"/>""")
            }
            val coordColor = if (dark) COORD_ON_DARK else COORD_ON_LIGHT
            if (col == 0) {    // 排數寫在最左一行的左上角
                sb.append("""<text x="${x + 2.7}" y="${y + 10.8}" font-family="sans-serif" font-size="9.9" font-weight="bold" fill="$coordColor">${rank + 1}</text>""")
            }
            if (row == 7) {    // 檔名寫在最下一排的右下角
                sb.append("""<text x="${x + 42.3}" y="${y + 41.4}" text-anchor="end" font-family="sans-serif" font-size="9.9" font-weight="bold" fill="$coordColor">${'a' + file}</text>""")
            }
        }
        for (sq in 0..63) {
            val file = sq % 8
            val rank = sq / 8
            val piece = board.getPiece(Square.encode(Rank.allRanks[rank], File.allFiles[file]))
            val symbol = piece.fenSymbol
            if (symbol.isBlank() || symbol == ".") continue
            val x = (if (flipped) 7 - file else file) * 45
            val y = (if (flipped) rank else 7 - rank) * 45
            sb.append("""<use xlink:href="#${pieceIds.getValue(symbol)}" transform="translate($x,$y)"/>""")
        }
        sb.append("""<rect x="0.5" y="0.5" width="359" height="359" fill="none" stroke="$BOARD_BORDER" stroke-width="1"/>""")
        return sb.append("</svg>").toString()
    }

    fun render(board: Board, orientation: String, sizePx: Int = 800, lastMove: String? = null): Bitmap {
        val svg = SVG.getFromString(buildSvg(board, orientation, lastMove))
        svg.documentWidth = sizePx.toFloat()
        svg.documentHeight = sizePx.toFloat()
        val bitmap = Bitmap.createBitmap(sizePx, sizePx, Bitmap.Config.ARGB_8888)
        svg.renderToCanvas(Canvas(bitmap))
        return bitmap
    }

    fun decodeBase64(data: String): ByteArray = Base64.decode(data, Base64.DEFAULT)
}
