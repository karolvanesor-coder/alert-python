import sys
import random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtGui import QMovie, QPainter, QColor, QPen, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QTimer, QPointF

# ⚡ Clase chispa decorativa
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

# 📺 Popup con GIF + chispas
class GifWithSparks(QWidget):
    def __init__(self, gif_path, width, height,
                 border_color=QColor("red"), border_width=20, border_radius=0):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(width, height)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(0)

        self.gif_label = QLabel()
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(self.size())
        self.gif_label.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        self.sparks = []
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)
        self.timer.start(50)

    def update_particles(self):
        if random.random() < 0.5:
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                x = random.randint(0, self.width()); y = 0
            elif side == "bottom":
                x = random.randint(0, self.width()); y = self.height()
            elif side == "left":
                x = 0; y = random.randint(0, self.height())
            else:
                x = self.width(); y = random.randint(0, self.height())
            self.sparks.append(Spark(x, y))
        self.sparks = [s for s in self.sparks if s.update()]
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(self.border_color, self.border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        rect = self.rect().adjusted(
            self.border_width // 2,
            self.border_width // 2,
            -self.border_width // 2,
            -self.border_width // 2
        )
        painter.drawRect(rect)
        for spark in self.sparks:
            painter.setPen(Qt.NoPen)
            painter.setBrush(spark.color)
            painter.drawEllipse(spark.pos, spark.size, spark.size)

# 📝 Popup de mensaje
class MessagePopup(QWidget):
    def __init__(self, message, width, height):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: black; border-radius: 20px;")
        self.init_ui(message, width, height)

    def init_ui(self, message, width, height):
        from PyQt5.QtWidgets import QScrollArea

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(10)

        label = QLabel(message)
        label.setFont(QFont("Arial", 18, QFont.Bold))
        label.setStyleSheet("color: white; background: transparent;")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        scroll.setWidget(label)

        layout.addWidget(scroll)

        # ✅ Cálculo dinámico
        fm = QFontMetrics(label.font())
        text_height = fm.boundingRect(0, 0, width - 80, 0, Qt.TextWordWrap, message).height()
        base_height = text_height + 80

        # ✅ Limite para evitar desborde
        max_height = int(height)

        final_height = min(max(200, base_height), max_height)

        self.resize(width, final_height)

# 🚀 Ejecución principal (sincronizada)
if __name__ == "__main__":
    gif_path = sys.argv[1]
    duration = int(sys.argv[2])
    message = sys.argv[3] if len(sys.argv) > 3 else "⚠️ Alerta"
    border_color = sys.argv[4] if len(sys.argv) > 4 else "red"

    app = QApplication([])
    screen = app.primaryScreen().geometry()

    gif_width = int(screen.width() * 0.7)
    gif_height = int(screen.height() * 0.5)
    msg_width = gif_width + 30
    msg_height = int(screen.height() * 0.2)

    gif_popup = GifWithSparks(gif_path, gif_width, gif_height, border_color=QColor(border_color))
    gif_x = (screen.width() - gif_width) // 2
    gif_y = (screen.height() - (gif_height + msg_height + 50)) // 2
    gif_popup.move(gif_x, gif_y)

    msg_popup = MessagePopup(message, msg_width, msg_height)
    msg_x = gif_x - 1
    msg_y = gif_y + gif_height + 30
    msg_popup.move(msg_x, msg_y)

    gif_popup.show()
    msg_popup.show()

    # 💡 Ambos se cierran exactamente juntos
    def close_both():
        gif_popup.close()
        msg_popup.close()

    QTimer.singleShot(duration * 1000, close_both)
    app.exec_()
