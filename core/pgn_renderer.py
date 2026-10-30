import io
import re
import chess
import chess.pgn
import chess.svg
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from core.i18n import t

def renderPgnToPng(pgn, boardSize=400, orientation="white"):
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return None    # PGN 無法解析

    board = game.board()
    for move in game.mainline_moves():
        board.push(move)

    svgData = chess.svg.board(board, size=boardSize, orientation=chess.BLACK if orientation == "black" else chess.WHITE)

    renderer = QSvgRenderer(QByteArray(svgData.encode("utf-8")))
    image = QImage(boardSize, boardSize, QImage.Format_ARGB32)
    image.fill(0)    # 透明背景
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def checkPgn(pgn):    # PGN 有誤回傳說明文字（已依目前語言翻譯）；空白或沒問題回傳 None
    if not pgn.strip():
        return None
    game = chess.pgn.read_game(io.StringIO(pgn))
    errors = getattr(game, "errors", []) if game else []
    if not errors:
        return None

    board = game.board()
    for move in game.mainline_moves():
        board.push(move)    # 走到出錯之前的最後一個合法局面，用來推算出錯的是第幾手、輪到誰
    side = t("sideWhite") if board.turn == chess.WHITE else t("sideBlack")
    match = re.search(r"'([^']+)'", str(errors[0]))    # python-chess 的錯誤訊息會用單引號框住有問題的著法
    if match:
        return t("pgnErrorMove", n=board.fullmove_number, side=side, move=match.group(1))
    return t("pgnErrorPlain", n=board.fullmove_number, side=side)


def savePngToFile(pngBytes, filePath):
    with open(filePath, "wb") as f:
        f.write(pngBytes)


def resolveImageBytes(pgn, imagePath, orientation="white", noImage=False):
    if noImage:
        return None    # 使用者刻意刪除圖片

    if imagePath:    # 有手動上傳圖則優先使用，直接讀取原始 bytes
        with open(imagePath, "rb") as f:
            return f.read()

    if not pgn.strip():
        return None    # 沒有 PGN 也沒有上傳圖，不顯示

    return renderPgnToPng(pgn, orientation=orientation)    # 回傳 None 代表 PGN 無法解析