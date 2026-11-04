import io
import re
import chess
import chess.pgn
import chess.svg
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from core.i18n import t

LEADING_NUMBER = re.compile(r"\s*(\d+)\s*(\.+)")
TRAILING_RESULT = re.compile(r"\s*(1-0|0-1|1/2-1/2|\*)\s*$")

def resolvePgn(pgn, startingPgn):    # Line 可寫完整 PGN，或只寫起始 PGN 之後的接續著法；回傳完整 PGN
    match = LEADING_NUMBER.match(pgn)
    if not startingPgn.strip() or not match:    # 沒帶手數一律視為完整 PGN，不合法就由後續解析回報錯誤
        return pgn
    if match.group(1) == "1" and len(match.group(2)) == 1:    # 「1.」開頭是完整 PGN；「1...」或其他手數才是接續
        return pgn
    return TRAILING_RESULT.sub("", startingPgn) + "\n" + pgn


# ### 與 html 互動棋盤相同的樣式 ###
LIGHT_SQUARE = "#f0e9d6"
DARK_SQUARE = "#c8b595"
LAST_MOVE_COLOR = "#a9664a"
COORD_ON_LIGHT = "#9a8460"
COORD_ON_DARK = "#f7f0df"
BOARD_BORDER = "#ddd3bf"

def buildHtmlStyleSvg(pieces, flipped, lastSquares, size):    # pieces: {格子編號 a1=0…h8=63: 棋子符號}；格子 45 單位，與 chess.svg 的棋子同尺寸；不畫箭頭
    ids = {symbol: re.search(r'id="([^"]+)"', svg).group(1) for symbol, svg in chess.svg.PIECES.items()}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 360 360" width="{size}" height="{size}">',
           "<defs>" + "".join(chess.svg.PIECES.values()) + "</defs>"]
    for sq in range(64):
        file, rank = sq % 8, sq // 8
        col = 7 - file if flipped else file
        row = rank if flipped else 7 - rank
        x, y = col * 45, row * 45
        dark = (file + rank) % 2 == 0
        out.append(f'<rect x="{x}" y="{y}" width="45" height="45" fill="{DARK_SQUARE if dark else LIGHT_SQUARE}"/>')
        if sq in lastSquares:
            out.append(f'<rect x="{x}" y="{y}" width="45" height="45" fill="{LAST_MOVE_COLOR}" fill-opacity="0.35"/>')
        coordColor = COORD_ON_DARK if dark else COORD_ON_LIGHT
        if col == 0:    # 排數寫在最左一行的左上角
            out.append(f'<text x="{x + 2.7}" y="{y + 10.8}" font-family="sans-serif" font-size="9.9" font-weight="bold" fill="{coordColor}">{rank + 1}</text>')
        if row == 7:    # 檔名寫在最下一排的右下角
            out.append(f'<text x="{x + 42.3}" y="{y + 41.4}" text-anchor="end" font-family="sans-serif" font-size="9.9" font-weight="bold" fill="{coordColor}">{"abcdefgh"[file]}</text>')
    for sq, symbol in pieces.items():
        file, rank = sq % 8, sq // 8
        x = (7 - file if flipped else file) * 45
        y = (rank if flipped else 7 - rank) * 45
        out.append(f'<use xlink:href="#{ids[symbol]}" transform="translate({x},{y})"/>')
    out.append(f'<rect x="0.5" y="0.5" width="359" height="359" fill="none" stroke="{BOARD_BORDER}" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


def renderPgnToPng(pgn, boardSize=400, orientation="white", htmlStyle=False):    # htmlStyle=True 時用與 html 互動棋盤相同的樣式（編輯器預覽用）
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return None    # PGN 無法解析

    board = game.board()
    lastMove = None
    for move in game.mainline_moves():
        board.push(move)
        lastMove = move

    if htmlStyle:
        pieces = {sq: board.piece_at(sq).symbol() for sq in range(64) if board.piece_at(sq)}
        lastSquares = (lastMove.from_square, lastMove.to_square) if lastMove else ()
        svgData = buildHtmlStyleSvg(pieces, orientation == "black", lastSquares, boardSize)
    else:
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


def checkPgn(pgn, startingPgn=""):    # PGN 有誤回傳說明文字（已依目前語言翻譯）；空白或沒問題回傳 None
    if not pgn.strip():
        return None
    pgn = resolvePgn(pgn, startingPgn)
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


def resolveImageBytes(pgn, imagePath, orientation="white", noImage=False, startingPgn="", htmlStyle=False):
    if noImage:
        return None    # 使用者刻意刪除圖片

    if imagePath:    # 有手動上傳圖則優先使用，直接讀取原始 bytes
        with open(imagePath, "rb") as f:
            return f.read()

    if not pgn.strip():
        return None    # 沒有 PGN 也沒有上傳圖，不顯示

    return renderPgnToPng(resolvePgn(pgn, startingPgn), orientation=orientation, htmlStyle=htmlStyle)    # 回傳 None 代表 PGN 無法解析