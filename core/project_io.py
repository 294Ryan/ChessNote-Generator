import json
import re
from core.models import Opening, Variant, SubCategory, Line, newId
from core.image_utils import imageSize, loadScaledBase64

KIND_JSON = "json"    # 暫存檔
KIND_HTML = "html"    # 筆記（內嵌專案資料的 html）
SUPPORTED_VERSION = 1
MAX_FILE_CHARS = 80_000_000
MAX_TEXT = 1_000_000
MAX_IMAGE = 30_000_000    # base64 字元數
MAX_PIXELS = 40_000_000
MAX_NODES = 50_000
MARKER = 'data-format="chessnote-project"'


class InvalidProjectFile(Exception):    # 非法檔案：格式不符或內容不合格
    pass


def saveProject(opening, filePath):
    with open(filePath, "w", encoding="utf-8") as f:
        json.dump(opening.toDict(), f, ensure_ascii=False, indent=2)


def loadProject(filePath):    # 回傳 (Opening, kind)；內容一律當成不可信輸入驗證，不合格丟 InvalidProjectFile
    with open(filePath, "r", encoding="utf-8", errors="replace") as f:    # 二進位檔解碼後會變亂碼，自然被判為非法
        opening, kind = parseProject(f.read())
    migrateLegacyImages(opening)
    return opening, kind


def parseProject(text):
    try:
        if len(text) > MAX_FILE_CHARS:
            raise InvalidProjectFile()
        trimmed = text.lstrip("\ufeff \t\r\n")
        if trimmed.startswith("{"):
            return validate(json.loads(trimmed)), KIND_JSON
        return validate(json.loads(extractProjectBlock(trimmed))), KIND_HTML
    except InvalidProjectFile:
        raise
    except Exception:
        raise InvalidProjectFile()    # json 解析失敗、巢狀過深等一律視為非法檔案


def extractProjectBlock(html):    # 只擷取筆記裡的專案資料區塊，不執行網頁中的任何程式碼
    markerPos = html.find(MARKER)
    if markerPos < 0:
        raise InvalidProjectFile()
    tagStart = html.rfind("<script", 0, markerPos)
    tagEnd = html.find(">", markerPos)
    if tagStart < 0 or tagEnd < 0 or html.find(">", tagStart) != tagEnd:
        raise InvalidProjectFile()
    match = re.search(r'data-version="(\d+)"', html[tagStart:tagEnd])
    if not match or int(match.group(1)) != SUPPORTED_VERSION:
        raise InvalidProjectFile()
    end = html.find("</script>", tagEnd)
    if end < 0:
        raise InvalidProjectFile()
    return html[tagEnd + 1:end]


### 欄位驗證 ###
def getText(obj, key, maxLength, required):
    if obj.get(key) is None:
        if required:
            raise InvalidProjectFile()
        return None
    value = obj[key]
    if not isinstance(value, str) or len(value) > maxLength:
        raise InvalidProjectFile()
    return value


def getFlag(obj, key):
    if obj.get(key) is None:
        return False
    if not isinstance(obj[key], bool):
        raise InvalidProjectFile()
    return obj[key]


def getObjects(obj, key):
    if obj.get(key) is None:
        return []
    value = obj[key]
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise InvalidProjectFile()
    return value


def checkImage(data):    # 上傳圖必須是能解碼的圖片，且尺寸不能大到載入時耗盡記憶體
    if data is None:
        return
    size = imageSize(data)
    if size is None or size[0] <= 0 or size[1] <= 0 or size[0] * size[1] > MAX_PIXELS:
        raise InvalidProjectFile()


def validate(root):
    if not isinstance(root, dict):
        raise InvalidProjectFile()
    usedIds = set()
    nodeCount = 0

    def idOf(obj):    # 節點計數；id 缺漏或重複就重新產生
        nonlocal nodeCount
        nodeCount += 1
        if nodeCount > MAX_NODES:
            raise InvalidProjectFile()
        given = getText(obj, "id", 100, False) or ""
        nodeId = given if given.strip() and given not in usedIds else newId()
        usedIds.add(nodeId)
        return nodeId

    def buildLine(obj):
        line = Line(getText(obj, "pgn", MAX_TEXT, True), getText(obj, "imagePath", MAX_TEXT, False), getFlag(obj, "noImage"))
        line.id = idOf(obj)
        line.imageData = getText(obj, "imageData", MAX_IMAGE, False)
        checkImage(line.imageData)
        return line

    opening = Opening(getText(root, "name", MAX_TEXT, True), getText(root, "description", MAX_TEXT, False) or "", getText(root, "startingPgn", MAX_TEXT, True))
    opening.orientation = getText(root, "orientation", 20, False) or "white"
    if opening.orientation not in ("white", "black"):
        raise InvalidProjectFile()
    opening.startingImagePath = getText(root, "startingImagePath", MAX_TEXT, False)
    opening.startingNoImage = getFlag(root, "startingNoImage")
    opening.startingImageData = getText(root, "startingImageData", MAX_IMAGE, False)
    checkImage(opening.startingImageData)

    for v in getObjects(root, "variants"):
        variant = Variant(getText(v, "name", MAX_TEXT, True), getText(v, "description", MAX_TEXT, False) or "")
        variant.id = idOf(v)
        for s in getObjects(v, "subCategories"):
            sub = SubCategory(getText(s, "name", MAX_TEXT, True), getText(s, "description", MAX_TEXT, False) or "")
            sub.id = idOf(s)
            sub.lines = [buildLine(l) for l in getObjects(s, "lines")]
            variant.subCategories.append(sub)
        variant.lines = [buildLine(l) for l in getObjects(v, "lines")]
        opening.variants.append(variant)
    return opening


### 舊存檔相容 ###
def migrateLegacyImages(opening):    # 舊存檔只有本機圖片路徑：檔案還在就轉成內嵌；找不到就保留原路徑，顯示時退回自動生成圖
    holders = [opening]
    for variant in opening.variants:
        holders += variant.lines
        for sub in variant.subCategories:
            holders += sub.lines
    for h in holders:
        isStarting = isinstance(h, Opening)
        path = h.startingImagePath if isStarting else h.imagePath
        data = h.startingImageData if isStarting else h.imageData
        noImage = h.startingNoImage if isStarting else h.noImage
        if not path or data or noImage:
            continue
        converted = loadScaledBase64(path)
        if converted is None:
            continue
        if isStarting:
            h.startingImageData, h.startingImagePath = converted, None
        else:
            h.imageData, h.imagePath = converted, None