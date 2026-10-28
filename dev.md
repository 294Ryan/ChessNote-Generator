### 專案概述

**Chess Opening Note Generator** 是一款 Windows 桌面應用程式，讓西洋棋學習者透過結構化 UI 輸入開局資料（Variant / 子分類 / Line / PGN），自動渲染棋盤圖並匯出為具有出版品質感的 `.docx` 或可折疊的自包含 `.html` 筆記。支援專案存檔，方便分次編輯。目標使用者是自己整理開局筆記的棋手與學習者。

---

### 核心功能列表

**編輯與資料結構**
- 🔴 三層結構：Variant > 子分類（選用）> Line。**Line 只有 PGN 與圖片**（已移除名稱與說明欄位）；各層內 Line 一律排在子分類之上（編輯區、左側樹、docx、html 順序一致）— **已完成**
- 🔴 開局基本資訊：名稱、**棋盤視角（White / Black 單選）**、概述、起始 PGN + 棋盤圖 — **已完成**
- 🔴 棋盤視角決定自動生成圖片的朝向（手動上傳圖不受影響），並輸出視角字樣（繁中為 `Perspective: White/Black`，其他語言隨翻譯）於 docx / html / pdf 的標題與概述之間 — **已完成**
- 🔴 PGN 自動渲染最終盤面（debounce 300ms，停止輸入後才重繪）— **已完成**
- 🔴 圖片三種狀態：自動生成 / 手動上傳 / 刪除（空白）。按鈕列為 `[▼][上傳圖片] …… [刪除圖片｜使用預設]`；預覽圖可用 ▼/▶ 收合（起始局面不可收合）— **已完成**
- 🔴 專案存檔 / 載入（`.json`）；新增欄位 `orientation`、`startingNoImage`、Line 的 `noImage`；舊存檔缺欄位時自動補預設、Line 舊的 `name`/`description` 讀取時忽略 — **已完成並測試**

**排序與導覽**
- 🔴 編輯區拖曳排序：每個區塊右上 ☰ 握把，紅色插入線、邊緣自動捲動；**只限同父層、同類型**（Variant 之間、同 Variant 下子分類之間、同父層 Line 之間），Variant 會連同底下內容整塊移動 — **已完成**
- 🔴 左側樹拖曳排序：規則同上，放開後由 model 重排並重建兩側 — **已完成**（游標禁止符號問題已改為強制接受，待實機確認）
- 🔴 左側樹：自製列（色條 + 同色系淡底 + 滑過加深）、Line 標題為 `Line.1`（滑過顯示完整 PGN）、✕ 刪除鈕滑過才出現、點擊跳至對應編輯區塊 — **已完成**
- 🔴 左側樹「+ 新增」列：平常整列隱藏不佔位，滑到所屬區塊（Variant／子分類）才展開；`+` 對齊新項目的色條左緣；新增一律加在該組最下面 — **已完成**

**外觀**
- 🟡 編輯區紙質感樣式（卡片圓角、輸入框聚焦用卡片主色、細捲軸、自繪單選框），集中於 `ui/editor_style.py` — **已完成**
- 🟡 選單列美化（底色、圓角項目、細邊線）與 **淺色 / 深色主題切換**（選單列右側按鈕，套用選單列 + 左側樹 + 編輯區；不記住選擇，每次啟動為淺色），色票集中於 `ui/theme.py` — **已完成**
- 🟡 自繪提示框 `ui/dialogs.py`（`showInfo` / `showConfirm`）：圖示、半透明遮罩、無動畫，色票取自 theme — **已完成**
- 🟡 自備字型 `assets/fonts/NotoSansTC-Regular.ttf`，僅影響編輯器顯示（UI 與使用者輸入），不影響匯出；PGN 輸入框維持等寬字型 — **已完成**
- 🟡 多語言：選單列「語言」項（繁中、简中、English、日、韓、西、俄、德、法），切換即時生效；字串集中於 `core/i18n.py`（`t(key)`，缺字退回英文），涵蓋 UI 與匯出檔固定標題；啟動依系統語言自動選擇，無對應則英文；新增語言只需在 `LANGUAGES` 與 `TEXTS` 各加一筆 — **已完成，待實機驗證版面**

**匯出**
- 🔴 `.html`：米白紙感、襯線字體、酒紅強調色；起始局面標題與 Variant 同格式；Line 卡片可折疊，**摺疊列直接顯示 PGN**（淡色底標記、字稍大，過長以 `...more` 截斷），展開後顯示完整 PGN 與圖片；無圖片的 Line 仍可展開（不留白佔位）；響應式與列印樣式 — **已完成**
- 🔴 `.docx`：黑白報告風格、棋盤圖近全寬、Line 僅輸出 PGN（12pt，前後以不換行空白墊底）與圖片、標題層級 26 / 20 / 16pt（使用者已自行微調）— **已完成**
- 🟡 `.pdf`：`core/exporter_pdf.py`，以 `QTextDocument` + `QPrinter` 輸出（不增加依賴、exe 不變大）；A4、邊距 5mm、Line 全展開、PGN 底色標記 + 圖片（棋盤圖統一寬度）— **已完成**
- 🟢 打包成單一 `.exe`（PyInstaller）— 指令已定，見「打包」；目標 Win10 以上
- 🟢 app 圖示 `assets/fonts/icons/app_icon.ico` — **已提供**

