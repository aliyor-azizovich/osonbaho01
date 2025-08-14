import os
import pandas as pd
from io import BytesIO
import re
import html
import shutil
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow, QLineEdit, QDateEdit, QPushButton,
    QDialog, QTextBrowser, QTabWidget, QWidget, QComboBox, QCheckBox, 
    QLabel, QTableWidgetItem, QStackedWidget, QVBoxLayout, QFileDialog, QMessageBox, QApplication
)
from PyQt5.QtCore import QDate, Qt, QObject
import requests
from PyQt5.QtGui import QIcon

from bs4 import BeautifulSoup
from ui.koefs import KoefsWidget
from ui.ukup_window import UkupWidget
from ui.comparative import ComparativeWidget
from ui.agreement import AgreementWidget
from ui.method__dialog import MethodRejectionDialog
from logic.data_entry import DataEntryForm
from ui.land_window import LandWidget
# from ui.income import IncomeWidget  
# from ui.income_dialogs.rent_temp_dialog import RentTempDialog
# from ui.income_dialogs.rent_dialog import RentDialog
# from ui.income_dialogs.management_dialog import ManagementDialog
# from ui.income_dialogs.discount_dialog import DiscountDialog 
# from ui.income_dialogs.collect_losses_dialog import CollectLossesDialog
# from ui.income_dialogs.loading_losses_dialog import LoadingLossesDialog
from logic.qr_parser import QRParser
from logic.paths import get_ui_path

from bs4 import BeautifulSoup



