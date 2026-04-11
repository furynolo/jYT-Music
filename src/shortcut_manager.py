from PySide6.QtCore import QObject, Signal
from pynput import keyboard
import time

class ShortcutManager(QObject):
    # This signal safely transmits background hotkey events to the Main GUI thread
    hotkey_triggered = Signal(str)

    def __init__(self, settings_manager, debug_mode=False):
        super().__init__()
        self.settings_manager = settings_manager
        self.debug_mode = debug_mode
        self.listener = None
        self.is_listening = False
        self._last_trigger_times = {} # Track cooldowns for performance
        self._COOLDOWN_MS = 300

    def _can_trigger(self, action):
        now = time.time() * 1000
        last_time = self._last_trigger_times.get(action, 0)
        if (now - last_time) < self._COOLDOWN_MS:
            if self.debug_mode: print(f"[DEBUG] ShortcutManager: Throttled '{action}' (within {self._COOLDOWN_MS}ms)")
            return False
        self._last_trigger_times[action] = now
        return True

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
        if self._can_trigger("play_pause"):
            if self.debug_mode: print("[DEBUG] Global Hotkey Caught: PLAY_PAUSE")
            self.hotkey_triggered.emit("play_pause")

    def _on_next_track(self):
        if self._can_trigger("next_track"):
            if self.debug_mode: print("[DEBUG] Global Hotkey Caught: NEXT_TRACK")
            self.hotkey_triggered.emit("next_track")

    def _on_prev_track(self):
        if self._can_trigger("prev_track"):
            if self.debug_mode: print("[DEBUG] Global Hotkey Caught: PREV_TRACK")
            self.hotkey_triggered.emit("prev_track")
