from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioEngine(QObject):
    # Signals for UI updates
    playback_state_changed = Signal(bool)
    track_changed = Signal(str)
    position_updated = Signal(int)
    duration_updated = Signal(int)
    track_finished = Signal()

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        
        # Connect the audio output to the player
        self.player.setAudioOutput(self.audio_output)
        
        # Defaults
        self.audio_output.setVolume(0.8)
        self.current_track_path = None

        # Ticking timer for progress
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._on_timer_tick)

        # Listen to state changes
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.durationChanged.connect(self.duration_updated.emit)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def play_file(self, source_path):
        """Play an arbitrary local file."""
        self.current_track_path = source_path
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
        self.player.stop()

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
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.track_finished.emit()

    def _on_timer_tick(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.position_updated.emit(self.player.position())