---

### 技術選型

- **開發語言**：Python
- **UI 框架**：PyQt5
- **棋盤渲染**：`python-chess`（PGN parse + SVG，支援黑白視角）、PyQt5 內建 `QtSvg`（SVG → PNG，避免 cairosvg 等 Windows 原生依賴）
- **docx 生成**：`python-docx`
- **HTML 生成**：Jinja2
- **存檔格式**：JSON
- **打包工具**：PyInstaller（單檔）
- **路徑處理**：動態路徑（`sys._MEIPASS` / `__file__`），`main.py` 動態解析 PyQt5 外掛路徑，修正中文使用者路徑下的 Qt 平台外掛載入失敗問題

**目前程式結構**
- `core/`：`models.py`（資料模型、`moveItem` 調序）、`pgn_renderer.py`、`project_io.py`、`exporter_docx.py`、`exporter_html.py`、`exporter_pdf.py`、`i18n.py`
- `ui/`：`main_window.py`（主視窗、選單、主題切換、樹調序）、`tree_panel.py`（左側樹）、`editor_panel.py`（編輯區 + 拖曳）、`line_widget.py`（PGN + 圖片編輯器）、`editor_style.py`、`theme.py`、`dialogs.py`
- `assets/fonts/`：自備字型與 `icons/app_icon.ico`
- `templates/`：`opening_note.html.j2`、`_line_card.html.j2`

---

### 設計系統

**HTML 版**：編輯式出版品風格
- 色彩：米白紙感背景、深墨色正文、酒紅強調色；PGN 標記底色 `#f7eee6`、字色 `#5c2222`
- 字體：襯線字體作標題正文、等寬字體作 PGN
- 層級：Variant 與「起始局面」同級（`<h2>`，不折疊）；子分類不折疊；**唯一可折疊的是 Line 卡片**

**docx 版**：素雅黑白報告風格
- 棋盤圖 5.5 吋、Variant 之間以段落下框線分隔、PGN 等寬字體 + 柔和酒紅色

**編輯器 UI**：
- 淺色沿用 html 的米白酒紅色調；深色為暖黑底
- 節點主色：Variant 藍、子分類綠、Line 棕（深色模式未另外調亮）
- 所有色票在 `ui/theme.py`，圓角與字型在 `ui/editor_style.py`

---

### 已知限制與邊界

- `.docx` 全展開，無互動折疊（Word 格式限制）
- 棋盤圖僅渲染 PGN 最終盤面，不做逐步動畫；不做 PGN 深度合法性驗證
- 欄位文字變動只刷新樹狀標籤，不重建整個編輯區；新增 / 刪除 / 拖曳調序 / 切換主題 / 切換語言 / 開啟存檔才完整重建兩側
- 拖曳只能在同父層同類型內調序，不支援跨父層搬移
- 棋盤視角只影響自動生成圖，不影響手動上傳圖；匯出檔不隨編輯器主題變化
- html 摺疊列的 `...more` 由 Python 端以 `PGN_PREVIEW_LENGTH` 截斷；視窗過窄時瀏覽器會改用預設的 `…`
- 主題與語言都不記憶；檔案對話框維持系統預設外觀（提示框為自繪）
- 下拉選單未做圓角（Qt popup 圓角在 Windows 易出黑角）
- **新版存檔無法被舊版程式讀取**（舊版讀 Line 時找不到 `name`）；舊檔用新版開啟再存檔後，Line 的名稱與說明會永久消失
- PDF 為 Qt 精簡版 HTML 渲染：無米白頁底色、無圓角／折疊；無法保證 Line 區塊不被跨頁切開；字型為 Georgia + 系統 fallback。不滿意再升級 `PyQtWebEngine`（約 +100MB）
- 說明欄位維持單一通用欄位，不拆分「說明 / 優點 / 缺點」
- 不做 Settings／About 頁面；不附 Bold 字型（粗體由 Qt 模擬，不滿意再補 `NotoSansTC-Bold.ttf`）
- 不支援線上同步
- 多語言：Variant／Line 為專有術語，各語言維持英文；繁中的視角字樣與單選鈕維持 `Perspective` / `White` / `Black`，docx 標題維持「基本局面」（避免改變既有筆記外觀）；日、韓、西、俄、德、法翻譯未經母語者審閱；不支援由右至左語言；docx 非中文字元的字型由 Word 自動替換
- 開發環境（沙盒）無 PyQt5 / python-chess：多數 UI 行為只以模擬元件驗證邏輯，視覺與手感需實機確認

---

### 打包

```
pyinstaller --noconfirm --clean --onefile --windowed --name ChessNoteGenerator --icon "assets\fonts\icons\app_icon.ico" --add-data "templates;templates" --add-data "assets/fonts/NotoSansTC-Regular.ttf;assets/fonts" --collect-data docx main.py
```

輸出：`dist\ChessNoteGenerator.exe`

---

### 待辦

- README 與 `requirements.txt` 尚未依近期變更複查（Line 欄位說明、視角與圖片按鈕、PDF 匯出、打包指令）