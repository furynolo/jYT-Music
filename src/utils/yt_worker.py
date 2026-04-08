from PySide6.QtCore import QThread, Signal
from yt_handler import YTHandler

class YTWorker(QThread):
    # Signals to communicate back to the main thread securely
    result_ready = Signal(dict) # track_info payload
    error_occurred = Signal(str)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query
        self.yt_handler = YTHandler()

    def run(self):
        try:
            track_info = self.yt_handler.extract_info(self.query)
            if track_info and track_info.get("url"):
                self.result_ready.emit(track_info)
            else:
                self.error_occurred.emit("Could not extract audio stream.")
        except Exception as e:
            self.error_occurred.emit(str(e))
        except BaseException as e:
            self.error_occurred.emit(f"Fatal background error: {str(e)}")
