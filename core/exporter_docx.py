import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from core.pgn_renderer import resolveImageBytes

BODY_FONT = "Calibri"
COLOR_BLACK = RGBColor(0x1a, 0x1a, 0x1a)
BOARD_WIDTH = Inches(5.5)    # 棋盤圖放大到接近版面全寬，方便實際讀譜


def setupStyles(doc):    # 統一全文字型，避免 Word 預設樣式跑掉
    normalStyle = doc.styles["Normal"]
    normalStyle.font.name = BODY_FONT
    normalStyle.font.size = Pt(11)
    normalStyle.font.color.rgb = COLOR_BLACK

    for levelName, size in [("Heading 1", 26), ("Heading 2", 17), ("Heading 3", 13), ("Heading 4", 11.5)]:
        headingStyle = doc.styles[levelName]
        headingStyle.font.name = BODY_FONT
        headingStyle.font.size = Pt(size)
        headingStyle.font.bold = True
        headingStyle.font.italic = False    # Word 內建 Heading 4 預設斜體，明確覆寫避免跑版
        headingStyle.font.color.rgb = COLOR_BLACK


def addHorizontalRule(doc):    # 段落下框線模擬分隔線，取代表格
    paragraph = doc.add_paragraph()
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "CCCCCC")
    pBdr.append(bottom)
    pPr.append(pBdr)


def addImageIfExists(doc, pgn, imagePath):
    rawBytes = resolveImageBytes(pgn, imagePath)
    if rawBytes:
        doc.add_picture(io.BytesIO(rawBytes), width=BOARD_WIDTH)


def addDescriptionIfExists(doc, obj):    # 粗體「說明」標籤 + 正文段落，呼應參考格式的標籤式區塊
    if obj.description:
        label = doc.add_paragraph()
        labelRun = label.add_run("說明")
        labelRun.bold = True
        labelRun.font.size = Pt(10.5)
        doc.add_paragraph(obj.description)


def addLineSection(doc, line, level):
    doc.add_heading(line.name, level=level)
    addDescriptionIfExists(doc, line)
    doc.add_paragraph(line.pgn)
    addImageIfExists(doc, line.pgn, line.imagePath)


def exportDocx(opening, outputPath):
    doc = Document()
    setupStyles(doc)

    doc.add_heading(opening.name, level=1)
    if opening.description:
        doc.add_paragraph(opening.description)

    doc.add_heading("基本局面", level=2)
    doc.add_paragraph(opening.startingPgn)
    addImageIfExists(doc, opening.startingPgn, opening.startingImagePath)

    for variant in opening.variants:
        addHorizontalRule(doc)
        doc.add_heading(variant.name, level=2)
        addDescriptionIfExists(doc, variant)

        for sub in variant.subCategories:
            doc.add_heading(sub.name, level=3)
            addDescriptionIfExists(doc, sub)
            for line in sub.lines:
                addLineSection(doc, line, level=4)

        for line in variant.lines:
            addLineSection(doc, line, level=3)

    doc.save(outputPath)