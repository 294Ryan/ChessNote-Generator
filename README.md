# Chess Opening Note Generator

輸入開局資料（Variant / 子分類 / Line + PGN），自動渲染棋盤圖，匯出為 `.docx` 或可折疊的自包含 `.html` 筆記。

## 安裝

```
pip install -r requirements.txt
```

## 執行

```
python main.py
```

## 專案結構

```
core/        商業邏輯（與 UI 無關）：資料模型、PGN 渲染、匯出、存檔
ui/          PyQt5 介面元件
templates/   HTML 匯出模板（Jinja2）
assets/      應用程式圖示等資源（放 icon.ico）
```

## 打包成 .exe（PyInstaller，後續步驟）

```
pyinstaller --onefile --windowed --add-data "templates;templates" main.py
```

## 已知狀態

- 核心邏輯（core/）已通過單元測試
- UI（ui/）已通過語法檢查，尚未在有 PyQt5 + 顯示器的環境實際執行測試，請在本機測試並回報問題
