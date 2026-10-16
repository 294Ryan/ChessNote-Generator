import io
from docx import Document
from docx.shared import Inches
from core.pgn_renderer import resolveImageBytes

def addImageIfExists(doc, pgn, imagePath):
    rawBytes = resolveImageBytes(pgn, imagePath)
    if rawBytes:
        doc.add_picture(io.BytesIO(rawBytes), width=Inches(4))


def addDescriptionIfExists(doc, obj):
    if obj.description:
        p = doc.add_paragraph(obj.description)
        p.runs[0].italic = True


def addLineSection(doc, line, level):
    doc.add_heading(line.name, level=level)
    addDescriptionIfExists(doc, line)
    doc.add_paragraph(line.pgn)
    addImageIfExists(doc, line.pgn, line.imagePath)


def exportDocx(opening, outputPath):
    doc = Document()

    doc.add_heading(opening.name, level=1)
    doc.add_paragraph(opening.description)

    doc.add_heading("起始局面", level=2)
    doc.add_paragraph(opening.startingPgn)
    addImageIfExists(doc, opening.startingPgn, opening.startingImagePath)

    for variant in opening.variants:
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