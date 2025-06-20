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

> 本專案採持續迭代方式精進，未來若支援播放記錄、快捷鍵或封裝安裝，將另記於後續版本紀錄。

