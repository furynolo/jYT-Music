import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QSpacerItem, QSizePolicy,
    QStackedWidget, QListWidget, QFileDialog, QSplitter, QSlider,
    QListWidgetItem, QStyle, QMenu, QApplication
)
from PySide6.QtGui import QIcon, QAction, QDesktopServices, QPixmap
from PySide6.QtCore import Qt, QTimer, QSize, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from ui.settings_dialog import SettingsDialog
from utils.scanner import LocalScanner
from audio_engine import AudioEngine
from utils.yt_worker import YTWorker
from utils.download_worker import DownloadWorker
from youtube_api import PlaylistLoaderWorker, PlaylistItemsWorker, RatingFetchWorker, SearchWorker
from ui.search_results_widget import SearchResultsWidget
from utils.duration_utils import parse_duration_to_seconds, format_seconds_to_human

from utils.queue_manager import QueueManager
from utils.image_worker import ImageWorker
from ui.track_widget import TrackItemWidget
from ui.volume_popup import VolumePopup
from ui.now_playing_widget import NowPlayingWidget
from ui.playlist_header_widget import PlaylistHeaderWidget

class MainWindow(QMainWindow):
    def __init__(self, settings_manager, shortcut_manager, audio_engine, auth_manager, youtube_api):
        super().__init__()
        self.settings_manager = settings_manager
        self.shortcut_manager = shortcut_manager
        self.audio_engine = audio_engine
        self.auth_manager = auth_manager
        self.youtube_api = youtube_api
        
        self.setWindowTitle("jYT Music Desktop App")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.resize(1100, 750)
        
        # Set Window Icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        self.setWindowIcon(QIcon(os.path.join(assets_dir, "logo.ico")))
        
        self.is_cloud_mode = True
        self.local_files = []
        self.yt_worker = None
        self.download_worker = None
        self.playlist_worker = None
        self.items_worker = None
        self.search_worker = None
        
        self.queue_manager = QueueManager()
        self.is_slider_being_dragged = False
        
        # Keep track of active image workers to prevent garbage collection
        self.image_workers = []
        
        # Currently selected cloud track
        self.current_cloud_url = None
        self.current_cloud_video_id = None
        
        # Recovery Logic
        self.recovery_mode = False
        self.recovery_retry_count = 0
        self.recovery_timer = QTimer(self)
        self.recovery_timer.setSingleShot(True)
        self.recovery_timer.timeout.connect(self.attempt_recovery)
        self.last_failure_pos = 0
        
        self._cached_playlists = []

        self.init_ui()
        self.init_bindings()
        
        # Auto-fetch if token exists
        self.update_auth_ui()
        
    def init_ui(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # --- Top Bar ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setSpacing(10)
        
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(32, 32)
        self.logo_label.setScaledContents(True)
        self.logo_label.setPixmap(QPixmap(os.path.join(assets_dir, "logo.svg")))
        top_bar_layout.addWidget(self.logo_label)
        
        title_label = QLabel("jYT Music Player")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        top_bar_layout.addWidget(title_label)

        # Added Search Controls to Top Bar
        top_bar_layout.addSpacing(15)
        
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border-radius: 4px; padding: 5px 10px; font-weight: bold; }
            QPushButton:hover { background-color: #555; }
        """)
        self.browse_btn.clicked.connect(self.browse_local_folder)
        self.browse_btn.hide()
        top_bar_layout.addWidget(self.browse_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search YouTube or Paste URL...")
        self.search_input.setMinimumWidth(350)
        self.search_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.search_input.returnPressed.connect(self.on_search_triggered)
        top_bar_layout.addWidget(self.search_input)
        
        self.action_btn = QPushButton("Play")
        self.action_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #555; }
        """)
        self.action_btn.clicked.connect(self.on_search_triggered)
        top_bar_layout.addWidget(self.action_btn)
        
        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border-radius: 4px; padding: 5px 10px; font-weight: bold; }
            QPushButton:hover { background-color: #555; }
        """)
        self.download_btn.clicked.connect(self.on_download_clicked)
        top_bar_layout.addWidget(self.download_btn)
        
        top_bar_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        self.login_btn = QPushButton("Log in to Google")
        self.login_btn.setStyleSheet("background-color: #4285F4; color: white; font-weight: bold;")
        self.login_btn.setFocusPolicy(Qt.NoFocus)
        self.login_btn.clicked.connect(self.on_login_clicked)
        top_bar_layout.addWidget(self.login_btn)

        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(QIcon(os.path.join(assets_dir, "settings.svg")))
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.setFixedSize(35, 35)
        self.settings_btn.setStyleSheet("QPushButton { background-color: #333; border-radius: 17px; border: none; } QPushButton:hover { background-color: #444; }")
        self.settings_btn.setFocusPolicy(Qt.NoFocus)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(top_bar_layout)
        
        # --- Splitter (Sidebar + Main Content) ---
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.sidebar_widget = QListWidget()
        self.sidebar_widget.setStyleSheet("background-color: #181818; font-size: 14px;")
        self.sidebar_widget.setCursor(Qt.PointingHandCursor)
        self.sidebar_widget.itemClicked.connect(self.on_playlist_selected)
        
        self.stacked_widget = QStackedWidget()
        
        self.cloud_view_widget = QWidget()
        cloud_layout = QHBoxLayout(self.cloud_view_widget)
        cloud_layout.setContentsMargins(10, 10, 0, 10)
        cloud_layout.setSpacing(0)
        
        self.playlist_header = PlaylistHeaderWidget()
        self.playlist_header.hide()
        self.playlist_header.play_all_clicked.connect(self.on_play_all_clicked)
        cloud_layout.addWidget(self.playlist_header)
        
        # Right Side Content (Status + List)
        self.cloud_content_layout = QVBoxLayout()
        self.cloud_content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cloud_status = QLabel("Ready for YouTube Search or Playlist Selection.")
        self.cloud_status.setAlignment(Qt.AlignCenter)
        self.cloud_status.setStyleSheet("font-size: 16px; color: #aaa;")
        self.cloud_status.setWordWrap(True)
        self.cloud_content_layout.addWidget(self.cloud_status)
        
        self.cloud_list_widget = QListWidget()
        self.cloud_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cloud_list_widget.setStyleSheet("background-color: #121212; font-size: 14px; border: none;")
        self.cloud_list_widget.setCursor(Qt.PointingHandCursor)
        self.cloud_list_widget.itemClicked.connect(self.on_cloud_track_selected)
        self.cloud_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cloud_content_layout.addWidget(self.cloud_list_widget)
        
        cloud_layout.addLayout(self.cloud_content_layout, 1)

        self.stacked_widget.addWidget(self.cloud_view_widget)
        
        self.local_view_widget = QWidget()
        local_layout = QVBoxLayout(self.local_view_widget)
        self.local_list_widget = QListWidget()
        self.local_list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.local_list_widget.setStyleSheet("background-color: #121212; font-size: 14px; border: none;")
        self.local_list_widget.setCursor(Qt.PointingHandCursor)
        self.local_list_widget.itemClicked.connect(self.on_local_track_selected)
        self.local_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        local_layout.addWidget(self.local_list_widget)
        self.stacked_widget.addWidget(self.local_view_widget)

        # Search Results View
        self.search_results_view = SearchResultsWidget()
        self.search_results_view.result_clicked.connect(self.on_search_result_clicked)
        self.search_results_view.filter_changed.connect(self.on_search_filter_changed)
        self.stacked_widget.addWidget(self.search_results_view)

        self.splitter.addWidget(self.sidebar_widget)
        self.splitter.addWidget(self.stacked_widget)
        # 1:3 ratio, allow sidebar to shrink to its minimum (handled by stylesheet or setMinimumWidth)
        self.sidebar_widget.setMinimumWidth(150)
        self.splitter.setSizes([200, 800])
        
        main_layout.addWidget(self.splitter, 1)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)
        
        # --- Slider Area ---
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal { border-radius: 2px; height: 4px; background: #333; }
            QSlider::handle:horizontal { background: #e0a96d; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
            QSlider::sub-page:horizontal { background: #e0a96d; border-radius: 2px; }
        """)
        main_layout.addWidget(self.progress_slider)
        
        # --- Bottom Control Bar ---
        bottom_bar_layout = QHBoxLayout()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        # LEFT FLANK
        self.bottom_left_layout = QHBoxLayout()
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon(os.path.join(assets_dir, "skip_previous.svg")))
        self.prev_btn.setFocusPolicy(Qt.NoFocus)
        self.prev_btn.setToolTip("Back")
        self.prev_btn.setFixedSize(35, 35)
        self.prev_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; font-size: 16px; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
        self.prev_btn.clicked.connect(self.on_prev_clicked)
        
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIcon(QIcon(os.path.join(assets_dir, "play.svg")))
        self.play_pause_btn.setFocusPolicy(Qt.NoFocus)
        self.play_pause_btn.setToolTip("Play/Pause")
        self.play_pause_btn.setFixedSize(45, 45)
        self.play_pause_btn.setStyleSheet("QPushButton { background-color: #FF0000; border-radius: 22px; outline: none; border: none; } QPushButton:hover { background-color: #CC0000; } QPushButton:pressed { background-color: #990000; border: none; }")
        self.play_pause_btn.clicked.connect(self.audio_engine.toggle_play_pause)
        
        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon(os.path.join(assets_dir, "skip_next.svg")))
        self.next_btn.setFocusPolicy(Qt.NoFocus)
        self.next_btn.setToolTip("Forward")
        self.next_btn.setFixedSize(35, 35)
        self.next_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; font-size: 16px; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
        self.next_btn.clicked.connect(self.on_next_clicked)
        
        self.time_label_combo = QLabel("0:00 / 0:00")
        self.time_label_combo.setStyleSheet("color: #aaa; font-size: 13px; margin-left: 10px;")
        
        self.bottom_left_layout.addWidget(self.prev_btn)
        self.bottom_left_layout.addWidget(self.play_pause_btn)
        self.bottom_left_layout.addWidget(self.next_btn)
        self.bottom_left_layout.addWidget(self.time_label_combo)
        self.bottom_left_layout.addStretch()
        
        # CENTER FLANK
        self.bottom_center_layout = QHBoxLayout()
        self.now_playing_widget = NowPlayingWidget(self)
        self.now_playing_widget.rating_clicked.connect(self.on_rate_clicked)
        self.now_playing_widget.menu_clicked.connect(self.show_now_playing_menu)
        self.cloud_list_widget.customContextMenuRequested.connect(self.show_cloud_context_menu)
        self.local_list_widget.customContextMenuRequested.connect(self.show_local_context_menu)
        self.playlist_header.play_all_clicked.connect(self.on_play_all_clicked)
        self.playlist_header.shuffle_play_clicked.connect(self.on_shuffle_play_clicked)
        # self.now_playing_widget.menu_clicked.connect(self.on_menu_clicked) # Placeholder Phase 4
        self.bottom_center_layout.addWidget(self.now_playing_widget)
        
        # RIGHT FLANK
        self.bottom_right_layout = QHBoxLayout()
        self.bottom_right_layout.addStretch()
        
        self.volume_btn = QPushButton()
        self.volume_btn.setIcon(QIcon(os.path.join(assets_dir, "volume_up.svg")))
        self.volume_btn.setFocusPolicy(Qt.NoFocus)
        self.volume_btn.setToolTip("Volume")
        self.volume_btn.setFixedSize(35, 35)
        self.volume_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; font-size: 16px; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
        
        saved_volume = self.settings_manager.settings.get("volume_level", 80)
        self.volume_popup = VolumePopup(self, initial_value=saved_volume)
        self.volume_popup.volume_changed.connect(self.on_volume_changed)
        self.audio_engine.set_volume(saved_volume / 100.0)
        
        self.volume_btn.clicked.connect(self.toggle_volume_popup)
        
        self.repeat_btn = QPushButton()
        self.repeat_btn.setIcon(QIcon(os.path.join(assets_dir, "repeat.svg")))
        self.repeat_btn.setFocusPolicy(Qt.NoFocus)
        self.repeat_btn.setToolTip("Loop")
        self.repeat_btn.setFixedSize(35, 35)
        self.repeat_btn.setStyleSheet("QPushButton { background-color: transparent; color: #888; font-size: 16px; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; color: white; }")
        self.repeat_btn.clicked.connect(self.on_repeat_toggled)
        
        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setIcon(QIcon(os.path.join(assets_dir, "shuffle.svg")))
        self.shuffle_btn.setFocusPolicy(Qt.NoFocus)
        self.shuffle_btn.setToolTip("Shuffle")
        self.shuffle_btn.setFixedSize(35, 35)
        self.shuffle_btn.setStyleSheet("QPushButton { background-color: transparent; color: #888; font-size: 16px; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; color: white; }")
        self.shuffle_btn.clicked.connect(self.on_shuffle_toggled)
        
        self.bottom_right_layout.addWidget(self.volume_btn)
        self.bottom_right_layout.addWidget(self.repeat_btn)
        self.bottom_right_layout.addWidget(self.shuffle_btn)
        
        # Combine flanks
        # Add stretches so center layout stays strictly in the middle
        bottom_bar_layout.addLayout(self.bottom_left_layout)
        bottom_bar_layout.addLayout(self.bottom_center_layout, 10) # Overwhelming stretch priority
        bottom_bar_layout.addLayout(self.bottom_right_layout)
        
        main_layout.addLayout(bottom_bar_layout)

    def init_bindings(self):
        self.shortcut_manager.hotkey_triggered.connect(self.on_hotkey_triggered)
        self.shortcut_manager.start()
        
        # Audio Engine signals
        self.audio_engine.playback_state_changed.connect(self.on_playback_state_changed)
        self.audio_engine.track_finished.connect(self.on_track_finished)
        self.audio_engine.position_updated.connect(self.on_position_updated)
        self.audio_engine.duration_updated.connect(self.on_duration_updated)
        self.audio_engine.error_occurred.connect(self.on_audio_error)
        
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.progress_slider.sliderMoved.connect(self.on_slider_moved)

    def toggle_volume_popup(self):
        import time
        now = time.time()
        last_hidden = getattr(self.volume_popup, "last_hidden_time", 0)
        
        if (now - last_hidden) < 0.2:
            return # Prevent instantaneous re-open if OS consumed the click as a focus-loss teardown
            
        if self.volume_popup.isVisible():
            self.volume_popup.hide()
        else:
            btn_pos = self.volume_btn.mapToGlobal(self.volume_btn.rect().topLeft())
            x = btn_pos.x() - (self.volume_popup.width() // 2) + (self.volume_btn.width() // 2)
            y = btn_pos.y() - self.volume_popup.height() - 10
            self.volume_popup.move(x, y)
            self.volume_popup.show()

    def update_auth_ui(self):
        if self.auth_manager.is_authenticated():
            self.login_btn.hide()
            self.load_playlists()
        else:
            self.login_btn.show()
            self.sidebar_widget.clear()
            self.cloud_list_widget.clear()
            self.cloud_list_widget.hide()
            self.cloud_status.show()
            self.cloud_status.setText("Log in to see your playlists.")

    def open_settings(self):
        dialog = SettingsDialog(self.settings_manager, self.is_cloud_mode, self)
        dialog.logout_requested.connect(self.on_logout_clicked)
        dialog.mode_toggled.connect(self.on_mode_toggled)
        if dialog.exec():
            self.shortcut_manager.start()
            self.flash_status("Settings saved. Shortcuts reloaded.")

    def on_login_clicked(self):
        try:
            success = self.auth_manager.login()
            if success:
                self.flash_status("Google OAuth Login Successful!", color="#4285F4")
                self.update_auth_ui()
        except Exception as e:
            self.flash_status(f"Login failed: {e}", color="#ff5555")

    def on_logout_clicked(self):
        self.auth_manager.logout()
        self.flash_status("Logged out successfully.")
        self.update_auth_ui()

    def load_playlists(self):
        self.flash_status("Fetching Playlists...")
        self.sidebar_widget.clear()
        
        self.playlist_worker = PlaylistLoaderWorker(self.youtube_api, parent=self)
        self.playlist_worker.playlists_loaded.connect(self.on_playlists_loaded)
        self.playlist_worker.error_occurred.connect(lambda e: self.flash_status(f"Error fetching playlists: {e}", "#ff5555"))
        self.playlist_worker.start()

    def on_playlists_loaded(self, playlists):
        self._cached_playlists = playlists
        for pl in playlists:
            title = pl.get('title')
            item = self.sidebar_widget.addItem(title)
            w_item = self.sidebar_widget.findItems(title, Qt.MatchExactly)[0]
            w_item.setData(Qt.UserRole, pl['id'])
            
        self.flash_status(f"Loaded {len(playlists)} playlists.", color="#4285F4")

    def on_playlist_selected(self, item):
        playlist_id = item.data(Qt.UserRole)
        
        # Pull rich payload from cache
        payload = next((p for p in self._cached_playlists if p['id'] == playlist_id), None)
        if payload:
            self.playlist_header.update_header(
                payload.get('title', 'Unknown'),
                payload.get('channel_title', 'Unknown Artist'),
                payload.get('item_count', 0),
                payload.get('thumbnail_url', '')
            )
            self.playlist_header.show()
            
        self.cloud_list_widget.clear()
        self.cloud_status.setText("Fetching playlist tracks...")
        self.cloud_status.show()
        self.cloud_list_widget.hide()
        
        self.image_workers = [] # Clear old workers
        self._current_playlist_total_seconds = 0
        self._current_playlist_track_count = 0

        self.items_worker = PlaylistItemsWorker(self.youtube_api, playlist_id, parent=self)
        self.items_worker.chunk_loaded.connect(self.on_playlist_chunk_loaded)
        self.items_worker.items_loaded.connect(self.on_playlist_items_loaded)
        self.items_worker.error_occurred.connect(lambda e: self.cloud_status.setText(f"Error fetching items: {e}"))
        self.items_worker.start()

    def on_playlist_chunk_loaded(self, tracks):
        # Show list if we have at least one chunk
        if self.cloud_status.isVisible():
            self.cloud_status.hide()
            self.cloud_list_widget.show()
            
        for track in tracks:
            self._current_playlist_total_seconds += parse_duration_to_seconds(track.get('duration', '0:00'))
            self._current_playlist_track_count += 1
            
            list_item = QListWidgetItem(self.cloud_list_widget)
            list_item.setData(Qt.UserRole, track)
            
            widget = TrackItemWidget(track)
            list_item.setSizeHint(widget.sizeHint())
            self.cloud_list_widget.setItemWidget(list_item, widget)
            
            thumb_url = track.get("thumbnail_url")
            if thumb_url:
                worker = ImageWorker(thumb_url, parent=self)
                worker.image_ready.connect(lambda p, _, w=widget: w.set_thumbnail(p))
                worker.start()
                self.image_workers.append(worker)
                
        # Live-update header metadata with running totals
        from utils.duration_utils import format_seconds_to_human
        duration_str = format_seconds_to_human(self._current_playlist_total_seconds)
        self.playlist_header.update_header(
            self.playlist_header.current_title,
            self.playlist_header.current_author,
            self._current_playlist_track_count,
            self.playlist_header.current_thumb,
            duration_str=duration_str
        )

    def on_playlist_items_loaded(self, all_tracks):
        # Final cleanup or status update when whole playlist is fetched
        self.flash_status(f"Fully loaded {len(all_tracks)} tracks.", color="#4285F4")

    def on_play_all_clicked(self):
        if self.cloud_list_widget.count() > 0:
            first_item = self.cloud_list_widget.item(0)
            self.on_cloud_track_selected(first_item)

    def on_cloud_track_selected(self, item):
        tracks = []
        for i in range(self.cloud_list_widget.count()):
            w = self.cloud_list_widget.item(i)
            track_dict = w.data(Qt.UserRole)
            if hasattr(track_dict, 'copy'):
                track_dict = track_dict.copy()
            track_dict["type"] = "cloud"
            tracks.append(track_dict)
            
        self.queue_manager.load_queue(tracks)
        
        clicked_track = item.data(Qt.UserRole)
        if hasattr(clicked_track, 'copy'):
            clicked_track = clicked_track.copy()
        clicked_track["type"] = "cloud"
        clicked_url = clicked_track.get("url")
        
        if not self.queue_manager.shuffle:
            idx = 0
            for track in tracks:
                if track.get("url") == clicked_url:
                    break
                idx += 1
            self.queue_manager.queue = tracks[idx+1:]
        else:
            self.queue_manager.queue = [t for t in self.queue_manager.queue if t.get("url") != clicked_url]
            
        self._play_track_object(clicked_track)

    def _play_track_object(self, track):
        if track["type"] == "cloud":
            self.search_input.setText(track.get("url", ""))
            
            if "video_id" in track:
                self.current_cloud_video_id = track["video_id"]
                
            self.now_playing_widget.update_track(
                title=track.get("title", ""),
                artist=track.get("author", "Unknown Artist"),
                thumbnail_url=track.get("thumbnail_url")
            )
            self.now_playing_widget.set_rating("none") # Standardize for new tracks
            self.current_cloud_url = track.get("url", "")
            
            # Sync active state down to track widgets
            for i in range(self.cloud_list_widget.count()):
                item = self.cloud_list_widget.item(i)
                widget = self.cloud_list_widget.itemWidget(item)
                if widget:
                    is_this_active = (widget.track_data.get("url") == self.current_cloud_url)
                    widget.set_active(is_this_active)
                    if is_this_active:
                        widget.set_playing(self.audio_engine.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState)
                        # Auto-Scroll to center the playing track
                        self.cloud_list_widget.scrollToItem(item, QListWidget.PositionAtCenter)
            
            self.yt_worker = YTWorker(self.current_cloud_url, parent=self)
            self.yt_worker.result_ready.connect(self.on_yt_result_ready)
            self.yt_worker.error_occurred.connect(self.on_yt_error)
            self.yt_worker.start()
            
            # Auto-fetch rating if authenticated
            if self.current_cloud_video_id and self.auth_manager.is_authenticated():
                self.rating_worker = RatingFetchWorker(self.youtube_api, self.current_cloud_video_id, self)
                self.rating_worker.rating_fetched.connect(self.on_rating_fetched)
                self.rating_worker.start()
            
        elif track["type"] == "local":
            self.audio_engine.play_file(track["path"])
            self.current_cloud_url = None
            self.current_cloud_video_id = None
            
            # Update background metadata for local files
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(base_dir, "..", "assets", "logo.svg")
            
            self.now_playing_widget.update_track(
                title=track.get("name", "Unknown Track"),
                artist="Local File",
                thumbnail_url=None, # Trigger the local default logic if needed
                pixmap=QPixmap(logo_path)
            )
            
            # Sync local active state
            for i in range(self.local_list_widget.count()):
                item = self.local_list_widget.item(i)
                data = item.data(Qt.UserRole)
                is_this_active = (data.get("path") == track["path"])
                if is_this_active:
                    item.setSelected(True)
                    self.local_list_widget.scrollToItem(item, QListWidget.PositionAtCenter)
                else:
                    item.setSelected(False)

    def on_prev_clicked(self):
        current_pos = self.progress_slider.value()
        total_duration = self.progress_slider.maximum()
        
        threshold_ms = 5000
        if total_duration > 0:
            percent_threshold = total_duration * 0.05
            threshold_ms = max(5000, percent_threshold)
            
        if current_pos > threshold_ms:
            self.audio_engine.seek(0)
            return

        track = self.queue_manager.previous_track()
        if track:
            self._play_track_object(track)
        else:
            self.audio_engine.seek(0)
            
    def on_next_clicked(self):
        track = self.queue_manager.next_track(manual_skip=True)
        if track:
            self._play_track_object(track)
        else:
            self.flash_status("End of queue.")

    def on_track_finished(self):
        track = self.queue_manager.next_track()
        if track:
            self._play_track_object(track)

    def on_shuffle_play_clicked(self):
        if not self.queue_manager.shuffle:
            self.on_shuffle_toggled()
            
        tracks = []
        for i in range(self.cloud_list_widget.count()):
            w = self.cloud_list_widget.item(i)
            track_dict = w.data(Qt.UserRole).copy()
            track_dict["type"] = "cloud"
            tracks.append(track_dict)
            
        if not tracks:
            return
            
        self.queue_manager.load_queue(tracks)
        next_track = self.queue_manager.next_track()
        if next_track:
            self._play_track_object(next_track)
            
    def on_shuffle_toggled(self):
        is_shuffled = not self.queue_manager.shuffle
        self.queue_manager.set_shuffle(is_shuffled)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        if is_shuffled:
            self.shuffle_btn.setIcon(QIcon(os.path.join(assets_dir, "shuffle_active.svg")))
            self.shuffle_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
        else:
            self.shuffle_btn.setIcon(QIcon(os.path.join(assets_dir, "shuffle.svg")))
            self.shuffle_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")

    def on_repeat_toggled(self):
        current_mode = self.queue_manager.repeat_mode
        if current_mode == "off":
            new_mode = "all"
        elif current_mode == "all":
            new_mode = "one"
        else:
            new_mode = "off"
            
        self.queue_manager.set_repeat_mode(new_mode)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        if new_mode == "all":
            self.repeat_btn.setIcon(QIcon(os.path.join(assets_dir, "repeat_active.svg")))
            self.repeat_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
            self.repeat_btn.setText("")
        elif new_mode == "one":
            self.repeat_btn.setIcon(QIcon(os.path.join(assets_dir, "repeat_active.svg")))
            self.repeat_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; color: #FF0000; font-weight: bold; font-size: 10px; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
            self.repeat_btn.setText("1")
        else:
            self.repeat_btn.setIcon(QIcon(os.path.join(assets_dir, "repeat.svg")))
            self.repeat_btn.setStyleSheet("QPushButton { background-color: transparent; border: none; } QPushButton:hover { background-color: #333; border-radius: 17px; }")
            self.repeat_btn.setText("")

    def on_volume_changed(self, value):
        volume_level = value / 100.0
        self.audio_engine.set_volume(volume_level)
        self.settings_manager.settings["volume_level"] = value

    def update_time_combo(self, current_ms=None, duration_ms=None):
        if current_ms is not None:
            self._current_pos_ms = current_ms
        if duration_ms is not None:
            self._duration_ms = duration_ms
            
        cur = getattr(self, '_current_pos_ms', 0)
        dur = getattr(self, '_duration_ms', 0)
        if dur > 0:
            self.time_label_combo.setText(f"{self.format_ms(cur)} / {self.format_ms(dur)}")

    def on_position_updated(self, position_ms):
        if not self.is_slider_being_dragged:
            self.progress_slider.setValue(position_ms)
            self.update_time_combo(current_ms=position_ms)

    def on_duration_updated(self, duration_ms):
        self.progress_slider.setRange(0, duration_ms)
        self.update_time_combo(duration_ms=duration_ms)

    def on_slider_pressed(self):
        self.is_slider_being_dragged = True

    def on_slider_released(self):
        self.is_slider_being_dragged = False
        position_ms = self.progress_slider.value()
        self.audio_engine.seek(position_ms)
        
    def on_slider_moved(self, position):
        self.update_time_combo(current_ms=position)

    def format_ms(self, ms):
        seconds = (ms // 1000) % 60
        minutes = (ms // (1000 * 60)) % 60
        hours = ms // (1000 * 60 * 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def on_search_triggered(self):
        if not self.is_cloud_mode:
            self.flash_status("Switch to Cloud Mode to search YouTube.", "#ff5555")
            return

        query = self.search_input.text().strip()
        if not query:
            return

        # Hide playlist stuff while searching
        self.cloud_list_widget.hide()
        self.cloud_status.show()
        
        self.cloud_status.setText(f"Extracting Stream...\nPlease wait.")
        self.cloud_status.setStyleSheet("font-size: 16px; color: #e0a96d; font-weight: bold;")
        self.action_btn.setEnabled(False)

        self.current_cloud_url = query 

        # New search flow
        self.stacked_widget.setCurrentIndex(2) # Switch to search results
        self.search_results_view.set_loading(query)
        
        self.search_worker = SearchWorker(self.youtube_api, query, parent=self)
        self.search_worker.results_ready.connect(self.on_search_results_ready)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_results_ready(self, results):
        self.action_btn.setEnabled(True)
        self.search_results_view.display_results(results)

    def on_search_error(self, error_msg):
        self.action_btn.setEnabled(True)
        self.flash_status(f"Search error: {error_msg}", "#ff5555")

    def on_search_filter_changed(self, category):
        query = self.search_input.text().strip()
        if not query:
            return
            
        self.search_worker = SearchWorker(self.youtube_api, query, filter_type=category, parent=self)
        self.search_worker.results_ready.connect(self.on_search_results_ready)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_result_clicked(self, data):
        kind = data.get("kind")
        if kind == 'youtube#video':
            # Play the video
            track = data.copy()
            track["type"] = "cloud"
            # Prepare queue (optional: add all results to queue?)
            # For now, just play this one like before
            self._play_track_object(track)
        elif kind == 'youtube#playlist':
            # Open playlist view
            # Create a dummy item to reuse on_playlist_selected
            from PySide6.QtWidgets import QListWidgetItem
            dummy_item = QListWidgetItem()
            dummy_item.setData(Qt.UserRole, data["id"])
            
            # Update cache so metadata pull works
            if not any(p['id'] == data['id'] for p in self._cached_playlists):
                self._cached_playlists.append({
                    "id": data["id"],
                    "title": data["title"],
                    "channel_title": data["author"],
                    "thumbnail_url": data["thumbnail_url"],
                    "item_count": 0 # Unknown for now
                })
            
            self.on_playlist_selected(dummy_item)
            self.stacked_widget.setCurrentIndex(0) # Back to cloud view
        elif kind == 'youtube#channel':
            # For now, maybe just show a message or list their playlists?
            self.flash_status(f"Artist search for {data['title']} - Playlist listing not yet implemented.")

    def on_rate_clicked(self, rating):
        if not self.auth_manager.is_authenticated() or not self.current_cloud_video_id:
            self.flash_status("Please login and play a cloud track to rate it.", "#ff5555")
            return
            
        success = self.youtube_api.rate_video(self.current_cloud_video_id, rating)
        if success:
            self.flash_status(f"Rated video as: {rating}", "#1ed760")
            self.now_playing_widget.set_rating(rating)

    def on_rating_fetched(self, video_id, rating):
        if video_id != self.current_cloud_video_id:
            return # Stale worker
            
        self.now_playing_widget.set_rating(rating)

    def on_yt_result_ready(self, track_info):
        self.action_btn.setEnabled(True)
        stream_url = track_info.get("url")
        title = track_info.get("title", 'Unknown')
        
        # In case we launched a generic raw search, update the widget safely
        self.now_playing_widget.update_track(
            title=title,
            artist=track_info.get("author", "Unknown Artist"),
            thumbnail_url=track_info.get("thumbnail_url")
        )
        
        if track_info.get("video_id"):
            self.current_cloud_video_id = track_info["video_id"]
            
            # Fetch rating organically
            if self.auth_manager.is_authenticated():
                self.rating_worker = RatingFetchWorker(self.youtube_api, self.current_cloud_video_id, self)
                self.rating_worker.rating_fetched.connect(self.on_rating_fetched)
                self.rating_worker.start()
            
        self.flash_status(f"Buffering: {title}")
        self.audio_engine.play_file(stream_url)
        
        if self.cloud_status.isVisible() and not self.cloud_list_widget.isVisible():
            self.cloud_status.setText(f"Loaded: {title}\n(Streaming)")
            self.cloud_status.setStyleSheet("font-size: 16px; color: #1ed760; font-weight: bold;")
        self.on_track_changed(title)

    def on_yt_error(self, error_msg):
        self.action_btn.setEnabled(True)
        self.cloud_status.setText(f"Error extracting stream:\n{error_msg}")
        self.cloud_status.setStyleSheet("font-size: 16px; color: #ff5555; font-weight: bold;")

    def on_download_clicked(self, target_url=None):
        if not target_url or isinstance(target_url, bool):
            target_url = self.current_cloud_url
            
        if not target_url:
            self.flash_status("Search or select a track first to download.", "#ff5555")
            return
            
        output_dir = self.settings_manager.settings.get("download_dir", "")
        if not output_dir:
            output_dir = self.settings_manager.settings.get("local_music_dir", "")
            
        if not output_dir:
            self.flash_status("Please set a Download Location in Settings first!", "#ff5555")
            return

        self.flash_status(f"Starting Download to {output_dir}...", color="#e0a96d")
        
        self.download_btn.setEnabled(False)
        self.download_worker = DownloadWorker(target_url, output_dir, parent=self)
        self.download_worker.download_finished.connect(self.on_download_finished)
        self.download_worker.start()

    def on_download_finished(self, msg, success):
        self.download_btn.setEnabled(True)
        self.flash_status(msg, "#1ed760" if success else "#ff5555")
        if success and not self.is_cloud_mode:
            self.scan_and_load_local(self.settings_manager.settings.get("download_dir", "") or self.settings_manager.settings.get("local_music_dir", ""))

    def on_audio_error(self, error_code, error_str):
        if self.is_cloud_mode and self.current_cloud_url:
            # We treat Demuxer failures during streaming as recoverable
            recoverable_codes = [
                3, # QMediaPlayer.Error.NetworkError
                5, # QMediaPlayer.Error.ResourceError
            ]
            
            # -10054 is often reported as ResourceError or NetworkError by Qt
            print(f"Detected potential stream failure: {error_str} (Code: {error_code})")
            
            if error_code in recoverable_codes or "demuxing failed" in error_str.lower():
                self.initiate_recovery()
            else:
                self.flash_status(f"Non-recoverable audio error: {error_str}", "#ff5555")

    def initiate_recovery(self):
        if self.recovery_mode: return
        
        self.recovery_mode = True
        self.last_failure_pos = self.audio_engine.player.position()
        self.flash_status("Streaming interrupted. Attempting to recover...", "#e0a96d")
        
        # Exponential backoff: 0.5s, 1s, 2s, 4s, 8s...
        delay = int(500 * (2 ** self.recovery_retry_count))
        # Cap at 30 seconds
        delay = min(delay, 30000)
        
        print(f"Starting recovery attempt {self.recovery_retry_count + 1} in {delay}ms...")
        self.recovery_timer.start(delay)

    def attempt_recovery(self):
        if not self.current_cloud_url:
            self.recovery_mode = False
            return
            
        self.recovery_retry_count += 1
        
        # Restart YT extraction
        if self.yt_worker:
            self.yt_worker.terminate()
            
        self.yt_worker = YTWorker(self.current_cloud_url, parent=self)
        self.yt_worker.result_ready.connect(self.on_recovery_result_ready)
        self.yt_worker.error_occurred.connect(self.on_recovery_error)
        self.yt_worker.start()

    def on_recovery_result_ready(self, track_info):
        print("Recovery successful: fresh stream URL obtained.")
        self.recovery_mode = False
        self.recovery_retry_count = 0
        
        stream_url = track_info['stream_url']
        self.audio_engine.player.setSource(QUrl(stream_url))
        self.audio_engine.player.play()
        
        # Seek to last known position
        if self.last_failure_pos > 0:
            print(f"Resuming from saved position: {self.last_failure_pos}ms")
            # Wait a tiny bit for the source to load before seeking
            QTimer.singleShot(500, lambda: self.audio_engine.seek(self.last_failure_pos))
            
        self.flash_status("Playback recovered successfully!", "#1ed760")

    def on_recovery_error(self, error_msg):
        print(f"Recovery attempt failed: {error_msg}")
        self.recovery_mode = False
        if self.recovery_retry_count < 5: # Max 5 automated retries
            self.initiate_recovery()
        else:
            self.flash_status("Recovery failed after multiple attempts.", "#ff5555")
            self.recovery_retry_count = 0

    def show_now_playing_menu(self):
        if not self.current_cloud_url:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2a2a2a; color: white; border: 1px solid #444; } QMenu::item:selected { background-color: #444; }")
        
        dl_action = QAction("⬇ Download Track", self)
        dl_action.triggered.connect(lambda: self.on_download_clicked(self.current_cloud_url))
        menu.addAction(dl_action)
        
        copy_action = QAction("Copy YouTube URL", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(self.current_cloud_url))
        menu.addAction(copy_action)
        
        browser_action = QAction("Open in Browser", self)
        browser_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(self.current_cloud_url)))
        menu.addAction(browser_action)
        
        btn_pos = self.now_playing_widget.ellipsis_btn.mapToGlobal(self.now_playing_widget.ellipsis_btn.rect().bottomLeft())
        menu.exec(btn_pos)

    def show_cloud_context_menu(self, pos):
        item = self.cloud_list_widget.itemAt(pos)
        if not item:
            return
            
        track_dict = item.data(Qt.UserRole)
        if hasattr(track_dict, 'copy'):
            track_dict = track_dict.copy()
        track_dict["type"] = "cloud"
        url = track_dict.get("url")
        if not url:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2a2a2a; color: white; border: 1px solid #444; padding: 5px; } QMenu::item { padding: 5px 20px; } QMenu::item:selected { background-color: #444; border-radius: 4px; }")
        
        play_next_action = QAction("Play Next", self)
        play_next_action.triggered.connect(lambda: self.queue_manager.insert_next(track_dict))
        menu.addAction(play_next_action)
        
        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self.queue_manager.queue.append(track_dict))
        menu.addAction(add_queue_action)
        
        menu.addSeparator()
        
        dl_action = QAction("⬇ Download Track", self)
        dl_action.triggered.connect(lambda: self.on_download_clicked(url))
        menu.addAction(dl_action)
        
        copy_action = QAction("Copy URL", self)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(url))
        menu.addAction(copy_action)
        
        menu.exec(self.cloud_list_widget.viewport().mapToGlobal(pos))
        
    def show_local_context_menu(self, pos):
        item = self.local_list_widget.itemAt(pos)
        if not item:
            return
            
        track_dict = item.data(Qt.UserRole)
        if hasattr(track_dict, 'copy'):
            track_dict = track_dict.copy()
        track_dict["type"] = "local"
        path = track_dict.get("path")
        if not path:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2a2a2a; color: white; border: 1px solid #444; padding: 5px; } QMenu::item { padding: 5px 20px; } QMenu::item:selected { background-color: #444; border-radius: 4px; }")
        
        play_next_action = QAction("Play Next", self)
        play_next_action.triggered.connect(lambda: self.queue_manager.insert_next(track_dict))
        menu.addAction(play_next_action)
        
        add_queue_action = QAction("Add to Queue", self)
        add_queue_action.triggered.connect(lambda: self.queue_manager.queue.append(track_dict))
        menu.addAction(add_queue_action)
        
        menu.addSeparator()
        
        explore_action = QAction("Show in Explorer", self)
        explore_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path))))
        menu.addAction(explore_action)
        
        menu.exec(self.local_list_widget.viewport().mapToGlobal(pos))

    def browse_local_folder(self):
        default_dir = self.settings_manager.settings.get("download_dir", "")
        if not default_dir:
            default_dir = self.settings_manager.settings.get("local_music_dir", "")
        folder_path = QFileDialog.getExistingDirectory(self, "Select Music Folder", default_dir)
        if folder_path:
            self.settings_manager.settings["local_music_dir"] = folder_path
            self.settings_manager.save()
            self.scan_and_load_local(folder_path)

    def scan_and_load_local(self, folder_path):
        self.local_files = LocalScanner.scan_directory(folder_path)
        self.local_list_widget.clear()
        if not self.local_files:
            return
        for f in self.local_files:
            item = QListWidgetItem(f["name"])
            item.setData(Qt.UserRole, f)
            self.local_list_widget.addItem(item)

    def on_local_track_selected(self, item):
        tracks = []
        for f in self.local_files:
            tracks.append({"type": "local", "path": f["path"], "name": f["name"]})
            
        self.queue_manager.load_queue(tracks)
        
        clicked_name = item.text()
        clicked_track = None
        
        if not self.queue_manager.shuffle:
            idx = 0
            for track in tracks:
                if track["name"] == clicked_name:
                    clicked_track = track
                    break
                idx += 1
            self.queue_manager.queue = tracks[idx+1:]
        else:
            clicked_track = next((t for t in tracks if t["name"] == clicked_name), None)
            self.queue_manager.queue = [t for t in self.queue_manager.queue if t["name"] != clicked_name]
            
        if clicked_track:
            self._play_track_object(clicked_track)

    def on_hotkey_triggered(self, action):
        if action == "play_pause":
            self.audio_engine.toggle_play_pause()
        elif action == "next_track":
            self.on_next_clicked()
        elif action == "prev_track":
            self.on_prev_clicked()

    def on_playback_state_changed(self, is_playing):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        if is_playing:
            self.play_pause_btn.setIcon(QIcon(os.path.join(assets_dir, "pause.svg")))
        else:
            self.play_pause_btn.setIcon(QIcon(os.path.join(assets_dir, "play.svg")))
            
        # Update playing state on widgets
        for i in range(self.cloud_list_widget.count()):
            w = self.cloud_list_widget.itemWidget(self.cloud_list_widget.item(i))
            if w and w.is_active:
                w.set_playing(is_playing)

    def on_track_changed(self, track_name):
        display = track_name.split("/")[-1].split("\\")[-1] if "googlevideo.com" not in track_name else track_name
        if "googlevideo.com" in display: return 
        self.flash_status(f"Playing: {display}")

    def flash_status(self, text, color="#FF0000"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: bold;")
        QTimer.singleShot(4000, lambda: self.status_label.setStyleSheet("font-size: 14px; color: #aaa;"))

    def on_mode_toggled(self, checked):
        self.is_cloud_mode = checked
        if self.is_cloud_mode:
            self.search_input.setPlaceholderText("Search YouTube or Paste URL...")
            self.browse_btn.hide()
            self.download_btn.show()
            self.sidebar_widget.show()
            self.stacked_widget.setCurrentIndex(0)
        else:
            self.search_input.setPlaceholderText("Search Local Directory (Filter)...")
            self.browse_btn.show()
            self.download_btn.hide()
            self.sidebar_widget.hide()
            self.stacked_widget.setCurrentIndex(1)
            if not self.local_files:
                saved_dir = self.settings_manager.settings.get("download_dir", "")
                if not saved_dir:
                    saved_dir = self.settings_manager.settings.get("local_music_dir", "")
                
                if saved_dir:
                    self.scan_and_load_local(saved_dir)

    def closeEvent(self, event):
        self.settings_manager.save()
        self.audio_engine.stop()
        self.shortcut_manager.stop()
        super().closeEvent(event)
