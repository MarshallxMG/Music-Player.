import sys
from PyQt5.QtWidgets import QApplication
from player import MusicPlayer
from styles.apply_stylesheet import apply_stylesheet

if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app, "styles/Combinear.qss")
    w = MusicPlayer()
    w.show()
    sys.exit(app.exec_())
