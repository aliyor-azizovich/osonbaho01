from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox, QLabel, QTableWidget, QDialog, QTableWidgetItem, QSizePolicy, QApplication
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os
from ui.cost_method_dialogs.land_analog_dialog import LandAnalogDialog
from logic.loading_animation import LoadingDialog
from logic.data_entry import DataEntryForm
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import base64
from logic.paths import get_ui_path
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QColor, QFont


class LandWidget(QWidget):
    def __init__(self, parent=None, main_window=None, valuation_window=None, data_service=None):
        super().__init__(parent)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(0, 0)  # опционально: снимает ограничения по минимальному размеру
        self.setMaximumSize(16777215, 16777215)  # опционально: снимает ограничения по максимальному размеру

        self.main_window = main_window
        self.valuation_window = valuation_window
        self.data_service = data_service or DataEntryForm()
        uic.loadUi(get_ui_path("land_window.ui"), self)
        
        self.init_ui()
        self.analog_count = 0


    def init_ui(self):
        
        self.pushButton__land_analog = self.findChild(QPushButton, "pushButton__land_analog")
        self.pushButton__land_analog.clicked.connect(self.open_land_analog_dialog)


        self.pushButton_check_land_analogs = self.findChild(QPushButton, 'pushButton_check_land_analogs')
        self.pushButton_check_land_analogs.clicked.connect(self.check_land_analogs)
        self.pushButton_check_land_analogs.setVisible(False)
        


        self.tableWidget_land_valuate = self.findChild(QTableWidget, 'tableWidget_land_valuate')
        self.tableWidget_land_valuate.itemChanged.connect(self.recalculate_land_valuation)
        self.tableWidget_land_valuate.setTabKeyNavigation(True)
        self.tableWidget_land_valuate.keyPressEvent = self.handle_key_press
        

        self.label_land_analog_count = self.findChild(QLabel, 'label_land_analog_count')
        self.label_land_analog_count.setText(f'Аналоги не выбраны')

        self.label_land_cost = self.findChild(QLabel, 'label_land_cost')
        self.label_land_cost.setText("")

        self.label_cost_per_sotka = self.findChild(QLabel, 'label_cost_per_sotka')

        self.pushButton_next = self.findChild(QPushButton, 'pushButton_next')
        self.pushButton_next.clicked.connect(self.switch_to_comparative)

        self.pushButton_save_analogs_to_pdf = self.findChild(QPushButton, "pushButton_save_analogs_to_pdf")
        self.pushButton_save_analogs_to_pdf.clicked.connect(self.save_analog_pages_as_pdf)
        self.tableWidget_land_valuate.horizontalHeader().sectionClicked.connect(self.handle_header_click)

    def open_land_analog_dialog(self):
         # Показать загрузку
        loading = LoadingDialog("Подбираем нужные аналоги...", self)
        loading.show()
        QApplication.processEvents()  # 
        dialog = LandAnalogDialog(
            parent=self,
            data_service=self.data_service,
            valuation_window=self.valuation_window
        )
        loading.close()
        if dialog.exec_() == QDialog.Accepted:
            selected = getattr(dialog, "selected_analogs", [])
            if selected:
                count_text = (f'Выбрано аналогов {len(selected)}')
                self.analog_count = count_text
                self.fill_land_valuation_table(selected)
            else:
                self.analog_count = 0
                self.label_land_analog_count.setText("Аналог не выбран")

        
    
    def fill_land_valuation_table(self, analogs):
        table = self.tableWidget_land_valuate
        table.clear()

        try:
            object_area = float(self.valuation_window.lineEdit_land_area.text().replace(",", "."))
        except:
            QMessageBox.warning(self, "Ошибка", "Введите корректную площадь оцениваемого участка.")
            return

        rayon = self.valuation_window.comboBox_rayon.currentText().strip()

        rows = [
            "Статус",
            "Стоимость предложения",
            "Местоположение", "Корректировка на местоположение",
            "Дата предложения", "Корректировка на дату",
            "Площадь участка (сотки)", "Корректировка на площадь",
            "Вид использования", "Корректировка на вид использования",
            "Экономические характеристики", "Корректировка на экономику",
            "Компоненты стоимости, не связанные с недвижимостью", "Корректировка на компоненты",
            "Скорректированная стоимость предложения",
            "Скорректированная стоимость за 1 сотку",
            "Средняя стоимость за 1 сотку"
        ]

        table.setRowCount(len(rows))
        table.setColumnCount(len(analogs) + 1)
        table.setVerticalHeaderLabels(rows)
        table.setHorizontalHeaderItem(0, QTableWidgetItem("Оцениваемый объект"))

        # Заголовки и значения аналогов
        for col, analog in enumerate(analogs, start=1):
            header_item = QTableWidgetItem(f"Аналог {col}")
            header_item.setData(Qt.UserRole, analog.get("url", ""))
            table.setHorizontalHeaderItem(col, header_item)
            table.setItem(0, col, QTableWidgetItem("Активен"))
            clean_price = str(analog['price']).replace("Договорная", "").strip()
            table.setItem(1, col, QTableWidgetItem(clean_price))
            table.setItem(2, col, QTableWidgetItem(f"{analog['location']}"))
            table.setItem(4, col, QTableWidgetItem(f"{analog['date']}"))
            table.setItem(6, col, QTableWidgetItem(str(analog['area'])))
            table.setItem(8, col, QTableWidgetItem("жилой"))

        # Значения для оцениваемого объекта
        table.setItem(0, 0, QTableWidgetItem("—"))
        table.setItem(1, 0, QTableWidgetItem(""))
        table.setItem(2, 0, QTableWidgetItem(rayon))
        table.setItem(4, 0, QTableWidgetItem("—"))
        table.setItem(6, 0, QTableWidgetItem(str(object_area / 100)))
        table.setItem(8, 0, QTableWidgetItem("жилой"))

        # Установка редактируемости
        editable_rows = [3, 5, 7, 9, 11, 13]

        for row in range(table.rowCount()):
            for col in range(1, table.columnCount()):
                item = table.item(row, col)
                if not item:
                    item = QTableWidgetItem("")
                    table.setItem(row, col, item)

                if row in editable_rows:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                    if not item.text():
                        item.setText("0%")
                else:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)


        # Жирный шрифт для некоторых строк
        bold_rows = [0, 1, 14, 15, 16]
        for row in bold_rows:
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

        # Вычисляем строку "Средняя стоимость за 1 сотку" (строка 16)
        try:
            total = 0.0
            count = 0
            for col in range(1, table.columnCount()):
                item = table.item(15, col)
                if item and item.text():
                    val = float(item.text().replace(" ", "").replace(",", "."))
                    total += val
                    count += 1
            if count > 0:
                average = total / count
                avg_item = QTableWidgetItem(f"{average:,.2f}".replace(",", " "))
                avg_item.setFlags(avg_item.flags() & ~Qt.ItemIsEditable)
                font = avg_item.font()
                font.setBold(True)
                avg_item.setFont(font)
                avg_item.setTextAlignment(Qt.AlignCenter)
                table.setItem(16, 0, avg_item)
                table.setSpan(16, 0, 1, table.columnCount())
        except Exception as e:
            print(f"[ERROR] Средняя стоимость: {e}")
        # Форматирование таблицы

        # Подгонка размеров таблицы
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Увеличенный шрифт в первом столбце (названия строк)
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item:
                font = item.font()
                font.setPointSize(12)
                item.setFont(font)

        # Жирный шрифт для "Оцениваемого объекта"
        for row in range(table.rowCount()):
            item = table.item(row, 1)
            if item:
                font = item.font()
                font.setBold(True)
                item.setFont(font)

        # Светлый фон для редактируемых строк
        editable_rows = [3, 5, 7, 9, 11, 13]
        light_bg = QColor("#fefbe9")

        for row in editable_rows:
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item:
                    item.setBackground(light_bg)

        # Обновляем счётчик аналогов
        if self.analog_count:
            self.label_land_analog_count.setText(f'{self.analog_count}')




    def recalculate_land_valuation(self):
        table = self.tableWidget_land_valuate
        table.blockSignals(True)
        try:
            rows = table.rowCount()
            cols = table.columnCount()

            for col in range(1, cols):  
                try:
                    base_price = self._parse_price(table.item(1, col)) 
                    if base_price is None:
                        continue

                    corrected = base_price
                    for row in [3, 5, 7, 9, 11, 13]:  # строки корректировок
                        cell = table.item(row, col)
                        percent = self._parse_percent(cell)
                        raw = cell.text()
                        if raw and not raw.strip().endswith("%"):
                            if re.match(r"^-?\d+([.,]\d+)?$", raw.strip()):
                                cell.setText(f"{raw.strip()}%")
                        corrected *= (1 + percent / 100)

                    # Скорректированная стоимость (строка 14)
                    table.setItem(14, col, QTableWidgetItem(f"{corrected:,.2f}".replace(",", " ")))

                    # Площадь участка
                    area_item = table.item(6, col)
                    if area_item:
                        area = float(area_item.text().replace(",", "."))
                        if area > 0:
                            per_sotka = corrected / area
                            table.setItem(15, col, QTableWidgetItem(f"{per_sotka:,.2f}".replace(",", " ")))
                except Exception as e:
                     _ = e 

            # Пересчёт средней стоимости за 1 сотку (строка 16)
            try:
                total = 0.0
                count = 0
                for col in range(1, cols):
                    item = table.item(15, col)
                    if item and item.text():
                        val = float(item.text().replace(" ", "").replace(",", "."))
                        total += val
                        count += 1
                if count > 0:
                    average = total / count
                    avg_item = QTableWidgetItem(f"{average:,.2f}".replace(",", " "))
                    avg_item.setFlags(avg_item.flags() & ~Qt.ItemIsEditable)
                    avg_item.setTextAlignment(Qt.AlignCenter)
                    font = avg_item.font()
                    font.setBold(True)
                    avg_item.setFont(font)
                    table.setItem(16, 0, avg_item)
                    table.setSpan(16, 0, 1, table.columnCount())

                    #  Обновление итоговых лейблов
                    try:
                        object_area = float(self.valuation_window.lineEdit_land_area.text().replace(",", "."))
                    except:
                        object_area = 0.0

                    total_cost = average * (object_area / 100)
                    self.label_land_cost.setText(
                        f"Стоимость права пользования землёй:{total_cost:,.2f} сум"
                        .replace(",", " ")
                    )

                    try:
                        rate_text = self.valuation_window.exchange_rate_input.text().replace(" ", "").replace(",", ".")
                        rate = float(rate_text) if rate_text else 1
                        converted = average / rate if rate else 0
                        self.cost_per_sotka_soum = total_cost / (object_area / 100)

                        self.label_cost_per_sotka.setText(
                            f"Стоимость за 1 сотку: {converted:,.2f} USD".replace(",", " ")
                        )
                    except Exception as e:
                        self.label_cost_per_sotka.setText("Ошибка при расчёте стоимости в долларах")
                        # print(f"[DEBUG] Ошибка конвертации курса: {e}")
            except Exception as e:
                print(f"[ERROR] Средняя строка: {e}")

        finally:
            table.blockSignals(False)
            table.resizeColumnsToContents()
            table.resizeRowsToContents()




    def _parse_percent(self, item):
        if not item or not item.text():
            return 0.0
        text = item.text().replace("%", "").strip()
        try:
            return float(text)
        except:
            return 0.0

    def _parse_price(self, item):
        if not item or not item.text():
            return None
        text = re.sub(r"[^\d.,]", "", item.text())
        text = text.replace(" ", "").replace(",", ".")
        try:
            return float(text)
        except:
            return None



    def handle_key_press(self, event):
        table = self.tableWidget_land_valuate
        current_row = table.currentRow()
        current_column = table.currentColumn()

        def close_editor():
            item = table.item(current_row, current_column)
            if item:
                table.closePersistentEditor(item)

        handled = False

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            
            next_row = min(current_row + 1, table.rowCount() - 1)
            table.setCurrentCell(next_row, current_column)
            handled = True
        elif event.key() == Qt.Key_Up:
            prev_row = max(0, current_row - 1)
            table.setCurrentCell(prev_row, current_column)
            handled = True
        elif event.key() == Qt.Key_Down:
            next_row = min(current_row + 1, table.rowCount() - 1)
            table.setCurrentCell(next_row, current_column)
            handled = True
        elif event.key() == Qt.Key_Left:
            prev_col = max(0, current_column - 1)
            table.setCurrentCell(current_row, prev_col)
            handled = True
        elif event.key() == Qt.Key_Right:
            next_col = min(current_column + 1, table.columnCount() - 1)
            table.setCurrentCell(current_row, next_col)
            handled = True
        elif event.text().isdigit():
            item = table.item(current_row, current_column)
            if item and (item.flags() & Qt.ItemIsEditable):
                table.editItem(item)
        if not handled:
            QTableWidget.keyPressEvent(table, event)




