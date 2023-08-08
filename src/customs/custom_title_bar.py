from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt


class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.mouse_pos = None
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel("Andus Launcher")
        self.title_label.setFont(QFont("Roboto", 16, weight=QFont.Bold))
        self.layout.addWidget(self.title_label)
        self.layout.addStretch(1)

        self.minimize_button = QPushButton("-")
        self.minimize_button.clicked.connect(self.parent.showMinimized)
        self.layout.addWidget(self.minimize_button)
        self.close_button = QPushButton("X")
        self.close_button.clicked.connect(self.parent.close)
        self.layout.addWidget(self.close_button)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #222")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.mouse_pos = event.globalPos() - self.parent.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.mouse_pos:
            self.parent.move(event.globalPos() - self.mouse_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.mouse_pos = None