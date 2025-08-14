from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QFileDialog
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os
import sys

from logic.data_entry import DataEntryForm
from selenium import webdriver
import shutil
import json
from docx.shared import Mm
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from jinja2 import DebugUndefined, Environment
import json
import os
import re
from logic.paths import get_ui_path, get_project_dir
from logic.paths import get_base_dir
from logic.paths import get_reports_templates_dir
from PyQt5.QtGui import QIcon


class AppraiserManInfo(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("appraiser_man_info.ui"), self)
        self.setWindowTitle("Оценщик")
        
        self.setWindowIcon(QIcon("icon.ico"))  
        

        self.main_window = main_window
      
        self.save_dir = os.path.join(get_project_dir(), "company_data")
        os.makedirs(self.save_dir, exist_ok=True)

        self.pushButton_load_sertificate = self.findChild(QPushButton, "pushButton_load_sertificate")
        self.pushButton_load_sertificate.clicked.connect(self.upload_certificate)


        self.pushButton_ok = self.findChild(QPushButton, "pushButton_ok")
        self.pushButton_ok.clicked.connect(self.accept_dialog)


        self.lineEdit_surname = self.findChild(QLineEdit, "lineEdit_surname")
        self.lineEdit_name = self.findChild(QLineEdit, "lineEdit_name")
       
        self.lineEdit_sertificate_number = self.findChild(QLineEdit, "lineEdit_sertificate_number")
        self.lineEdit_sertificate_date = self.findChild(QLineEdit, "lineEdit_sertificate_date")
        

        self.load_lineedit_data_from_settings()
        # Упорядоченный список всех QLineEdit
        self.line_edits = [
            self.lineEdit_surname,
            self.lineEdit_name,
            self.lineEdit_sertificate_number,
            self.lineEdit_sertificate_date
        ]

        # Установка фильтра событий
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

    def get_settings_path(self):
        import os
        base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "OsonBaho")  # Или другое имя
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "settings.json")


    def accept_dialog(self):
        lines = [
            self.lineEdit_surname, self.lineEdit_name, self.lineEdit_sertificate_number, self.lineEdit_sertificate_date]

        for c in lines:
            if not c.text().strip():
                QMessageBox.warning(self, "Ошибка", "Вы не заполнили все поля")
                return 
        
        self.save_lineedit_data_to_settings()
        
        self.generate_final_docx_report()
        # После сохранения данных, перед self.accept()
        if not getattr(self.main_window, "save_directory", ""):
            QMessageBox.information(self, "Путь сохранения", "Сейчас выберите папку, в которую будут сохраняться отчёты.")
            self.main_window.select_save_directory()

        self.accept()

        
    


   





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


    def upload_certificate(self):
        self._upload_document(
            title="Выберите файл сертификата",
            filename="appraiser_sertificate",
            button=self.pushButton_load_sertificate
        )

  

    


    def save_lineedit_data_to_settings(self):
        settings_path = self.get_settings_path()

        name = self.lineEdit_name.text().strip()
        surname = self.lineEdit_surname.text().strip()

        # Собираем данные
        data = {
            "appraiser_name": name,
            "appraiser_surname": surname,
            "sertificate_number": self.lineEdit_sertificate_number.text().strip(),
            "sertificate_date": self.lineEdit_sertificate_date.text().strip(),
            "appraiser_cutted_name": f"{name[0]}. {surname}" if name and surname else ""
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




    # ВСТАВКА ЛОГТИПА В ВОРД

    
    

    def resource_path(self, relative_path):
        return os.path.join(get_base_dir(), relative_path)

    

   

    def generate_final_docx_report(self):
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

            # Загружаем настройки с реквизитами компании и оценщика
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            name = settings.get("appraiser_name", "").strip()
            surname = settings.get("appraiser_surname", "").strip()
            cutted_name = settings.get("appraiser_cutted_name", f"{name[0]}. {surname}" if name and surname else "")

            # Ищем логотип
            logo_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                logo_candidate = os.path.join(save_dir, f"company_logo{ext}")
                if os.path.exists(logo_candidate):
                    logo_path = logo_candidate
                    break
            env = Environment(undefined=DebugUndefined)
            doc = DocxTemplate(template_path)
            doc.env = env
            
            # Полный контекст
            context = {
                # --- Статичные данные (фирма и оценщик) ---
                "company_logo": (
                    InlineImage(doc, logo_path, width=Mm(40))
                    if logo_path and os.path.isfile(logo_path)
                    else "{{ company_logo }}"
                ),
                "valuator_company_name": settings.get("valuator_company_name", "{{ valuator_company_name }}"),
                "valuator_inn": settings.get("valuator_inn", "{{ valuator_inn }}"),
                "valuator_address": settings.get("valuator_address", "{{ valuator_address }}"),
                "bank": settings.get("bank", "{{ bank }}"),
                "mfo": settings.get("mfo", "{{ mfo }}"),
                "bank_account": settings.get("bank_account", "{{ bank_account }}"),
                "insurance_number": settings.get("insurance_number", "{{ insurance_number }}"),
                "insurance_name": settings.get("insurance_name", "{{ insurance_name }}"),
                "insurance_date": settings.get("insurance_date", "{{ insurance_date }}"),
                "license_number": settings.get("license_number", "{{ license_number }}"),
                "license_date": settings.get("license_date", "{{ license_date }}"),
                "appraiser_name": name or "{{ appraiser_name }}",
                "appraiser_surname": surname or "{{ appraiser_surname }}",
                "appraiser_cutted_name": cutted_name or "{{ appraiser_cutted_name }}",
                "sertificate_number": settings.get("sertificate_number", "{{ sertificate_number }}"),
                "sertificate_date": settings.get("sertificate_date", "{{ sertificate_date }}"),

                # --- Флаги переменных одного отчёта ---
                            "administrative": {
                    "oblast": "{{ administrative.oblast }}",
                    "rayon": "{{ administrative.rayon }}"
                },
                "report_number": "{{ report_number }}",
                "reg_number": "{{ reg_number }}",
                "contract_date": "{{ contract_date }}",
                "inspection_date": "{{ inspection_date }}",
                "valuation_date": "{{ valuation_date }}",  # если используешь отдельно
                "exchange_rate": "{{ exchange_rate }}",
                "address": "{{ address }}",
                "owner_name": "{{ owner_name }}",
                "valuation_purpose": "{{ valuation_purpose }}",
                "price_type": "{{ price_type }}",
                "buyer_type": "{{ buyer_type }}",
                "buyer_name": "{{ buyer_name }}",
                "buyer_passport_series": "{{ buyer_passport_series }}",
                "buyer_passport_number": "{{ buyer_passport_number }}",
                "buyer_address": "{{ buyer_address }}",
                "land_area": "{{ land_area }}",
                "total_area": "{{ total_area }}",
                "useful_area": "{{ useful_area }}",
                "living_area": "{{ living_area }}",
                "cadastral_number": "{{ cadastral_number }}",
                "profit": "{{ profit }}",
                "comparative_table": "[ comparative_table ]",
                "agreement_method_summary": "{{ agreement_method_summary }}",
                'agreement_table': "[ agreement_table ]",
                'koeff_table': "[ koeff_table ]",

                 "agreement": {
                    "method": "{{ agreement.method }}",
                    "use_cost": "{{ agreement.use_cost }}",
                    "use_comparative": "{{ agreement.use_comparative }}",
                    "cost_percent": "{{ agreement.cost_percent }}",
                    "comparative_percent": "{{ agreement.comparative_percent }}",
                    "final_cost": "{{ agreement.final_cost }}",
                    "edited_final_cost": "{{ agreement.edited_final_cost }}",
                    "amount_in_words": "{{ agreement.amount_in_words }}",
                    "building_cost": "{{ agreement.building_cost }}",
                    "land_cost": "{{ agreement.land_cost }}",
                    "total_cost_value": "{{ agreement.total_cost_value }}",
                    "comparative_final_cost_value": "{{ agreement.comparative_final_cost_value }}"
                },
                "TABLE_KADASTR": "{{ TABLE_KADASTR }}",
                "liters": [
                    {
                        "building_type": "{{ liter.building_type }}",
                        "replacement_cost": "{{ liter.replacement_cost }}",
                        "wear_price": "{{ liter.wear_price }}",
                        "final_cost": "{{ liter.final_cost }}",
                        "corrected_price": "{{ liter.corrected_price }}",
                        "unit": "{{ liter.unit }}",
                        "unit_type": "{{ liter.unit_type }}",
                        "reg_coeff": "{{ liter.reg_coeff }}",
                        "stat_coeff": "{{ liter.stat_coeff }}",
                        "developer_percent": "{{ liter.developer_percent }}",
                        "inconsistency": "{{ liter.inconsistency }}",
                        "wear_percent": "{{ liter.wear_percent }}",
                        "facade_corrected_price": "{{ liter.facade_corrected_price }}",
                        "height_corrected_price": "{{ liter.height_corrected_price }}",
                        "improvement_correction": "{{ liter.improvement_correction }}",
                        "deviation_correction": "{{ liter.deviation_correction }}",
                        "reg_coeff_type": "{{ liter.reg_coeff_type }}",
                        "facade_type": "{{ liter.facade_type }}",
                        "analog_description_html": "{{ liter.analog_description_html }}",
                        "analog_index": "{{ liter.analog_index }}",
                        "number": "{{ liter.number }}",
                        "measurements": {
                            "square": "{{ liter.measurements.square }}",
                            "height": "{{ liter.measurements.height }}",
                            "volume": "{{ liter.measurements.volume }}",
                            "length": "{{ liter.measurements.length }}",
                            "ukup_price_label": "{{ liter.measurements.ukup_price_label }}"
                            },
                            "filters": {
                                "Этажность": "{{ liter.filters.Этажность }}",
                                "Материал стен": "{{ liter.filters.Материал стен }}",
                                "Кровля": "{{ liter.filters.Кровля }}",
                                "Фундаменты": "{{ liter.filters.Фундаменты }}",
                                "Отделка": "{{ liter.filters.Отделка }}"
                            },
                            "structural_elements": [
                                {
                                    "Конструкции": "{{ se.Конструкции }}",
                                    "Доля %": "{{ se.Доля % }}",
                                    "Поправка к удельным весам %": "{{ se.Поправка к удельным весам % }}",
                                    "Физический износ %": "{{ se.Физический износ % }}"
                                }
                            ]
                        }
                    ],
                           "liter_tables":"[[LITER_TABLES_PLACEHOLDER]]",
                           'analogs_count': "{{ analogs_count }}",
                            "LAND_TABLE": "[ LAND_TABLE ]",
                     #
                           "liters_block": "{{ liters_block }}",
                           "regional_market_analysis": "{{ regional_market_analysis | safe }}",
                            "engineering_description": "{{ engineering_description }}",
                            "density": "{{ density }}",
                            "lineEdit_CBUF": "{{ lineEdit_CBUF }}",
                            "profit": "{{ profit }}",
                            "method_rejection_reason": "{{ method_rejection_reason }}"
                            

                    }
            variants = [
                        ("report_sh.docx", "result.docx"),
                        ("report_sh_1.docx", "result_1.docx"),
                        ("report_sh_2.docx", "result_2.docx"),
                        ("report_sh_3.docx", "result_3.docx"),
                        ("report_sh_4.docx", "result_4.docx")
                    ]

            for tpl_name, result_name in variants:
                template_path = self.resource_path(f"reports/{tpl_name}")
                result_path = os.path.join(get_reports_templates_dir(), result_name)

                if not os.path.exists(template_path):
                    # print(f"[WARN] Шаблон не найден: {template_path}")
                    continue

                try:
                    doc = DocxTemplate(template_path)
                    doc.env = Environment(undefined=DebugUndefined)
                    doc.render(context)
                    print(f"[DEBUG] Сохраняю результат в: {result_path}")

                    doc.save(result_path)
                except Exception as e:
                    print(f"[ERROR] Ошибка при рендере {tpl_name}: {e}")

            QMessageBox.information(self, "Успех", f"Все шаблоны успешно сгенерированы в:\n{get_reports_templates_dir()}")


        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании шаблонов: {str(e)}")





    def load_lineedit_data_from_settings(self):
        settings_path = self.get_settings_path()
        if not os.path.exists(settings_path):
            return

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)

            fields = {
                self.lineEdit_name: "appraiser_name",
                self.lineEdit_surname: "appraiser_surname",
                self.lineEdit_sertificate_number: "sertificate_number",
                self.lineEdit_sertificate_date: "sertificate_date"
            }

            for widget, key in fields.items():
                widget.setText(settings.get(key, ""))

        except (json.JSONDecodeError, IOError, KeyError, AttributeError) as e:
            print(f"[WARNING] Ошибка при загрузке настроек оценщика: {str(e)}")