# СОБИРАЕМ ДАННЫЕ И ОТОБРАЖАЕМ ОБРАТНО


    def collect_land_data(self):
        self.recalculate_land_valuation()

        table = self.tableWidget_land_valuate
        data = {
            "analogs_count": self.analog_count,
            "land_total_cost": self.label_land_cost.text(),
            "cost_per_sotka": self.label_cost_per_sotka.text(),
            "cost_per_sotka_soum": "",
            "vertical_headers": [],
            "horizontal_headers": [],
            "table_data": []
        }
        try:
            if hasattr(self, "cost_per_sotka_soum"):
                data["cost_per_sotka_soum"] = f"{self.cost_per_sotka_soum:,.2f} сум".replace(",", " ")
        except Exception as e:
            print(f"[WARNING] Не удалось сохранить cost_per_sotka_soum: {e}")


        # Сохраняем заголовки строк
        for row in range(table.rowCount()):
            header_item = table.verticalHeaderItem(row)
            data["vertical_headers"].append(header_item.text() if header_item else "")

        # Сохраняем заголовки столбцов
        for col in range(1, table.columnCount()):
            header_item = table.horizontalHeaderItem(col)
            if header_item:
                data["horizontal_headers"].append({
                    "text": header_item.text(),
                    "url": header_item.data(Qt.UserRole) or ""
                })


        # Сохраняем данные ячеек таблицы
        for row in range(table.rowCount()):
            row_data = []
            for col in range(1, table.columnCount()):  # <-- С col = 1
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
            data["table_data"].append(row_data)

        return data






    def load_land_data(self, full_data):
        try:
            table = self.tableWidget_land_valuate

            land_data = full_data.get("land_valuation", {})
            self.analog_count = land_data.get("analogs_count", 0)
            self.label_land_analog_count.setText(f"{self.analog_count}")
            self.label_land_cost.setText(land_data.get("land_total_cost", ""))
            self.label_cost_per_sotka.setText(land_data.get("cost_per_sotka", ""))

            table_data = land_data.get("table_data", [])
            v_headers = land_data.get("vertical_headers", [])
            h_headers = land_data.get("horizontal_headers", [])

            if not table_data:
                return

            row_count = len(table_data)
            col_count = len(table_data[0]) + 1

            table.setRowCount(row_count)
            table.setColumnCount(col_count)

            # Заголовки
            if v_headers and len(v_headers) == row_count:
                table.setVerticalHeaderLabels(v_headers)

            if h_headers and len(h_headers) == col_count - 1:
                table.setHorizontalHeaderItem(0, QTableWidgetItem("Оцениваемый объект"))
                for col, header in enumerate(h_headers, start=1):
                    item = QTableWidgetItem(header.get("text", ""))
                    item.setData(Qt.UserRole, header.get("url", ""))
                    table.setHorizontalHeaderItem(col, item)


            # Район
            rayon = full_data.get("administrative", {}).get("rayon", "—")
            try:
                area = float(full_data.get("land_area", "0").replace(",", ".")) / 100
            except:
                area = 0.0

            first_column_values = [
                "—", "", rayon, "", "—", "", str(area), "", "жилой", "", "", "", "", "", "", "", ""
            ]
            while len(first_column_values) < row_count:
                first_column_values.append("")

            for row_idx in range(row_count):
                item = QTableWidgetItem(first_column_values[row_idx])
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                table.setItem(row_idx, 0, item)

            editable_rows = [3, 5, 7, 9, 11, 13]
            for row_idx, row_data in enumerate(table_data):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(value)
                    table_col = col_idx + 1
                    if row_idx in editable_rows:
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
                        if not value.strip().endswith("%") and re.match(r"^-?\d+([.,]\d+)?$", value.strip()):
                            item.setText(f"{value.strip()}%")
                    else:
                        item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    table.setItem(row_idx, table_col, item)

            bold_rows = [0, 1, 14, 15, 16]
            for row in bold_rows:
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

            self.recalculate_land_valuation()
            

            # Форматирование таблицы
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            # Увеличенный шрифт в первом столбце (названия строк)
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item:
                    font = item.font()
                    font.setPointSize(12)
                    item.setFont(font)

            # Жирный шрифт для "Оцениваемого объекта"
            for row in range(table.rowCount()):
                item = table.item(row, 1)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

            # Светлый фон для редактируемых строк
            editable_rows = [3, 5, 7, 9, 11, 13]
            light_bg = QColor("#fefbe9")

            for row in editable_rows:
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    if item:
                        item.setBackground(light_bg)

        except Exception as e:
            print(f"[ERROR] Не удалось загрузить данные LandWidget: {e}")

        if self.tableWidget_land_valuate.rowCount() > 0 and self.tableWidget_land_valuate.columnCount() > 1:
            self.pushButton_check_land_analogs.setVisible(True)
        else:
            self.pushButton_check_land_analogs.setVisible(False)


    def handle_header_click(self, index):
        item = self.tableWidget_land_valuate.horizontalHeaderItem(index)
        if item:
            url = item.data(Qt.UserRole)
            if url:
                import webbrowser
                webbrowser.open(url)



    # Проверяем актуальность объявлений

    def check_land_analogs(self):
        loading = LoadingDialog("Подождите. Идёт проверка объявлений на сайте...", self)
        loading.show()
        QApplication.processEvents()

        table = self.tableWidget_land_valuate
        status_row = 0
        date_row = 4
        price_row = 1
        area_row = 6

        updates = []
        inactive_count = 0

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(options=options)

        try:
            for col in range(1, table.columnCount()):
                header = table.horizontalHeaderItem(col)
                if not header:
                    print(f"[SKIP] Столбец {col} — нет заголовка")
                    continue
                url = header.data(Qt.UserRole)


                if not url:
                    continue

                try:
                    driver.get(url)
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    body = driver.page_source

                    if "Объявление больше не доступно" in body:
                        table.setItem(status_row, col, QTableWidgetItem("Неактивен"))
                        inactive_count += 1
                        continue

                    # Цена
                    try:
                        price_elem = driver.find_element(By.CSS_SELECTOR, "h3.css-12vqlj3")
                        new_price = price_elem.text.strip()
                    except:
                        new_price = ""

                    # Дата
                    try:
                        date_elem = driver.find_element(By.CSS_SELECTOR, "span.css-19yf5ek")
                        new_date = date_elem.text.strip()
                    except:
                        new_date = ""

                    # Площадь — из заголовка
                    try:
                        title_elem = driver.find_element(By.CSS_SELECTOR, "h1.css-1so6z2e")
                        new_area = self._extract_area_from_title(title_elem.text)
                    except:
                        new_area = ""

                    # Сравнение и обновление
                    def update_if_changed(row, new_value, label):
                        current = table.item(row, col).text().strip() if table.item(row, col) else ""
                        if new_value and current != new_value:
                            table.setItem(row, col, QTableWidgetItem(new_value))
                            updates.append(f"Аналог {col}: изменено поле {label}")

                    update_if_changed(price_row, new_price, "цена")
                    update_if_changed(date_row, new_date, "дата")
                    update_if_changed(area_row, new_area, "площадь")

                except Exception as e:
                    print(f"[WARN] Ошибка проверки аналога {col}: {e}")
                    continue
        finally:
            driver.quit()
            loading.close()


        # Вывод результатов
        if inactive_count > 0:
            QMessageBox.warning(self, "Неактуальные объявления", "Объявления уже не актуальны. Подберите новые аналоги.")
        elif updates:
            QMessageBox.information(self, "Обновлено", "\n".join(updates))
        else:
            QMessageBox.information(self, "Проверка завершена", "Объявления актуальны.")


    def _extract_area_from_title(self, title: str):
        title = title.lower()
        patterns = [
            (r'([\d.,]+)\s*(га|гектар)', 100),
            (r"([\d.,]+)\s*(сотик|соток|сотки|sotih|so'tq)", 1),
            (r'([\d.,]+)\s*(кв.м|кв|м2|квадрат)', 1/100)
        ]
        for pattern, multiplier in patterns:
            match = re.search(pattern, title)
            if match:
                val = float(match.group(1).replace(",", "."))
                return str(round(val * multiplier, 2))
        return ""
    
    
    
    # Сохраняем прайсы

    def save_analog_pages_as_pdf(self):
        loading = LoadingDialog("Подождите. Идёт сохранение pdf...", self)
        loading.show()
        QApplication.processEvents()
        try:
            save_dir = self.valuation_window.main_window.save_directory
            reg_number = self.valuation_window.lineEdit_reg_number.text().strip()
            if not save_dir or not reg_number:
                QMessageBox.warning(self, "Ошибка", "Не выбрана папка проекта или не указан номер отчёта.")
                return

            report_folder = os.path.join(save_dir, reg_number)
            os.makedirs(report_folder, exist_ok=True)

            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--window-size=1920,1080')

            driver = webdriver.Chrome(options=options)

            table = self.tableWidget_land_valuate
            for col in range(1, table.columnCount()):
                header = table.horizontalHeaderItem(col)
                if not header:
                    continue

                url = header.data(Qt.UserRole)
                if not url:
                    continue

                try:
                    driver.get(url)
                    driver.execute_cdp_cmd("Page.enable", {})
                    result = driver.execute_cdp_cmd("Page.printToPDF", {
                        "landscape": False,
                        "printBackground": True,
                        "preferCSSPageSize": True,
                        "pageRanges": "1-2"
                    })

                    pdf_data = base64.b64decode(result['data'])
                    file_path = os.path.join(report_folder, f"прайс_Аналог_{col}.pdf")

                    with open(file_path, "wb") as f:
                        f.write(pdf_data)

                except Exception as e:
                    print(f"[WARN] Не удалось сохранить аналог {col} в PDF: {e}")

            QMessageBox.information(self, "Успешно", "PDF-файлы успешно сохранены.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при сохранении PDF: {e}")
        finally:
            try:
                driver.quit()
                loading.close()
            except:
                pass






    def switch_to_comparative(self):
        """Переключает на вкладку сравнительный подход"""
        # Найдём индекс вкладки "Сравнительный подход"
        index = self.valuation_window.tab_widget.indexOf(self.valuation_window.comparative_tab)
        if index != -1:
           
            self.valuation_window.tab_widget.setCurrentIndex(index)
        self.valuation_window.save_report()