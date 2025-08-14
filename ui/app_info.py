from PyQt5.QtWidgets import QDialog, QPushButton, QLabel, QMessageBox
from PyQt5.uic import loadUi
from logic.license_checker import get_client_id, get_public_id
from PyQt5.QtWidgets import QApplication

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        loadUi("ui/dialog_about_user.ui", self)  # путь к твоему .ui файлу

        # Получение виджетов из UI
        self.pushButton_copy_id: QPushButton = self.findChild(QPushButton, "pushButton_copy_id")
        self.pushButton_ok: QPushButton = self.findChild(QPushButton, "pushButton_ok")
        self.label_public_id: QLabel = self.findChild(QLabel, "label_public_id")

        self.fill_info()

        # Сигналы
        self.pushButton_copy_id.clicked.connect(self.copy_id_to_clipboard)
        self.pushButton_ok.clicked.connect(self.accept)

    def fill_info(self):
        client_id = get_client_id()
        self.public_id = get_public_id(client_id)
        self.label_public_id.setText(f"ID для поддержки: {self.public_id}")

    def copy_id_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.public_id)
        QMessageBox.information(self, "Скопировано", "ID скопирован в буфер обмена.")

