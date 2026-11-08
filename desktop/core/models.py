import uuid

def newId():    # Generate a unique id for tree node mapping
    return str(uuid.uuid4())


def moveItem(items, itemId, insertIndex):    # Move itemId before insertIndex (index is pre-move); returns True if the order changed
    oldIndex = next(i for i, n in enumerate(items) if n.id == itemId)
    newIndex = insertIndex - 1 if insertIndex > oldIndex else insertIndex
    if newIndex == oldIndex:
        return False
    items.insert(newIndex, items.pop(oldIndex))
    return True


class Line:
    def __init__(self, pgn="", imagePath=None, noImage=False, imageData=None):
        self.id = newId()
        self.pgn = pgn
        self.imagePath = imagePath    # Legacy local image path from old saves; kept as-is, no longer used; new uploads are always stored in imageData
        self.noImage = noImage    # True means no image on purpose
        self.imageData = imageData    # Base64 (PNG) of the uploaded image; None means auto-generated

    def toDict(self):
        data = {
            "id": self.id,
            "pgn": self.pgn,
            "imagePath": self.imagePath,
            "noImage": self.noImage,
        }
        if self.imageData is not None:
            data["imageData"] = self.imageData
        return data

    @staticmethod
    def fromDict(data):
        line = Line(data["pgn"], data.get("imagePath"), data.get("noImage", False), data.get("imageData"))    # Legacy name / description are ignored
        line.id = data["id"]
        return line


class SubCategory:
    def __init__(self, name="", description=""):
        self.id = newId()
        self.name = name
        self.description = description    # Optional description
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
        self.description = description    # Optional description
        self.subCategories = []
        self.lines = []    # Lines may attach directly, without a subcategory

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
        self.startingImagePath = None    # Legacy local image path from old saves; kept as-is, no longer used
        self.startingImageData = None    # Base64 (PNG) of the uploaded image; None means auto-generated
        self.startingNoImage = False    # True means no image for the starting position on purpose
        self.orientation = "white"    # Board orientation of the auto-generated image: white / black
        self.variants = []

    def addVariant(self, variant=None):
        variant = variant or Variant()
        self.variants.append(variant)
        return variant

    ### Serialization / deserialization for JSON saves ###
    def toDict(self):
        data = {
            "name": self.name,
            "description": self.description,
            "startingPgn": self.startingPgn,
            "startingImagePath": self.startingImagePath,
            "startingNoImage": self.startingNoImage,
            "orientation": self.orientation,
            "variants": [v.toDict() for v in self.variants],
        }
        if self.startingImageData is not None:
            data["startingImageData"] = self.startingImageData
        return data

    @staticmethod
    def fromDict(data):
        opening = Opening(data["name"], data["description"], data["startingPgn"])
        opening.startingImagePath = data.get("startingImagePath")
        opening.startingImageData = data.get("startingImageData")
        opening.startingNoImage = data.get("startingNoImage", False)
        opening.orientation = data.get("orientation", "white")
        opening.variants = [Variant.fromDict(v) for v in data["variants"]]
        return opening