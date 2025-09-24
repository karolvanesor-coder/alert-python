import sys
import random
import math
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QTimer, QPointF

class Spark:
    def __init__(self, x, y):
        self.pos = QPointF(x, y)
        self.vel = QPointF(random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5))
        self.life = random.randint(20, 60)  # duración en frames
        self.size = random.randint(4, 8)
        self.color = QColor(random.choice(["yellow", "orange", "red"]))

    def update(self):
        self.pos += self.vel
        self.life -= 1
        alpha = max(0, int(255 * (self.life / 60)))
        self.color.setAlpha(alpha)
        return self.life > 0

class GifWithSparks(QLabel):
    def __init__(self, gif_path, width=1200, height=700, border_color=QColor("orange"), border_width=10, border_radius=50):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(width, height)

        # 🎬 GIF rectangular
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())
        self.setMovie(self.movie)
        self.movie.start()

        # ⚡ partículas
        self.sparks = []

        # 🎨 borde
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

        # ⏱ animación de partículas
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)  # ~20 FPS

    def update_particles(self):
        # generar chispas en los bordes del rectángulo
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
            else:  # right
                x = self.width()
                y = random.randint(0, self.height())
            self.sparks.append(Spark(x, y))

        # actualizar partículas existentes
        self.sparks = [s for s in self.sparks if s.update()]
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 🎨 borde con esquinas redondeadas
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

        # ⚡ dibujar chispas
        for spark in self.sparks:
            painter.setPen(Qt.NoPen)
            painter.setBrush(spark.color)
            painter.drawEllipse(spark.pos, spark.size, spark.size)

if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])

    app = QApplication([])

    # 📏 dimensiones rectangulares grandes
    width, height = 1600, 900
    label = GifWithSparks(
        gif_path,
        width=width,
        height=height,
        border_color=QColor("orange"),
        border_width=20,
        border_radius=70
    )

    # 📍 centrar en la pantalla
    screen = app.primaryScreen().geometry()
    x = (screen.width() - width) // 2
    y = (screen.height() - height) // 2
    label.move(x, y)

    label.show()

    # ⏱ cerrar automáticamente
    QTimer.singleShot(duration * 1000, app.quit)

    app.exec_()
