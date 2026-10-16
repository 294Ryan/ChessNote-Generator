import uuid

def newId():    # 產生唯一識別碼，供樹狀節點對應用
    return str(uuid.uuid4())


class Line:
    def __init__(self, name="", pgn="", imagePath=None, description=""):
        self.id = newId()
        self.name = name
        self.pgn = pgn
        self.imagePath = imagePath    # None 代表用自動生成圖，否則為手動上傳覆蓋的路徑
        self.description = description    # 選填說明

    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pgn": self.pgn,
            "imagePath": self.imagePath,
            "description": self.description,
        }

    @staticmethod
    def fromDict(data):
        line = Line(data["name"], data["pgn"], data.get("imagePath"), data.get("description", ""))
        line.id = data["id"]
        return line


class SubCategory:
    def __init__(self, name="", description=""):
        self.id = newId()
        self.name = name
        self.description = description    # 選填說明
        self.lines = []

    def addLine(self, line=None):
        line = line or Line()
        self.lines.append(line)
        return line

    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "lines": [l.toDict() for l in self.lines],
        }

    @staticmethod
    def fromDict(data):
        sub = SubCategory(data["name"], data.get("description", ""))
        sub.id = data["id"]
        sub.lines = [Line.fromDict(l) for l in data["lines"]]
        return sub


class Variant:
    def __init__(self, name="", description=""):
        self.id = newId()
        self.name = name
        self.description = description    # 選填說明
        self.subCategories = []
        self.lines = []    # 允許不經子分類，直接掛 Line

    def addSubCategory(self, sub=None):
        sub = sub or SubCategory()
        self.subCategories.append(sub)
        return sub

    def addLine(self, line=None):
        line = line or Line()
        self.lines.append(line)
        return line

    def toDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "subCategories": [s.toDict() for s in self.subCategories],
            "lines": [l.toDict() for l in self.lines],
        }

    @staticmethod
    def fromDict(data):
        variant = Variant(data["name"], data.get("description", ""))
        variant.id = data["id"]
        variant.subCategories = [SubCategory.fromDict(s) for s in data["subCategories"]]
        variant.lines = [Line.fromDict(l) for l in data["lines"]]
        return variant


class Opening:
    def __init__(self, name="", description="", startingPgn=""):
        self.name = name
        self.description = description
        self.startingPgn = startingPgn
        self.startingImagePath = None    # None 代表用自動生成圖
        self.variants = []

    def addVariant(self, variant=None):
        variant = variant or Variant()
        self.variants.append(variant)
        return variant

    ### 序列化／反序列化，供 JSON 存檔使用 ###
    def toDict(self):
        return {
            "name": self.name,
            "description": self.description,
            "startingPgn": self.startingPgn,
            "startingImagePath": self.startingImagePath,
            "variants": [v.toDict() for v in self.variants],
        }

    @staticmethod
    def fromDict(data):
        opening = Opening(data["name"], data["description"], data["startingPgn"])
        opening.startingImagePath = data.get("startingImagePath")
        opening.variants = [Variant.fromDict(v) for v in data["variants"]]
        return opening