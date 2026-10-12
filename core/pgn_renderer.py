import io
import chess
import chess.pgn
import chess.svg
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice

def renderPgnToPng(pgn, boardSize=400):
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return None    # PGN 無法解析

    board = game.board()
    for move in game.mainline_moves():
        board.push(move)

    svgData = chess.svg.board(board, size=boardSize)

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


def savePngToFile(pngBytes, filePath):
    with open(filePath, "wb") as f:
        f.write(pngBytes)


def resolveImageBytes(pgn, imagePath):
    if imagePath:    # 有手動上傳圖則優先使用，直接讀取原始 bytes
        with open(imagePath, "rb") as f:
            return f.read()

    if not pgn.strip():
        return None    # 沒有 PGN 也沒有上傳圖，不顯示

    return renderPgnToPng(pgn)    # 回傳 None 代表 PGN 無法解析