package com.chessnote.core

import com.github.bhlangonijr.chesslib.Board
import com.github.bhlangonijr.chesslib.Piece
import com.github.bhlangonijr.chesslib.Side
import com.github.bhlangonijr.chesslib.move.Move

class PgnError(val fullMove: Int, val side: Side, val move: String)    // First unparseable move, with the move number and side to move at that point

class PgnResult(val board: Board, val error: PgnError?, val startFen: String, val uci: List<String>) {    // uci: main-line moves up to the error
    val lastMove: String? get() = uci.lastOrNull()
}

const val STANDARD_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

private val leadingNumberRe = Regex("""^\s*(\d+)\s*(\.+)""")
private val trailingResultRe = Regex("""\s*(1-0|0-1|1/2-1/2|\*)\s*$""")

fun resolvePgn(pgn: String, startingPgn: String): String {    // A Line may be full PGN or just the continuation after the starting PGN; returns the full PGN (same as desktop resolvePgn)
    val match = leadingNumberRe.find(pgn)
    if (startingPgn.isBlank() || match == null) return pgn    // No move number: treat as full PGN; if invalid, the later parse reports the error
    if (match.groupValues[1] == "1" && match.groupValues[2].length == 1) return pgn    // Starting with '1.' means full PGN
    return trailingResultRe.replace(startingPgn, "") + "\n" + pgn    // '1...' or another number means continuation
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
            text = variationRe.replace(text, " ")    // Main line only; nested variations are stripped inside-out
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
                return PgnResult(board, PgnError(board.moveCounter, board.sideToMove, token), startFen, uci)    // board stays at the last legal position before the error
            }
            uci.add(uciOf(board.backup.last().move))
        }
        return PgnResult(board, null, startFen, uci)
    }
}
