from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt

class LoadingDialog(QDialog):
    def __init__(self, message="Загрузка...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Пожалуйста, подождите")
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        layout = QVBoxLayout()
        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.setLayout(layout)
        self.resize(300, 100)
