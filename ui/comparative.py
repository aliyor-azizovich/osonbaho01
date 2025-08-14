from PyQt5.QtWidgets import QWidget, QPushButton, QMessageBox, QLabel, QTableWidget, QDialog, QTableWidgetItem, QSizePolicy, QApplication
from PyQt5.QtCore import Qt
from PyQt5 import uic
import os
from ui.comparative_dialogs.comparative_analog_dialog import ComparativeAnalogDialog
from logic.data_entry import DataEntryForm
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import base64
from logic.loading_animation import LoadingDialog
from logic.paths import get_ui_path, get_project_dir
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtGui import QColor, QFont

class ComparativeWidget(QWidget):
    def __init__(self, parent=None, main_window=None, valuation_window=None, data_service=None):
        super().__init__(parent)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(size_policy)
        self.setMinimumSize(0, 0)  # опционально: снимает ограничения по минимальному размеру
        self.setMaximumSize(16777215, 16777215)  # опционально: снимает ограничения по максимальному размеру

        self.main_window = main_window
        self.valuation_window = valuation_window
        self.data_service = data_service or DataEntryForm()
        uic.loadUi(get_ui_path("comparative_widget.ui"), self)

        
        self.init_ui()
       


    def init_ui(self):
        
        self.pushButton_choose_comparative_analogs = self.findChild(QPushButton, "pushButton_choose_comparative_analogs")
        self.pushButton_choose_comparative_analogs.clicked.connect(self.open_comparative_analog_dialog)


        self.pushButton_check_comparative_analogs = self.findChild(QPushButton, "pushButton_check_comparative_analogs")
        self.pushButton_check_comparative_analogs.clicked.connect(self.check_analogs)
        self.pushButton_check_comparative_analogs.setVisible(False)

        self.tableWidget_comparative_valuate = self.findChild(QTableWidget, 'tableWidget_comparative_valuate')
        self.tableWidget_comparative_valuate.itemChanged.connect(self.recalculate_comparative_valuation)
        self.tableWidget_comparative_valuate.setTabKeyNavigation(True)
        self.tableWidget_comparative_valuate.keyPressEvent = self.handle_key_press
        self.tableWidget_comparative_valuate.horizontalHeader().sectionClicked.connect(self.handle_header_click)

        self.pushButton_save_analogs_to_pdf = self.findChild(QPushButton, "pushButton_save_analogs_to_pdf")
        self.pushButton_save_analogs_to_pdf.clicked.connect(self.save_analog_pages_as_pdf)
        self.label_comparative_final_cost = self.findChild(QLabel, 'label_comparative_final_cost')
       

        
        self.pushButton_next = self.findChild(QPushButton, "pushButton_next")
        self.pushButton_next.clicked.connect(self.switch_to_agreement)

        

    def open_comparative_analog_dialog(self):
         
        loading = LoadingDialog("Подбираем нужные аналоги...", self)
        loading.show()
        QApplication.processEvents()
        dialog = ComparativeAnalogDialog(self, self.data_service, self.valuation_window)
        loading.close()

        if dialog.exec_() == QDialog.Accepted:
            selected = dialog.selected_analogs
            self.fill_home_valuation_table(selected)


        
    def fill_home_valuation_table(self, analogs):
        table = self.tableWidget_comparative_valuate
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
            "Корректировка на уторговывание",
            "Местоположение", "Корректировка на местоположение",
            "Дата предложения", "Корректировка на дату",
            "Площадь участка (сотки)", "Корректировка на площадь",
            "Физическое состояние дома", "Корректировки на физические характеристики объекта оценки",
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
            table.setItem(3, col, QTableWidgetItem(f"{analog['location']}"))
            table.setItem(5, col, QTableWidgetItem(f"{analog['date']}"))
            table.setItem(7, col, QTableWidgetItem(str(analog['area'])))
            table.setItem(9, col, QTableWidgetItem("жилой"))

        # Значения для оцениваемого объекта
        table.setItem(0, 0, QTableWidgetItem("—"))
        table.setItem(1, 0, QTableWidgetItem(""))
        table.setItem(2, 0, QTableWidgetItem(""))
        table.setItem(3, 0, QTableWidgetItem(rayon))
        table.setItem(5, 0, QTableWidgetItem("—"))
        table.setItem(7, 0, QTableWidgetItem(str(object_area / 100)))
        table.setItem(9, 0, QTableWidgetItem("жилой"))

        # Установка редактируемости
        editable_rows = [2, 4, 6, 8, 10, 12, 14]

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

        # Вычисляем строку "Средняя стоимость за 1 сотку" (строка 17)
        try:
            total = 0.0
            count = 0
            for col in range(1, table.columnCount()):
                item = table.item(16, col)
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
                table.setItem(17, 0, avg_item)
                table.setSpan(17, 0, 1, table.columnCount())
        except Exception as e:
            print(f"[ERROR] Средняя стоимость: {e}")

        # Обновляем счётчик аналогов
       # Настройка отображения
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        


    def recalculate_comparative_valuation(self):
        table = self.tableWidget_comparative_valuate
        table.blockSignals(True)

        try:
            rows = table.rowCount()
            cols = table.columnCount()

            for col in range(1, cols):  # пропускаем колонку оцениваемого объекта (0)
                try:
                    base_price = self._parse_price(table.item(1, col))  # строка 1: Стоимость предложения
                    if base_price is None:
                        continue

                    corrected = base_price
                    for row in [2, 4, 6, 8, 10, 12, 14]:  # строки корректировок
                        cell = table.item(row, col)
                        percent = self._parse_percent(cell)
                        raw = cell.text()
                        if raw and not raw.strip().endswith("%"):
                            if re.match(r"^-?\d+([.,]\d+)?$", raw.strip()):
                                cell.setText(f"{raw.strip()}%")
                        corrected *= (1 + percent / 100)

                    # Строка 15: Скорректированная стоимость
                    table.setItem(15, col, QTableWidgetItem(f"{corrected:,.2f}".replace(",", " ")))

                    # Строка 7: Площадь участка
                    area_item = table.item(7, col)
                    if area_item:
                        area = float(area_item.text().replace(",", "."))
                        if area > 0:
                            per_sotka = corrected / area
                            table.setItem(16, col, QTableWidgetItem(f"{per_sotka:,.2f}".replace(",", " ")))
                except Exception as e:
                    _ = e  # подавление лишних ошибок в цикле

            # строка 17: Средняя стоимость за 1 сотку
            try:
                total = 0.0
                count = 0
                for col in range(1, cols):
                    item = table.item(16, col)
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
                    table.setItem(17, 0, avg_item)
                    table.setSpan(17, 0, 1, table.columnCount())

                    # Обновление метки с оценкой
                    try:
                        area_val = float(self.valuation_window.lineEdit_land_area.text().replace(",", ".")) / 100
                    except:
                        area_val = 0.0

                    total_cost = average * area_val
                    self.label_comparative_final_cost.setText(
                        f"Оценочная стоимость сравнительным подходом: {total_cost:,.2f} сум".replace(",", " ")
                    )
                    self.comparative_cost = total_cost
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
        table = self.tableWidget_comparative_valuate
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



    def handle_header_click(self, index):
        item = self.tableWidget_comparative_valuate.horizontalHeaderItem(index)
        if item:
            url = item.data(Qt.UserRole)
            if url:
                import webbrowser
                webbrowser.open(url)



    # Проверяем актуальность объявлений

    def check_analogs(self):
        loading = LoadingDialog("Подождите. Идёт проверка объявлений на сайте...", self)
        loading.show()
        QApplication.processEvents()

        table = self.tableWidget_comparative_valuate
        status_row = 0
        date_row = 5
        price_row = 1
        area_row = 7

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

            table = self.tableWidget_comparative_valuate
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
                    file_path = os.path.join(report_folder, f"прайс_дом_Аналог_{col}.pdf")

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




    # Сохраняем и отображаем страницу

    def collect_comparative_data(self):
        self.recalculate_comparative_valuation()

        table = self.tableWidget_comparative_valuate
        data = {
           "label_comparative_final_cost": self.label_comparative_final_cost.text(),
            "vertical_headers": [],
            "horizontal_headers": [],
            "table_data": []
        }

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






    def load_comparative_data(self, full_data):
        try:
            table = self.tableWidget_comparative_valuate
            

            comparative_data = full_data
            self.label_comparative_final_cost.setText(comparative_data.get("label_comparative_final_cost", ""))
            

            table_data = comparative_data.get("table_data", [])
            v_headers = comparative_data.get("vertical_headers", [])
            h_headers = comparative_data.get("horizontal_headers", [])

            if not table_data:
                return

            row_count = len(table_data)
            col_count = len(table_data[0]) + 1

            table.setRowCount(row_count)
            # Гарантируем, что ячейки в 0-м столбце созданы
            for row in range(table.rowCount()):
                if not table.item(row, 0):
                    table.setItem(row, 0, QTableWidgetItem(""))

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
                area_raw = full_data.get("land_area", "").replace(",", ".")
                area = float(area_raw) / 100 if area_raw else ""
                
            except:
                area = "f;b,e;"

            first_column_values = [""] * table.rowCount()
            first_column_values[0] = "—"
            first_column_values[3] = rayon
            first_column_values[5] = "—"
            first_column_values[7] = f"{area:.2f}" if area else ""
            first_column_values[9] = "жилой"

            while len(first_column_values) < row_count:
                first_column_values.append("")

            for row_idx in range(row_count):
                item = QTableWidgetItem(first_column_values[row_idx])
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                table.setItem(row_idx, 0, item)

            editable_rows = [2, 4, 6, 8, 10, 12, 14]
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
            # форматирование таблицы после загрузки
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            

            self.recalculate_comparative_valuation()
            print("[DEBUG]", self.valuation_window.lineEdit_land_area.text())
            print("[DEBUG]", self.valuation_window.comboBox_rayon.currentText())

        except Exception as e:
            print(f"[ERROR] Не удалось загрузить данные ComparativeWidget: {e}")

        if self.tableWidget_comparative_valuate.rowCount() > 0 and self.tableWidget_comparative_valuate.columnCount() > 1:
            self.pushButton_check_comparative_analogs.setVisible(True)
        else:
            self.pushButton_check_comparative_analogs.setVisible(False)





    def switch_to_agreement(self):
        """Переключает на вкладку согласование"""
        # Найдём индекс вкладки "согласование"
        index = self.valuation_window.tab_widget.indexOf(self.valuation_window.agreement_tab)
        if index != -1:
            # Устанавливаем текущую вкладку
            self.valuation_window.tab_widget.setCurrentIndex(index)
        self.valuation_window.save_report()