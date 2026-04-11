from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioEngine(QObject):
    # Signals for UI updates
    playback_state_changed = Signal(bool)
    track_changed = Signal(str)
    position_updated = Signal(int)
    duration_updated = Signal(int)
    track_finished = Signal()
    error_occurred = Signal(int, str) # error_code, error_message

    def __init__(self, debug_mode=False):
        super().__init__()
        self.debug_mode = debug_mode
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        # Connect the audio output to the player
        self.player.setAudioOutput(self.audio_output)
        
        # Defaults
        self.audio_output.setVolume(0.8)
        self.current_track_path = None
        self._ignore_finish_signal = False # Sticky flag to prevent phantom skips

        # Ticking timer for progress
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._on_timer_tick)

        # Listen to state changes
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.durationChanged.connect(self.duration_updated.emit)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_error_occurred)

    def play_file(self, source_path):
        """Play an arbitrary local file or URL."""
        if self.debug_mode: print(f"[DEBUG] AudioEngine: play_file('{source_path}')")
        # --- HARD RESET PROTOCOL ---
        # 1. Set sticky flag to ignore any phantom finish signals during reset
        self._ignore_finish_signal = True
        
        # 2. Stop playback
        self.player.stop()
        # 3. CLEAR the source to flush FFmpeg network buffers instantly
        self.player.setSource(QUrl())
        
        self.current_track_path = source_path
        
        # Determine if it's a URL or a file
        if source_path.startswith("http"):
            self.player.setSource(QUrl(source_path))
        else:
            self.player.setSource(QUrl.fromLocalFile(source_path))
            
        self.player.play()
        self.track_changed.emit(source_path)

    def play(self):
        """Resume playback."""
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self.player.play()

    def pause(self):
        """Pause playback."""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()

    def stop(self):
        self._ignore_finish_signal = True
        self.player.stop()
        self.player.setSource(QUrl())

    def toggle_play_pause(self):
        """Toggle state. Used primarily by hotkeys."""
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play()
        elif state == QMediaPlayer.PlaybackState.StoppedState and self.current_track_path:
            # Replay if stopped but track is loaded
            self.play()

    def set_volume(self, value: float):
        """Set volume from 0.0 to 1.0."""
        self.audio_output.setVolume(value)

    def seek(self, position_ms):
        self.player.setPosition(position_ms)

    def _on_state_changed(self, state):
        is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        if is_playing:
            self.timer.start()
        else:
            self.timer.stop()
        self.playback_state_changed.emit(is_playing)

    def _on_media_status_changed(self, status):
        if self.debug_mode: print(f"[DEBUG] AudioEngine: MediaStatus -> {status}")
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.debug_mode: print(f"[DEBUG] AudioEngine: EndOfMedia reached. Signal Silenced? {self._ignore_finish_signal}")
            if not self._ignore_finish_signal:
                # Double Guard: Only emit if position is actually at the end
                if self.player.duration() > 0 and abs(self.player.position() - self.player.duration()) < 2000:
                    self.track_finished.emit()
            
            # Auto-reset flag once we've handled the signal
            self._ignore_finish_signal = False
            
        elif status == QMediaPlayer.MediaStatus.NoMedia:
            # We explicitly clear the flag when media is removed
            self._ignore_finish_signal = False

    def _on_timer_tick(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.position_updated.emit(self.player.position())

    def _on_error_occurred(self, error, error_str):
        print(f"AudioEngine Error ({error}): {error_str}")
        self.error_occurred.emit(error.value, error_str)
