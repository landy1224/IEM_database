# IEM_database

代謝營養主資料庫：嬰幼兒特殊奶粉、罕病特殊配方、低蛋白食品、熱量補充品等品項的營養成分查詢與份量換算工具。

## 檔案

| 路徑 | 用途 |
|---|---|
| `index.html` | 單檔查詢版（資料與產品圖內嵌，唯讀），由 GitHub Pages 部署在網站根目錄。資料快照 2026-11-12。 |
| `editable/index.html` | 可編輯版頁面，發布為 Claude Artifact（資料存在 artifact 資料庫 collection `items`，可新增／編輯／建立新版本／刪除，並可新增／更換／移除產品照片）。無法連線資料庫時（例如在 GitHub Pages 上開啟 `/editable/`）自動改讀 `seed.json`，唯讀。 |
| `editable/seed.json` | 2026-11-12 快照 228 筆，資料庫為空時可由頁面上的「匯入快照資料」按鈕寫入。 |
| `editable/img/` | 117 張產品圖（檔名＝品項 id）。 |
| `tools/build_editable.py`、`tools/patch_photos.py` | 由根目錄 `index.html` 重新產生 `editable/`：先 `python3 -I tools/build_editable.py index.html editable`，再 `python3 -I tools/patch_photos.py editable/index.html`（加入照片上傳）。 |

## 注意

- 資料僅供臨床參考，使用前請對照台灣實際產品包裝標示或廠商資料；橘色「估」為估算值。
- 可編輯版的最新資料在 artifact 資料庫裡，`seed.json` 只是初始快照，不會自動同步。
- 照片：內建 117 張在 `editable/img/`（品項欄位 `img`）；在網頁上傳的照片存在 artifact 的 assets（品項欄位 `imgAsset`，網址 `/_blob/<id>`），不在 repo 裡。
