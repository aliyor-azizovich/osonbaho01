from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QFileDialog
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

import os
import sys
from logic.paths import get_reports_templates_dir

from logic.data_entry import DataEntryForm
from selenium import webdriver
import shutil
import json
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from logic.paths import get_ui_path, get_project_dir
from logic.paths import get_base_dir

import re


class AppraiserCompanyInfo(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("appraiser_company_info.ui"), self)

        

        self.main_window = main_window
        self.save_dir = os.path.join(get_project_dir(), "company_data")
        os.makedirs(self.save_dir, exist_ok=True)
        self.setWindowTitle("Оценочная организация")
        
        self.setWindowIcon(QIcon("icon.ico"))  
        
        self.pushButton_registration = self.findChild(QPushButton, "pushButton_registration")
        self.pushButton_load_insurance = self.findChild(QPushButton, "pushButton_load_insurance")
        self.pushButton_load_license = self.findChild(QPushButton, "pushButton_load_license")
        self.pushButton_load_license.clicked.connect(self.upload_license)
        self.pushButton_load_insurance.clicked.connect(self.upload_insurance)
        self.pushButton_registration.clicked.connect(self.upload_registration)


        self.pushButton_load_logo = self.findChild(QPushButton, "pushButton_load_logo")
        self.pushButton_load_logo.clicked.connect(self.upload_logo)


        self.pushButton_ok = self.findChild(QPushButton, "pushButton_ok")
        self.pushButton_ok.clicked.connect(self.accept_dialog)


        self.lineEdit_bank_account = self.findChild(QLineEdit, "lineEdit_bank_account")
        self.lineEdit_MFO = self.findChild(QLineEdit, "lineEdit_MFO")
        self.lineEdit_bank = self.findChild(QLineEdit, "lineEdit_bank")
        self.lineEdit_incurance_date = self.findChild(QLineEdit, "lineEdit_incurance_date")
        self.lineEdit_insurance_number = self.findChild(QLineEdit, "lineEdit_insurance_number")
        self.lineEdit_insurance_name = self.findChild(QLineEdit, "lineEdit_insurance_name")
        self.lineEdit_license_date = self.findChild(QLineEdit, "lineEdit_license_date")
        self.lineEdit_license_number = self.findChild(QLineEdit, "lineEdit_license_number")
        self.lineEdit_adress = self.findChild(QLineEdit, "lineEdit_adress")
        self.lineEdit_INN = self.findChild(QLineEdit, "lineEdit_INN")
        self.lineEdit_company_name = self.findChild(QLineEdit, "lineEdit_company_name")

        self.load_lineedit_data_from_settings()

        self.line_edits = [
        self.lineEdit_company_name,
        self.lineEdit_INN,
        self.lineEdit_adress,
        self.lineEdit_license_number,
        self.lineEdit_license_date,
        self.lineEdit_insurance_name,
        self.lineEdit_insurance_number,
        self.lineEdit_incurance_date,
        self.lineEdit_bank,
        self.lineEdit_MFO,
        self.lineEdit_bank_account
        
    ]

        # Устанавливаем фильтр событий для каждого
        for line_edit in self.line_edits:
            line_edit.installEventFilter(self)


    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Down):
                self.focus_next_lineedit(obj)
                return True
            elif event.key() == Qt.Key_Up:
                self.focus_prev_lineedit(obj)
                return True
        return super().eventFilter(obj, event)


    def focus_next_lineedit(self, current):
        try:
            index = self.line_edits.index(current)
            if index + 1 < len(self.line_edits):
                self.line_edits[index + 1].setFocus()
        except ValueError:
            pass

    def focus_prev_lineedit(self, current):
        try:
            index = self.line_edits.index(current)
            if index > 0:
                self.line_edits[index - 1].setFocus()
        except ValueError:
            pass


    def accept_dialog(self):
        lines = [
            self.lineEdit_bank_account, self.lineEdit_MFO, self.lineEdit_bank, self.lineEdit_incurance_date,
            self.lineEdit_insurance_number, self.lineEdit_insurance_name, self.lineEdit_license_date,
            self.lineEdit_license_number, self.lineEdit_adress, self.lineEdit_INN, self.lineEdit_company_name
        ]

        for c in lines:
            if not c.text().strip():
                QMessageBox.warning(self, "Ошибка", "Вы не заполнили все поля")
                return 
        
        self.save_lineedit_data_to_settings()
        
       
        self.accept()

        
    


    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл логтипа",
            "",
            "Изображения (*.jpg *.jpeg *.png)"
        )

        if not file_path:
            return

        try:
            save_dir = self.save_dir

                                  
            report_folder = os.path.join(save_dir)
            os.makedirs(report_folder, exist_ok=True)

            _, new_ext = os.path.splitext(file_path)
            new_ext = new_ext.lower()
            if new_ext not in ['.jpg', '.jpeg', '.png']:
                QMessageBox.warning(self, "Неверный формат", "Поддерживаются только JPG, JPEG и PNG файлы.")
                return

            base_filename = f"company_logo"

            for ext in ['.jpg', '.jpeg', '.png']:
                existing_file = os.path.join(report_folder, base_filename + ext)
                if os.path.exists(existing_file) and ext != new_ext:
                    os.remove(existing_file)

            target_path = os.path.join(report_folder, base_filename + new_ext)
            shutil.copy(file_path, target_path)

            QMessageBox.information(self, "Успех", "Логотип успешно загружен.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла: {str(e)}")






    def _upload_document(self, title, filename, button):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            "Документы (*.doc *.docx *.pdf *.jpg *.jpeg *.png)"
        )

        if not file_path:
            return

        try:
            save_dir = self.save_dir


            report_folder = os.path.join(save_dir)
            os.makedirs(report_folder, exist_ok=True)

            _, new_ext = os.path.splitext(file_path)
            new_ext = new_ext.lower()
            if new_ext not in [".doc", ".docx", ".pdf", ".jpg", ".jpeg", ".png"]:
                QMessageBox.warning(self, "Неверный формат", "Поддерживаются только PDF, JPG, JPEG и PNG файлы.")
                return

            # Удаляем старые версии документа с другим расширением
            for ext in [".doc", ".docx", ".pdf", ".jpg", ".jpeg", ".png"]:
                existing_file = os.path.join(report_folder, filename + ext)
                if os.path.exists(existing_file) and ext != new_ext:
                    os.remove(existing_file)

            target_path = os.path.join(report_folder, filename + new_ext)
            shutil.copy(file_path, target_path)

            QMessageBox.information(self, "Успех", f"Файл «{filename}» успешно загружен.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла: {str(e)}")


    def upload_license(self):
        self._upload_document(
            title="Выберите файл лицензии",
            filename="company_license",
            button=self.pushButton_load_license
        )

    def upload_insurance(self):
        self._upload_document(
            title="Выберите файл страхового полиса",
            filename="company_insurance",
            button=self.pushButton_load_insurance
        )

    def upload_registration(self):
        self._upload_document(
            title="Выберите файл свидетельства о регистрации",
            filename="company_registration",
            button=self.pushButton_registration
        )


    


    def save_lineedit_data_to_settings(self):
        settings_path = self.get_settings_path()

        # Собираем данные
        data = {
            "valuator_company_name": self.lineEdit_company_name.text().strip(),
            "valuator_inn": self.lineEdit_INN.text().strip(),
            "valuator_address": self.lineEdit_adress.text().strip(),
            "bank": self.lineEdit_bank.text().strip(),
            "mfo": self.lineEdit_MFO.text().strip(),
            "bank_account": self.lineEdit_bank_account.text().strip(),
            "insurance_number": self.lineEdit_insurance_number.text().strip(),
            "insurance_name": self.lineEdit_insurance_name.text().strip(),
            "insurance_date": self.lineEdit_incurance_date.text().strip(),
            "license_number": self.lineEdit_license_number.text().strip(),
            "license_date": self.lineEdit_license_date.text().strip()
        }

        # Загружаем старые настройки (если есть)
        settings = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except Exception:
                pass

        # Обновляем и сохраняем
        settings.update(data)

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)


    def load_lineedit_data_from_settings(self):
        settings_path = self.get_settings_path()
        if not os.path.exists(settings_path):
            return

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            self.lineEdit_company_name.setText(settings.get("valuator_company_name", ""))
            self.lineEdit_INN.setText(settings.get("valuator_inn", ""))
            self.lineEdit_adress.setText(settings.get("valuator_address", ""))
            self.lineEdit_bank.setText(settings.get("bank", ""))
            self.lineEdit_MFO.setText(settings.get("mfo", ""))
            self.lineEdit_bank_account.setText(settings.get("bank_account", ""))
            self.lineEdit_insurance_number.setText(settings.get("insurance_number", ""))
            self.lineEdit_insurance_name.setText(settings.get("insurance_name", ""))
            self.lineEdit_incurance_date.setText(settings.get("insurance_date", ""))
            self.lineEdit_license_number.setText(settings.get("license_number", ""))
            self.lineEdit_license_date.setText(settings.get("license_date", ""))
        except Exception:
            pass


    def get_settings_path(self):
        
        base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "OsonBaho")  # Или другое имя
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "settings.json")


    # ВСТАВКА ЛОГТИПА В ВОРД

    def generate_docx_with_logo(self):
        try:
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            template_path = self.resource_path("reports/report_sh.docx")
            result_path = os.path.join(get_reports_templates_dir(), "result.docx")
            save_dir = self.save_dir

            if not os.path.exists(template_path):
                QMessageBox.warning(self, "Ошибка", "Шаблон report_sh.docx не найден.")
                return

            # Ищем файл логотипа с любым допустимым расширением
            logo_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                path = os.path.join(save_dir, f"company_logo{ext}")
                if os.path.exists(path):
                    logo_path = path
                    break

            if not logo_path:
                QMessageBox.warning(self, "Ошибка", "Логотип не найден. Убедитесь, что он загружен (PNG, JPG, JPEG).")
                return

            # Пропускаем, если файл уже сгенерирован
            if os.path.exists(result_path):
                return

            # Генерация документа
            doc = DocxTemplate(template_path)
            logo_img = InlineImage(doc, logo_path, width=Mm(40))

            context = {
                "company_logo": logo_img
            }

            doc.render(context)
            doc.save(result_path)

            print("[INFO] Итоговый .docx с логотипом создан.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать .docx файл: {str(e)}")


   

    def resource_path(self, relative_path):
        return os.path.join(get_base_dir(), relative_path)

    

    def generate_docx_report(self):
        try:
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            template_path = self.resource_path("reports/report_sh.docx")
            result_path = os.path.join(get_reports_templates_dir(), "result.docx")
            save_dir = self.save_dir
            settings_path = self.get_settings_path()

            if not os.path.exists(template_path):
                QMessageBox.warning(self, "Ошибка", "Шаблон report_sh.docx не найден.")
                return

            if not os.path.exists(settings_path):
                QMessageBox.warning(self, "Ошибка", "Файл настроек settings.json не найден.")
                return

            # Ищем логотип
            logo_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                path = os.path.join(save_dir, f"company_logo{ext}")
                if os.path.exists(path):
                    logo_path = path
                    break

            if not logo_path:
                QMessageBox.warning(self, "Ошибка", "Логотип не найден. Убедитесь, что он загружен.")
                return

            # Загружаем настройки
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            # Формируем общий контекст
            doc = DocxTemplate(template_path)
            context = {
                "company_logo": InlineImage(doc, logo_path, width=Mm(40)),
                "valuator_company_name": settings.get("valuator_company_name", ""),
                "valuator_inn": settings.get("valuator_inn", ""),
                "valuator_address": settings.get("valuator_address", ""),
                "bank": settings.get("bank", ""),
                "mfo": settings.get("mfo", ""),
                "bank_account": settings.get("bank_account", ""),
                "insurance_number": settings.get("insurance_number", ""),
                "insurance_name": settings.get("insurance_name", ""),
                "insurance_date": settings.get("insurance_date", ""),
                "license_number": settings.get("license_number", ""),
                "license_date": settings.get("license_date", "")
            }

            
            doc.save(result_path)
            print("[INFO] Итоговый .docx с логотипом и реквизитами создан.")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании .docx файла: {str(e)}")
