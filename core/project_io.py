import json
from core.models import Opening

def saveProject(opening, filePath):
    with open(filePath, "w", encoding="utf-8") as f:
        json.dump(opening.toDict(), f, ensure_ascii=False, indent=2)


def loadProject(filePath):
    with open(filePath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Opening.fromDict(data)
