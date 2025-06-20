#!/bin/bash
set -e

echo "🛠️ 安裝 MPV GNOME 小工具中..."

INSTALL_DIR="$HOME/.local/bin"
AUTOSTART_DIR="$HOME/.config/autostart"
CONFIG_DIR="$HOME/.config"
DESKTOP_FILE="./mpvwidget.desktop"
CONFIG_FILE="./config/mpvwidget-site.conf"
TARGET_DESKTOP_FILE="$AUTOSTART_DIR/mpvwidget.desktop"
TARGET_SCRIPT="$INSTALL_DIR/mpvwidget"

# 建立必要資料夾
mkdir -p "$INSTALL_DIR"
mkdir -p "$AUTOSTART_DIR"
mkdir -p "$CONFIG_DIR"

# 安裝主程式
cp ./mpv_widget.py "$TARGET_SCRIPT"
chmod +x "$TARGET_SCRIPT"
echo "✅ 已安裝主程式到 $TARGET_SCRIPT"

# 安裝設定檔（如尚未存在）
if [ ! -f "$CONFIG_DIR/mpvwidget-site.conf" ]; then
    cp "$CONFIG_FILE" "$CONFIG_DIR/"
    echo "✅ 已複製預設設定檔到 $CONFIG_DIR/mpvwidget-site.conf"
else
    echo "⚠️ 發現已存在設定檔，未覆蓋：$CONFIG_DIR/mpvwidget-site.conf"
fi

# 安裝自動啟動捷徑（取代 Exec 內容）
sed "s|^Exec=.*|Exec=$TARGET_SCRIPT|" "$DESKTOP_FILE" > "$TARGET_DESKTOP_FILE"
chmod +x "$TARGET_DESKTOP_FILE"
echo "✅ 已安裝開機啟動捷徑到 $TARGET_DESKTOP_FILE"

# 建議依賴
echo ""
echo "📦 請確認以下依賴已安裝："
echo "    sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-notify-0.7 gir1.2-ayatanaappindicator3-0.1 mpv"
echo ""

# 問是否現在啟動
read -p "是否要現在啟動 mpvwidget？(y/N) " choice
if [[ "$choice" =~ ^[Yy]$ ]]; then
    "$TARGET_SCRIPT" &
    echo "✅ 已啟動 mpvwidget"
else
    echo "📌 你可以稍後使用指令手動執行：$TARGET_SCRIPT"
fi

echo "🎉 安裝完成！"

