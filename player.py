import sys, os, random
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QSlider, QHBoxLayout, QListWidget, QMessageBox,
    QLineEdit
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3

class MusicPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Smart Music Player")
        self.setGeometry(200, 200, 600, 800)
        self.setAcceptDrops(True)

        self.player = QMediaPlayer()
        self.playlist = []
        self.current_index = -1
        self.repeat = False
        self.shuffle = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

        self.init_ui()

    def init_ui(self):
        # Load external QSS
        qss_path = "E:/Python Projects/Music Player/Combinear.qss"
        if os.path.exists(qss_path):
            with open(qss_path, "r") as f:
                self.setStyleSheet(f.read())
        else:
            print("❌ Combinear.qss not found. Default style will be used.")

        layout = QVBoxLayout()

        layout.addWidget(QLabel("🎵 Smart Music Player", alignment=Qt.AlignCenter))
        self.label = QLabel("No song loaded", alignment=Qt.AlignCenter)
        layout.addWidget(self.label)

        self.album_art = QLabel(alignment=Qt.AlignCenter)
        self.album_art.setFixedSize(200, 200)
        self.album_art.setStyleSheet("border: 2px solid #ccc; border-radius: 8px;")
        layout.addWidget(self.album_art)

        self.meta_label = QLabel("", alignment=Qt.AlignCenter)
        layout.addWidget(self.meta_label)

        # (REMOVED) Graph/Visualizer section

        self.progress = QSlider(Qt.Horizontal)
        self.progress.sliderMoved.connect(self.set_position)
        layout.addWidget(self.progress)

        tlay = QHBoxLayout()
        self.current_time = QLabel("00:00")
        self.total_time = QLabel("00:00")
        tlay.addWidget(self.current_time)
        tlay.addWidget(self.total_time)
        layout.addLayout(tlay)

        ctl = QHBoxLayout()
        buttons = [
            ("⏮ Prev", self.play_previous),
            ("▶ Play", self.toggle_play),
            ("⏭ Next", self.play_next),
            ("🔀 Shuffle", self.toggle_shuffle),
            ("🔁 Repeat", self.toggle_repeat),
        ]
        for text, cb in buttons:
            b = QPushButton(text)
            if 'Shuffle' in text or 'Repeat' in text:
                b.setCheckable(True)
            b.clicked.connect(cb)
            if 'Play' in text:
                self.play_btn = b
            ctl.addWidget(b)
        layout.addLayout(ctl)

        vlay = QHBoxLayout()
        vlay.addWidget(QLabel("🔊 Volume"))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(50)
        self.volume.valueChanged.connect(self.player.setVolume)
        vlay.addWidget(self.volume)
        self.vpct = QLabel("50%")
        self.volume.valueChanged.connect(lambda v: self.vpct.setText(f"{v}%"))
        vlay.addWidget(self.vpct)
        layout.addLayout(vlay)

        for txt, cb in [
            ("📁 Browse MP3", self.browse_file),
            ("💾 Save Playlist", self.save_playlist),
            ("📂 Load Playlist", self.load_playlist),
        ]:
            b = QPushButton(txt)
            b.clicked.connect(cb)
            layout.addWidget(b)

        self.filter = QLineEdit()
        self.filter.setPlaceholderText("🔍 Filter playlist")
        self.filter.textChanged.connect(self.apply_filter)
        layout.addWidget(self.filter)

        layout.addWidget(QLabel("📃 Playlist:"))
        self.list_widget = QListWidget()
        self.list_widget.doubleClicked.connect(lambda _: self.play_song(self.list_widget.currentRow()))
        layout.addWidget(self.list_widget)

        self.setLayout(layout)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.accept()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.mp3'):
                self.playlist.append(path)
                self.list_widget.addItem(os.path.basename(path))

    def toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶ Play")
            self.timer.stop()
        else:
            if self.current_index == -1 and self.playlist:
                self.play_song(0)
            else:
                self.player.play()
                self.play_btn.setText("⏸ Pause")
                self.timer.start(1000)

    def browse_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open MP3", filter="MP3 Files (*.mp3)")
        if f:
            self.playlist.append(f)
            self.list_widget.addItem(os.path.basename(f))
            self.play_song(len(self.playlist) - 1)

    def play_song(self, idx):
        if 0 <= idx < len(self.playlist):
            self.current_index = idx
            path = self.playlist[idx]
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
            self.player.play()
            self.play_btn.setText("⏸ Pause")
            self.timer.start(1000)
            self.label.setText(os.path.basename(path))
            self.show_metadata(path)

    def play_next(self):
        if self.shuffle:
            i = random.randrange(len(self.playlist))
        elif self.current_index + 1 < len(self.playlist):
            i = self.current_index + 1
        elif self.repeat:
            i = 0
        else:
            return
        self.play_song(i)

    def play_previous(self):
        if self.current_index > 0:
            self.play_song(self.current_index - 1)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle

    def toggle_repeat(self):
        self.repeat = not self.repeat

    def update_progress(self):
        d = self.player.duration()
        p = self.player.position()
        if d > 0:
            pct = int(p / d * 100)
            self.progress.setValue(pct)
            self.current_time.setText(self.ms_to_str(p))
            self.total_time.setText(self.ms_to_str(d))
        if self.player.state() == QMediaPlayer.StoppedState:
            self.play_next()

    def ms_to_str(self, ms):
        s = ms // 1000
        return f"{s // 60:02}:{s % 60:02}"

    def set_position(self, pos):
        d = self.player.duration()
        if d > 0:
            self.player.setPosition(int(d * (pos / 100)))

    def show_metadata(self, path):
        try:
            a = EasyID3(path)
            art = a.get("artist", ["Unknown"])[0]
            t = a.get("title", ["Unknown"])[0]
            self.meta_label.setText(f"{art} – {t}")
        except:
            self.meta_label.setText("")
        try:
            tags = ID3(path)
            ap = tags.getall("APIC")
            if ap:
                img = ap[0].data
                pix = QPixmap()
                pix.loadFromData(img)
                self.album_art.setPixmap(pix.scaled(200, 200, Qt.KeepAspectRatio))
            else:
                self.album_art.clear()
        except:
            self.album_art.clear()

    def save_playlist(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Playlist", filter="Playlist (*.m3u)")
        if path:
            with open(path, 'w') as f:
                f.write("\n".join(self.playlist))
            QMessageBox.information(self, "Saved", "Playlist saved successfully")

    def load_playlist(self):
        p = QFileDialog.getOpenFileName(self, "Load Playlist", filter="Playlist (*.m3u)")[0]
        if p and os.path.exists(p):
            with open(p) as f:
                lst = [l.strip() for l in f if l.strip()]
            self.playlist = lst
            self.refresh_playlist()
            if lst:
                self.play_song(0)

    def refresh_playlist(self):
        self.list_widget.clear()
        self.list_widget.addItems([os.path.basename(f) for f in self.playlist])
        self.apply_filter()

    def apply_filter(self):
        term = self.filter.text().lower()
        self.list_widget.clear()
        for f in self.playlist:
            if term in os.path.basename(f).lower():
                self.list_widget.addItem(os.path.basename(f))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Use absolute path to Combinear.qss
    qss_path = r"E:\Python Projects\Music Player\Combinear.qss"
    try:
        with open(qss_path, "r") as file:
            style = file.read()
            app.setStyleSheet(style)
    except FileNotFoundError:
        print("❌ Combinear.qss not found. Default style will be used.")

    w = MusicPlayer()
    w.show()
    sys.exit(app.exec_())

