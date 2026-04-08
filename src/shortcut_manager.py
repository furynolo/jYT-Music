from PySide6.QtCore import QObject, Signal
from pynput import keyboard

class ShortcutManager(QObject):
    # This signal safely transmits background hotkey events to the Main GUI thread
    hotkey_triggered = Signal(str)

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.listener = None
        self.is_listening = False

    def start(self):
        if self.is_listening:
            self.stop()
        
        # Load shortcuts from settings
        hotkeys = {
            self.settings_manager.get_shortcut("play_pause"): self._on_play_pause,
            self.settings_manager.get_shortcut("next_track"): self._on_next_track,
            self.settings_manager.get_shortcut("prev_track"): self._on_prev_track
        }

        # Filter out empty bindings if any
        hotkeys = {k: v for k, v in hotkeys.items() if k}

        if hotkeys:
            self.listener = keyboard.GlobalHotKeys(hotkeys)
            self.listener.start()
            self.is_listening = True
            print("Global shortcuts listening started")
        else:
            print("No valid hotkeys configured.")

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.is_listening = False
        print("Global shortcuts listening stopped")

    def _on_play_pause(self):
        self.hotkey_triggered.emit("play_pause")

    def _on_next_track(self):
        self.hotkey_triggered.emit("next_track")

    def _on_prev_track(self):
        self.hotkey_triggered.emit("prev_track")