class ValuationMainWindow(QMainWindow):
    # Константа для полей отчета
    REPORT_FIELDS = {
        "number": "report_number",
        "reg_number":"reg_number",
        "date": "report_date",
        "last_change_date": "last_change_date",
        "owner": "owner_name",
        "buyer_type": "buyer_type",
        "buyer_name": "buyer_name",
        "buyer_passport_series": "buyer_passport_series",
        "buyer_passport_number": "buyer_passport_number",
        "buyer_inn": "buyer_inn",
        "buyer_director": "buyer_director",
        "buyer_address": "buyer_address",
        "address": "address",
        "valuation_cost": "valuation_cost",
        "exchange_rate": "exchange_rate",
        'lineEdit_CBUF': 'lineEdit_CBUF',
        "contract_date": "contract_date",
        "inspection_date": "inspection_date",
        "communications": "communications",
        "heating": "heating",
        "administrative": "administrative",
        "valuation_purpose": "valuation_purpose",
        "price_type": "price_type",
        "profit": "profit"
    }


    def __init__(self, main_window, report_number):
        super().__init__()
        uic.loadUi(get_ui_path("valuation_main.ui"), self)

        self.main_window = main_window
        self.project_dir = self.main_window.project_dir
        self.data_service = DataEntryForm()
        
        self.setWindowTitle("OsonBaho-Hovli")
        self.setWindowIcon(QIcon("icon_change.jpg")) 
        # Основной виджет с вкладками
        self.tab_widget = self.findChild(QTabWidget, "tabWidget")

        # Вкладка «Общие сведения»
        self.general_info_tab = QWidget()
        uic.loadUi(get_ui_path("general_info.ui"), self.general_info_tab)  # ✅ подгружаем правильный .ui
        self.tab_widget.addTab(self.general_info_tab, "Общие сведения")   # добавляем на вкладку

        
        screen_geometry = QApplication.desktop().availableGeometry()
        screen_height = screen_geometry.height()
        screen_width = screen_geometry.width()

        # Например, 90% от экрана
        self.resize(int(screen_width * 0.75), int(screen_height * 0.75))


        # self.tab_widget.showMaximized()
               
        self.report_number_input = self.general_info_tab.findChild(QLineEdit, "reportNumberEdit")
        self.exchange_rate_input = self.general_info_tab.findChild(QLineEdit, "reportNumberEdit_2")
        self.lineEdit_CBUF = self.general_info_tab.findChild(QLineEdit, 'lineEdit_CBUF')
        self.contract_date_input = self.general_info_tab.findChild(QDateEdit, "dateEdit")
        self.inspection_date_input = self.general_info_tab.findChild(QDateEdit, "dateEdit_2")
        self.lineEdit_owner = self.general_info_tab.findChild(QLineEdit, "lineEdit_owner")
        self.comboBox_valuating_point = self.general_info_tab.findChild(QComboBox, "comboBox_valuating_point")
        self.comboBox_price_type = self.general_info_tab.findChild(QComboBox, "comboBox_price_type")
        self.comboBox_oblast = self.general_info_tab.findChild(QComboBox, "comboBox_oblast")
        self.comboBox_rayon = self.general_info_tab.findChild(QComboBox, "comboBox_rayon")
        self.lineEdit_adress = self.general_info_tab.findChild(QLineEdit, "lineEdit_adress")
        self.save_report_button = self.findChild(QPushButton, "save_report_button")
        self.buyer_stacked_widget = self.general_info_tab.findChild(QStackedWidget, "stackedWidget_buyer")
        self.buyer_man_button = self.general_info_tab.findChild(QPushButton, "pushButton_buyer_man")
        self.buyer_company_button = self.general_info_tab.findChild(QPushButton, "pushButton_buyer_company")
        self.pushButton_refresh_exchange = self.general_info_tab.findChild(QPushButton, "pushButton_refresh_exchange")
        self.lineEdit_land_area = self.general_info_tab.findChild(QLineEdit, "lineEdit_land_area")
        self.lineEdit_total_area = self.general_info_tab.findChild(QLineEdit, "lineEdit_total_area")
        self.lineEdit_useful_area = self.general_info_tab.findChild(QLineEdit, "lineEdit_useful_area")
        self.lineEdit_living_area = self.general_info_tab.findChild(QLineEdit, "lineEdit_living_area")
        self.lineEdit_developer = self.general_info_tab.findChild(QLineEdit, "lineEdit_developer")
       
        self.lineEdit_cadastral_number = self.general_info_tab.findChild(QLineEdit, "lineEdit_cadastral_number")
        self.label_land_area = self.general_info_tab.findChild(QLabel, "label_land_area")
        self.label_total_area = self.general_info_tab.findChild(QLabel, "label_total_area")
        self.label_useful_area = self.general_info_tab.findChild(QLabel, "label_useful_area")
        self.label_living_area = self.general_info_tab.findChild(QLabel, "label_living_area")
        self.lineEdit_occupied_land = self.general_info_tab.findChild(QLineEdit, 'lineEdit_occupied_land')
        self.label_cadastral_number = self.general_info_tab.findChild(QLabel, "label_cadastral_number")
        self.lineEdit_cadastral_number.textChanged.connect(self.format_cadastral_number)

        self.pushButton_upload_kadastr = self.general_info_tab.findChild(QPushButton, "pushButton_upload_kadastr")
        self.pushButton_upload_kadastr.clicked.connect(self.upload_kadastr_file)

        self.pushButton_upload_kochirma = self.general_info_tab.findChild(QPushButton, "pushButton_upload_kochirma")
        self.pushButton_upload_kochirma.clicked.connect(self.upload_kochirma_file)

        self.pushButton_parse_kadastr = self.general_info_tab.findChild(QPushButton, "pushButton_parse_kadastr")
        self.pushButton_parse_kadastr.clicked.connect(self.parse_kadastr_data)

        self.lineEdit_reg_number = self.findChild(QLineEdit, 'lineEdit_reg_number')
        
        self.buyer_stacked_widget.setCurrentIndex(1)

        
        self.buyer_man_button.clicked.connect(lambda: self.buyer_stacked_widget.setCurrentIndex(1))
        self.buyer_company_button.clicked.connect(lambda: self.buyer_stacked_widget.setCurrentIndex(0))

        buyer_page = self.buyer_stacked_widget.widget(1)  # Первая страница (физическое лицо)
        company_page = self.buyer_stacked_widget.widget(0)  # Вторая страница (компания)

        
        # Cтраница физического лица
        self.lineEdit_name_man = buyer_page.findChild(QLineEdit, "lineEdit_name_man")
        self.lineEdit_passportS_man = buyer_page.findChild(QLineEdit, "lineEdit_passportS_man")
        self.lineEdit_passportN_man = buyer_page.findChild(QLineEdit, "lineEdit_passportN_man")
        self.lineEdit_adress_man = buyer_page.findChild(QLineEdit, "lineEdit_adress_man")

        # Элементы на странице компании
        self.INN_LineEdit = company_page.findChild(QLineEdit, "INN_LineEdit")
        self.lineEdit_name_company = company_page.findChild(QLineEdit, "lineEdit_name_company")
        self.lineEdit_director = company_page.findChild(QLineEdit, "lineEdit_director")
        self.LineEdit_adress_company = company_page.findChild(QLineEdit, "LineEdit_adress_company")


        self.pushButton_next = self.findChild(QPushButton, "pushButton_next")
        self.pushButton_refresh_F = self.general_info_tab.findChild(QPushButton, 'pushButton_refresh_F')

        # Инженерные коммуникации
        self.checkBox_gas = self.general_info_tab.findChild(QCheckBox, "checkBox_gas")
        self.checkBox_Electric = self.general_info_tab.findChild(QCheckBox, "checkBox_Electric")
        self.checkBox_water = self.general_info_tab.findChild(QCheckBox, "checkBox_water")
        self.checkBox_Sewerage = self.general_info_tab.findChild(QCheckBox, "checkBox_Sewerage")
        self.checkBox_ADSL = self.general_info_tab.findChild(QCheckBox, "checkBox_ADSL")
        self.checkBox_Ariston = self.general_info_tab.findChild(QCheckBox, "checkBox_Ariston")
        self.checkBox_hot_water = self.general_info_tab.findChild(QCheckBox, "checkBox_hot_water")
        self.comboBox_Heating = self.general_info_tab.findChild(QComboBox, "comboBox_Heating")


        # Сигналы
        self.comboBox_oblast.currentIndexChanged.connect(self.update_rayon_combobox)
        self.comboBox_rayon.currentIndexChanged.connect(self.update_koeffs)
        self.save_report_button.clicked.connect(self.save_report)
        self.pushButton_refresh_exchange.clicked.connect(self.load_exchange_rate)
        self.pushButton_refresh_F.clicked.connect(self.load_refinancing_rate)

        self.exchange_rate_input.setReadOnly(True)
        self.lineEdit_CBUF.setReadOnly(True)
        self.report_number_input.setVisible(False)
        # Вкладки подходов
        self.cost_tab = QTabWidget()
        self.tab_widget.addTab(self.cost_tab, "Затратный подход")
        self.ukup_tab = UkupWidget(parent=self, main_window=self.main_window, valuation_window=self)
        self.cost_tab.addTab(self.ukup_tab, "Оценка по УКУП")
        self.pushButton_next.clicked.connect(self.save_report)
        self.pushButton_next.clicked.connect(self.switch_to_ukup_tab)

        # self.cost_tab.addTab(QWidget(), "Оценка земельного участка")
        self.land_tab = LandWidget(parent=self, main_window=self.main_window, valuation_window=self)
        self.cost_tab.addTab(self.land_tab, "Оценка земельного участка")

        # self.cost_tab.addTab(QWidget(), "Оценка по сметной документации")
        self.koefs_tab = KoefsWidget(parent=self, main_window=self)
        self.cost_tab.addTab(self.koefs_tab, "Коэффициенты удорожания")

        # РЕАЛИЗАЦИЯ ДОХОДНОГО ПОДХОДА (ВРЕМЕННО ОТКАЗАЛСЯ)
        # self.income_tab = QTabWidget()
        # self.tab_widget.addTab(self.income_tab, "Доходный подход")
        # self.income_widget = IncomeWidget(parent=self, main_window=self.main_window, valuation_window=self)
        # self.income_tab.addTab(self.income_widget, "Оценка доходным подходом")
       


        self.comparative_tab = QTabWidget()
        self.tab_widget.addTab(self.comparative_tab, "Сравнительный подход")
        self.comparative_widget = ComparativeWidget(parent=self, main_window=self.main_window, valuation_window=self)
        self.comparative_tab.addTab(self.comparative_widget, "Оценка сравнительным подходом")
       
       
        self.agreement_tab = QTabWidget()
        self.tab_widget.addTab(self.agreement_tab, "Согласование")
        self.agreement_widget = AgreementWidget(parent=self, main_window=self.main_window, valuation_window=self)
        self.agreement_tab.addTab(self.agreement_widget, "Согласование результатов")

        # self.method_dialog = MethodRejectionDialog(self, valuation_window=self)
        # Установка значений
        self.report_number_input.setText(str(report_number))
        self.report_number_input.setVisible(False)
        self.contract_date_input.setDate(QDate.currentDate())
        self.inspection_date_input.setDate(QDate.currentDate())
        self.load_exchange_rate()
        self.load_refinancing_rate()
        
        self.populate_oblast_combobox()
        self.populate_valuating_point_combobox()
        self.populate_price_type_combobox()
        self.populate_heating_combobox()
       
        self.saved_liters = []
    
        self.line_edits = [
            self.lineEdit_reg_number,
            self.lineEdit_CBUF,
            self.lineEdit_land_area,
            self.lineEdit_living_area,
            self.lineEdit_total_area,
            self.lineEdit_useful_area,
            self.lineEdit_cadastral_number,
            self.lineEdit_owner,
            self.lineEdit_adress,
            self.lineEdit_name_man,
            self.lineEdit_passportS_man,
            self.lineEdit_passportN_man,
            self.lineEdit_adress_man,
            self.INN_LineEdit,
            self.lineEdit_name_company,
            self.lineEdit_director,
            self.LineEdit_adress_company,
            self.checkBox_hot_water,
            self.checkBox_Sewerage,
            self.checkBox_Ariston,
            self.checkBox_water,
            self.checkBox_Electric,
            self.checkBox_gas,
            self.checkBox_ADSL,
            self.lineEdit_developer
        ]

        

     # Установка фильтра событий на каждое поле
        for line_edit in self.line_edits:
            line_edit.installEventFilter(self)
        
        
        for button in [ self.pushButton_upload_kadastr,
            self.pushButton_upload_kochirma,
            self.pushButton_parse_kadastr, self.buyer_man_button,
            self.buyer_company_button,  self.pushButton_refresh_exchange,
            self.pushButton_refresh_F, self.save_report_button,
            self.pushButton_next]:
            button.setFocusPolicy(Qt.StrongFocus)
            button.setAutoDefault(True)
            button.setDefault(True)

    def eventFilter(self, obj: QObject, event):
        if event.type() == event.KeyPress and isinstance(obj, QLineEdit):
            if event.key() == Qt.Key_Down:
                self.focus_next_lineedit(obj)
                return True
            elif event.key() == Qt.Key_Up:
                self.focus_previous_lineedit(obj)
                return True
            elif event.key() == Qt.Key_Right:
                if obj.cursorPosition() == len(obj.text()):
                    self.focus_next_lineedit(obj)
                    return True
            elif event.key() == Qt.Key_Left:
                if obj.cursorPosition() == 0:
                    self.focus_previous_lineedit(obj)
                    return True
        return super().eventFilter(obj, event)


    def calculate_profit(self):
        """
        Расчёт прибыли предпринимателя.
        F — ставка рефинансирования (в процентах, из поля lineEdit_CBUF),
        G — доля авансовых платежей (процент),
        H — число лет строительства.
        """
        try:
            H = 1.5
            O = float(self.lineEdit_CBUF.text().replace('%', '').strip())/100
            G = 25/100
            F = float(O*H)
            profit = round(round(0.5 * H * F * (1 + H * F / 3 + G * (1 + (2 * H**2 * F**2) / 3))*100, 0))
            self.lineEdit_developer.setText(f"{profit:.0f}%")
            self.profit = profit  
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось вычислить прибыль: {e}")
        

    def assign_owner_to_buyer_fields(self):
        owner_text = self.lineEdit_owner.text().strip()

        if '"' in owner_text or 'МЧЖ' in owner_text.upper():
            # Компания
            self.buyer_stacked_widget.setCurrentIndex(0)  # Страница компании
            self.lineEdit_name_company.setText(owner_text)
        else:
            # Физлицо
            self.buyer_stacked_widget.setCurrentIndex(1)  # Страница физлица
            self.lineEdit_name_man.setText(owner_text)





    def eventFilter(self, obj: QObject, event):
        if event.type() == event.KeyPress and isinstance(obj, QLineEdit):
            if event.key() == Qt.Key_Down:
                self.focus_next_lineedit(obj)
                return True
            elif event.key() == Qt.Key_Up:
                self.focus_previous_lineedit(obj)
                return True
            elif event.key() == Qt.Key_Right:
                if obj.cursorPosition() == len(obj.text()):
                    self.focus_next_lineedit(obj)
                    return True
            elif event.key() == Qt.Key_Left:
                if obj.cursorPosition() == 0:
                    self.focus_previous_lineedit(obj)
                    return True
        return super().eventFilter(obj, event)

    def focus_next_lineedit(self, current):
        if current in self.line_edits:
            idx = self.line_edits.index(current)
            next_idx = (idx + 1) % len(self.line_edits)
            self.line_edits[next_idx].setFocus()

    def focus_previous_lineedit(self, current):
        if current in self.line_edits:
            idx = self.line_edits.index(current)
            prev_idx = (idx - 1) % len(self.line_edits)
            self.line_edits[prev_idx].setFocus()



    def parse_kadastr_data(self):
        try:
            reg_number = self.lineEdit_reg_number.text().strip()
            if not reg_number:
                QMessageBox.warning(self, "Ошибка", "Не указан номер отчёта.")
                return

            save_dir = getattr(self.main_window, "save_directory", None)
            if not save_dir:
                QMessageBox.warning(self, "Ошибка", "Не выбрана папка для сохранения.")
                return

            report_folder = os.path.join(save_dir, reg_number)

            qr_parser = QRParser()
            link = qr_parser.extract_qr_from_report(report_folder, reg_number)

            if link:
                # Если QR-код считан
                html_data = qr_parser.fetch_data_from_link(link)
                parsed_data = qr_parser.parse_data(html_data)
                # print("ℹ️ Попытка парсинга через старый метод parse_data.")
                # Если все основные поля "Не указано", пробуем другой парсер
                # essential_fields = ["cadastral_number", "address", "owner_name", "land_area"]
                # if parsed_data.get("land_area", "Не указано") == "Не указано":
                #     print("⚠️ Старый парсер не дал результата. Пробуем modern формат.")
                #     parsed_data = qr_parser.parse_modern_format(html_data)
                #     print("✅ Сработал метод parse_modern_format.")
                
                if html_data:
                    html_table = self.extract_html_table(html_data)
                    self.kadastr_table_html = html_table
                else:
                    self.kadastr_table_html = ""
                

            
            else:
                # Если QR-код НЕ считан — пробуем загрузить Ko'chirma
                

                # Ищем файл
                possible_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                kochirma_path = None

                for ext in possible_extensions:
                    candidate_path = os.path.join(report_folder, f"Ko'chirma - Отчёт№{reg_number}{ext}")
                    if os.path.exists(candidate_path):
                        kochirma_path = candidate_path
                        break

                if not kochirma_path:
                    QMessageBox.warning(self, "Ошибка", "Файл Ko'chirma не найден. Пожалуйста, загрузите его.")
                    return

                # Работаем с kochirma_path
                link = qr_parser.extract_qr_from_pdf(kochirma_path)
                if link:
                    html_data = qr_parser.fetch_data_from_link(link)
                    parsed_data = qr_parser.parse_kochirma_data(html_data)
                    if html_data:
                        html_table = self.extract_html_table(html_data)
                        self.kadastr_table_html = html_table
                    else:
                        self.kadastr_table_html = ""
                   
                else:
                    QMessageBox.warning(self, "Ошибка", "QR-код в Ko'chirma тоже не считан. Невозможно продолжить.")
                    return

            # Заполняем интерфейс
            self.lineEdit_cadastral_number.setText(str(parsed_data.get("cadastral_number", "")))

            address_raw = parsed_data.get("address", "")
            address_formatted = self.format_address(address_raw)
            self.lineEdit_adress.setText(address_formatted)

            owner_raw = parsed_data.get("owner_name", "")
            owner_cyrillic = self.latin_to_cyrillic(owner_raw)
            self.lineEdit_owner.setText(owner_cyrillic)

            self.lineEdit_land_area.setText(str(parsed_data.get("land_area", "")))
            self.lineEdit_total_area.setText(str(parsed_data.get("total_area", "")))
            self.lineEdit_living_area.setText(str(parsed_data.get("living_area", "")))
            self.lineEdit_useful_area.setText(str(parsed_data.get("usefull_area", "")))
            self.lineEdit_owner.setText(owner_cyrillic)
            self.assign_owner_to_buyer_fields()

            QMessageBox.information(self, "Успех", "Данные успешно считаны!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при парсинге данных: {str(e)}")


    def extract_html_table(self, html_data) -> str:
        soup = BeautifulSoup(html_data, "html.parser")

        table = soup.find("table", class_="table")
        if not table:
            return ""

        rows = []
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) != 2:
                continue  # Пропускаем строки не с двумя ячейками
            key = tds[0].get_text(strip=True)
            value = tds[1].get_text(separator=" ", strip=True)
            rows.append((key, value))

        # Преобразуем в HTML-таблицу вручную
        html_result = "<table border='1' cellspacing='0' cellpadding='4'>"
        html_result += "<thead><tr><th>Поле</th><th>Значение</th></tr></thead><tbody>"
        for key, value in rows:
            html_result += f"<tr><td>{key}</td><td>{value}</td></tr>"
        html_result += "</tbody></table>"

        return html_result







    def latin_to_cyrillic(self, text):
        replacements = {
            'sh': 'ш', 'ch': 'ч', 'ya': 'я', 'yo': 'ё', 'yu': 'ю',
            'o‘': 'ў', 'g‘': 'ғ'
        }

        single_letters = {
            'a': 'а', 'b': 'б', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
            'h': 'х', 'i': 'и', 'j': 'ж', 'k': 'к', 'l': 'л', 'm': 'м',
            'n': 'н', 'o': 'о', 'p': 'п', 'q': 'қ', 'r': 'р', 's': 'с',
            't': 'т', 'u': 'у', 'v': 'в', 'x': 'х', 'y': 'й', 'z': 'з'
        }

        result = ""
        i = 0
        while i < len(text):
           
            if i + 1 < len(text):
                pair = text[i:i+2].lower()
                if pair in replacements:
                    
                    if text[i].isupper():
                        result += replacements[pair].upper()
                    else:
                        result += replacements[pair]
                    i += 2
                    continue

            
            char = text[i]
            lower_char = char.lower()
            if lower_char in single_letters:
                if char.isupper():
                    result += single_letters[lower_char].upper()
                else:
                    result += single_letters[lower_char]
            else:
                result += char
            i += 1

        return result

    def format_address(self, address_text):
        if not address_text:
            return ""

        address = address_text

        # 1. Заменяем "МФЙ" на "МСГ"
        if "МФЙ" in address:
            parts = address.split("МФЙ")
            if len(parts) == 2:
                neighborhood = parts[0].strip()
                rest = parts[1].strip()
                address = f"МСГ {neighborhood}, {rest}"

        # 2. Удаляем "кучаси"
        address = address.replace("кучаси", "").strip()

        # 3. Удаляем "-уй"
        address = address.replace("-уй", "").strip()

        # 4. Переставляем "улица"
        parts = [p.strip() for p in address.split(",")]

        if len(parts) >= 2:
            parts[1] = f"улица {parts[1]}"
            address = ", ".join(parts)

        return address


            








    def upload_kadastr_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл кадастра",
            "",
            "Все файлы (*);;PDF файлы (*.pdf);;Изображения (*.jpg *.jpeg *.png)"
        )

        if not file_path:
            return 

        try:
            save_dir = getattr(self.main_window, "save_directory", None)
            if not save_dir:
                QMessageBox.warning(self, "Ошибка", "Не выбрана папка для сохранения отчётов. Сначала укажите её в меню.")
                return
            
            reg_number = self.lineEdit_reg_number.text().strip()
            if not reg_number:
                QMessageBox.warning(self, "Ошибка", "Не указан номер отчёта.")
                return

            # Папка отчёта
            report_folder = os.path.join(save_dir, reg_number)
            os.makedirs(report_folder, exist_ok=True)

            _, new_ext = os.path.splitext(file_path)
            new_ext = new_ext.lower()
            if new_ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                QMessageBox.warning(self, "Неверный формат", "Поддерживаются только PDF, JPG, JPEG и PNG файлы.")
                return

            base_filename = f"Kadastr - Отчёт №{reg_number}"
            
            # Удаляем старый файл
            for ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                existing_file = os.path.join(report_folder, base_filename + ext)
                if os.path.exists(existing_file) and ext != new_ext:
                    os.remove(existing_file)

            # Сохраняем файл
            target_path = os.path.join(report_folder, base_filename + new_ext)
            shutil.copy(file_path, target_path)

            QMessageBox.information(self, "Успех", f"Кадастр успешно загружен и сохранён в папку:\n{target_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла: {str(e)}")






    def upload_kochirma_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл Ko'chirma",
            "",
            "Все файлы (*);;PDF файлы (*.pdf);;Изображения (*.jpg *.jpeg *.png)"
        )

        if not file_path:
            return

        try:
            save_dir = getattr(self.main_window, "save_directory", None)
            if not save_dir:
                QMessageBox.warning(self, "Ошибка", "Не выбрана папка для сохранения отчётов. Сначала укажите её в меню.")
                return
            
            reg_number = self.lineEdit_reg_number.text().strip()
            if not reg_number:
                QMessageBox.warning(self, "Ошибка", "Не указан номер отчёта.")
                return
            
            report_folder = os.path.join(save_dir, reg_number)
            os.makedirs(report_folder, exist_ok=True)

            _, new_ext = os.path.splitext(file_path)
            new_ext = new_ext.lower()
            if new_ext not in ['.pdf', '.jpg', '.jpeg', '.png']:
                QMessageBox.warning(self, "Неверный формат", "Поддерживаются только PDF, JPG, JPEG и PNG файлы.")
                return

            base_filename = f"Ko'chirma - Отчёт№{reg_number}"

            for ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                existing_file = os.path.join(report_folder, base_filename + ext)
                if os.path.exists(existing_file) and ext != new_ext:
                    os.remove(existing_file)

            target_path = os.path.join(report_folder, base_filename + new_ext)
            shutil.copy(file_path, target_path)

            QMessageBox.information(self, "Успех", f"Ko'chirma успешно загружена и сохранена в папку:\n{target_path}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке файла: {str(e)}")


    def switch_to_ukup_tab(self):
        """Переключает на вкладку Затратный подход"""

        # Проверка: если поле с курсом пустое — загружаем курс
        if not self.exchange_rate_input.text().strip():
            self.load_exchange_rate()

        # Проверка: если ставка ЦБ пустая — загружаем ставку
        if not self.lineEdit_CBUF.text().strip():
            self.load_refinancing_rate()

        index = self.tab_widget.indexOf(self.cost_tab)
        if index != -1:
            self.tab_widget.setCurrentIndex(index)

            


    def closeEvent(self, event):
        self.main_window.show()  
        event.accept()  
    
    


    

    def format_cadastral_number(self, text):
        # Удаляем все нецифры
        digits = ''.join(filter(str.isdigit, text))

        # Ограничиваем максимум до 14 цифр (5 блоков по 2 + 1 блок из 4)
        digits = digits[:14]

        # Разбиваем по шаблону
        parts = []
        splits = [2, 2, 2, 2, 2, 4]
        i = 0
        for s in splits:
            if i + s <= len(digits):
                parts.append(digits[i:i+s])
                i += s
            else:
                parts.append(digits[i:])
                break

        formatted = ':'.join(parts)
        
        # Отключаем сигнал временно
        self.lineEdit_cadastral_number.blockSignals(True)
        self.lineEdit_cadastral_number.setText(formatted)
        self.lineEdit_cadastral_number.blockSignals(False)
        self.auto_select_oblast_and_rayon_by_kadastr()






    def populate_oblast_combobox(self):
        df_territorial = self.data_service.territorial_correction()
        if df_territorial is not None:
            regions = df_territorial['region'].dropna().unique().tolist()
            self.comboBox_oblast.clear()
            self.comboBox_oblast.addItems(regions)
        self.update_rayon_combobox()

    def update_rayon_combobox(self):
        selected_region = self.comboBox_oblast.currentText()
        df_territorial = self.data_service.territorial_correction()
        df_province = self.data_service.province_choose()
        if df_territorial is not None and df_province is not None:
            region_id_row = df_territorial[df_territorial['region'] == selected_region]
            if not region_id_row.empty:
                region_id = region_id_row.iloc[0]['region_id']
                filtered_provinces = df_province[df_province['region_id'] == region_id]['province'].dropna().tolist()
                self.comboBox_rayon.clear()
                self.comboBox_rayon.addItems(filtered_provinces)

    def populate_valuating_point_combobox(self):
        values = [
            "Для передачи объекта в качестве залога", "Для вклада в уставный фонд",
            "Консультация заказчика о рыночной стоимости объекта", "Для передачи объекта на баланс предприятия",
            "Для предоставления отчётности в налоговые органы", "Для раздела имущества", "Для реализации"
        ]
        self.comboBox_valuating_point.clear()
        self.comboBox_valuating_point.addItems(values)

    def populate_price_type_combobox(self):
        values = [
            "рыночная стоимость", "стоимость для налогообложения", "ликвидационная стоимость",
            "балансовая стоимость", "инвестиционная стоимость", "страховая стоимость", "утилизационная стоимость"
        ]
        self.comboBox_price_type.clear()
        self.comboBox_price_type.addItems(values)
    
    
    def auto_select_oblast_and_rayon_by_kadastr(self):
        
        text = self.lineEdit_cadastral_number.text()
        
        
        digits = ''.join(filter(str.isdigit, text))
        if len(digits) < 4:
            
            return

        parts = text.split(":")
        if len(parts) >= 2:
            aa = parts[0]
            bb = parts[1]
            
        else:
            
            return

        df_territorial = self.data_service.territorial_correction()
        df_province = self.data_service.province_choose()

        oblast_row = df_territorial[df_territorial['kadastr'].astype(str).str.zfill(2) == aa.zfill(2)]
        if not oblast_row.empty:
            region = oblast_row.iloc[0]['region']
            region_id = oblast_row.iloc[0]['region_id']
            
            self.comboBox_oblast.setCurrentText(region)

            self.update_rayon_combobox()

            

            province_row = df_province[
                (df_province['region_id'] == region_id) &
                (df_province['kadastr'].astype(str).str.zfill(2) == bb.zfill(2))
            ]
            
            if not province_row.empty:
                province = province_row.iloc[0]['province']
                
                self.comboBox_rayon.setCurrentText(province)
            else:
                
                if self.comboBox_rayon.count() > 0:
                    default_rayon = self.comboBox_rayon.itemText(0)
                
                    self.comboBox_rayon.setCurrentIndex(0)
        else:
            print(f"[DEBUG] Область с кодом {aa.zfill(2)} не найдена.")


        




    def save_report(self):
        data = self.collect_general_info()
        # data["income_valuation"] = self.income_widget.collect_income_data()
        data["koefs"] = self.koefs_tab.collect_koefs_data()
        data['comparative'] = self.comparative_widget.collect_comparative_data()
        data["agreement"] = self.agreement_widget.collect_agreement_data()
        data["rejection"] = getattr(self, "rejection_data", {})

        report_number = data.get(self.REPORT_FIELDS["number"], "")
        reg_number = data.get(self.REPORT_FIELDS['reg_number'], '')
        report_date = data.get(self.REPORT_FIELDS["contract_date"], "Не указана")
        last_change_date = QDate.currentDate().toString("yyyy-MM-dd")
        
        
        # Фильтрация данных
        filtered_data = self.main_window.filter_report_data(data)
        try:
            
            # Обновляем или добавляем отчет в реестр
            self.main_window.report_registry.update_report(
                report_number=filtered_data["report_number"],
                reg_number = filtered_data['reg_number'],
                report_date=filtered_data["report_date"],
                last_change_date=filtered_data["last_change_date"],
                owner_name=filtered_data["owner_name"],
                buyer_name=filtered_data["buyer_name"],
                adress=filtered_data["adress"],
                valuation_cost=filtered_data["valuation_cost"],
                
            )
        except Exception as e:
            print(f"Ошибка обновления реестра: {str(e)}")
        
        try:
            # Обновляем данные в таблице
            existing_row_index = self.main_window.find_report_row(report_number)
            if existing_row_index is not None:
                self.main_window.update_report_entry(
                    existing_row_index,
                    report_number,
                    reg_number,
                    report_date,
                    last_change_date,
                    filtered_data["owner_name"],
                    filtered_data["buyer_name"],
                    filtered_data["adress"],
                    filtered_data["valuation_cost"]
                    
                )
            else:
                self.main_window.add_new_report_entry(
                    report_number,
                    reg_number,
                    report_date,
                    last_change_date,
                    filtered_data["owner_name"],
                    filtered_data["buyer_name"],
                    filtered_data["adress"],
                    filtered_data["valuation_cost"]
                    
                )
            
        except Exception as e:
            print("")

        try:
            # Обновляем литеры
            data["liters"] = self.main_window.saved_liters
            data["land_valuation"] = self.land_tab.collect_land_data()

            # Добавляем таблицу из кадастра, если она есть
            if hasattr(self, "kadastr_table_html"):
                data["kadastr_table_html"] = self.kadastr_table_html


            # Сохранение данных на диск
            self.main_window.report_manager.save_report_data(report_number, data)

           

            # Загрузка литеров в таблицу
            liters = data.get("liters", [])
            if liters:
                self.ukup_tab.load_liters_to_table(liters)
                
            self.agreement_widget.load_costs_from_json(data)

        except Exception as e:
            print(f"Ошибка сохранения отчёта: {str(e)}")

        




    def update_koeffs(self):
        self.koefs_tab.load_table_data()

    def load_exchange_rate(self):
        try:
            response = requests.get("https://cbu.uz/ru/arkhiv-kursov-valyut/json/", timeout=5)
            usd_rate = next((item["Rate"] for item in response.json() if item["Ccy"] == "USD"), None)
            self.exchange_rate_input.setText(str(usd_rate) if usd_rate else "Ошибка загрузки")
        except:
            self.exchange_rate_input.setText("Нет соединения")


    def populate_heating_combobox(self):
        heating = ['Центральное отопление', 'Печное отопление', 'Водяное отопление (АГВ, двухконтурный котёл)']
        self.comboBox_Heating.clear()
        self.comboBox_Heating.addItems(heating)        
        self.comboBox_Heating.setCurrentIndex(0)  

    
    def collect_general_data(self):
        general_data = {
            'газификация': self.checkBox_gas.isChecked(),
            'электроосвещение': self.checkBox_Electric.isChecked(),
            'водоснабжение': self.checkBox_water.isChecked(),
            'канализация': self.checkBox_Sewerage.isChecked(),
            'телефонная_линия': self.checkBox_ADSL.isChecked(),
            'электрический_водонагреватель': self.checkBox_Ariston.isChecked(),
            'горячее_водоснабжение': self.checkBox_hot_water.isChecked(),
            'отопление': self.comboBox_Heating.currentText().lower()  # Получаем выбранный текст и приводим к нижнему регистру
        }
        return general_data


    
    
    def load_data(self, data):
        # income_data = data.get("income_valuation")
        # if income_data:
        #     self.income_widget.load_income_data(income_data)

        koefs_data = data.get("koefs")
        if koefs_data:
            self.koefs_tab.load_koefs_data(koefs_data)

        comparative_data = data.get("comparative")
        if comparative_data:
            comparative_data["land_area"] = data.get("land_area", "")
            comparative_data["administrative"] = data.get("administrative", {})
            self.comparative_widget.load_comparative_data(comparative_data)

        agreement_data = data.get("agreement")
        self.agreement_widget.load_agreement_data(agreement_data)
        self.agreement_widget.load_costs_from_json(data)


        
        # Основная информация
        report_number = data.get(ValuationMainWindow.REPORT_FIELDS["number"], "")
        if data.get("is_copy", False):
            # Если это копия, отображаем новый номер
            self.report_number_input.setText(report_number)
        else:
            # Если оригинал, отображаем обычный номер
            self.report_number_input.setText(report_number)
        self.lineEdit_reg_number.setText(data.get("reg_number", ""))
        self.exchange_rate_input.setText(data.get("exchange_rate", ""))
        self.lineEdit_CBUF.setText(data.get('lineEdit_CBUF', ''))
        self.lineEdit_developer.setText(data.get("profit", ""))  #

        self.lineEdit_adress.setText(data.get("address", ""))
        self.lineEdit_owner.setText(data.get("owner_name", ""))

        # Сохраняем литеры в saved_liters
        self.main_window.saved_liters = data.get("liters", [])
        land_data = data.get("land_valuation")
        if land_data:
            self.land_tab.load_land_data(data)

        
        

        # Даты
        report_date = data.get("contract_date", "Не указан")
        inspection_date = data.get("inspection_date", "Не указан")
        self.contract_date_input.setDate(QDate.fromString(report_date, "yyyy-MM-dd"))
        self.inspection_date_input.setDate(QDate.fromString(inspection_date, "yyyy-MM-dd"))

        # Инженерные коммуникации
        communications = data.get("communications", {})
        self.checkBox_gas.setChecked(communications.get("газификация", False))
        self.checkBox_Electric.setChecked(communications.get("электроосвещение", False))
        self.checkBox_water.setChecked(communications.get("водоснабжение", False))
        self.checkBox_Sewerage.setChecked(communications.get("канализация", False))
        self.checkBox_ADSL.setChecked(communications.get("телефонная_линия", False))
        self.checkBox_Ariston.setChecked(communications.get("электрический_водонагреватель", False))
        self.checkBox_hot_water.setChecked(communications.get("горячее_водоснабжение", False))

        # Отопление
        self.comboBox_Heating.setCurrentText(data.get("heating", "Центральное отопление"))

        # Административное деление
        administrative = data.get("administrative", {})
        self.comboBox_oblast.setCurrentText(administrative.get("oblast", "Не указан"))
        self.comboBox_rayon.setCurrentText(administrative.get("rayon", "Не указан"))

        # Цель оценки и вид стоимости
        self.comboBox_valuating_point.setCurrentText(data.get("valuation_purpose", "Не указана"))
        self.comboBox_price_type.setCurrentText(data.get("price_type", "Не указан"))

        # Загрузка данных заказчика
        buyer_type = data.get(self.REPORT_FIELDS["buyer_type"], "неизвестно")

        if buyer_type == "физическое лицо":
            # Переключаем на страницу физического лица
            self.buyer_stacked_widget.setCurrentIndex(1)
            self.lineEdit_name_man.setText(data.get(self.REPORT_FIELDS["buyer_name"], ""))
            self.lineEdit_passportS_man.setText(data.get(self.REPORT_FIELDS["buyer_passport_series"], ""))
            self.lineEdit_passportN_man.setText(data.get(self.REPORT_FIELDS["buyer_passport_number"], ""))
            self.lineEdit_adress_man.setText(data.get(self.REPORT_FIELDS["buyer_address"], ""))
            
        elif buyer_type == "юридическое лицо":
            # Переключаем на страницу юридического лица
            self.buyer_stacked_widget.setCurrentIndex(0)
            self.lineEdit_name_company.setText(data.get(self.REPORT_FIELDS["buyer_name"], ""))
            self.INN_LineEdit.setText(data.get(self.REPORT_FIELDS["buyer_inn"], ""))
            self.lineEdit_director.setText(data.get(self.REPORT_FIELDS["buyer_director"], ""))
            self.LineEdit_adress_company.setText(data.get(self.REPORT_FIELDS["buyer_address"], ""))
        # Новые поля
        self.lineEdit_land_area.setText(data.get("land_area", ""))
        self.lineEdit_total_area.setText(data.get("total_area", ""))
        self.lineEdit_useful_area.setText(data.get("useful_area", ""))
        self.lineEdit_living_area.setText(data.get("living_area", ""))
        self.lineEdit_cadastral_number.setText(data.get("cadastral_number", ""))
        # Восстанавливаем HTML-таблицу из кадастра, если она есть
        self.kadastr_table_html = data.get("kadastr_table_html", "")

        

           


        

        
        
    @staticmethod
    def parse_date(date_str):
       
        for fmt in ["dd.MM.yyyy", "yyyy-MM-dd", "dd/MM/yyyy"]:
            date = QDate.fromString(date_str, fmt)
            if date.isValid():
                return date
        return QDate.currentDate() 
        

       


    def collect_general_info(self):
        general_info = {}

        # Основная информация
        general_info[self.REPORT_FIELDS["number"]] = self.report_number_input.text()
        general_info[self.REPORT_FIELDS["exchange_rate"]] = self.exchange_rate_input.text()
        general_info[self.REPORT_FIELDS["lineEdit_CBUF"]] = self.lineEdit_CBUF.text()
        general_info[self.REPORT_FIELDS["reg_number"]] = self.lineEdit_reg_number.text()

        # Даты
        general_info[self.REPORT_FIELDS["contract_date"]] = self.contract_date_input.date().toString("yyyy-MM-dd")
        general_info[self.REPORT_FIELDS["inspection_date"]] = self.inspection_date_input.date().toString("yyyy-MM-dd")

        # Адрес объекта
        general_info[self.REPORT_FIELDS["address"]] = self.lineEdit_adress.text() or "Не указан"

        general_info[self.REPORT_FIELDS["owner"]] = self.lineEdit_owner.text() or "Не указан"

         # Инженерные коммуникации
        communications = {
            "газификация": self.checkBox_gas.isChecked(),
            "электроосвещение": self.checkBox_Electric.isChecked(),
            "водоснабжение": self.checkBox_water.isChecked(),
            "канализация": self.checkBox_Sewerage.isChecked(),
            "телефонная_линия": self.checkBox_ADSL.isChecked(),
            "электрический_водонагреватель": self.checkBox_Ariston.isChecked(),
            "горячее_водоснабжение": self.checkBox_hot_water.isChecked()
        }
        general_info[self.REPORT_FIELDS["communications"]] = communications

        # Отопление
        general_info[self.REPORT_FIELDS["heating"]] = self.comboBox_Heating.currentText()

        # Административное деление
        general_info[self.REPORT_FIELDS["administrative"]] = {
            "oblast": self.comboBox_oblast.currentText(),
            "rayon": self.comboBox_rayon.currentText()
        }

        # Цель оценки и вид стоимости
        general_info[self.REPORT_FIELDS["valuation_purpose"]] = self.comboBox_valuating_point.currentText()
        general_info[self.REPORT_FIELDS["price_type"]] = self.comboBox_price_type.currentText()

        
        current_buyer_page = self.buyer_stacked_widget.currentIndex()

        # Данные заказчика в зависимости от выбранной страницы
        if current_buyer_page == 1:
            # Физическое лицо
            general_info[self.REPORT_FIELDS["buyer_type"]] = "физическое лицо"
            general_info[self.REPORT_FIELDS["buyer_name"]] = self.lineEdit_name_man.text() or "Не указан"
            general_info[self.REPORT_FIELDS["buyer_passport_series"]] = self.lineEdit_passportS_man.text() or "Не указан"
            general_info[self.REPORT_FIELDS["buyer_passport_number"]] = self.lineEdit_passportN_man.text() or "Не указан"
            general_info[self.REPORT_FIELDS["buyer_address"]] = self.lineEdit_adress_man.text() or "Не указан"

        elif current_buyer_page == 0:
            # Юридическое лицо
            general_info[self.REPORT_FIELDS["buyer_type"]] = "юридическое лицо"
            general_info[self.REPORT_FIELDS["buyer_name"]] = self.lineEdit_name_company.text() or "Не указано"
            general_info[self.REPORT_FIELDS["buyer_inn"]] = self.INN_LineEdit.text() or "Не указан"
            general_info[self.REPORT_FIELDS["buyer_director"]] = self.lineEdit_director.text() or "Не указан"
            general_info[self.REPORT_FIELDS["buyer_address"]] = self.LineEdit_adress_company.text() or "Не указан"
        else:
            general_info[self.REPORT_FIELDS["buyer_type"]] = "неизвестно"
            general_info[self.REPORT_FIELDS["buyer_name"]] = "Не указан"


        # Новые поля
        general_info["land_area"] = self.lineEdit_land_area.text()
        general_info["total_area"] = self.lineEdit_total_area.text()
        general_info["useful_area"] = self.lineEdit_useful_area.text()
        general_info["living_area"] = self.lineEdit_living_area.text()
        general_info["cadastral_number"] = self.lineEdit_cadastral_number.text()
        general_info["profit"] = self.lineEdit_developer.text().strip()

        return general_info



    def load_refinancing_rate(self):
        try:
            response = requests.get("https://cbu.uz/ru/", timeout=5)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Ищем div
            rate_block = soup.find("div", class_="dashboard__informer_text")
            if rate_block:
                span = rate_block.find("span")
                rate_text = span.text.strip() if span else None
                self.lineEdit_CBUF.setText(rate_text if rate_text else "Не найдено")
            else:
                self.lineEdit_CBUF.setText("Не найдено")
        except Exception as e:
            self.lineEdit_CBUF.setText("Нет соединения")
        self.calculate_profit()
    

