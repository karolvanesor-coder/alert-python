import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie, QRegion, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer

class RoundGifLabel(QLabel):
    def __init__(self, gif_path, size=300, border_color=QColor("yellow"), border_width=6):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(size, size)

        # 🎯 máscara circular
        circle = QRegion(0, 0, size, size, QRegion.Ellipse)
        self.setMask(circle)

        # 🎞️ GIF
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())
        self.setMovie(self.movie)
        self.movie.start()

        # 🎨 borde
        self.border_color = border_color
        self.border_width = border_width

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self.rect().adjusted(
            self.border_width//2,
            self.border_width//2,
            -self.border_width//2,
            -self.border_width//2
        ))

if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])

    app = QApplication([])

    size = 250
    label = RoundGifLabel(gif_path, size=size)

    # 📍 posición: esquina superior derecha
    screen = app.primaryScreen().geometry()
    x = screen.width() - size - 20
    y = 20
    label.move(x, y)

    label.show()

    # ⏱️ cerrar automáticamente
    QTimer.singleShot(duration * 1000, app.quit)

    app.exec_()
