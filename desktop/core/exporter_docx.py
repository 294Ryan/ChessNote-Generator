import io
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from core.pgn_renderer import resolveImageBytes
from core.i18n import t, getLanguage

BODY_FONT = "Cambria"    # Serif font echoing the HTML publication look (affects Latin characters only)
BODY_FONT_CJK = "PMingLiU"    # PMingLiU for CJK characters; serif style matches Cambria
CJK_FONTS = {"zh-CN": "SimSun", "ja": "MS Mincho", "ko": "Batang"}    # CJK serif font switches by language; other languages use BODY_FONT_CJK
PGN_FONT = "Consolas"    # Monospace font so moves line up
LINE_SIZE = Pt(12)
PGN_SIZE = LINE_SIZE
COLOR_BLACK = RGBColor(0x1a, 0x1a, 0x1a)
COLOR_SUBCATEGORY = RGBColor(0x4a, 0x4a, 0x4a)
COLOR_PGN = RGBColor(0x8a, 0x35, 0x35)    # Soft wine red, matches the HTML version
PGN_HIGHLIGHT_FILL = "F6E3E3"    # PGN background: pale tint of the text color
BOARD_WIDTH = Inches(5.5)    # Board image enlarged to near full page width for easier reading


def setStyleEastAsiaFont(style, fontName):    # python-docx font.name only affects Latin characters; CJK must be set separately
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), fontName)


def setupStyles(doc):    # Unify fonts across the document so Word defaults don't leak in
    cjkFont = CJK_FONTS.get(getLanguage(), BODY_FONT_CJK)
    normalStyle = doc.styles["Normal"]
    normalStyle.font.name = BODY_FONT
    normalStyle.font.size = Pt(12.5)
    normalStyle.font.color.rgb = COLOR_BLACK
    setStyleEastAsiaFont(normalStyle, cjkFont)

    headingSpecs = [
        ("Heading 1", 26, COLOR_BLACK),
        ("Heading 2", 20, COLOR_BLACK),
        ("Heading 3", 16, COLOR_SUBCATEGORY),
    ]
    for levelName, size, color in headingSpecs:
        headingStyle = doc.styles[levelName]
        headingStyle.font.name = BODY_FONT
        headingStyle.font.size = Pt(size)
        headingStyle.font.bold = True
        headingStyle.font.italic = False
        headingStyle.font.color.rgb = color
        setStyleEastAsiaFont(headingStyle, cjkFont)

    doc.styles["Heading 1"].paragraph_format.space_before = Pt(0)    # Heading 1 space-before stacks on the page top margin, pushing the title too far down; zero it

    for section in doc.sections:    # Tighten the top page margin too so the title sits closer to the top
        section.top_margin = Inches(0.75)


def addHorizontalRule(doc):    # Paragraph bottom border acts as a divider instead of a table
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


def addPgnParagraph(doc, pgnText):    # PGN: monospace + soft wine red + tinted background; padded with a space on each side so the background doesn't touch the text
    paragraph = doc.add_paragraph()
    run = paragraph.add_run(f"\u00A0{pgnText}\u00A0")    # Use non-breaking spaces; Word drops regular spaces at paragraph ends
    run.font.name = PGN_FONT
    run.font.size = PGN_SIZE    # Lock the size so Normal style changes don't affect it
    run.font.color.rgb = COLOR_PGN
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:eastAsia"), PGN_FONT)

    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), PGN_HIGHLIGHT_FILL)
    rPr.append(shd)
    return paragraph


def addImageIfExists(doc, pgn, imageData, orientation, noImage, startingPgn=""):
    rawBytes = resolveImageBytes(pgn, imageData, orientation, noImage, startingPgn, htmlStyle=True)    # Same board style as the HTML
    if rawBytes:
        doc.add_picture(io.BytesIO(rawBytes), width=BOARD_WIDTH)


def addDescriptionIfExists(doc, obj, color=None):    # Show the description body directly with no label (same as HTML)
    if obj.description:
        paragraph = doc.add_paragraph()
        run = paragraph.add_run(obj.description)
        if color:
            run.font.color.rgb = color


def addLineSection(doc, line, orientation, startingPgn):
    addPgnParagraph(doc, line.pgn)
    addImageIfExists(doc, line.pgn, line.imageData, orientation, line.noImage, startingPgn)


def exportDocx(opening, outputPath):
    doc = Document()
    setupStyles(doc)

    doc.add_heading(opening.name, level=1)
    doc.add_paragraph(f"{t('perspective')}: {t(opening.orientation)}")
    if opening.description:
        doc.add_paragraph(opening.description)

    doc.add_heading(t("basePosition"), level=2)
    addPgnParagraph(doc, opening.startingPgn)
    addImageIfExists(doc, opening.startingPgn, opening.startingImageData, opening.orientation, opening.startingNoImage)

    for variant in opening.variants:
        addHorizontalRule(doc)
        doc.add_heading(variant.name, level=2)
        addDescriptionIfExists(doc, variant)

        for line in variant.lines:    # Lines come before subcategories
            addLineSection(doc, line, opening.orientation, opening.startingPgn)

        for sub in variant.subCategories:
            doc.add_heading(sub.name, level=3)
            addDescriptionIfExists(doc, sub)
            for line in sub.lines:
                addLineSection(doc, line, opening.orientation, opening.startingPgn)

    doc.save(outputPath)