from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFormLayout, QFrame,
    QRadioButton, QFileDialog
)
from PySide6.QtCore import Signal, Qt

class SettingsDialog(QDialog):
    logout_requested = Signal()
    mode_toggled = Signal(bool)

    def __init__(self, settings_manager, is_cloud_mode, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.is_cloud_mode = is_cloud_mode
        self.setWindowTitle("Preferences & Settings")
        self.resize(400, 420)
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # --- TOP Section: Application Preferences ---
        app_group = QVBoxLayout()
        header_app = QLabel("<b>Application Preferences</b>")
        header_app.setStyleSheet("font-size: 15px; color: #FF0000;")
        app_group.addWidget(header_app)
        
        # Mode Selection (Radio Buttons)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("font-weight: bold; margin-right: 10px;")
        
        self.cloud_radio = QRadioButton("Cloud")
        self.local_radio = QRadioButton("Local")
        self.cloud_radio.setChecked(self.is_cloud_mode)
        self.local_radio.setChecked(not self.is_cloud_mode)
        
        self.cloud_radio.toggled.connect(self.on_mode_radio_toggled)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.cloud_radio)
        mode_layout.addWidget(self.local_radio)
        mode_layout.addStretch()
        app_group.addLayout(mode_layout)

        # Download Location
        dl_layout = QHBoxLayout()
        dl_label = QLabel("Download Location:")
        dl_label.setStyleSheet("font-weight: bold;")
        self.dl_input = QLineEdit(self.settings_manager.settings.get("download_dir", ""))
        self.dl_input.setReadOnly(True)
        self.dl_input.setPlaceholderText("Fallback to Local Music Dir")
        
        dl_browse_btn = QPushButton("Browse")
        dl_browse_btn.setFixedSize(85, 28)
        dl_browse_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: white; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #555; }
        """)
        dl_browse_btn.clicked.connect(self.browse_download_dir)
        
        dl_layout.addWidget(dl_label)
        dl_layout.addWidget(self.dl_input, 1)
        dl_layout.addWidget(dl_browse_btn)
        app_group.addLayout(dl_layout)
        
        # Logout Button (Red)
        logout_btn = QPushButton("Log out of Google")
        logout_btn.setStyleSheet("""
            QPushButton { background-color: #FF0000; color: white; padding: 10px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #CC0000; }
        """)
        logout_btn.clicked.connect(self.on_logout_clicked)
        app_group.addWidget(logout_btn)
        
        main_layout.addLayout(app_group)
        
        # Separation Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #333;")
        main_layout.addWidget(line)
        
        # --- BOTTOM Section: Keyboard Shortcuts ---
        shortcut_group = QVBoxLayout()
        header_shortcuts = QLabel("<b>Keyboard Shortcuts</b>")
        header_shortcuts.setStyleSheet("font-size: 15px; color: #FF0000;")
        shortcut_group.addWidget(header_shortcuts)
        
        info_label = QLabel("Global Hotkeys (pynput format, e.g. <ctrl>+<shift>+p)")
        info_label.setStyleSheet("color: #888; font-size: 11px;")
        info_label.setWordWrap(True)
        shortcut_group.addWidget(info_label)

        form_layout = QFormLayout()
        self.play_input = QLineEdit(self.settings_manager.get_shortcut("play_pause"))
        form_layout.addRow("Play / Pause:", self.play_input)
        self.next_input = QLineEdit(self.settings_manager.get_shortcut("next_track"))
        form_layout.addRow("Next Track:", self.next_input)
        self.prev_input = QLineEdit(self.settings_manager.get_shortcut("prev_track"))
        form_layout.addRow("Previous Track:", self.prev_input)
        
        shortcut_group.addLayout(form_layout)
        main_layout.addLayout(shortcut_group)
        
        main_layout.addStretch()

        # Bottom Action Buttons
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save and Close")
        save_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #555; }
        """)
        save_btn.clicked.connect(self.save_settings)
        
        close_btn = QPushButton("Close without Saving")
        close_btn.setStyleSheet("""
            QPushButton { background-color: #444; color: #aaa; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #555; color: white; }
        """)
        close_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)

    def on_mode_radio_toggled(self, checked):
        # We only emit if cloud is toggled (True = Cloud, False = Local)
        self.is_cloud_mode = self.cloud_radio.isChecked()
        self.mode_toggled.emit(self.is_cloud_mode)

    def on_logout_clicked(self):
        self.logout_requested.emit()
        self.accept()

    def browse_download_dir(self):
        default_dir = self.dl_input.text() if self.dl_input.text() else self.settings_manager.settings.get("local_music_dir", "")
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder", default_dir)
        if folder:
            self.dl_input.setText(folder)

    def save_settings(self):
        self.settings_manager.set_shortcut("play_pause", self.play_input.text().strip())
        self.settings_manager.set_shortcut("next_track", self.next_input.text().strip())
        self.settings_manager.set_shortcut("prev_track", self.prev_input.text().strip())
        self.settings_manager.settings["download_dir"] = self.dl_input.text().strip()
        self.settings_manager.save()
        self.accept()

