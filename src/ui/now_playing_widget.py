from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from utils.image_worker import ImageWorker
from ui.common import ElidedLabel
import os

class NowPlayingWidget(QWidget):
    rating_clicked = Signal(str) # "like" or "dislike"
    menu_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_worker = None
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 0)
        main_layout.setSpacing(15)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(50, 50)
        self.thumbnail_label.setStyleSheet("background-color: #333; border-radius: 4px;")
        self.thumbnail_label.setAlignment(Qt.AlignCenter)

        # Meta Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        
        self.title_label = ElidedLabel("Not Playing")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        # Remove setFixedWidth to allow dynamic scaling
        
        self.artist_label = ElidedLabel("")
        self.artist_label.setAlignment(Qt.AlignCenter)
        self.artist_label.setStyleSheet("font-size: 12px; color: #aaa;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)

        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(5)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        self.like_btn = QPushButton()
        self.like_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_up_outline.svg")))
        self.like_btn.setFocusPolicy(Qt.NoFocus)
        self.like_btn.setToolTip("Like")
        self.like_btn.setFixedSize(30, 30)
        self.like_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; border-radius: 4px; font-size: 14px; } QPushButton:hover { background-color: #333; }")
        self.like_btn.clicked.connect(lambda: self.rating_clicked.emit("like"))
        
        self.dislike_btn = QPushButton()
        self.dislike_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_down_outline.svg")))
        self.dislike_btn.setFocusPolicy(Qt.NoFocus)
        self.dislike_btn.setToolTip("Dislike")
        self.dislike_btn.setFixedSize(30, 30)
        self.dislike_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; border-radius: 4px; font-size: 14px; } QPushButton:hover { background-color: #333; }")
        self.dislike_btn.clicked.connect(lambda: self.rating_clicked.emit("dislike"))
        
        self.ellipsis_btn = QPushButton()
        self.ellipsis_btn.setIcon(QIcon(os.path.join(assets_dir, "more_vert.svg")))
        self.ellipsis_btn.setFocusPolicy(Qt.NoFocus)
        self.ellipsis_btn.setToolTip("More Options")
        self.ellipsis_btn.setFixedSize(30, 30)
        self.ellipsis_btn.setStyleSheet("QPushButton { background-color: transparent; color: white; font-weight: bold; font-size: 18px; border-radius: 15px; } QPushButton:hover { background-color: #333; }")
        self.ellipsis_btn.clicked.connect(self.menu_clicked.emit)

        actions_layout.addWidget(self.dislike_btn)
        actions_layout.addWidget(self.like_btn)
        actions_layout.addWidget(self.ellipsis_btn)

        main_layout.addStretch() # Left spacer to help center
        main_layout.addWidget(self.thumbnail_label)
        main_layout.addLayout(text_layout, 1) # Text still grows to fill space
        main_layout.addLayout(actions_layout)
        main_layout.addStretch() # Right spacer to help center
        
    def set_rating(self, rating):
        """
        Swaps icons between outline and solid based on the current rating.
        rating: 'like', 'dislike', or 'none'
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "..", "assets")
        
        if rating == "like":
            self.like_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_up.svg"))) # Solid
            self.dislike_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_down_outline.svg")))
        elif rating == "dislike":
            self.like_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_up_outline.svg")))
            self.dislike_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_down.svg"))) # Solid
        else: # none
            self.like_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_up_outline.svg")))
            self.dislike_btn.setIcon(QIcon(os.path.join(assets_dir, "thumb_down_outline.svg")))

    def update_track(self, title, artist, thumbnail_url=None, pixmap=None):
        self.title_label.setText(title)
        self.title_label.setToolTip(title)
        self.artist_label.setText(artist)
        self.artist_label.setToolTip(artist)
        
        if pixmap:
            self.set_thumbnail(pixmap, None)
        elif thumbnail_url:
            if self.image_worker:
                self.image_worker.terminate()
            self.image_worker = ImageWorker(thumbnail_url)
            self.image_worker.image_ready.connect(self.set_thumbnail)
            self.image_worker.start()
        else:
            self.thumbnail_label.setPixmap(QIcon().pixmap(50, 50)) # Clear
            
    def set_thumbnail(self, pixmap, url=None):
        self.thumbnail_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
