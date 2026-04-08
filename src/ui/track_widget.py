from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
import os

class TrackItemWidget(QWidget):
    def __init__(self, track_data, parent=None):
        super().__init__(parent)
        self.track_data = track_data
        self.is_active = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 20, 5)
        
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(60, 45) # 4:3 default thumbnail approx
        self.thumb_label.setStyleSheet("background-color: #333; border-radius: 4px;")
        self.thumb_label.setAlignment(Qt.AlignCenter)
        
        # Transparent overlay for play/pause
        self.overlay_label = QLabel(self.thumb_label)
        self.overlay_label.setFixedSize(60, 45)
        self.overlay_label.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); border-radius: 4px;")
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.hide()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(base_dir, "..", "assets")
        
        raw_title = track_data.get('title', 'Unknown Title')
        max_chars = 50
        if len(raw_title) > max_chars:
            display_title = raw_title[:max_chars - 8] + "..." + raw_title[-5:]
        else:
            display_title = raw_title
            
        self.title_label = QLabel(display_title)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        
        self.type_label = QLabel(track_data.get('result_type', ''))
        self.type_label.setStyleSheet("""
            font-size: 10px; 
            color: #aaa; 
            background-color: #333; 
            border-radius: 3px; 
            padding: 2px 5px;
            font-weight: bold;
        """)
        if not track_data.get('result_type'):
            self.type_label.hide()
            
        self.duration_label = QLabel(track_data.get('duration', '0:00'))
        self.duration_label.setStyleSheet("font-size: 12px; color: #888;")
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(self.thumb_label)
        layout.addWidget(self.type_label)
        layout.addWidget(self.title_label, 1) # Title takes extra space
        layout.addWidget(self.duration_label)

    def set_thumbnail(self, pixmap):
        scaled_pixmap = pixmap.scaled(self.thumb_label.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.thumb_label.setPixmap(scaled_pixmap)

    def enterEvent(self, event):
        if not self.is_active:
            self.overlay_label.setPixmap(QIcon(os.path.join(self.assets_dir, "play.svg")).pixmap(24, 24))
            self.overlay_label.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_active:
            self.overlay_label.hide()
        super().leaveEvent(event)

    def set_active(self, active):
        self.is_active = active
        if active:
            # YouTube Red Border (2px) + Dimmed background for the row
            self.setStyleSheet("TrackItemWidget { background-color: #222; border: 2px solid #FF0000; border-radius: 4px; }")
            self.overlay_label.show()
        else:
            self.setStyleSheet("TrackItemWidget { background-color: transparent; border: none; }")
            self.overlay_label.hide()
            
    def set_playing(self, is_playing):
        if self.is_active:
            icon_name = "pause.svg" if is_playing else "play.svg"
            self.overlay_label.setPixmap(QIcon(os.path.join(self.assets_dir, icon_name)).pixmap(24, 24))
