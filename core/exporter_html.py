import io
import os
import json
import base64
import chess
import chess.pgn
import chess.svg
from jinja2 import Environment, FileSystemLoader
from core.pgn_renderer import resolveImageBytes
from core.i18n import t, getLanguage

def buildImageDataUri(pgn, imagePath, orientation, noImage):    # 只用於手動上傳圖；自動生成圖改由 html 內的互動棋盤繪製
    rawBytes = resolveImageBytes(pgn, imagePath, orientation, noImage)
    if rawBytes is None:
        return None

    ext = os.path.splitext(imagePath)[1].lstrip(".").lower()
    mimeType = "jpeg" if ext in ("jpg", "jpeg") else ext

    encoded = base64.b64encode(rawBytes).decode("ascii")
    return f"data:image/{mimeType};base64,{encoded}"


def extractMoves(pgn):    # 回傳 [起始 FEN（標準開局為空字串）, 以空白分隔的 UCI 著法]；PGN 無法解析回傳 None
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        return None

    board = game.board()
    startFen = "" if board.fen() == chess.STARTING_FEN else board.fen()
    moves = [move.uci() for move in game.mainline_moves()]    # 只取主線，走到出錯之前為止
    return [startFen, " ".join(moves)]


def buildPieceDefs():    # 以 python-chess 內建棋子 SVG 組成 symbol，與編輯器預覽用同一套棋子
    return "".join(f'<symbol id="pc-{key}" viewBox="0 0 45 45">{svg}</symbol>' for key, svg in chess.svg.PIECES.items())


def buildBoardJson(orientation, lines):
    data = {
        "o": orientation,
        "l": lines,
        "t": {"prev": t("boardPrev"), "reset": t("boardReset"), "next": t("boardNext")},
    }
    return json.dumps(data, separators=(",", ":")).replace("</", "<\\/")


def buildContext(opening, templateDir):
    lines = []    # 全部 Line 的著法，起始局面棋盤依此建立全局可走的分支

    def registerLine(pgn):    # 回傳著法在 lines 中的索引；空白或無法解析回傳 None
        if not pgn.strip():
            return None
        moves = extractMoves(pgn)
        if moves is None:
            return None
        lines.append(moves)
        return len(lines) - 1

    startingIndex = registerLine(opening.startingPgn)
    hasStartingImage = opening.startingImagePath and not opening.startingNoImage

    context = {
        "name": opening.name,
        "description": opening.description,
        "orientation": t(opening.orientation),
        "lang": getLanguage(),
        "perspective": t("perspective"),
        "eyebrow": t("eyebrow"),
        "startingPosition": t("startingPosition"),
        "expand": t("expand"),
        "collapse": t("collapse"),
        "altStarting": t("altStarting"),
        "altLine": t("altLine"),
        "startingPgn": opening.startingPgn,
        "startingImage": buildImageDataUri(opening.startingPgn, opening.startingImagePath, opening.orientation, opening.startingNoImage) if hasStartingImage else None,
        "startingBoard": startingIndex if not opening.startingNoImage and not opening.startingImagePath else None,
        "variants": [],
    }

    for variant in opening.variants:
        variantData = {
            "name": variant.name,
            "description": variant.description,
            "subCategories": [],
            "lines": [buildLineContext(l, opening.orientation, registerLine) for l in variant.lines],
        }
        for sub in variant.subCategories:
            variantData["subCategories"].append({
                "name": sub.name,
                "description": sub.description,
                "lines": [buildLineContext(l, opening.orientation, registerLine) for l in sub.lines],
            })
        context["variants"].append(variantData)

    context["hasBoards"] = bool(lines)
    context["boardJson"] = buildBoardJson(opening.orientation, lines)
    context["pieceDefs"] = buildPieceDefs()
    with open(os.path.join(templateDir, "board.js"), encoding="utf-8") as f:
        context["boardJs"] = f.read()

    return context


PGN_PREVIEW_LENGTH = 60    # 折疊時 PGN 預覽的字元數上限

def buildLineContext(line, orientation, registerLine):
    pgn = line.pgn
    isTruncated = len(pgn) > PGN_PREVIEW_LENGTH
    pgnPreview = pgn[:PGN_PREVIEW_LENGTH] + "...more" if isTruncated else pgn
    index = registerLine(pgn)    # 每條 Line 都登記，即使用了手動圖也要讓起始局面棋盤看得到它的分支

    isAuto = not line.imagePath and not line.noImage
    return {
        "pgn": pgn,
        "pgnPreview": pgnPreview,
        "image": buildImageDataUri(pgn, line.imagePath, orientation, line.noImage) if line.imagePath else None,
        "board": index if isAuto else None,
    }


def exportHtml(opening, outputPath, templateDir=None):
    templateDir = templateDir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(templateDir))
    template = env.get_template("opening_note.html.j2")

    html = template.render(opening=buildContext(opening, templateDir))
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(html)
