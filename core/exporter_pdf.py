import html
import itertools
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QTextDocument, QImage, QFont
from PyQt5.QtPrintSupport import QPrinter
from core.pgn_renderer import resolveImageBytes
from core.i18n import t

IMAGE_WIDTH = 360    # 單位 px，Qt 會依列印解析度換算；所有棋盤圖統一大小
PGN_BG = "#f7eee6"
PGN_COLOR = "#5c2222"
ACCENT = "#7a2e2e"
SOFT = "#655c4e"
RULE = "#ddd3bf"

imageCounter = itertools.count()    # 圖片資源名稱需唯一


def escapeText(text):
    return html.escape(text).replace("\n", "<br>")


def buildImageTag(doc, pgn, imageData, orientation, noImage, width, startingPgn=""):
    rawBytes = resolveImageBytes(pgn, imageData, orientation, noImage, startingPgn, htmlStyle=True)    # 與 html 相同的棋盤樣式
    if rawBytes is None:
        return ""

    image = QImage.fromData(rawBytes)
    if image.isNull():
        return ""

    name = f"img{next(imageCounter)}"
    doc.addResource(QTextDocument.ImageResource, QUrl(name), image)    # 以資源註冊，避免依賴 data URI 支援
    height = int(width * image.height() / image.width())
    return f'<p align="center"><img src="{name}" width="{width}" height="{height}"></p>'


def buildPgnBlock(pgn):
    return (f'<table width="100%" cellpadding="6" cellspacing="0" style="margin-top:8px;"><tr>'
            f'<td bgcolor="{PGN_BG}" style="color:{PGN_COLOR}; font-family:Consolas; white-space:pre-wrap;">'
            f'{html.escape(pgn)}</td></tr></table>')


def buildDescription(text):
    if not text:
        return ""
    return f'<p style="font-style:italic; color:{SOFT};">{escapeText(text)}</p>'


def buildLines(doc, lines, orientation, startingPgn):
    return "".join(
        buildPgnBlock(l.pgn) + buildImageTag(doc, l.pgn, l.imageData, orientation, l.noImage, IMAGE_WIDTH, startingPgn)
        for l in lines
    )


def buildHtml(doc, opening):
    orientation = opening.orientation
    parts = [
        '<body style="color:#2a2520;">',
        f'<h1 style="font-size:24pt;">{html.escape(opening.name)}</h1>',
        f'<p style="color:{SOFT};">{t('perspective')}: {t(orientation)}</p>',
        buildDescription(opening.description),
        '<h2 style="font-size:18pt;">{t("startingPosition")}</h2>',
        buildPgnBlock(opening.startingPgn),
        buildImageTag(doc, opening.startingPgn, opening.startingImageData, orientation, opening.startingNoImage, IMAGE_WIDTH),
    ]

    for variant in opening.variants:
        parts.append(f'<hr style="color:{RULE};">')
        parts.append(f'<h2 style="font-size:18pt;"><span style="color:{ACCENT};">§</span> {html.escape(variant.name)}</h2>')
        parts.append(buildDescription(variant.description))
        parts.append(buildLines(doc, variant.lines, orientation, opening.startingPgn))
        for sub in variant.subCategories:
            parts.append(f'<h3 style="font-size:14pt;">{html.escape(sub.name)}</h3>')
            parts.append(buildDescription(sub.description))
            parts.append(buildLines(doc, sub.lines, orientation, opening.startingPgn))

    parts.append('</body>')
    return "".join(parts)


def exportPdf(opening, outputPath):
    doc = QTextDocument()
    doc.setDefaultFont(QFont("Georgia", 11))    # 中文字由 Qt 自動 fallback 到系統字型
    doc.setDocumentMargin(0)    # 去除文件內建留白，邊距只由 printer 控制
    doc.setHtml(buildHtml(doc, opening))

    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(outputPath)
    printer.setPageSize(QPrinter.A4)
    printer.setPageMargins(5, 5, 5, 5, QPrinter.Millimeter)
    doc.print_(printer)