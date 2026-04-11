import sys
import os

# Suppress annoying FFmpeg skipped sample stdout warnings
os.environ["QT_LOGGING_RULES"] = "qt.multimedia.ffmpeg.debug=false;qt.multimedia.ffmpeg.warning=false"

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.config import settings_manager, get_resource_path
from shortcut_manager import ShortcutManager
from audio_engine import AudioEngine
from utils.auth import AuthManager
from youtube_api import YouTubeAPI

def load_stylesheet(app):
    try:
        qss_path = get_resource_path("ui/style.qss")
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Stylesheet not found. Using default styles.")

def main():
    app = QApplication(sys.argv)
    
    # Check for diagnostic mode
    debug_mode = "-D" in sys.argv
    if debug_mode:
        print("\n" + "="*40)
        print(" DIAGNOSTIC MODE ACTIVE ")
        print("="*40 + "\n")

    # Load custom QSS
    load_stylesheet(app)
    
    # Initialize Core Managers
    audio_engine = AudioEngine(debug_mode=debug_mode)
    shortcut_manager = ShortcutManager(settings_manager, debug_mode=debug_mode)
    auth_manager = AuthManager()
    youtube_api = YouTubeAPI(auth_manager)

    # Initialize Main Window
    window = MainWindow(settings_manager, shortcut_manager, audio_engine, auth_manager, youtube_api, debug_mode=debug_mode)
    window.show()
    
    # App Loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
