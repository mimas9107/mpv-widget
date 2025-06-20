### v1.5 feature2 2025/06/20
1. 增加 title超過 24個字會自動滾動顯示.

### v1.5 feature1 2025/06/20
1. 更新 title處理24個字元後會插入一個 \n避免 menu中顯示過長字串.

---
### ~v1.5 2025/06/20 
1. ![參考changelog](changelog.md)
2. 捨棄 notify-send指令的 殭屍執行緒問題, 改採用 Notify來推送通知.
3. 在 system tray的圖示下拉可以顯示目前播放曲目.
4. 修正 mpv子執行緒的 mpvsocket與主程式的先後polling機制. 
5. 補充：debug mpvsocket訊息工具指令, 
```bash
echo '{"command": ["observe_property", 1, "metadata"]}' | socat - /tmp/mpvsocket

or

echo '{"command": ["get_property", "metadata"]}' | socat - /tmp/mpvsocket

```
---
### v1.0 2025/06/19 initial

---
### 功能說明
一個用 Python 撰寫的 GNOME 系統圖示工具，點擊圖示即可播放或停止指定的網路串流（使用 mpv 播放器），支援：
* GNOME system tray integration（使用 libayatana-appindicator3）

* 串流清單來自 ~/.config/mpvwidget-site.conf

* 點選清單即播放；再點「停止播放」即中止 mpv

![screenshot](image/screenshot2.png)


### 檔案結構
```
mpv-widget
├── architecture-gpt.md      ##要讓ai / gpt快速讀懂架構的文件
├── changelog.md             ##版本紀錄
├── config
│   └── mpvwidget-site.conf ##串流站台設定檔
├── image
│   └── screenshot2.png     ##專案說明文件會嵌入的範例圖 
├── mpvwidget.desktop        ##要安裝到 ~/.config/autostart的捷徑檔
├── mpv_widget.py            ##主程式
├── install.sh               ##安裝程式
├── readme-gpt.md            ##要讓ai / gpt快速讀懂架構的文件
└── README.md                ##本說明文件
```

### 安裝需求
```bash
sudo apt update
sudo apt install mpv python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 libnotify-bin
```
##[手動]
---
### 使用者安裝步驟
```
git clone <this_repo_url>
cd mpv-widget
```

```bash
mkdir -p ~/.config
mkdir -p ~/bin
cp config/mpvwidget-site.conf ~/.config/
cp mpv_widget.py ~/bin/
#curl -o ~/.config/mpvwidget-site.conf https://example.com/mpvwidget-site.conf  # 或自己建立
#curl -o ~/bin/mpv_widget.py https://example.com/mpv_widget.py
chmod +x ~/bin/mpv_widget.py
```
### 設定串流清單
建立或編輯檔案：
```bash
nano ~/.config/mpvwidget-site.conf
```
```
#格式為每行一筆：
名稱1|https://網址1
名稱2|https://網址2
```

### 執行程式
```bash
~/bin/mpv_widget.py &
```
圖示會出現在 GNOME 系統右上角，點選即可播放串流。

### 建立桌面啟動器
repo.中已建立一個起動器捷徑檔, 複製到自己的桌面環境應用程式捷徑區.
```bash
cp mpvwidget.desktop ~/.local/share/applications/mpvwidget.desktop
```
```bash
並且編輯其中的路徑YOUR_USERNAME為你的使用者id,
====
[Desktop Entry]
Type=Application
Name=MPV 控制器
Exec=/home/YOUR_USERNAME/bin/mpv_widget.py
Icon=media-playback-start
Terminal=false
Categories=Audio;Player;
Comment=控制 mpv 播放器的 GNOME 小工具
====
```

