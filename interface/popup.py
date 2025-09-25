import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QMovie, QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer

# 📺 Popup con GIF + borde sobrio
class GifPopup(QWidget):
    def __init__(self, gif_path, duration,
                 width=2000, height=1000,
                 border_color=QColor("#B71C1C"), border_width=6, border_radius=10):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(width, height)

        # 🎬 GIF centrado
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)
        self.gif_label = QLabel()
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())  # ocupa todo
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        # 🎨 Configuración de borde
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

        # ⏱ cierre automático
        QTimer.singleShot(duration * 1000, self.close)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Borde rojo sobrio
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        rect = self.rect().adjusted(
            self.border_width // 2,
            self.border_width // 2,
            -self.border_width // 2,
            -self.border_width // 2
        )
        painter.drawRoundedRect(rect, self.border_radius, self.border_radius)

# 📝 Popup de mensaje sobrio
class MessagePopup(QWidget):
    def __init__(self, message, duration, width=2010, height=200):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: rgba(20, 20, 20, 230); border: 3px solid #B71C1C; border-radius: 10px;")
        self.resize(width, height)

        layout = QVBoxLayout(self)
        text_label = QLabel(message)
        text_label.setFont(QFont("Segoe UI", 22, QFont.Medium))
        text_label.setStyleSheet("color: white; background: transparent;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        QTimer.singleShot(duration * 1000, self.close)

if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])
    message = sys.argv[3] if len(sys.argv) > 3 else "⚠️ Alerta detectada"

    app = QApplication([])

    # popup GIF
    gif_popup = GifPopup(gif_path, duration)
    screen = app.primaryScreen().geometry()
    gif_x = (screen.width() - gif_popup.width()) // 2
    gif_y = (screen.height() - gif_popup.height()) // 2 - 150
    gif_popup.move(gif_x, gif_y)

    # popup mensaje (debajo del GIF)
    msg_popup = MessagePopup(message, duration)
    msg_x = (screen.width() - msg_popup.width()) // 2
    msg_y = gif_y + gif_popup.height() + 25
    msg_popup.move(msg_x, msg_y)

    gif_popup.show()
    msg_popup.show()

    app.exec_()
