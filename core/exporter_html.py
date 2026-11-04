import io
import os
import json
import base64
import chess
import chess.pgn
import chess.svg
from jinja2 import Environment, FileSystemLoader
from core.pgn_renderer import resolveImageBytes, resolvePgn
from core.i18n import t, getLanguage

def buildImageDataUri(pgn, imagePath, orientation, noImage):    # 只用於手動上傳圖；自動生成圖改由 html 內的互動棋盤繪製
    rawBytes = resolveImageBytes(pgn, imagePath, orientation, noImage)
    if rawBytes is None:
        return None

    ext = os.path.splitext(imagePath)[1].lstrip(".").lower()
    mimeType = "jpeg" if ext in ("jpg", "jpeg") else ext

    encoded = base64.b64encode(rawBytes).decode("ascii")
    return f"data:image/{mimeType};base64,{encoded}"


def extractMoves(pgn, startingPgn=""):    # 回傳 (起始 FEN（標準開局為空字串）, UCI 著法清單)；PGN 無法解析回傳 None
    game = chess.pgn.read_game(io.StringIO(resolvePgn(pgn, startingPgn)))
    if game is None:
        return None

    board = game.board()
    startFen = "" if board.fen() == chess.STARTING_FEN else board.fen()
    moves = [move.uci() for move in game.mainline_moves()]    # 只取主線，走到出錯之前為止
    return startFen, moves


def buildPieceDefs():    # 以 python-chess 內建棋子 SVG 組成 symbol，與編輯器預覽用同一套棋子
    return "".join(f'<symbol id="pc-{key}" viewBox="0 0 45 45">{svg}</symbol>' for key, svg in chess.svg.PIECES.items())


def buildBoardJson(orientation, lines):
    data = {
        "o": orientation,
        "l": lines,
        "t": {"viewAll": t("boardViewAll", n="{n}")},    # {n} 由 JS 代入符合的 Line 數
    }
    return json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")    # 避免資料中出現 </script> 破壞頁面


def buildContext(opening, templateDir):
    lines = []    # 全部 Line 的 [起始 FEN, 著法, 與起始 PGN 相同的手數, 是否需截斷顯示文字]
    starting = {"fen": "", "moves": []}

    def registerLine(pgn, isStarting=False):    # 回傳在 lines 中的索引；空白或無法解析回傳 None
        if not pgn.strip():
            return None
        startingPgn = "" if isStarting else opening.startingPgn
        parsed = extractMoves(pgn, startingPgn)
        if parsed is None:
            return None

        fen, moves = parsed
        skip = len(starting["moves"])
        if not (skip and fen == starting["fen"] and len(moves) > skip and moves[:skip] == starting["moves"]):
            skip = 0    # 沒有以起始 PGN 開頭（或沒有多出新著法）就不截斷
        cut = 1 if skip and resolvePgn(pgn, startingPgn) == pgn else 0    # 完整寫法才需要截掉文字；接續寫法本來就是從起始 PGN 之後開始
        lines.append([fen, " ".join(moves), skip, cut])
        return len(lines) - 1

    startingIndex = registerLine(opening.startingPgn, isStarting=True)
    if startingIndex is not None:
        starting["fen"] = lines[0][0]
        starting["moves"] = lines[0][1].split()
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
        "startingIndex": startingIndex,
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


def buildLineContext(line, orientation, registerLine):
    pgn = line.pgn
    index = registerLine(pgn)    # 每條 Line 都登記，即使用了手動圖也要讓起始局面棋盤看得到它的分支

    isAuto = not line.imagePath and not line.noImage
    return {
        "pgn": pgn,
        "index": index,
        "image": buildImageDataUri(pgn, line.imagePath, orientation, line.noImage) if line.imagePath else None,
        "board": index if isAuto else None,
    }


def exportHtml(opening, outputPath, templateDir=None):
    templateDir = templateDir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(templateDir), autoescape=True)    # 使用者輸入的名稱、說明、PGN 一律跳脫
    template = env.get_template("opening_note.html.j2")

    html = template.render(opening=buildContext(opening, templateDir))
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(html)
