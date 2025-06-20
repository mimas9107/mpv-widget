## 🧩 MPV Widget 專案架構與邏輯流程說明

本文件針對 AI 模型（如 ChatGPT）閱讀設計，說明整體結構、主要邏輯與元件之間的關聯，以利協助後續開發與推論。

---

### 📦 專案組成

- `mpv_widget.py`：主要執行檔，包含整個 GUI 構建、mpv 播放控制、metadata 接收與顯示邏輯。
- `~/.config/mpvwidget-site.conf`：使用者設定檔，儲存串流來源清單。
- `/tmp/mpvsocket`：mpv 播放器建立的 Unix socket，用於 JSON IPC 通訊。

---

### ⚙️ 使用技術棧與元件

| 名稱                | 說明                                      |
|---------------------|-------------------------------------------|
| Python 3            | 主程式語言                                 |
| Gtk 3               | 圖形介面（使用 gi.repository）            |
| AyatanaAppIndicator3| GNOME 系統托盤圖示（AppIndicator）       |
| libnotify           | 顯示系統通知                              |
| mpv                 | 播放音訊串流，啟用 IPC 模式                |
| UNIX socket         | 與 mpv 通訊（`/tmp/mpvsocket`）           |

---

### 🧠 核心流程邏輯

```text
[選擇串流] -> [建立 mpv 子程序 + socket] -> [等待 socket 建立] ->
[啟動監聽執行緒] -> [發送 observe_property/get_property] ->
[接收 metadata] -> [顯示通知 + 更新選單文字]
```

---

### 📄 `mpvwidget-site.conf` 格式

```
<顯示名稱> | <串流網址>
範例：
古典電台 | https://example.com/classic.aac
```

---

### 🔍 主要類別與方法說明（簡要）

#### `MPVWidget` 類
整體控制器。包含以下主要方法：

- `__init__()`：初始化 GUI、AppIndicator、讀取設定
- `load_streams()`：讀取串流清單設定檔
- `build_menu()`：建立 GTK 選單，含狀態列與播放按鈕
- `on_stream_selected()`：點擊串流來源後：
  - 終止前一播放、刪除 socket（若存在）
  - 啟動 mpv（含 IPC socket）
  - 執行 socket polling 等待 mpv socket 準備好
  - 建立監聽執行緒
- `ipc_listen_loop()`：
  - 連線 mpv socket，送出 `observe_property` 與 `get_property`
  - 迴圈接收訊息、交給 `handle_ipc_message()` 處理
- `handle_ipc_message()`：解析 icy-title 並更新 GUI
- `notify()`：用 libnotify 顯示通知
- `stop_playback()`：終止 mpv 與監聽執行緒

---

### 🧪 metadata 取得策略

- 使用 `observe_property` 訂閱 metadata
- 並搭配初始的 `get_property`，解決 mpv 啟動初期 metadata 不主動推送的問題
- icy-title 的來源為 HTTP ICY 資訊（通常為電台所提供）

---

### ✅ 設計重點與可擴充建議

- 已考慮 zombie process 問題（用 Notify API 而非 `notify-send`）
- socket 連線使用溫和 polling（避免 sleep 固定等待）
- 未來可擴充：
  - 快捷鍵播放/暫停切換
  - 儲存播放紀錄、最後播放曲目
  - 以 XDG_CONFIG_HOME 改寫設定路徑

---

> 本文件設計目標為「讓 AI 能快速理解本專案結構、執行流程與依賴項目」，可配合 `LESSON_LEARNED.md` 一併理解專案演進脈絡。

