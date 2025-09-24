import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QMovie, QFont
from PyQt5.QtCore import Qt, QTimer

class GifPopup(QWidget):
    def __init__(self, gif_path, duration, message):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout()

        # GIF
        gif_label = QLabel()
        movie = QMovie(gif_path)
        gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(gif_label, alignment=Qt.AlignCenter)

        # Mensaje
        text_label = QLabel(message)
        text_label.setFont(QFont("Arial", 24, QFont.Bold))
        text_label.setStyleSheet("color: red;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        self.setLayout(layout)
        self.resize(1000, 700)

        # Cerrar automático
        QTimer.singleShot(duration * 1000, self.close)

if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])
    message = sys.argv[3] if len(sys.argv) > 3 else "⚠️ Alerta"

    app = QApplication([])
    popup = GifPopup(gif_path, duration, message)
    popup.show()
    app.exec_()
