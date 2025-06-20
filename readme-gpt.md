# 🎧 MPV Widget - GNOME System Tray 音樂播放控制器

這是一個 Python 撰寫的小工具，整合於 GNOME 系統托盤（System Tray）中，方便地播放自訂串流音樂來源，並顯示目前播放的曲目信息。

## 🔍 專案簡介

MPV Widget 使用 `mpv` 播放器與 IPC 機制，並以 Gtk + AyatanaAppIndicator 建立 GUI，透過系統通知與選單顯示目前播放的歌曲 metadata，適合用於播放線上廣播或音樂串流站台。

## ✨ 功能特色

- 在 System Tray 點擊選單即可播放/停止串流
- 支援多個串流來源，從設定檔自訂
- 自動顯示目前曲目（icy-title）於選單與通知
- 使用 mpv socket 與 JSON-RPC 取得 metadata
- 溫和 polling 確保 mpv socket 啟用後才建立監聽
- 系統通知不會產生 zombie process

## 🧱 安裝依賴

請先確保系統已安裝以下元件：

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-ayatanaappindicator3-0.1 mpv
```

## ⚙️ 執行方式

```bash
chmod +x mpv_widget.py
./mpv_widget.py &
```

或將其加入自動啟動。

## 📝 串流來源設定檔

設定檔位於： `~/.config/mpvwidget-site.conf`

格式為每行一筆：
```
<顯示名稱> | <串流網址>
```

範例：
```
古典音樂 | https://mscp3.live-streams.nl:8252/class-high.aac
NPO Radio1 | https://icecast.omroep.nl/radio1-bb-mp3
```

## 📂 專案架構

- `mpv_widget.py`：主程式入口
- `~/.config/mpvwidget-site.conf`：使用者自訂站台清單
- `/tmp/mpvsocket`：mpv 的 IPC socket（執行時動態建立）
- `ARCHITECTURE.md`：系統邏輯與流程說明
- `LESSON_LEARNED.md`：版本演進與設計紀錄

## 📌 注意事項

- GNOME / Wayland 下 System Tray 不支援 tooltip，因此 `set_title()` 僅作狀態同步用途
- 須確保 mpv 執行環境與串流網址可用，部分站台可能會阻擋或斷線
- socket 於播放停止後不會自動刪除，必要時可手動清除 `/tmp/mpvsocket`

## 📈 發展歷程

請參考 `LESSON_LEARNED.md`，記錄 v1.0 ~ v1.5 各階段重點改進。

## 🔮 未來可能功能

- 播放熱鍵快捷鍵（Pause/Play）
- 封裝為 .deb 套件安裝
- 歌曲歷史記錄與上次播放紀錄保存

---

本專案為個人學習與生活整合所建，歡迎自由 fork、改作與貢獻意見。

