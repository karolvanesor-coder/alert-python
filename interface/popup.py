import sys
import random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QFrame
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

# 📺 Popup con GIF + borde + chispas + mensaje separado
class GifWithSparks(QWidget):
    def __init__(self, gif_path, duration, message,
                 width=2400, height=1350,
                 border_color=QColor("orange"), border_width=20, border_radius=0):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(width, height)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 🎬 GIF con borde y chispas
        self.gif_label = QLabel()
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        # 📝 Mensaje en un recuadro naranja
        self.message_box = QFrame()
        self.message_box.setStyleSheet("""
            QFrame {
                background-color: orange;
                border-radius: 20px;
                border: 6px solid black;
            }
        """)
        msg_layout = QVBoxLayout(self.message_box)
        msg_layout.setContentsMargins(20, 10, 20, 10)

        self.text_label = QLabel(message)
        self.text_label.setFont(QFont("Arial", 40, QFont.Bold))
        self.text_label.setStyleSheet("color: black;")  # Texto negro sobre naranja
        self.text_label.setAlignment(Qt.AlignCenter)
        msg_layout.addWidget(self.text_label)

        layout.addWidget(self.message_box, alignment=Qt.AlignCenter)

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
        # generar chispas en bordes
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

        # 🎨 borde rectangular principal
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

if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])
    message = sys.argv[3] if len(sys.argv) > 3 else "⚠️ Alerta"

    app = QApplication([])

    width, height = 2400, 1350
    popup = GifWithSparks(gif_path, duration, message, width, height)

    # 📍 centrar pantalla
    screen = app.primaryScreen().geometry()
    x = (screen.width() - width) // 2
    y = (screen.height() - height) // 2
    popup.move(x, y)

    popup.show()
    app.exec_()
