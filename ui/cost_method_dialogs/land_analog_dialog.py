from PyQt5.QtWidgets import (
    QDialog, QScrollArea, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QCheckBox, QAbstractScrollArea
)
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os
import webbrowser
from logic.data_entry import DataEntryForm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
from logic.paths import get_ui_path
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QHeaderView


class LandAnalogDialog(QDialog):
    def __init__(self, parent=None, data_service=None, valuation_window=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("cost_method_dialogs/land_analog_dialog.ui"), self)

        self.setWindowTitle("Выбор аналогов для оценки земельного участка")
        
        self.setWindowIcon(QIcon("icon.ico"))  

        self.parent = parent
        self.data_service = data_service or DataEntryForm()
        self.valuation_window = valuation_window

        self.tableWidget = self.findChild(QTableWidget, "tableWidget_analogs")
        self.tableWidget.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.pushButton_analog_OK = self.findChild(QPushButton, 'pushButton_analog_OK')
        self.pushButton_analog_OK.clicked.connect(self.return_selected_cards)

        self.rayon_data = self.data_service.province_choose()
        rayon = self.valuation_window.comboBox_rayon.currentText().strip()

        cards = self.fetch_olx_land_analogs(rayon)
        self.populate_table(cards, rayon)
        self.tableWidget.cellClicked.connect(self.open_link)  # одиночный клик
        self.tableWidget.itemChanged.connect(self.recalculate_price_per_unit)

    def fetch_olx_land_analogs(self, rayon):
        def parse_price(price_str):
            price_str_lower = price_str.lower()
            numbers = re.findall(r'\d+', price_str.replace(" ", ""))
            if numbers:
                return int("".join(numbers))
            return None


        def extract_area_from_title(title: str):
            title = title.lower()
            patterns = [
                (r'([\d.,]+)\s*(га|гектар)', 100),
                (r"([\d.,]+)\s*(сотик|сотих|соток|сотки|сотых|sotih|sotihli|sotik|sotix|-сотик|sotikli|сотах|-соток|so'tq)", 1),
                (r'([\d.,]+)\s*(кв|kv|кв.м|квадрат|м2)', 1/100)
            ]
            for pattern, multiplier in patterns:
                match = re.search(pattern, title)
                if match:
                    val = float(match.group(1).replace(",", "."))
                    return round(val * multiplier, 2)
            return ""

        # --- Найти информацию о районе ---
        filtered_rayon = self.rayon_data[
            self.rayon_data['province'].str.strip().str.lower().apply(lambda x: x in rayon.lower())
        ]

        if filtered_rayon.empty:
            QMessageBox.warning(self, "Ошибка", f"Не найдено латинское имя для района: {rayon}")
            return []

        # --- Построение URL в зависимости от типа района ---
        is_tashkent = filtered_rayon.get('is_tashkent_rayon', False).iloc[0]
        if is_tashkent:
            district_id = filtered_rayon['district_id'].iloc[0]
            url = f"https://www.olx.uz/nedvizhimost/zemlja/tashkent/?search%5Bdistrict_id%5D={district_id}&currency=UZS"
        else:
            rayon_latin_name = filtered_rayon['province_latin_name'].iloc[0]
            url = f"https://www.olx.uz/nedvizhimost/zemlja/prodazha/{rayon_latin_name}/?currency=UZS"

        # --- Настройки браузера ---
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome(options=options)

        cards = []
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='l-card']"))
            )

            ad_elements = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='l-card']")[:50]

            for ad in ad_elements:
                try:
                    title = ad.find_element(By.CSS_SELECTOR, "h4.css-1g61gc2").text
                    price_str = ad.find_element(By.CSS_SELECTOR, "p[data-testid='ad-price']").text
                    raw_location = ad.find_element(By.CSS_SELECTOR, "p[data-testid='location-date']").text
                    location_parts = raw_location.split(" - ")
                    location = location_parts[0].strip()
                    date_str = location_parts[1].strip() if len(location_parts) > 1 else "—"
                    price = parse_price(price_str)
                    area = extract_area_from_title(title)
                    price_per_sotka = round(price / area, 2) if price and area else None
                    url = ad.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                    cards.append({
                        "title": title,
                        "price": price_str,
                        "price_numeric": price,
                        "location": location,
                        "date": date_str,
                        "area": area,
                        "price_per_unit": price_per_sotka,
                        "url": url
                    })
                except Exception as e:
                    print(f"[WARN] Пропущена карточка: {e}")
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки OLX: {e}")
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить объявления.")
        finally:
            driver.quit()

        cards.sort(key=lambda c: c["price_per_unit"] or float('inf'))
        return cards[:30]


    def populate_table(self, cards, rayon):
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(["", "Заголовок", "Дата", "Локация", "Площадь", "Цена", "Цена за сотку"])

        matches = [c for c in cards if any(r in c["location"].lower() for r in rayon.lower().split(", "))]
        others = [c for c in cards if c not in matches]
        all_rows = matches + [{}] + others
        self.tableWidget.setRowCount(len(all_rows))
        self.tableWidget.setColumnWidth(0, 8)  # минимальная ширина для чекбокса


        base_price = matches[0]["price_per_unit"] if matches and matches[0]["price_per_unit"] else None

        for row, card in enumerate(all_rows):
            if not card:
                label_item = QTableWidgetItem("Аналоги из соседних регионов")
                label_item.setFlags(Qt.ItemIsEnabled)
                label_item.setTextAlignment(Qt.AlignCenter)
                font = label_item.font()
                font.setItalic(True)
                label_item.setFont(font)
                self.tableWidget.setItem(row, 0, label_item)
                self.tableWidget.setSpan(row, 0, 1, 7)
                continue

            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.update_highlighting_based_on_selection)
            self.tableWidget.setCellWidget(row, 0, checkbox)


            wrapped_title = "\n".join([card["title"][i:i+50] for i in range(0, len(card["title"]), 50)])
            title_item = QTableWidgetItem(wrapped_title)
            title_item.setForeground(Qt.blue)
            title_item.setToolTip(card["title"])
            title_item.setData(Qt.UserRole, card["url"])
            title_item.setFlags(Qt.ItemIsEnabled)
            title_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.tableWidget.setItem(row, 1, title_item)


            for i, key in enumerate(["date", "location", "area", "price", "price_per_unit"], start=2):
                value = card.get(key, "")
                item = QTableWidgetItem()
                if key == "area":
                    item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)
                else:
                    item.setFlags(Qt.ItemIsEnabled)
                if key == "price_per_unit" and isinstance(value, (float, int)):
                    item.setText(f"{value:,.2f}".replace(",", " "))
                elif key == "price" and isinstance(value, (float, int)):
                    item.setText(f"{value:,}".replace(",", " "))
                else:
                    item.setText(str(value))
                self.tableWidget.setItem(row, i, item)

            


    def recalculate_price_per_unit(self, item):
        row = item.row()
        col = item.column()
        if col == 4:  # Столбец "Площадь"
            try:
                area_str = item.text().strip().replace(",", ".")
                if not area_str:
                    self.tableWidget.setItem(row, 6, QTableWidgetItem(""))  # очищаем "Цена за сотку"
                    return

                area = float(area_str)
                price_item = self.tableWidget.item(row, 5)  # Столбец "Цена"
                if price_item:
                    price_str = price_item.text().replace(" ", "").replace(",", ".")
                    price_numbers = re.findall(r'\d+', price_str)
                    price = float("".join(price_numbers)) if price_numbers else 0

                    if area > 0:
                        unit_price = round(price / area, 2)
                        formatted = f"{unit_price:,.2f}".replace(",", " ")
                        self.tableWidget.setItem(row, 6, QTableWidgetItem(formatted))
            except Exception as e:
                print(f"[WARN] Ошибка пересчёта price_per_unit: {e}")


    def open_link(self, row, col):
        if col == 1:
            item = self.tableWidget.item(row, col)
            if item:
                url = item.data(Qt.UserRole)
                if url:
                    webbrowser.open(url)

    def return_selected_cards(self):
        selected_cards = []
        for row in range(self.tableWidget.rowCount()):
            checkbox = self.tableWidget.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                title_item = self.tableWidget.item(row, 1)
                url = title_item.data(Qt.UserRole)
                selected_cards.append({
                    "title": title_item.text(),
                    "date": self.tableWidget.item(row, 2).text(),
                    "location": self.tableWidget.item(row, 3).text(),
                    "area": self.tableWidget.item(row, 4).text(),
                    "price": self.tableWidget.item(row, 5).text(),
                    "price_per_unit": self.tableWidget.item(row, 6).text(),
                    "url": url
                })

        if len(selected_cards) < 3:
            QMessageBox.warning(self, "Недостаточно аналогов", "Аналогов должно быть не меньше 3-х.")
            return

        self.selected_analogs = selected_cards
        if hasattr(self.parent, "fill_land_valuation_table"):
            self.parent.fill_land_valuation_table(selected_cards)
        
        self.accept()

    def update_highlighting_based_on_selection(self):
        selected_price = None
        for row in range(self.tableWidget.rowCount()):
            checkbox = self.tableWidget.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                price_item = self.tableWidget.item(row, 6)  # Цена за сотку
                if price_item:
                    try:
                        price_str = price_item.text().replace(" ", "").replace(",", ".")
                        selected_price = float(price_str)
                        break
                    except:
                        continue

        for row in range(self.tableWidget.rowCount()):
            for col in range(7):
                item = self.tableWidget.item(row, col)
                if item:
                    item.setBackground(Qt.white)  # Сброс цвета

        if selected_price is None:
            return

        for row in range(self.tableWidget.rowCount()):
            checkbox = self.tableWidget.cellWidget(row, 0)
            price_item = self.tableWidget.item(row, 6)
            if price_item and price_item.text().strip():
                try:
                    price_str = price_item.text().replace(" ", "").replace(",", ".")
                    price = float(price_str)
                    diff = abs(price - selected_price) / selected_price
                    for col in range(7):
                        item = self.tableWidget.item(row, col)
                        if item:
                            if diff <= 0.5:
                                item.setBackground(Qt.green)
                            elif diff <= 0.7:
                                item.setBackground(Qt.yellow)
                except:
                    continue
