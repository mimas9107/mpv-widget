#!/usr/bin/env python3
import os
import subprocess
import signal
import gi
gi.require_version("Gtk","3.0")
gi.require_version("AyatanaAppIndicator3","0.1")
from gi.repository import Gtk, GLib, AyatanaAppIndicator3 as AppIndicator

CONFIG_PATH = os.path.expanduser("~/.config/mpvwidget-site.conf")
ICON_PATH = "media-playback-start"  # 可換成其他圖示名或完整路徑

class MPVWidget:
    def __init__(self):
        self.streams = self.load_streams()
        self.current_proc = None
        self.current_label = None

        self.indicator = AppIndicator.Indicator.new(
            "mpvwidget", ICON_PATH,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.build_menu()

    def load_streams(self):
        streams = []
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                for line in f:
                    line = line.strip()
                    if line and '|' in line:
                        label, url = line.split('|', 1)
                        streams.append((label.strip(), url.strip()))
        return streams

    def build_menu(self):
        menu = Gtk.Menu()

        for label, url in self.streams:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", self.on_stream_selected, label, url)
            menu.append(item)

        stop_item = Gtk.MenuItem(label="停止播放")
        stop_item.connect("activate", self.stop_playback)
        menu.append(stop_item)

        quit_item = Gtk.MenuItem(label="退出")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        self.indicator.set_menu(menu)

    def on_stream_selected(self, widget, label, url):
        self.stop_playback()
        self.current_label = label
        self.notify(f"開始播放：{label}")
        self.current_proc = subprocess.Popen(["mpv", "--no-video", url])

    def stop_playback(self, *args):
        if self.current_proc and self.current_proc.poll() is None:
            self.current_proc.terminate()
            self.notify(f"已停止：{self.current_label}")
            self.current_proc = None

    def notify(self, message):
        subprocess.Popen(["notify-send", "MPV 控制器", message])

    def quit(self, widget):
        self.stop_playback()
        Gtk.main_quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = MPVWidget()
    Gtk.main()

