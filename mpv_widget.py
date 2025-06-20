#!/usr/bin/env python3
import os
import subprocess
import signal
import gi
import json
import socket
import threading
import time

gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, Notify, GLib, AyatanaAppIndicator3 as AppIndicator

CONFIG_PATH = os.path.expanduser("~/.config/mpvwidget-site.conf")
ICON_NAME = "media-playback-start"
SOCKET_PATH = "/tmp/mpvsocket"

class MPVWidget:
    def __init__(self):
        self.streams = self.load_streams()
        self.current_proc = None
        self.current_label = None
        self.current_title = None
        self.ipc_thread = None
        self.ipc_stop_flag = threading.Event()

        Notify.init("MPV 控制器")

        self.indicator = AppIndicator.Indicator.new(
            "mpvwidget", ICON_NAME,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.build_menu()

    def load_streams(self):
        streams = []
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                for line in f:
                    if '|' in line:
                        label, url = line.strip().split('|', 1)
                        streams.append((label.strip(), url.strip()))
        return streams

    def build_menu(self):
        menu = Gtk.Menu()

        # 狀態顯示的 MenuItem，預設為「未播放」
        self.status_item = Gtk.MenuItem(label="未播放")
        self.status_item.set_sensitive(True)  # 灰掉無法點擊
        self.status_item.connect("activate",self.dummy)
        menu.append(self.status_item)

        for label, url in self.streams:
            item = Gtk.MenuItem(label="▶️ "+label)
            item.connect("activate", self.on_stream_selected, label, url)
            menu.append(item)
        
        reload_item = Gtk.MenuItem(label="🔁 重新載入串流清單")
        reload_item.connect("activate", self.reload_streams)
        menu.append(reload_item)

        stop_item = Gtk.MenuItem(label="⏹️ 停止播放")
        stop_item.connect("activate", self.stop_playback)
        menu.append(stop_item)

        quit_item = Gtk.MenuItem(label="⏏️ 退出")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)
    
    def reload_streams(self, *args):
        self.streams = self.load_streams()
        self.build_menu()
        self.notify("✅ 串流清單已重新載入")

    def on_stream_selected(self, widget, label, url):
        self.stop_playback()
        self.current_label = label
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.current_proc = subprocess.Popen([
            "mpv", "--no-video",
            "--input-ipc-server=" + SOCKET_PATH,
            "--cache=yes", "--cache-secs=20",
            url
        ])
        ## 稍後再取得 metadata (這裡是初版本利用的架構, 在引入 thread自己控制就捨棄了, 但坑可能就在這！)
        # GLib.timeout_add_seconds(2, self.try_show_metadata)
        
        ## debug發現上面開的 mpv socket可能與接下來的 thread有關,
        ##所以暫停 2秒讓 mpv建好mpvsocket取好資料在開始執行緒監聽
        # time.sleep(2)

        for _ in range(60):
            if os.path.exists(SOCKET_PATH):
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.connect(SOCKET_PATH)
                    break
                except socket.error:
                    pass
            time.sleep(0.1)  
        
        # 啟動監聽執行緒
        self.ipc_stop_flag.clear()
        self.ipc_thread = threading.Thread(target=self.ipc_listen_loop, daemon=True)
        self.ipc_thread.start()
    
    def salt_title(self, title):
        i=0
        buf=""
        if len(title)>24:
            for c in title:
               i=i+1
               buf=buf+c
               if(i%24==0):
                   buf+="\n"
                   i=0
            title=buf
        return title
 
    def update_status_title(self, title):
        if hasattr(self, "status_item"):
            GLib.idle_add(self.status_item.set_label, f"▷ {self.salt_title(title)}")
            GLib.idle_add(self.status_item.show)
            # 雖然 GNOME 可能不顯示
        GLib.idle_add(self.indicator.set_title, f"正在播放：{self.salt_title(title)}")

    def ipc_listen_loop(self):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(SOCKET_PATH)
                # 訂閱 metadata 屬性
                subscribe_cmd = {"command": ["observe_property", 1, "metadata"]}
                s.sendall(json.dumps(subscribe_cmd).encode() + b"\n")
                get_cmd = {"command": ["get_property", "metadata"]}
                s.sendall(json.dumps(get_cmd).encode() + b"\n")
                buffer = b""
                while not self.ipc_stop_flag.is_set():
                    data = s.recv(4096)
                    # print(data) ## socket debug
                    if not data:
                        break
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if line:
                            self.handle_ipc_message(line)
                            # print(line,buffer,end='\r',flush=False)
        except Exception as e:
            # 連線失敗或結束時不必強制處理
            pass

    def handle_ipc_message(self, raw_json_bytes):
        try:
            msg = json.loads(raw_json_bytes.decode())
            if msg.get("event") == "property-change" or msg.get("error")=="success":
                metadata = msg.get("data", {})
                title = metadata.get("icy-title") or metadata.get("title") or None
                if title and title != self.current_title:
                    self.current_title = title
                    self.update_status_title(title)
                    GLib.idle_add(self.notify, f"🎵 正在播放：\n{title}")
        except Exception:
            pass

    
    def stop_playback(self, *args):
        if self.current_proc and self.current_proc.poll() is None:
            self.current_proc.terminate()
        self.current_proc = None

        # 停止 IPC 監聽執行緒
        self.ipc_stop_flag.set()
        if self.ipc_thread:
            self.ipc_thread.join()
            self.ipc_thread = None

        self.notify(f"已停止：{self.current_label}")

    def notify(self, message):
        n = Notify.Notification.new("MPV 控制器", message, ICON_NAME)
        n.show()

    def quit(self, widget):
        self.stop_playback()
        Gtk.main_quit()
    
    def dummy(self,widget):
        pass


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = MPVWidget()
    Gtk.main()
