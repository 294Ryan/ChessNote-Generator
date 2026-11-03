### 專案概述

**Chess Opening Note Generator** 是一款 Windows 桌面應用程式（PyQt5），讓西洋棋學習者透過結構化 UI 輸入開局資料（Variant / 子分類 / Line / PGN），自動渲染棋盤圖並匯出為具有出版品質感的 `.docx`、可折疊的自包含 `.html`，或 `.pdf` 筆記。支援專案存檔、淺色／深色主題與 9 種介面語言，方便不同語言的棋手分次整理自己的開局筆記。目標使用者是自己整理開局筆記的棋手與學習者。

---

### 核心功能列表

**編輯與資料結構**
- 🔴 三層結構：Variant > 子分類（選用）> Line；**Line 只有 PGN 與圖片**；各層內 Line 一律排在子分類之上（編輯區、左側樹、三種匯出順序一致）— **已完成**
- 🔴 開局基本資訊：名稱、棋盤視角（White / Black 單選）、概述、起始 PGN + 棋盤圖；視角決定自動生成圖的朝向，並以 `Perspective` 行輸出於標題與概述之間 — **已完成**
- 🔴 PGN 自動渲染最終盤面（debounce 300ms）— **已完成**
- 🔴 **PGN 錯誤提示**：PGN 無法解析時，輸入框邊框變紅並顯示「第 N 手（白/黑）「著法」無法解析，圖片只顯示到這之前」（隨語言翻譯）— **已完成**
- 🔴 圖片三種狀態：自動生成 / 手動上傳 / 刪除（空白）；預覽可收合（起始局面不可）— **已完成**
- 🔴 專案存檔 / 載入（`.json`）：含 `orientation`、`startingNoImage`、Line 的 `noImage`；舊存檔缺欄位自動補預設，Line 舊的 `name`/`description` 讀取時忽略 — **已完成**
- 🔴 **未存檔保護**：關閉視窗、開啟其他專案前若有未存修改，詢問「儲存 / 不儲存 / 取消」；標題列顯示檔名，有未存修改時前面加 `*`（以內容快照比對，切換主題與語言不算修改）— **已完成**
- 🔴 **儲存確認與快捷鍵**：「儲存專案」「另存專案」執行前各有一次自繪確認框；`Ctrl+O` / `Ctrl+S` / `Ctrl+Shift+S`；未命名專案按儲存時直接走另存；在「尚未儲存」提示中選儲存不會再跳第二次確認 — **已完成**

**排序與導覽**
- 🔴 編輯區與左側樹皆可拖曳排序，只限同父層、同類型；Variant 連同底下內容整塊移動 — **已完成**
- 🔴 左側樹：自製列（色條 + 同色系淡底 + 滑過加深）、`Line.N` 標題（滑過顯示完整 PGN）、✕ 滑過才出現；「+ 新增」列平常整列隱藏，滑到所屬區塊才展開，`+` 對齊新項目位置 — **已完成**

**外觀與多語言**
- 🟡 編輯區紙質感樣式（`ui/editor_style.py`）、選單列美化、**淺色 / 深色主題切換**（色票集中於 `ui/theme.py`，不記住選擇）— **已完成**
- 🟡 **自繪提示框**取代原生 `QMessageBox`（`ui/dialogs.py`）：info、確認（warn / check 圖示、可標危險色）、三按鈕的「尚未儲存」選擇；半透明背景遮罩，色票跟隨主題 — **已完成**
- 🟡 **編輯器自備字型** `NotoSansTC-Regular.ttf`（`assets/fonts/`），只影響編輯器顯示，不影響匯出檔字型；粗體由 Qt 模擬 — **已完成**
- 🟡 **多語言**：選單列「語言」項切換，9 種語言（繁中、簡中、English、日本語、한국어、Español、Русский、Deutsch、Français）；啟動時依系統語言，找不到則用英文；不記住選擇；匯出檔固定標題隨語言（`core/i18n.py`，共 64 個 key，缺字退回英文）— **已完成**

