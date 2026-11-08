# 主題色票與視窗層級樣式（選單列、分隔線、tooltip）。切換主題只要改 setTheme，各處重建後即套用新色票
from types import SimpleNamespace

LIGHT = SimpleNamespace(
    name="light",
    pageBg="#faf8f3", cardBg="#ffffff", cardBorder="#e6dfcf",
    inputBg="#fcfbf7", inputBorder="#ddd3bf",
    ink="#2a2520", inkSoft="#655c4e", inkFaint="#9a9080",
    scrollHandle="#d6ccb6", scrollHandleHover="#b9ad92", radioBorder="#b9ae98",
    treeBg="#ffffff",
    menuBg="#f3efe4", menuBorder="#ddd3bf", popupBg="#ffffff",
    hoverBg="rgba(122, 46, 46, 0.10)",    # 選單項目滑過底色
    danger="#b91c1c",
    chipAlpha=0.10, chipHoverAlpha=0.20,    # 左側樹節點底色與滑過底色的透明度
)

DARK = SimpleNamespace(
    name="dark",
    pageBg="#1a1816", cardBg="#262321", cardBorder="#3a352f",
    inputBg="#1f1c1a", inputBorder="#4a443c",
    ink="#ece6da", inkSoft="#b8ae98", inkFaint="#857c6c",
    scrollHandle="#4a443c", scrollHandleHover="#645c50", radioBorder="#6b6354",
    treeBg="#201d1b",
    menuBg="#141210", menuBorder="#3a352f", popupBg="#262321",
    hoverBg="rgba(236, 230, 218, 0.12)",
    danger="#f87171",
    chipAlpha=0.20, chipHoverAlpha=0.32,
)

_current = LIGHT


def palette():
    return _current


def isDark():
    return _current is DARK


def setTheme(name):
    global _current
    _current = DARK if name == "dark" else LIGHT


def scrollbarStyle():    # 編輯區與左側樹共用的細捲軸
    p = _current
    return f"""
QScrollBar:vertical {{ width: 10px; background: transparent; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {p.scrollHandle}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p.scrollHandleHover}; }}
QScrollBar:horizontal {{ height: 10px; background: transparent; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {p.scrollHandle}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {p.scrollHandleHover}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


def windowStyle():    # 主視窗層級：背景、選單列、下拉選單、分隔線、tooltip、主題切換鈕
    p = _current
    return f"""
QMainWindow {{ background: {p.pageBg}; }}
QMenuBar {{
    background: {p.menuBg};
    color: {p.ink};
    border-bottom: 1px solid {p.menuBorder};
    padding: 4px 8px;
    spacing: 2px;
    font-size: 13px;
}}
QMenuBar::item {{ background: transparent; padding: 5px 14px; border-radius: 6px; }}
QMenuBar::item:selected {{ background: {p.hoverBg}; }}
QMenu {{ background: {p.popupBg}; color: {p.ink}; border: 1px solid {p.menuBorder}; padding: 6px; font-size: 13px; }}
QMenu::item {{ padding: 6px 28px 6px 14px; border-radius: 5px; }}
QMenu::item:selected {{ background: {p.hoverBg}; }}
QMenu::item:disabled {{ color: {p.inkFaint}; }}
QMenu::separator {{ height: 1px; background: {p.menuBorder}; margin: 5px 8px; }}
QSplitter::handle {{ background: {p.menuBorder}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QToolTip {{ background: {p.popupBg}; color: {p.ink}; border: 1px solid {p.menuBorder}; padding: 4px 6px; }}
#themeToggle {{ background: transparent; color: {p.ink}; border: none; border-radius: 6px; padding: 5px 12px; font-size: 13px; }}
#themeToggle:hover {{ background: {p.hoverBg}; }}
"""