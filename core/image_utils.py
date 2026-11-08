import base64
from PyQt5.QtGui import QImage, QImageReader
from PyQt5.QtCore import Qt, QByteArray, QBuffer, QIODevice

MAX_SIDE = 1200    # 上傳圖縮到最長邊 1200px，避免存檔過大


def loadScaledBase64(filePath):    # 讀圖並縮放後轉成 PNG 的 base64；讀不到或不是圖片回傳 None
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


def imageSize(base64Text):    # 回傳 (寬, 高)；不是可解碼的圖片回傳 None；只讀檔頭，不會把整張圖解碼進記憶體
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