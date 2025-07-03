#!/usr/bin/env python3
import os
import subprocess
import signal
import gi
import json
import socket
import threading
import time

# GTK 與 AppIndicator 初始化
gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, Notify, GLib, AyatanaAppIndicator3 as AppIndicator

CONFIG_PATH = os.path.expanduser("~/.config/mpvwidget-site.conf")
ICON_NAME = "media-playback-start"
SOCKET_PATH = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "mpvsocket")

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

        self.try_attach_to_existing_mpv()
        
        self.poll_thread = None
        self.poll_stop_flag = threading.Event()


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

        self.status_item = Gtk.MenuItem(label="未播放")
        self.status_item.set_sensitive(True)
        self.status_item.connect("activate", self.dummy)
        menu.append(self.status_item)

        for label, url in self.streams:
            item = Gtk.MenuItem(label="▶️ " + label)
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

    def start_marquee(self):
        self.marquee_pos = 0
        GLib.timeout_add(500, self.scroll_title)

    def scroll_title(self):
        if not self.current_title:
            return False
        title = self.current_title
        if len(title) <= 24:
            display = title
        else:
            pos = self.marquee_pos % (len(title) + 4)
            padded = title + "     "
            display = padded[pos:pos + 24]
            self.marquee_pos += 1

        GLib.idle_add(self.status_item.set_label, f"▷ {display}")
        return True

    def try_attach_to_existing_mpv(self):
        if os.path.exists(SOCKET_PATH):
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.connect(SOCKET_PATH)
                self.notify("🌀 已接管現有 mpv 播放")
                self.ipc_stop_flag.clear()
                self.ipc_thread = threading.Thread(target=self.ipc_listen_loop, daemon=True)
                self.ipc_thread.start()
                return True
            except socket.error:
                os.remove(SOCKET_PATH)
        return False

    def on_stream_selected(self, widget, label, url):
        self.stop_playback()
        self.kill_orphan_mpv()

        self.current_label = label
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

        self.current_proc = subprocess.Popen([
            "mpv", "--no-video",
            "--input-ipc-server=" + SOCKET_PATH,
            "--cache=yes", "--cache-secs=30",
            url
        ])

        for _ in range(60):
            if os.path.exists(SOCKET_PATH):
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.connect(SOCKET_PATH)
                    break
                except socket.error:
                    pass
            time.sleep(0.1)

        self.ipc_stop_flag.clear()
        self.ipc_thread = threading.Thread(target=self.ipc_listen_loop, daemon=True)
        self.ipc_thread.start()
        # 如果是本地 cvlc，啟動 status.xml polling
        if "localhost" in url or "127.0.0.1" in url:
            self.poll_stop_flag.clear()
            self.poll_thread = threading.Thread(target=self.poll_vlc_status, daemon=True)
            self.poll_thread.start()
        else:
            self.poll_stop_flag.set()
            self.poll_thread = None


    def kill_orphan_mpv(self):
        if os.path.exists(SOCKET_PATH):
            try:
                os.remove(SOCKET_PATH)
            except:
                pass
            subprocess.call(["pkill", "-f", "mpv.*--input-ipc-server=" + SOCKET_PATH])

    def update_status_title(self, title):
        GLib.idle_add(self.status_item.set_label, f"▷ {title}")
        GLib.idle_add(self.indicator.set_title, f"正在播放：{title}")
        self.start_marquee()

    def ipc_listen_loop(self):
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.connect(SOCKET_PATH)
                subscribe_cmd = {"command": ["observe_property", 1, "metadata"]}
                s.sendall(json.dumps(subscribe_cmd).encode() + b"\n")
                get_cmd = {"command": ["get_property", "metadata"]}
                s.sendall(json.dumps(get_cmd).encode() + b"\n")
                buffer = b""
                while not self.ipc_stop_flag.is_set():
                    data = s.recv(4096)
                    if not data:
                        break
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        if line:
                            self.handle_ipc_message(line)
        except Exception:
            pass

    def handle_ipc_message(self, raw_json_bytes):
        try:
            msg = json.loads(raw_json_bytes.decode())
            if msg.get("event") == "property-change" or msg.get("error") == "success":
                metadata = msg.get("data", {})
                title = metadata.get("icy-title") or metadata.get("title")
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
        self.ipc_stop_flag.set()
        if self.ipc_thread:
            self.ipc_thread.join()
            self.ipc_thread = None
        
        self.poll_stop_flag.set()
        if self.poll_thread:
            self.poll_thread.join()
            self.poll_thread = None

        self.notify(f"已停止：{self.current_label}")

    def notify(self, message):
        n = Notify.Notification.new("MPV 控制器", message, ICON_NAME)
        n.show()

    def quit(self, widget):
        self.stop_playback()
        Gtk.main_quit()

    def dummy(self, widget):
        pass
    def poll_vlc_status(self):
        while not self.poll_stop_flag.is_set():
            try:
                out = subprocess.check_output(["curl", "-u", ":vlcpass", "-s", "http://localhost:8081/requests/status.xml"], timeout=2)
                import xml.etree.ElementTree as ET
                tree = ET.fromstring(out)
                title = None
                for info in tree.findall(".//info"):
                    if info.attrib.get("name") == "title":
                        title = info.text
                        break
                if title and title != self.current_title:
                    self.current_title = title
                    self.update_status_title(title)
                    GLib.idle_add(self.notify, f"🎵 本地播放：\n{title}")
            except Exception:
                pass
            time.sleep(5)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = MPVWidget()
    Gtk.main()

