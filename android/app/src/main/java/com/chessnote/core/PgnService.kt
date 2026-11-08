package com.chessnote.core

import com.github.bhlangonijr.chesslib.Board
import com.github.bhlangonijr.chesslib.Piece
import com.github.bhlangonijr.chesslib.Side
import com.github.bhlangonijr.chesslib.move.Move

class PgnError(val fullMove: Int, val side: Side, val move: String)    // 第一個無法解析的著法與當時的手數、輪到誰

class PgnResult(val board: Board, val error: PgnError?, val startFen: String, val uci: List<String>) {    // uci：主線走到出錯之前的著法
    val lastMove: String? get() = uci.lastOrNull()
}

const val STANDARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

private val leadingNumberRe = Regex("""^\s*(\d+)\s*(\.+)""")
private val trailingResultRe = Regex("""\s*(1-0|0-1|1/2-1/2|\*)\s*$""")

// Line 可寫完整 PGN，或只寫起始 PGN 之後的接續著法；回傳完整 PGN（與桌面版 resolvePgn 相同）
fun resolvePgn(pgn: String, startingPgn: String): String {
    val match = leadingNumberRe.find(pgn)
    if (startingPgn.isBlank() || match == null) return pgn    // 沒帶手數一律視為完整 PGN，不合法就由後續解析回報錯誤
    if (match.groupValues[1] == "1" && match.groupValues[2].length == 1) return pgn    // 「1.」開頭是完整 PGN
    return trailingResultRe.replace(startingPgn, "") + "\n" + pgn    // 「1...」或其他手數才是接續
}

private fun uciOf(move: Move): String {
    val promotion = if (move.promotion != Piece.NONE) move.promotion.fenSymbol.lowercase() else ""
    return move.from.name.lowercase() + move.to.name.lowercase() + promotion
}

object PgnService {
    private val fenRe = Regex("""\[\s*FEN\s+"([^"]+)"\s*\]""", RegexOption.IGNORE_CASE)
    private val headerRe = Regex("""^\s*\[.*\]\s*$""", RegexOption.MULTILINE)
    private val commentRe = Regex("""\{[^}]*\}|;[^\n]*""")
    private val variationRe = Regex("""\([^()]*\)""")
    private val nagRe = Regex("""\$\d+""")
    private val moveNumberRe = Regex("""\d+\.(\.\.)?""")
    private val resultSet = setOf("1-0", "0-1", "1/2-1/2", "*")

    private fun tokenize(pgn: String): List<String> {
        var text = headerRe.replace(pgn, " ")
        text = commentRe.replace(text, " ")
        while (variationRe.containsMatchIn(text)) {
            text = variationRe.replace(text, " ")    // 只走主線，巢狀變體由內而外剝除
        }
        text = nagRe.replace(text, " ")
        text = moveNumberRe.replace(text, " ")
        return text.split(Regex("""\s+"""))
            .map { it.trimEnd('!', '?') }
            .filter { it.isNotEmpty() && it !in resultSet }
    }

    fun play(pgn: String): PgnResult {
        val board = Board()
        fenRe.find(pgn)?.let { board.loadFromFen(it.groupValues[1]) }
        val startFen = board.fen
        val uci = mutableListOf<String>()
        for (token in tokenize(pgn)) {
            val ok = try {
                board.doMove(token)
            } catch (e: Exception) {
                false
            }
            if (!ok) {
                return PgnResult(board, PgnError(board.moveCounter, board.sideToMove, token), startFen, uci)    // board 停在出錯前的最後合法局面
            }
            uci.add(uciOf(board.backup.last().move))
        }
        return PgnResult(board, null, startFen, uci)
    }
}
