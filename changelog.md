## 🧠 MPV Widget 開發歷程 v1.0 \~ v1.5 技術重點整理

本文件記錄從初版 v1.0 到 v1.5 的演進過程，每版重點摘要，作為本專案的開發紀錄與技術演進說明。

---

### 🔹 v1.0：基本播放控制功能

**技術重點：**
以 Python + Gtk + AppIndicator 建立系統托盤工具，讀取 `.config/mpvwidget-site.conf` 播放串流網址，提供簡單播放、停止、退出功能。初版使用 `subprocess.Popen` 呼叫 `mpv` 播放，不含 metadata 顯示與通知功能。

---

### 🔹 v1.1：加入系統通知（Notify）

**技術重點：**
導入 `gi.repository.Notify`，播放與停止動作透過 `notify-send` 顯示系統通知。不再使用外部命令，改為用 `Notify.Notification.new()` 呼叫通知，避免 zombie process 問題，提升穩定性與整合度。

---

### 🔹 v1.2：支援 mpv metadata（socket IPC）

**技術重點：**
啟用 mpv 的 `--input-ipc-server` 參數建立 socket，使用 UNIX domain socket 與 JSON RPC 通訊，訂閱 `metadata` 屬性。實作背景 thread 持續監聽 `icy-title` 變化，自動推送目前曲目信息至通知。

---

### 🔹 v1.3：整合 UI 狀態顯示

**技術重點：**
將目前播放曲目顯示於選單第一行（disabled MenuItem），同步更新 `AppIndicator.set_title()` 顯示曲目。雖然 GNOME Wayland 不支援 tooltip，但內部狀態已完整呈現，提升使用體驗一致性。

---

### 🔹 v1.4：解決初始 metadata 無法取得問題

**技術重點：**
加入首次啟動後自動發送 `"get_property"` 命令取得初始 metadata，避免只靠 `"observe_property"` 無法即時觸發時出現空白狀況。修正 `handle_ipc_message()` 判斷條件支援雙模式。

---

### 🔹 v1.5：優化 socket 初始化（溫和 polling）

**技術重點：**
以溫和 polling（最多 3 秒，每 100ms 嘗試）確認 `/tmp/mpvsocket` 已建立並可連線，取代不精準的 `time.sleep()`，提升穩定性與跨環境兼容性。至此版本整體架構穩定，可實用部署。

---

### * 多來源 mpv 播放情境下，若遇本地 cvlc raw stream，必須用 python polling status.xml 更新目前曲目資訊，同時保留 icy-title 事件處理，達成一致的托盤顯示。

**技術解決重點**

    - VLC 其實會透過 http://localhost:8081/requests/status.xml 提供目前曲目信息

    - 在 python 中額外啟動一個 thread
      → 定期輪詢 status.xml
      → 把拿到的 title 直接更新 self.current_title
      → 這樣就能在 AppIndicator 中正確顯示本地串流的曲目

    - 同時保留原本 mpv 的 metadata 監聽邏輯
      → 讓其他外部線上電台依然可自動處理 icy-title
    
    - {"command": ["show-text",...]} 指令只能讓 mpv 顯示 OSD，不會回寫 metadata, 也就是我們不是 icecast server我們無從下手改 metadata,

    - VLC 不會主動把曲目送到 mpv, 必須靠自己的程式作為「協調者」
      → 主動抓 status.xml
      → 並更新 GUI

    - 維持 polling thread 與 mpv 的 IPC thread 並行，邏輯互不干擾
