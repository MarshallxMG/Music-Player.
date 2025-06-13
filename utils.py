from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

def ms_to_str(ms):
    s = ms // 1000
    return f"{s // 60:02}:{s % 60:02}"

def read_metadata(path):
    try:
        audio = EasyID3(path)
        artist = audio.get("artist", ["Unknown"])[0]
        title = audio.get("title", ["Unknown"])[0]
        return f"{artist} – {title}"
    except:
        return ""

def extract_album_art(path):
    try:
        tags = ID3(path)
        ap = tags.getall("APIC")
        if ap:
            img_data = ap[0].data
            pix = QPixmap()
            pix.loadFromData(img_data)
            return pix.scaled(200, 200, Qt.KeepAspectRatio)
    except:
        pass
    return None
