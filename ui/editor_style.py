# 編輯區的集中樣式：色票在 ui/theme.py，這裡只負責把色票組成 QSS
from ui.theme import palette, scrollbarStyle

CARD_RADIUS = 8    # 卡片圓角（像素）
INPUT_RADIUS = 6    # 輸入框與按鈕圓角（像素）
MONO_FONT = "Consolas, 'Courier New', monospace"


def tint(hexColor, alpha):    # #rrggbb 轉成帶透明度的 rgba
    r, g, b = (int(hexColor[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


def editorStyle():    # 編輯區最外層：頁面底色與捲軸
    p = palette()
    return f"""
QScrollArea {{ background: {p.pageBg}; border: none; }}
#editorContainer {{ background: {p.pageBg}; }}
""" + scrollbarStyle()


def cardStyle(accent):    # 卡片內容區的樣式，accent 為該卡片主色（聚焦框與滑過色）
    p = palette()
    return f"""
#card {{
    background: {p.cardBg};
    border: 1px solid {p.cardBorder};
    border-left: none;
    border-top-right-radius: {CARD_RADIUS}px;
    border-bottom-right-radius: {CARD_RADIUS}px;
}}
#card QLabel {{ background: transparent; color: {p.inkSoft}; font-size: 12px; }}
#card QLineEdit, #card QTextEdit, #card QPlainTextEdit {{
    background: {p.inputBg};
    color: {p.ink};
    border: 1px solid {p.inputBorder};
    border-radius: {INPUT_RADIUS}px;
    padding: 5px 8px;
    font-size: 13px;
    selection-background-color: {tint(accent, 0.25)};
    selection-color: {p.ink};
}}
#card QPlainTextEdit {{ font-family: {MONO_FONT}; }}
#card QPlainTextEdit[invalid="true"], #card QPlainTextEdit[invalid="true"]:focus {{ border: 1px solid {p.danger}; }}
#card QLineEdit:focus, #card QTextEdit:focus, #card QPlainTextEdit:focus {{
    background: {p.cardBg};
    border: 1px solid {accent};
}}
#card QPushButton {{
    background: transparent;
    color: {p.inkSoft};
    border: 1px solid {p.inputBorder};
    border-radius: {INPUT_RADIUS}px;
    padding: 4px 14px;
    font-size: 12px;
}}
#card QPushButton:hover {{ background: {tint(accent, 0.10)}; border-color: {accent}; color: {accent}; }}
#card QPushButton:pressed {{ background: {tint(accent, 0.20)}; }}
#card QPushButton[danger="true"]:hover {{ background: {tint(p.danger, 0.10)}; border-color: {p.danger}; color: {p.danger}; }}
#card QRadioButton {{ color: {p.ink}; font-size: 13px; spacing: 6px; }}
#card QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 1px solid {p.radioBorder};
    background: {p.cardBg};
}}
#card QRadioButton::indicator:checked {{
    border: 1px solid {accent};
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 {accent}, stop:0.5 {accent}, stop:0.55 {p.cardBg}, stop:1 {p.cardBg});
}}
"""