import base64
from PyQt5.QtGui import QImage, QImageReader
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice

MAX_SIDE = 1200    # Uploads are shrunk to a 1200px longest side to keep saves small


def loadScaledBase64(filePath):    # Read, resize, and return PNG as base64; None if unreadable or not an image
    image = QImage(filePath)
    if image.isNull():
        return None
    if max(image.width(), image.height()) > MAX_SIDE:
        image = image.scaled(MAX_SIDE, MAX_SIDE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return base64.b64encode(bytes(data)).decode("ascii")


def imageSize(base64Text):    # Returns (width, height); None if not a decodable image; reads only the header, never decodes the whole image
    try:
        raw = base64.b64decode(base64Text)
    except ValueError:
        return None
    data = QByteArray(raw)
    buffer = QBuffer(data)
    buffer.open(QIODevice.ReadOnly)
    size = QImageReader(buffer).size()
    if not size.isValid():
        return None
    return size.width(), size.height()