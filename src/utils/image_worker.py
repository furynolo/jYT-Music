import urllib.request
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap

class ImageWorker(QThread):
    image_ready = Signal(QPixmap, str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            if not self.url:
                return
            data = urllib.request.urlopen(self.url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.image_ready.emit(pixmap, self.url)
        except Exception as e:
            print(f"Failed to load image {self.url}: {e}")
