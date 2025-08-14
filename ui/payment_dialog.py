from PyQt5.QtWidgets import QDialog, QPushButton, QVBoxLayout, QLabel, QMessageBox, QCheckBox
import json
import os
from PyQt5 import uic
from logic.paths import get_ui_path
from PyQt5.QtGui import QIcon
import webbrowser
import webbrowser
from datetime import datetime
from logic.license_checker import get_client_id

class PaymaentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("payment_dialog.ui"), self)

        self.setWindowIcon(QIcon("icon.ico")) 
        self.setWindowTitle("Приобретение подписки")

        self.setWindowTitle("Оплатите подписку")
        self.setMinimumWidth(300)

        
        self.checkBox_year = self.findChild(QCheckBox, "checkBox_year")
        self.checkBox_month = self.findChild(QCheckBox, "checkBox_month")
        self.checkBox_day = self.findChild(QCheckBox, "checkBox_day")
        
        self.pushButton_click = self.findChild(QPushButton, "pushButton_click")
        self.pushButton_click.clicked.connect(self.real_click_payment)

        self.pushButton_bank = self.findChild(QPushButton, "pushButton_bank")

       

        self.checkboxes = [self.checkBox_year, self.checkBox_month, self.checkBox_day]

        self.paid = False
        self.checkBox_year.clicked.connect(self.single_selection) 
        self.checkBox_month.clicked.connect(self.single_selection) 
        self.checkBox_day.clicked.connect(self.single_selection) 
        self.pushButton_bank.clicked.connect(lambda: webbrowser.open("https://t.me/a_azizovich"))
        self.client_id = get_client_id()

    def setup_connections(self):
        self.pushButton_bank.clicked.connect(self.open_telegram_chat)

    def open_telegram_chat(self):
        url = "https://t.me/a_azizovich"
        webbrowser.open(url)

    def single_selection(self):
        """Обеспечиваем выбор только одного чекбокса"""
        sender = self.sender()
        for cb in self.checkboxes:
            if cb != sender:
                cb.setChecked(False)




   

    def real_click_payment(self):
        amount = 0
        period = ""
        if self.checkBox_day.isChecked():
            amount = 9375  # пример
            period = "day"
        elif self.checkBox_month.isChecked():
            amount = 187500
            period = "month"
        elif self.checkBox_year.isChecked():
            amount = 2062500
            period = "year"
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите вариант подписки.")
            return

        date_str = datetime.now().strftime("%Y%m%d")
        self.short_client_id = self.client_id[:40]  # обрезаем до 40 символов
        transaction_param = f"{period}_{self.short_client_id}"
        url = (
            f"https://my.click.uz/services/pay"
            f"?service_id=75611"
            f"&merchant_id=41279"
            f"&amount={amount}"
            f"&transaction_param={transaction_param}"
        )
        print(len(transaction_param))
        webbrowser.open(url)
        # QMessageBox.information(self, "Оплата", "Ссылка для оплаты открыта в браузере.")
        # self.paid = False
        self.accept()
 