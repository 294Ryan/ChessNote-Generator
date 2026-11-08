import io
import re
import base64
import chess
import chess.pgn
import chess.svg
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice
from core.i18n import t

LEADING_NUMBER = re.compile(r"\s*(\d+)\s*(\.+)")
TRAILING_RESULT = re.compile(r"\s*(1-0|0-1|1/2-1/2|\*)\s*$")

def resolvePgn(pgn, startingPgn):    # A Line may be full PGN or just the continuation after the starting PGN; returns the full PGN
    match = LEADING_NUMBER.match(pgn)
    if not startingPgn.strip() or not match:    # No move number: treat as full PGN; if invalid, the later parse reports the error
        return pgn
    if match.group(1) == "1" and len(match.group(2)) == 1:    # Starting with '1.' means full PGN; '1...' or another number means continuation
        return pgn
    return TRAILING_RESULT.sub("", startingPgn) + "\n" + pgn


### Same style as the HTML interactive board ###
LIGHT_SQUARE = "#f0e9d6"
DARK_SQUARE = "#c8b595"
LAST_MOVE_COLOR = "#a9664a"
COORD_ON_LIGHT = "#9a8460"
COORD_ON_DARK = "#f7f0df"
BOARD_BORDER = "#ddd3bf"

def buildHtmlStyleSvg(pieces, flipped, lastSquares, size):    # pieces: {square index a1=0..h8=63: piece symbol}; squares are 45 units like chess.svg pieces; no arrows
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
        if col == 0:    # Rank number at the top-left of the leftmost column
            out.append(f'<text x="{x + 2.7}" y="{y + 10.8}" font-family="sans-serif" font-size="9.9" font-weight="bold" fill="{coordColor}">{rank + 1}</text>')
        if row == 7:    # File letter at the bottom-right of the bottom rank
            out.append(f'<text x="{x + 42.3}" y="{y + 41.4}" text-anchor="end" font-family="sans-serif" font-size="9.9" font-weight="bold" fill="{coordColor}">{"abcdefgh"[file]}</text>')
    for sq, symbol in pieces.items():
        file, rank = sq % 8, sq // 8
        x = (7 - file if flipped else file) * 45
        y = (rank if flipped else 7 - rank) * 45
        out.append(f'<use xlink:href="#{ids[symbol]}" transform="translate({x},{y})"/>')
    out.append(f'<rect x="0.5" y="0.5" width="359" height="359" fill="none" stroke="{BOARD_BORDER}" stroke-width="1"/>')
    out.append("</svg>")
    return "".join(out)


def renderPgnToPng(pgn, boardSize=400, orientation="white", htmlStyle=False):    # htmlStyle=True uses the same style as the HTML interactive board (for editor preview)
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return None

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
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def checkPgn(pgn, startingPgn=""):    # Returns the error text if the PGN is wrong (translated to the current language); None if blank or fine
    if not pgn.strip():
        return None
    pgn = resolvePgn(pgn, startingPgn)
    game = chess.pgn.read_game(io.StringIO(pgn))
    errors = getattr(game, "errors", []) if game else []
    if not errors:
        return None

    board = game.board()
    for move in game.mainline_moves():
        board.push(move)    # Last legal position before the error, used to work out which move failed and who was to move
    side = t("sideWhite") if board.turn == chess.WHITE else t("sideBlack")
    match = re.search(r"'([^']+)'", str(errors[0]))    # python-chess error messages wrap the offending move in single quotes
    if match:
        return t("pgnErrorMove", n=board.fullmove_number, side=side, move=match.group(1))
    return t("pgnErrorPlain", n=board.fullmove_number, side=side)


def savePngToFile(pngBytes, filePath):
    with open(filePath, "wb") as f:
        f.write(pngBytes)


def resolveImageBytes(pgn, imageData, orientation="white", noImage=False, startingPgn="", htmlStyle=False):
    if noImage:
        return None

    if imageData:    # A manually uploaded image takes priority (base64 decoded back to raw bytes)
        return base64.b64decode(imageData)

    if not pgn.strip():
        return None

    return renderPgnToPng(resolvePgn(pgn, startingPgn), orientation=orientation, htmlStyle=htmlStyle)