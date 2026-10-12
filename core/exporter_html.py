import os
import base64
from jinja2 import Environment, FileSystemLoader
from core.pgn_renderer import resolveImageBytes

def buildImageDataUri(pgn, imagePath):
    rawBytes = resolveImageBytes(pgn, imagePath)
    if rawBytes is None:
        return None

    if imagePath:
        ext = os.path.splitext(imagePath)[1].lstrip(".").lower()
        mimeType = "jpeg" if ext in ("jpg", "jpeg") else ext
    else:
        mimeType = "png"    # 自動渲染一律為 png

    encoded = base64.b64encode(rawBytes).decode("ascii")
    return f"data:image/{mimeType};base64,{encoded}"


def buildContext(opening):
    context = {
        "name": opening.name,
        "description": opening.description,
        "startingPgn": opening.startingPgn,
        "startingImage": buildImageDataUri(opening.startingPgn, opening.startingImagePath),
        "variants": [],
    }

    for variant in opening.variants:
        variantData = {
            "name": variant.name,
            "subCategories": [],
            "lines": [buildLineContext(l) for l in variant.lines],
        }
        for sub in variant.subCategories:
            variantData["subCategories"].append({
                "name": sub.name,
                "lines": [buildLineContext(l) for l in sub.lines],
            })
        context["variants"].append(variantData)

    return context


def buildLineContext(line):
    return {
        "name": line.name,
        "pgn": line.pgn,
        "image": buildImageDataUri(line.pgn, line.imagePath),
    }


def exportHtml(opening, outputPath, templateDir=None):
    templateDir = templateDir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    env = Environment(loader=FileSystemLoader(templateDir))
    template = env.get_template("opening_note.html.j2")

    html = template.render(opening=buildContext(opening))
    with open(outputPath, "w", encoding="utf-8") as f:
        f.write(html)
