import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt, QTimer

gif_path = sys.argv[1]
duration = int(sys.argv[2])

app = QApplication([])

label = QLabel()
label.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)  # arriba y sin bordes
label.setAttribute(Qt.WA_TranslucentBackground)

movie = QMovie(gif_path)
label.setMovie(movie)
movie.start()
label.show()

# ⏱️ cerrar automáticamente
QTimer.singleShot(duration * 1000, app.quit)

app.exec_()
