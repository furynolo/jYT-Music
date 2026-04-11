import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QIcon
from utils.image_worker import ImageWorker

class PlaylistHeaderWidget(QWidget):
    play_all_clicked = Signal()
    shuffle_play_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedWidth(260) # Anchor side-column width
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 15, 5) # Pad right to separate from list
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Cover Art
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(240, 240)
        self.cover_label.setStyleSheet("background-color: #222; border-radius: 8px;")
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setText("No Image")
        main_layout.addWidget(self.cover_label)
        
        # Type Indicator
        type_label = QLabel("PLAYLIST")
        type_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        main_layout.addWidget(type_label)
        
        # Title
        self.title_label = QLabel("Playlist Title")
        self.title_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; margin-top: -5px;")
        self.title_label.setWordWrap(True)
        main_layout.addWidget(self.title_label)
        
        # Metadata
        self.meta_label = QLabel("Author • 0 songs")
        self.meta_label.setStyleSheet("color: #aaa; font-size: 13px;")
        self.meta_label.setWordWrap(True)
        main_layout.addWidget(self.meta_label)
        
        # Play Buttons
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignLeft)
        
        self.play_btn = QPushButton()
        self.play_btn.setFixedSize(48, 48)
        self.play_btn.setToolTip("Play All")
        self.play_btn.setIcon(QIcon(os.path.join(assets_dir, "play.svg")))
        self.play_btn.setStyleSheet("""
            QPushButton { background-color: #FF0000; border-radius: 24px; border: none; } 
            QPushButton:hover { background-color: #CC0000; }
        """)
        self.play_btn.setFocusPolicy(Qt.NoFocus)
        self.play_btn.setCursor(Qt.PointingHandCursor)
        self.play_btn.clicked.connect(self.play_all_clicked.emit)
        
        self.shuffle_play_btn = QPushButton()
        self.shuffle_play_btn.setFixedSize(48, 48)
        self.shuffle_play_btn.setToolTip("Shuffle Play")
        self.shuffle_play_btn.setIcon(QIcon(os.path.join(assets_dir, "shuffle.svg")))
        self.shuffle_play_btn.setStyleSheet("""
            QPushButton { background-color: #333; border-radius: 24px; border: none; } 
            QPushButton:hover { background-color: #444; }
        """)
        self.shuffle_play_btn.setFocusPolicy(Qt.NoFocus)
        self.shuffle_play_btn.setCursor(Qt.PointingHandCursor)
        self.shuffle_play_btn.clicked.connect(self.shuffle_play_clicked.emit)
        
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.shuffle_play_btn)
        main_layout.addLayout(btn_layout)
        
        main_layout.addStretch() # Push everything to top
        self.image_worker = None

    def update_header(self, title, author, item_count, thumbnail_url, duration_str=None):
        # Determine if we actually need to change the image
        url_changed = (thumbnail_url != getattr(self, 'current_thumb', None))
        has_pixmap = self.cover_label.pixmap() is not None and not self.cover_label.pixmap().isNull()

        self.current_title = title
        self.current_author = author
        self.current_count = item_count
        self.current_thumb = thumbnail_url

        self.title_label.setText(title)
        
        meta_text = f"{author} • {item_count} tracks"
        if duration_str:
            meta_text += f"\n{duration_str}" # Newline for vertical column
        self.meta_label.setText(meta_text)
        
        # Only trigger image load if the URL is new OR if we don't have an image yet
        if thumbnail_url:
            if url_changed or not has_pixmap:
                # Only show "Loading..." if we don't have a valid image yet
                if not has_pixmap:
                    self.cover_label.clear()
                    self.cover_label.setText("Loading...")
                
                self.image_worker = ImageWorker(thumbnail_url, parent=self)
                self.image_worker.image_ready.connect(self.set_cover)
                self.image_worker.start()
        else:
            self.cover_label.clear()
            self.cover_label.setText("No Image")

    def set_cover(self, pixmap):
        scaled_pixmap = pixmap.scaled(240, 240, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.cover_label.setPixmap(scaled_pixmap)
