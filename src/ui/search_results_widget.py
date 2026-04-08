from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QLabel, QListWidgetItem, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from ui.track_widget import TrackItemWidget
from utils.image_worker import ImageWorker

class SearchResultsWidget(QWidget):
    # Signal emitted when a filter is changed
    filter_changed = Signal(str) # category
    # Signal emitted when a result is clicked
    result_clicked = Signal(dict) # result data

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_filter = "All"
        self.image_workers = []
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # --- Filter Bar ---
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)
        
        self.filters = ["All", "Songs", "Albums", "Community Playlists", "Artists", "Videos"]
        self.filter_buttons = {}
        
        for f in self.filters:
            btn = QPushButton(f)
            btn.setCheckable(True)
            if f == "All":
                btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: white;
                    border-radius: 15px;
                    padding: 5px 20px;
                    font-size: 13px;
                    border: none;
                }
                QPushButton:checked {
                    background-color: white;
                    color: black;
                }
                QPushButton:hover:!checked {
                    background-color: #444;
                }
            """)
            btn.clicked.connect(lambda checked, cat=f: self.on_filter_btn_clicked(cat))
            filter_layout.addWidget(btn)
            self.filter_buttons[f] = btn
            
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)
        
        # --- Status Label ---
        self.status_label = QLabel("Search Results")
        self.status_label.setStyleSheet("font-size: 14px; color: #888; font-weight: bold; margin-left: 5px;")
        main_layout.addWidget(self.status_label)
        
        # --- Results List ---
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("background-color: transparent; border: none; outline: none;")
        self.results_list.itemClicked.connect(self.on_item_clicked)
        main_layout.addWidget(self.results_list, 1)

    def on_filter_btn_clicked(self, category):
        # Uncheck others
        for name, btn in self.filter_buttons.items():
            if name != category:
                btn.setChecked(False)
        
        # Ensure the clicked one stays checked
        self.filter_buttons[category].setChecked(True)
        
        if self.active_filter != category:
            self.active_filter = category
            self.filter_changed.emit(category)

    def on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        self.result_clicked.emit(data)

    def display_results(self, results):
        self.results_list.clear()
        self.image_workers = [] # Clear old workers
        
        if not results:
            self.status_label.setText("No results found.")
            return
            
        category_label = "" if self.active_filter == "All" else f" for {self.active_filter}"
        self.status_label.setText(f"Top results{category_label}")
        
        for res in results:
            list_item = QListWidgetItem(self.results_list)
            list_item.setData(Qt.UserRole, res)
            
            # Use TrackItemWidget for consistency
            widget = TrackItemWidget(res)
            list_item.setSizeHint(widget.sizeHint())
            self.results_list.setItemWidget(list_item, widget)
            
            thumb_url = res.get("thumbnail_url")
            if thumb_url:
                worker = ImageWorker(thumb_url, parent=self)
                worker.image_ready.connect(lambda p, _, w=widget: w.set_thumbnail(p))
                worker.start()
                self.image_workers.append(worker)

    def set_loading(self, query):
        self.results_list.clear()
        self.status_label.setText(f"Searching for '{query}'...")
