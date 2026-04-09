from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFontMetrics

class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(10) # Minimum readable width
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        # Elide text based on current width
        elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        # Preserve vertical alignment
        # We use the label's existing alignment flags
        painter.drawText(self.rect(), self.alignment() | Qt.TextSingleLine, elided)
