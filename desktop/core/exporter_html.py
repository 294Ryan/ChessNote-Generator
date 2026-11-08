import io
import os
import json
import chess
import chess.pgn
import chess.svg
from jinja2 import Environment, FileSystemLoader
from core.pgn_renderer import resolvePgn
from core.i18n import t, getLanguage

def buildImageDataUri(imageData, noImage):    # Only for manually uploaded images; auto-generated images are drawn by the interactive board in the HTML
    if noImage or not imageData:
        return None
    return f"data:image/png;base64,{imageData}"


def extractMoves(pgn, startingPgn=""):    # Returns (starting FEN (empty string for the standard start), UCI move list); None if the PGN can't be parsed
    game = chess.pgn.read_game(io.StringIO(resolvePgn(pgn, startingPgn)))
    if game is None:
        return None

    board = game.board()
    startFen = "" if board.fen() == chess.STARTING_FEN else board.fen()
    moves = [move.uci() for move in game.mainline_moves()]    # Main line only, up to the first error
    return startFen, moves


def buildPieceDefs():    # Build symbols from python-chess's built-in piece SVGs, same set as the editor preview
    return "".join(f'<symbol id="pc-{key}" viewBox="0 0 45 45">{svg}</symbol>' for key, svg in chess.svg.PIECES.items())


def buildBoardJson(orientation, lines):
    data = {
        "o": orientation,
        "l": lines,
        "t": {"viewAll": t("boardViewAll", n="{n}"), "collapse": t("collapse")},    # {n} is filled in by JS with the number of matching Lines
    }
    return json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")    # Prevents </script> in the data from breaking the page


def buildProjectJson(opening):    # Project data embedded in the note: same format as the draft file but without local image paths; the note can be reopened in the editor
    data = opening.toDict()
    data["startingImagePath"] = None
    for variant in data["variants"]:
        for line in variant["lines"]:
            line["imagePath"] = None
        for sub in variant["subCategories"]:
            for line in sub["lines"]:
                line["imagePath"] = None
    return json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")    # Prevents </script> in the data from ending the block early


def buildContext(opening, templateDir):
    lines = []    # All Lines as [starting FEN, moves, move count shared with the starting PGN, whether to trim the displayed text]
    starting = {"fen": "", "moves": []}

    def registerLine(pgn, isStarting=False):    # Returns the index in lines; None if blank or unparseable
        if not pgn.strip():
            return None
        startingPgn = "" if isStarting else opening.startingPgn
        parsed = extractMoves(pgn, startingPgn)
        if parsed is None:
            return None

        fen, moves = parsed
        skip = len(starting["moves"])
        if not (skip and fen == starting["fen"] and len(moves) > skip and moves[:skip] == starting["moves"]):
            skip = 0    # Not trimmed if it doesn't start with the starting PGN (or adds no new moves)
        cut = 1 if skip and resolvePgn(pgn, startingPgn) == pgn else 0    # Only full-form Lines need trimming; continuation form already starts after the starting PGN
        lines.append([fen, " ".join(moves), skip, cut])
        return len(lines) - 1

    startingIndex = registerLine(opening.startingPgn, isStarting=True)
    if startingIndex is not None:
        starting["fen"] = lines[0][0]
        starting["moves"] = lines[0][1].split()
    hasStartingImage = opening.startingImageData and not opening.startingNoImage

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
        "startingImage": buildImageDataUri(opening.startingImageData, opening.startingNoImage) if hasStartingImage else None,
        "startingBoard": startingIndex if not opening.startingNoImage and not opening.startingImageData else None,
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
    context["projectJson"] = buildProjectJson(opening)
    context["pieceDefs"] = buildPieceDefs()
    with open(os.path.join(templateDir, "board.js"), encoding="utf-8") as f:
        context["boardJs"] = f.read()

    return context


def buildLineContext(line, orientation, registerLine):
    pgn = line.pgn
    index = registerLine(pgn)    # Register every Line, even those with a manual image, so the starting-position board shows its branches

    isAuto = not line.imageData and not line.noImage
    return {
        "pgn": pgn,
        "index": index,
        "image": buildImageDataUri(line.imageData, line.noImage),
        "board": index if isAuto else None,
    }


def exportHtml(opening, outputPath, templateDir=None):
    templateDir = templateDir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(templateDir), autoescape=True)    # User-entered names, descriptions and PGN are always escaped
    template = env.get_template("opening_note.html.j2")

    html = template.render(opening=buildContext(opening, templateDir))
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(html)