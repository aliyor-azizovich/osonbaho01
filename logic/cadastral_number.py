from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox


class EnterCadastralNumberDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введите кадастровый номер")
        self.setFixedSize(300, 120)

        layout = QVBoxLayout(self)

        self.label = QLabel("Введите кадастровый номер:")
        layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_cadastral_number(self):
        return self.line_edit.text().strip()



from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QDialogButtonBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class EnterCaptchaDialog(QDialog):
    def __init__(self, captcha_image_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Введите капчу")
        self.setFixedSize(300, 300)

        layout = QVBoxLayout(self)

        self.label = QLabel("Введите текст с картинки:")
        layout.addWidget(self.label)

        # Показываем изображение капчи
        self.captcha_label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(captcha_image_data)
        self.captcha_label.setPixmap(pixmap)
        self.captcha_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.captcha_label)

        # Поле для ввода капчи
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Введите капчу...")
        layout.addWidget(self.line_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def get_captcha_text(self):
        return self.line_edit.text().strip()
