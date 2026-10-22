import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from core.pgn_renderer import resolveImageBytes

BODY_FONT = "Cambria"    # 襯線字體，呼應 html 版的出版品質感（僅影響英數字元）
BODY_FONT_CJK = "PMingLiU"    # 新細明體，中文字元搭配用，襯線風格與 Cambria 呼應
PGN_FONT = "Consolas"    # 等寬字體，讓棋步對齊更整齊
PGN_SIZE = Pt(11)
COLOR_BLACK = RGBColor(0x1a, 0x1a, 0x1a)
COLOR_HEADING_LIGHT = RGBColor(0x6e, 0x6e, 0x6e)    # 小標題用淺灰，與大/副標題做出層級區隔
COLOR_PGN = RGBColor(0x8a, 0x35, 0x35)    # 柔和酒紅，與 html 版呼應但不搶眼
BOARD_WIDTH = Inches(5.5)    # 棋盤圖放大到接近版面全寬，方便實際讀譜


def setStyleEastAsiaFont(style, fontName):    # python-docx 的 font.name 只影響英數字元，中文需另外設定
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), fontName)


def setupStyles(doc):    # 統一全文字型，避免 Word 預設樣式跑掉
    normalStyle = doc.styles["Normal"]
    normalStyle.font.name = BODY_FONT
    normalStyle.font.size = Pt(12.5)
    normalStyle.font.color.rgb = COLOR_BLACK
    setStyleEastAsiaFont(normalStyle, BODY_FONT_CJK)

    headingSpecs = [
        ("Heading 1", 32, COLOR_BLACK),
        ("Heading 2", 20, COLOR_BLACK),
        ("Heading 3", 13, COLOR_HEADING_LIGHT),
        ("Heading 4", 11.5, COLOR_HEADING_LIGHT),
    ]
    for levelName, size, color in headingSpecs:
        headingStyle = doc.styles[levelName]
        headingStyle.font.name = BODY_FONT
        headingStyle.font.size = Pt(size)
        headingStyle.font.bold = True
        headingStyle.font.italic = False    # Word 內建 Heading 4 預設斜體，明確覆寫避免跑版
        headingStyle.font.color.rgb = color
        setStyleEastAsiaFont(headingStyle, BODY_FONT_CJK)

    # Heading 1 的段前距離疊加頁面上邊界，導致標題離頁首過遠，歸零修正
    doc.styles["Heading 1"].paragraph_format.space_before = Pt(0)

    # 頁面上邊界也一併收緊，讓標題視覺上更貼近頁首
    for section in doc.sections:
        section.top_margin = Inches(0.75)


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


def addPgnParagraph(doc, pgnText):    # PGN 用等寬字體 + 柔和酒紅色，與正文區隔但不搶重點
    paragraph = doc.add_paragraph()
    run = paragraph.add_run(pgnText)
    run.font.name = PGN_FONT
    run.font.size = PGN_SIZE    # 明確鎖定大小，不受 Normal 字級調整影響
    run.font.color.rgb = COLOR_PGN
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), PGN_FONT)
    return paragraph


def addImageIfExists(doc, pgn, imagePath):
    rawBytes = resolveImageBytes(pgn, imagePath)
    if rawBytes:
        doc.add_picture(io.BytesIO(rawBytes), width=BOARD_WIDTH)


def addDescriptionIfExists(doc, obj):    # 直接顯示說明正文，不加標籤文字（比照 html 版）
    if obj.description:
        doc.add_paragraph(obj.description)


def addLineSection(doc, line, level):
    doc.add_heading(line.name, level=level)
    addDescriptionIfExists(doc, line)
    addPgnParagraph(doc, line.pgn)
    addImageIfExists(doc, line.pgn, line.imagePath)


def exportDocx(opening, outputPath):
    doc = Document()
    setupStyles(doc)

    doc.add_heading(opening.name, level=1)
    if opening.description:
        doc.add_paragraph(opening.description)

    doc.add_heading("基本局面", level=2)
    addPgnParagraph(doc, opening.startingPgn)
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