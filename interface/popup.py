import sys
import random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QMovie, QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, QPointF

# ⚡ Clase chispa
class Spark:
    def __init__(self, x, y):
        self.pos = QPointF(x, y)
        self.vel = QPointF(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5))
        self.life = random.randint(20, 60)
        self.size = random.randint(4, 8)
        self.color = QColor(random.choice(["yellow", "orange", "red"]))

    def update(self):
        self.pos += self.vel
        self.life -= 1
        alpha = max(0, int(255 * (self.life / 60)))
        self.color.setAlpha(alpha)
        return self.life > 0

# 📺 Popup con GIF + borde + chispas
class GifWithSparks(QWidget):
    def __init__(self, gif_path, duration,
                 width=2000, height=1000,
                 border_color=QColor("orange"), border_width=20, border_radius=0):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(width, height)

        # 🎬 GIF
        layout = QVBoxLayout(self)
        self.gif_label = QLabel()
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        # ⚡ partículas
        self.sparks = []
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

        # ⏱ animación de partículas
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)

        # ⏱ cierre automático
        QTimer.singleShot(duration * 1000, self.close)

    def update_particles(self):
        if random.random() < 0.5:
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                x = random.randint(0, self.width())
                y = 0
            elif side == "bottom":
                x = random.randint(0, self.width())
                y = self.height()
            elif side == "left":
                x = 0
                y = random.randint(0, self.height())
            else:
                x = self.width()
                y = random.randint(0, self.height())
            self.sparks.append(Spark(x, y))

        self.sparks = [s for s in self.sparks if s.update()]
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 🎨 borde
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

        # ⚡ chispas
        for spark in self.sparks:
            painter.setPen(Qt.NoPen)
            painter.setBrush(spark.color)
            painter.drawEllipse(spark.pos, spark.size, spark.size)

# 📝 Ventana de mensaje separada
class MessagePopup(QWidget):
    def __init__(self, message, duration, width=2050, height=200):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: white; border: 5px solid red; border-radius: 20px;")
        self.resize(width, height)

        layout = QVBoxLayout(self)
        text_label = QLabel(message)
        text_label.setFont(QFont("Arial", 20, QFont.Bold))
        text_label.setStyleSheet("color: #B22222; background: transparent;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        QTimer.singleShot(duration * 1000, self.close)

if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])
    message = sys.argv[3] if len(sys.argv) > 3 else "⚠️ Alerta"

    app = QApplication([])

    # popup GIF
    gif_popup = GifWithSparks(gif_path, duration)
    screen = app.primaryScreen().geometry()
    gif_x = (screen.width() - gif_popup.width()) // 2
    gif_y = (screen.height() - gif_popup.height()) // 2 - 150
    gif_popup.move(gif_x, gif_y)

    # popup mensaje (debajo del GIF)
    msg_popup = MessagePopup(message, duration)
    msg_x = (screen.width() - msg_popup.width()) // 2 + 30
    msg_y = gif_y + gif_popup.height() + 80  # debajo del GIF
    msg_popup.move(msg_x, msg_y)

    gif_popup.show()
    msg_popup.show()

    app.exec_()
