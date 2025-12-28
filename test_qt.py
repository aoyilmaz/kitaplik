from PyQt6.QtWidgets import QApplication, QLabel
import sys

app = QApplication(sys.argv)
label = QLabel("Merhaba!")
label.show()
sys.exit(app.exec())