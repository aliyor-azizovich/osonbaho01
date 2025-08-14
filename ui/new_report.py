
import os
from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLineEdit, QDateEdit, QMessageBox, QCheckBox
from PyQt5.QtCore import QDate
from .valuation_main import ValuationMainWindow
from logic.paths import get_project_dir, get_ui_path

class NewReportWindow(QDialog):
    def __init__(self, main_window):
        super().__init__()
        ui_path = get_ui_path("newReport.ui")
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"Файл {ui_path} не найден!")
        uic.loadUi(ui_path, self)
        self.setWindowIcon(QIcon("icon.ico")) 
        self.setWindowTitle("Создание нового отчёта оценки")

        self.main_window = main_window

        self.report_number_input = self.findChild(QLineEdit, "NumberEdit")
        self.report_number_input.setVisible(False)
        self.report_date_input = self.findChild(QDateEdit, "dateEdit")
        self.button_box = self.findChild(QDialogButtonBox, "OkNotButton")
        self.checkBox_valuate_object = self.findChild(QCheckBox, "checkBox_valuate_object")
        self.checkBox_valuate_object.setChecked(True)
        if not self.report_number_input or not self.report_date_input or not self.button_box:
            raise AttributeError("Отсутствуют элементы интерфейса. Проверьте объектные имена в Qt Designer.")

        last_report_number = self.main_window.get_last_report_number()
        self.report_number_input.setText(str(last_report_number))
        self.report_date_input.setDate(QDate.currentDate())

        self.button_box.accepted.connect(self.create_new_report)
        self.button_box.rejected.connect(self.close)

    def create_new_report(self):
        report_number = self.report_number_input.text()
        report_date = self.report_date_input.date().toString("dd/MM/yyyy")
        last_change_date = QDate.currentDate().toString("dd/MM/yyyy")
        
        # Временно записываем пустые данные
        owner_name = "Не указан"
        buyer_name = "Не указан"
        adress = "Не указан"
        valuated_price = "Не указан"
        reg_number = 'Не указан'
        report_data = {
            "report_number": report_number,
            'reg_number': reg_number,
            "report_date": report_date,
            "last_change_date": last_change_date,
            "owner_name": owner_name,
            "buyer_name": buyer_name,
            "adress": adress,
            "valuated_price": valuated_price            
        }

        # Добавляем отчёт в реестр через главное окно
        self.main_window.add_report_to_registry(report_number, reg_number, report_date, owner_name, buyer_name, adress, valuation_cost="Оценка не окончена")

    # Создаём пустой файл отчёта через менеджер
        self.main_window.report_manager.create_report_file(reg_number)
        if hasattr(self.main_window, "save_directory") and self.main_window.save_directory:
            report_folder = os.path.join(self.main_window.save_directory, reg_number)
            os.makedirs(report_folder, exist_ok=True)
           
        self.accept()

        # Открываем окно ValuationMainWindow
        self.valuation_window = ValuationMainWindow(self.main_window, report_number)
        self.valuation_window.show()
        self.close()