**匯出與發佈**
- 🔴 `.html`：米白紙感、襯線字體、酒紅強調色；起始局面標題與 Variant 同格式；Line 卡片可折疊，摺疊列直接顯示 PGN（淡色底標記，過長以 `...more` 截斷），展開後顯示完整 PGN 與圖片；無圖片的 Line 仍可展開；`<html lang>` 隨語言；響應式與列印樣式 — **已完成**
- 🔴 `.html` 互動棋盤：自動生成圖改由 html 內的 SVG 棋盤繪製（棋子取自 `chess.svg.PIECES`），不再嵌入 PNG；只有「上一步／下一步／重置」三顆按鈕，支援點擊與拖曳（電腦、手機皆可）；**只能走筆記內已登錄的著法**，並以箭頭畫出該局面所有已登錄的下一步；預設與重置皆為該 PGN 最終局面。範圍：起始局面棋盤＝全部 Line（含起始 PGN）；Line 棋盤＝僅自己的 PGN。箭頭：該棋盤自己 PGN 的下一步為酒紅主色，其他分支為淡色。手動上傳圖維持靜態 `<img>`，刪除圖不放棋盤；下一步優先走自己 PGN 的那步，其次才重做，離開 PGN 後遇分支由使用者自己走。尺寸暫定起始 340px、Line 300px，待實機微調 — **已完成（待實機驗證）**
- 🔴 `.docx`：黑白報告風格、Line 僅輸出 PGN（12pt）與圖片、標題 26 / 20 / 16pt — **已完成**
- 🟡 `.pdf`：以 `QTextDocument` + `QPrinter` 產生，頁邊距 5mm，所有棋盤圖統一寬度；外觀可比 html 版略簡單 — **已完成**
- 🟡 單一 `.exe` 打包（PyInstaller，`ChessNoteGenerator.spec`），圖示 `assets/fonts/icons/app_icon.ico` — **已完成**

**評估後決定不做**：複製節點、匯入 PGN 檔、記住主題或語言、settings 頁面、about 頁面、全英文版（改為多語言切換）、額外的 Noto Sans TC Bold 字型檔

---

### 技術選型

- 開發語言：Python
- 主要套件／框架：PyQt5（UI、`QtSvg` 渲染棋盤、`QTextDocument` / `QPrinter` 產生 PDF）、`python-chess`（PGN 解析與棋盤 SVG，支援黑白視角）、`python-docx`（docx）、Jinja2（html）
- 執行環境：Windows 桌面（Windows 10 以上）；以 PyInstaller 打包為單一 exe，路徑一律動態解析（`sys._MEIPASS` / `__file__`），`main.py` 動態解析 PyQt5 外掛路徑，避免中文使用者路徑下 Qt 平台外掛載入失敗
- 其他工具：JSON 存檔；自製 i18n 字典（`core/i18n.py`，`t(key, **kwargs)`）；QSS 集中樣式（`ui/theme.py`、`ui/editor_style.py`）；自備字型 Noto Sans TC

**程式結構**
- `core/`：`models.py`（資料模型、`moveItem` 調序）、`pgn_renderer.py`（渲染與 `checkPgn`）、`project_io.py`、`exporter_docx.py`、`exporter_html.py`、`exporter_pdf.py`、`i18n.py`
- `ui/`：`main_window.py`（主視窗、選單、快捷鍵、未存檔保護、主題與語言切換、樹調序）、`tree_panel.py`、`editor_panel.py`、`line_widget.py`、`dialogs.py`、`editor_style.py`、`theme.py`
- `templates/`：`opening_note.html.j2`、`_line_card.html.j2`、`board.js`（互動棋盤，由 `exporter_html.py` 讀入後內嵌，不是 Jinja 模板）
- `assets/`：字型與圖示；`ChessNoteGenerator.spec`：打包設定

---

### 設計系統

- **HTML 版**：編輯式出版品風格；米白紙感背景、深墨色正文、酒紅強調色；PGN 標記底色 `#f7eee6`、字色 `#5c2222`；襯線標題 + 等寬 PGN；Variant 與「起始局面」同級，唯一可折疊的是 Line 卡片
- **docx 版**：素雅黑白報告風格；棋盤圖 5.5 吋、Variant 之間以下框線分隔、PGN 等寬字體 + 柔和酒紅色
- **編輯器 UI**：淺色沿用 html 的米白酒紅色調、深色為暖黑底；節點主色 Variant 藍、子分類綠、Line 棕（深色主題主色維持現狀）；所有色票在 `ui/theme.py`，圓角與字型在 `ui/editor_style.py`；提示框強調色 `#7a2e2e`，危險色 `#b91c1c`（見 `ui/dialogs.py`）

