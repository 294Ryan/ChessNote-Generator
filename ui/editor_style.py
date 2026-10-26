# 編輯區的集中樣式：色票與 QSS 都在這裡，想換風格只要改色票

PAGE_BG = "#faf8f3"    # 頁面底色（與 html 輸出同色系）
CARD_BG = "#ffffff"
CARD_BORDER = "#e6dfcf"
INPUT_BG = "#fcfbf7"
INPUT_BORDER = "#ddd3bf"
INK = "#2a2520"
INK_SOFT = "#655c4e"
INK_FAINT = "#9a9080"
DANGER = "#b91c1c"    # 刪除類按鈕滑過時的顏色

CARD_RADIUS = 8    # 卡片圓角（像素）
INPUT_RADIUS = 6    # 輸入框與按鈕圓角（像素）
MONO_FONT = "Consolas, 'Courier New', monospace"


def tint(hexColor, alpha):    # #rrggbb 轉成帶透明度的 rgba
    r, g, b = (int(hexColor[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha})"


EDITOR_STYLE = f"""
QScrollArea {{ background: {PAGE_BG}; border: none; }}
#editorContainer {{ background: {PAGE_BG}; }}
QScrollBar:vertical {{ width: 10px; background: transparent; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #d6ccb6; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: #b9ad92; }}
QScrollBar:horizontal {{ height: 10px; background: transparent; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #d6ccb6; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: #b9ad92; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


def cardStyle(accent):    # 卡片內容區的樣式，accent 為該卡片主色（聚焦框與滑過色）
    return f"""
#card {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-left: none;
    border-top-right-radius: {CARD_RADIUS}px;
    border-bottom-right-radius: {CARD_RADIUS}px;
}}
#card QLabel {{ background: transparent; color: {INK_SOFT}; font-size: 12px; }}
#card QLineEdit, #card QTextEdit, #card QPlainTextEdit {{
    background: {INPUT_BG};
    color: {INK};
    border: 1px solid {INPUT_BORDER};
    border-radius: {INPUT_RADIUS}px;
    padding: 5px 8px;
    font-size: 13px;
    selection-background-color: {tint(accent, 0.25)};
    selection-color: {INK};
}}
#card QPlainTextEdit {{ font-family: {MONO_FONT}; }}
#card QLineEdit:focus, #card QTextEdit:focus, #card QPlainTextEdit:focus {{
    background: {CARD_BG};
    border: 1px solid {accent};
}}
#card QPushButton {{
    background: transparent;
    color: {INK_SOFT};
    border: 1px solid {INPUT_BORDER};
    border-radius: {INPUT_RADIUS}px;
    padding: 4px 14px;
    font-size: 12px;
}}
#card QPushButton:hover {{ background: {tint(accent, 0.10)}; border-color: {accent}; color: {accent}; }}
#card QPushButton:pressed {{ background: {tint(accent, 0.20)}; }}
#card QPushButton[danger="true"]:hover {{ background: {tint(DANGER, 0.08)}; border-color: {DANGER}; color: {DANGER}; }}
#card QRadioButton {{ color: {INK}; font-size: 13px; spacing: 6px; }}
#card QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 1px solid #b9ae98;
    background: {CARD_BG};
}}
#card QRadioButton::indicator:checked {{
    border: 1px solid {accent};
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
        stop:0 {accent}, stop:0.5 {accent}, stop:0.55 {CARD_BG}, stop:1 {CARD_BG});
}}
"""