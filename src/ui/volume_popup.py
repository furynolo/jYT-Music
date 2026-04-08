from PySide6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel
from PySide6.QtCore import Qt, Signal

class VolumePopup(QWidget):
    volume_changed = Signal(int)

    def __init__(self, parent=None, initial_value=80):
        super().__init__(parent)
        # Use Qt.ToolTip or Qt.Popup flag to make it float above the main window
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Main background widget
        self.bg_widget = QWidget(self)
        self.bg_widget.setStyleSheet("background-color: #222; border-radius: 8px; border: 1px solid #444;")
        self.setFixedSize(50, 160)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.bg_widget)
        
        layout = QVBoxLayout(self.bg_widget)
        layout.setContentsMargins(10, 15, 10, 10)
        
        # Value Label
        self.val_label = QLabel(str(initial_value))
        self.val_label.setAlignment(Qt.AlignCenter)
        self.val_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold; border: none;")
        
        # Vertical Slider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(0, 100)
        self.slider.setValue(initial_value)
        self.slider.setMinimumHeight(100)
        self.slider.setStyleSheet("""
            QSlider::groove:vertical { background: #333; width: 4px; border-radius: 2px; }
            QSlider::handle:vertical { background: white; height: 12px; margin: 0 -4px; border-radius: 6px; }
            QSlider::sub-page:vertical { background: #1ed760; border-radius: 2px; }
            QSlider::add-page:vertical { background: #333; border-radius: 2px; }
        """)
        
        self.slider.valueChanged.connect(self.on_slider_changed)
        
        layout.addWidget(self.val_label)
        layout.addWidget(self.slider, alignment=Qt.AlignHCenter)

    def on_slider_changed(self, value):
        self.val_label.setText(str(value))
        self.volume_changed.emit(value)
        
    def hideEvent(self, event):
        import time
        self.last_hidden_time = time.time()
        super().hideEvent(event)