---

### 已知限制與邊界

- `.docx` 全展開，無互動折疊（Word 格式限制）；`.pdf` 外觀比 html 版簡單（不使用 QtWebEngine，避免 exe 變大）
- docx / pdf 的棋盤圖僅渲染 PGN 最終盤面，不做逐步動畫；html 版為互動棋盤；PGN 錯誤提示只指出第一個無法解析的著法
- 拖曳只能在同父層同類型內調序，不支援跨父層搬移
- 棋盤視角只影響自動生成圖，不影響手動上傳圖；匯出檔不隨編輯器主題變化
- 主題與語言都不記住，每次啟動：主題為淺色、語言依系統；語言清單固定 9 種，新增語言需在 `LANGUAGES` 與 `TEXTS` 各加一筆
- 編輯器粗體由 Qt 模擬；自備字型只涵蓋編輯器顯示，匯出檔仍用各自設定的字型
- html 摺疊列的 `...more` 由 Python 端依 `PGN_PREVIEW_LENGTH` 截斷，視窗過窄時瀏覽器改用預設的 `…`
- html 互動棋盤：只取 PGN 主線（註解、變著、NAG 忽略）；PGN 有誤時走到出錯之前；不支援 Chess960；不同路線以「棋子位置＋輪到誰＋易位權利」判斷是否同一局面（不看吃過路兵）；箭頭只顯示、不接收點擊；視角（White / Black）也影響互動棋盤方向；JS 不判斷合法性，著法一律由 Python 端 python-chess 解析；html 內無棋盤的 Line（手動圖、刪除圖）其著法仍會登錄到起始局面棋盤
- 未存檔判斷以整份資料的 JSON 快照比對，切換主題、語言、重建畫面不會被視為修改
- 檔案選擇對話框（開啟 / 儲存 / 選圖）為系統原生外觀
- **新版存檔無法被舊版程式讀取**；舊檔用新版開啟再存檔後，Line 的名稱與說明會永久消失
- 說明欄位維持單一通用欄位；不支援線上同步

---

### 待確認事項

- **新功能實機驗證**（開發沙盒無 PyQt5 / python-chess，以下僅以模擬元件驗證過邏輯）：
  - 未存檔保護與儲存 / 另存確認：關閉視窗、開啟專案兩個入口與三個按鈕的行為，三按鈕對話框在 9 種語言下按鈕是否被擠壓
  - `Ctrl+S` 在文字輸入框內是否被攔截
  - PGN 錯誤提示：真實 python-chess 的錯誤訊息格式（著法是否正確擷取）、帶 FEN 的 PGN 手數顯示、紅框樣式
- **html 互動棋盤實機驗證**（沙盒沒有 PyQt5 / python-chess，以模擬的 python-chess 搭配 headless Chromium 測過走子、拖曳、觸控、列印與黑方視角，共 54 項通過）：
  - 真實 `chess.svg.PIECES` 的格式與棋子外觀是否正常（沙盒用圓形模擬棋子）
  - 真實 python-chess 的 FEN 標頭、著法錯誤時的 `mainline_moves()` 行為
  - 匯出檔實際大小（預估：固定約 40–60KB，加上手動上傳圖）
  - iOS Safari / Android Chrome 實機：拖曳棋子時頁面不捲動、點擊與拖曳手感
  - 棋盤尺寸（起始 340px、Line 300px）與配色（淺格 `#f0e9d6`、深格 `#c8b595`）微調
  - 按鈕文字的 9 種語言翻譯（尤其 `boardReset` 在窄螢幕是否被截斷）
- 翻譯品質：尚未經母語者審稿，特別是俄文、韓文、日文的棋類用語與較長的句子
- 重新打包 exe：既有的 `ChessNoteGenerator.exe` 是舊版本，需以 `pyinstaller ChessNoteGenerator.spec` 重新產生才會包含本次變更
