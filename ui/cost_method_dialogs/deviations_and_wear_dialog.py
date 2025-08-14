from PyQt5.QtWidgets import QDialog, QGridLayout, QCheckBox, QPushButton, QLabel, QGroupBox, QMessageBox, QVBoxLayout, QComboBox, QWidget, QTableWidget, QLineEdit, QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os
import pandas as pd
from logic.data_entry import DataEntryForm
from logic.paths import get_ui_path
from PyQt5.QtGui import QIcon

# from  ui.ukup_window import UkupWidget
class DeviationsAndWearDialog(QDialog):
    def __init__(self, parent=None, data_service=None, valuation_window=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("cost_method_dialogs/deviations_and_wear_dialog.ui"), self)

        self.setWindowTitle("Применение корректировок и рассчёт износа")
        
        self.setWindowIcon(QIcon("icon.ico"))  
        self.parent = parent
        self.data_service = data_service or DataEntryForm()
        self.valuation_window = valuation_window  # <-- добавляем

        self.building_id = parent.selected_analog_index
        self.altitude_data = self.data_service.altitude()
        self.tableWidget_wear = self.findChild(QTableWidget, 'tableWidget_wear')
        
        self.tableWidget_wear.keyPressEvent = self.handle_key_press

        wear_df = self.load_structural_elements(self.building_id)  # или другая функция
        if wear_df is not None:
            self.populate_wear_table(wear_df)
        

        self.groupBox_deviations = self.findChild(QGroupBox, 'groupBox_deviations')
        self.groupBox_improvements = self.findChild(QGroupBox, 'groupBox_improvements')

        self.comboBox_facade = self.findChild(QComboBox, "comboBox_facade")
        self.label_injener_correct = self.findChild(QLabel, 'label_injener_correct')
        self.comboBox_type_koeff = self.findChild(QComboBox, 'comboBox_type_koeff')
        self.comboBox_type_koeff.currentTextChanged.connect(self.on_type_selected)


        self.label_unit_corrected_price = self.findChild(QLabel, 'label_unit_corrected_price')
        self.label_unit = self.findChild(QLabel, 'label_unit')
        self.label_reg_koeff = self.findChild(QLabel, 'label_reg_koeff')
        self.label_stat_koeff = self.findChild(QLabel, 'label_stat_koeff')
        self.label_developper = self.findChild(QLabel, 'label_developper')
        self.label_inconsistency = self.findChild(QLabel, 'label_inconsistency')

        self.label_wear = self.findChild(QLabel, 'label_wear')
        self.label_final_cost = self.findChild(QLabel, 'label_final_cost')
        self.label_facade_result = self.findChild(QLabel, "label_facade_result")
        self.label_height_correction = self.findChild(QLabel, 'label_height_correction')
        self.label_sesmos = self.findChild(QLabel, "label_sesmos")
        self.lineEdit_corrected_price = self.findChild(QLineEdit, 'lineEdit_corrected_price')
        self.lineEdit_unit = self.findChild(QLineEdit, 'lineEdit_unit')
        self.lineEdit_reg_koeff = self.findChild(QLineEdit, 'lineEdit_reg_koeff')
        self.lineEdit_stat_koeff = self.findChild(QLineEdit, 'lineEdit_stat_koeff')
        self.lineEdit_developper = self.findChild(QLineEdit, 'lineEdit_developper')
        self.lineEdit_sesmos = self.findChild(QLineEdit, "lineEdit_sesmos")
        self.lineEdit_sesmos.setReadOnly(True)

        self.lineEdit_developper.setText(self.valuation_window.lineEdit_developer.text())
        text = float(self.lineEdit_developper.text().replace('%', '').strip())
        self.developer = text if text else 0


        self.lineEdit_inconsistency = self.findChild(QLineEdit, 'lineEdit_inconsistency')
        self.lineEdit_inconsistency.textChanged.connect(self.recalculate_all)

        self.lineEdit_wear = self.findChild(QLineEdit, 'lineEdit_wear')
        self.lineEdit_final_cost = self.findChild(QLineEdit, 'lineEdit_final_cost')
        self.pushButton_OK = self.findChild(QPushButton, 'pushButton_OK')
        self.pushButton_OK.clicked.connect(self.on_accept)

        self.lineEdit_corrected_price.setReadOnly(True)
        self.lineEdit_wear.setReadOnly(True)

        self.set_seismic_correction()
        self.facade_data = self.data_service.facade()  
        self.fill_facade_combobox()
        self.comboBox_facade.currentIndexChanged.connect(self.on_facade_selected)
        self.set_stat_koeff()
        self.set_reg_coeff()
        self.update_label_unit()
        self.show_improvements_labels()
        self.show_deviations_checkboxes()
        self.high_correction()
        self.recalculate_all()
        
        self.finalize_replacement_cost()

    def fill_facade_combobox(self):
        if self.facade_data is not None:
            facade_types = self.facade_data['facade_type'].dropna().unique()
            self.comboBox_facade.addItem("Выберите фасад")
            self.comboBox_facade.addItems(facade_types)


    def on_facade_selected(self, index):
        if self.building_id is None:
            return
        if index == 0:
            self.facade_corrected_price = 0  # ✅ Устанавливаем в 0, если фасад не выбран
            self.label_facade_result.setText("Фасад не выбран")
            return

        # Применяется только к ID 1–136 и 140–155
        if not (1 <= self.building_id <= 136 or 140 <= self.building_id <= 144 or 153 <= self.building_id <= 155):
            self.facade_corrected_price = 0  # ✅ Обнуляем, если фасад не применяется
            self.label_facade_result.setText("Поправка на фасад не применяется для данного типа здания")
            return

        selected_type = self.comboBox_facade.currentText()
        row = self.facade_data[self.facade_data['facade_type'] == selected_type]

        if row.empty:
            QMessageBox.warning(self, "Ошибка", f"Не найдена запись для фасада: {selected_type}")
            self.facade_corrected_price = 0  # ✅ Устанавливаем 0, если фасад не найден
            return

        try:
            percent = row['%'].values[0]
            price_str = self.parent.label_price_result.text().replace("Стоимость за м² по УКУП:", "").strip().split()[0]
            price = float(price_str.replace(",", "").replace(" ", ""))
            self.facade_corrected_price = price * percent  # ✅ Расчет корректировки

            self.label_facade_result.setText(
                f"Стоимость корректировки на улучшение фасада: {self.facade_corrected_price:,.2f} сум"
            )
            self.recalculate_all()

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось применить корректировку: {e}")
            self.facade_corrected_price = 0  # ✅ Устанавливаем 0 в случае ошибки
        





    def show_improvements_labels(self):
        """Отображает QLabel'ы с инженерными корректировками (без чекбоксов)"""
        improvements_df = self.data_service.Improvements()

        # 📌 Даже если нет улучшений — всё равно нужно базовую цену задать!
        label_price_result = self.parent.label_price_result.text().replace("Стоимость за м² по УКУП:", "").strip().split()[0]
        self.ukup_price = float(label_price_result.replace(" ", "").replace(",", ""))

        if improvements_df is None or self.building_id not in improvements_df.index:
            self.improvement_correction = 0.0  # ⬅️ по умолчанию
            return

        _, applied_improvements = self.apply_improvements_logic(self.building_id, price_per_m2=0.0)

        if self.groupBox_improvements.layout() is None:
            self.groupBox_improvements.setLayout(QVBoxLayout())
        layout = self.groupBox_improvements.layout()

        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            layout.removeWidget(widget)
            widget.setParent(None)

        total_percent = 0.0

        for name, correction in applied_improvements:
            total_percent += correction
            percent_str = f"{correction * 100:+.2f}%"
            label = QLabel(f"{name}: {percent_str}")
            layout.addWidget(label)

        total_sum = self.ukup_price * total_percent
        total_label = QLabel(f"<b>Сумма всех инженерных корректировок: {total_sum:,.2f} сум</b>")
        layout.addWidget(total_label)

        self.improvement_correction = total_sum






    def show_deviations_checkboxes(self):
        """Отображает чекбоксы с отклонениями и итоговую корректировку"""
        deviations_df = self.data_service.Deviations()

        if deviations_df is None or self.building_id not in deviations_df.index:
            return

        row = deviations_df.loc[self.building_id]

        # Убедимся, что layout у groupBox_deviations есть
        if self.label_injener_correct.layout() is None:
            self.label_injener_correct.setLayout(QVBoxLayout())

        layout = self.label_injener_correct.layout()

        # Очистим старые элементы
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            layout.removeWidget(widget)
            widget.setParent(None)

        self.deviation_checkboxes = {}
        self.deviation_correction = 0.0

        for column, value in row.items():
            if pd.notna(value) and str(value).strip() != '':
                checkbox = QCheckBox(f"{column}: {float(value):+.2f} сум")
                checkbox.stateChanged.connect(self.update_selected_deviations)
                layout.addWidget(checkbox)
                self.deviation_checkboxes[column] = (checkbox, float(value))

        # Добавим QLabel для итоговой суммы
        self.label_deviation_total = QLabel("Суммарная корректировка: 0.00 сум")
        layout.addWidget(self.label_deviation_total)


    def update_selected_deviations(self):
        """Обновляет сумму отклонений по выбранным чекбоксам"""
        if not hasattr(self, 'deviation_checkboxes'):
            return

        total = 0.0
        for _, (checkbox, value) in self.deviation_checkboxes.items():
            if checkbox.isChecked():
                total += value

        self.deviation_correction = total
        self.label_deviation_total.setText(f"Суммарная корректировка: {total:,.2f} сум")
        self.recalculate_all()
        



    def apply_improvements_logic(self, building_id, price_per_m2):
        """Применяет инженерные корректировки к цене и сохраняет сумму поправок"""
        general_data = self.valuation_window.collect_general_data()

        improvements_df = self.parent.data_service.Improvements()

        if building_id not in improvements_df.index:
            self.improvement_correction = 0
            return price_per_m2, []

        analog_improvements = improvements_df.loc[[building_id]]

        improvements_mapping = {
            'газификация': 'газификация',
            'электроосвещение': 'электроосвещение',
            'водоснабжение': 'водоснабжение',
            'канализация': 'канализация',
            'телефонная_линия': 'телефонная линия',
            'электрический_водонагреватель': 'электрический водонагреватель',
            'горячее_водоснабжение': 'горячее водоснабжение',
            'отопление_печное': 'печное отопление',
            'отопление_центральное': 'центральное отопление',
            'отопление_АГВ': 'водяное отопление (АГВ, двухконтурный котёл)'
        }

        applied_improvements = []
        total_percent = 0.0
        heating_selected = general_data.get('отопление', '').lower()

        central_correction_applied = False
        central_heating_present = False
        alternative_heating_selected = heating_selected in ['водяное отопление (агв, двухконтурный котёл)', 'печное отопление']

        for _, row in analog_improvements.iterrows():
            improvement_name = row['Улучшение']
            has_improvement = row['Имеется']
            correction_factor = row['Поправка']

            # 📌 НЕ добавляем "Центральное отопление" сразу
            if improvement_name.lower() == 'центральное отопление':
                central_heating_present = has_improvement == 1
                continue  # ⛔ НЕ добавляем эту корректировку в основном цикле!

            elif improvement_name.lower() in ['печное отопление', 'водяное отопление (агв, двухконтурный котёл)']:
                if heating_selected == improvement_name.lower() and has_improvement == 0:
                    applied_improvements.append((f'Наличие {improvement_name}', correction_factor))
                    total_percent += correction_factor
                elif heating_selected != improvement_name.lower() and has_improvement == 1:
                    applied_improvements.append((f'Отсутствие {improvement_name}', -correction_factor))
                    total_percent -= correction_factor
                continue

            for general_key, mapped_name in improvements_mapping.items():
                if mapped_name.lower() == improvement_name.lower():
                    user_selected = general_data.get(general_key, False)

                    if has_improvement == 0 and user_selected:
                        applied_improvements.append((improvement_name, correction_factor))
                        total_percent += correction_factor

                    elif has_improvement == 1 and not user_selected:
                        applied_improvements.append((improvement_name, -correction_factor))
                        total_percent -= correction_factor
                    break

        # 📌 Теперь обрабатываем Центральное отопление отдельно, если нужно
        if central_heating_present and alternative_heating_selected and not central_correction_applied:
            correction_factor = analog_improvements[
                analog_improvements['Улучшение'].str.lower() == 'центральное отопление'
            ]['Поправка'].values[0]

            applied_improvements.append(('Отсутствие центрального отопления', -correction_factor))
            total_percent -= correction_factor

            # ✅ Проверяем, есть ли выбранное пользователем отопление в аналоге
            selected_heating_row = analog_improvements[
                analog_improvements['Улучшение'].str.lower() == heating_selected
            ]

            if not selected_heating_row.empty:
                # Если отопление найдено в аналоге, берем его поправку
                selected_heating_correction = selected_heating_row['Поправка'].values[0]
                applied_improvements.append((f'Наличие {heating_selected}', selected_heating_correction))
                total_percent += selected_heating_correction
            else:
                # Если отопления нет в аналоге, прибавляем стандартные 0.065
                applied_improvements.append(('Наличие альтернативного отопления ', 0.065))
                total_percent += 0.065

            central_correction_applied = True  # ✅ Корректировка применена, больше не повторяется

        
        # ✅ Рассчитываем итоговую сумму в деньгах
        try:
            price_str = self.parent.label_price_result.text().replace("Стоимость за м² по УКУП:", "").strip().split()[0]
            base_price = float(price_str.replace(" ", "").replace(",", ""))
            self.improvement_correction = base_price * total_percent
            
        except Exception as e:
            self.improvement_correction = 0
           

        return price_per_m2, applied_improvements
    

    def update_selected_improvements(self):
        """Подсчитывает сумму выбранных улучшений (без отображения)"""
        if not hasattr(self, 'improvement_checkboxes'):
            return

        total_percent = 0.0
        for _, (checkbox, value) in self.improvement_checkboxes.items():
            if checkbox.isChecked():
                total_percent += value

        try:
            price_str = self.parent.label_price_result.text().replace("Стоимость за м² по УКУП:", "").strip().split()[0]
            price = float(price_str.replace(" ", "").replace(",", ""))
            self.improvement_correction = price * total_percent
        except Exception:
            self.improvement_correction = 0.0
        


    def high_correction(self, index=None):
        try:
            # Применяется только к ID от 1 до 108
            if not (1 <= self.building_id <= 108):
                self.label_height_correction.setText("Поправка на высоту не применяется для данного типа здания")
                self.high_corrected_price = 0
                return

            height_str = self.parent.lineEdit_height.text().replace(',', '.')
            fact_high_value = float(height_str)

            if fact_high_value < 2.4:
                koeff = 1.06
            elif fact_high_value > 4.0:
                koeff = 0.9
            else:
                filter_high_df = self.altitude_data[
                    self.altitude_data['Полезная высота, м'] == fact_high_value
                ]
                if filter_high_df.empty:
                    self.label_height_correction.setText("Коэффициент для высоты не найден")
                    self.high_corrected_price = 0
                    return

                koeff = filter_high_df['Поправочный коэффициент'].values[0]

            price_str = self.parent.label_price_result.text().replace("Стоимость за м² по УКУП:", "").strip().split()[0]
            price_per_m2 = float(price_str.replace(",", "").replace(" ", ""))

            high_correction_result = price_per_m2 * (koeff - 1)
            self.high_corrected_price = high_correction_result

            self.label_height_correction.setText(
                f"Стоимость корректировки на высоту: {high_correction_result:,.2f} сум"
            )
            self.recalculate_all()
            
        except Exception as e:
            # QMessageBox.warning(self, "Ошибка", f"Ошибка при расчёте поправки на высоту: {e}")
            self.high_corrected_price = 0



    def update_corrected_price(self):
        """Пересчитывает и обновляет итоговую скорректированную цену с отладочным выводом"""
        ukup = getattr(self, 'ukup_price', 0.0)
        improvement = getattr(self, 'improvement_correction', 0.0)
        deviation = getattr(self, 'deviation_correction', 0.0)
        height = getattr(self, 'high_corrected_price', 0.0)
        facade = getattr(self, 'facade_corrected_price', 0.0)

        total = ukup + improvement + deviation + height + facade
        self.total_ukup = total
        

        if self.lineEdit_corrected_price is not None:
            self.lineEdit_corrected_price.setText(f"{total:,.2f}")
        
    def update_label_unit(self):
        """Обновляет label_unit и значение unit_value на основе данных UKUP"""
        df = self.data_service.ukup()
        if self.building_id not in df.index:
            self.label_unit.setText("Ед. изм. не определена")
            self.unit_value = 1
            self.lineEdit_unit.setText("1")
            return

        row = df.loc[self.building_id]

        # Значения из интерфейса
        square = self.parent.lineEdit_square.text().strip().replace(",", ".")
        volume = self.parent.lineEdit_volume.text().strip().replace(",", ".")
        length = self.parent.lineEdit_length.text().strip().replace(",", ".")

        # Если есть площадь — в первую очередь проверяем её
        if pd.notna(row.get('Площадь до м2')) and square:
            try:
                self.unit_value = float(square)
            except ValueError:
                self.unit_value = 1.0
            self.label_unit.setText("Площадь: м²")
            self.lineEdit_unit.setText(str(self.unit_value))

        elif pd.notna(row.get('Объём до м3')) and volume:
            try:
                self.unit_value = float(volume)
            except ValueError:
                self.unit_value = 1.0
            self.label_unit.setText("Объём: м³")
            self.lineEdit_unit.setText(str(self.unit_value))

        elif pd.notna(row.get('Протяженность')) and length:
            try:
                self.unit_value = float(length)
            except ValueError:
                self.unit_value = 1.0
            self.label_unit.setText("Длина: м")
            self.lineEdit_unit.setText(str(self.unit_value))

        else:
            self.unit_value = 1.0
            self.label_unit.setText("За штуку")
            self.lineEdit_unit.setText("1")

        
    def set_seismic_correction(self):
        try:
            df = self.data_service.territorial_correction()
            if df is None:
                raise ValueError("Не удалось загрузить таблицу территориальных корректировок.")

            selected_region = self.valuation_window.comboBox_oblast.currentText()
            match = df[df['region'] == selected_region]

            if match.empty:
                raise ValueError(f"Область '{selected_region}' не найдена в таблице.")

            # Применяем территориальный коэффициент всегда
            self.territorial = float(match.iloc[0]['correction'])

            # Применяем сейсмический коэффициент только для 1, 2, 107, 108
            if self.building_id in [1, 2, 107, 108]:
                self.sesmos = float(match.iloc[0]['sesmos_correction'])
                self.lineEdit_sesmos.setText(f"{self.sesmos:.3f}")
                self.lineEdit_sesmos.show()
                if hasattr(self, "label_sesmos"):
                    self.label_sesmos.show()
            else:
                self.sesmos = 1.0
                self.lineEdit_sesmos.setText("1.000")
                self.lineEdit_sesmos.hide()
                if hasattr(self, "label_sesmos"):
                    self.label_sesmos.hide()

        except Exception as e:
            self.sesmos = 1.0
            self.territorial = 1.0
            self.lineEdit_sesmos.setText("1.000")
            self.lineEdit_sesmos.hide()
            if hasattr(self, "label_sesmos"):
                self.label_sesmos.hi_



    def set_reg_coeff(self):
        

        oblast = self.valuation_window.comboBox_oblast.currentText()
        
        # Загружаем таблицы
        df_reg = self.data_service.territorial_correction() 
        df_reg_coeff = self.data_service.load_regional_coff()


        # Ищем region_id по названию области
        reg_row = df_reg[df_reg['region'] == oblast]
        if reg_row.empty:
            QMessageBox.warning(self, "Ошибка", f"Регион '{oblast}' не найден в справочнике.")
            return

        reg_id = reg_row.iloc[0]['region_id']  # получаем значение region_id

        # Фильтруем коэффициенты по region_id
        filtered = df_reg_coeff[df_reg_coeff['region_id'] == reg_id]

        if filtered.empty:
            QMessageBox.warning(self, "Нет данных", f"Нет коэффициентов для региона: {oblast}")
            return
        self.filtered_reg_coeff = filtered  # ← добавь это!

        self.comboBox_type_koeff.clear()  # очищаем комбобокс перед добавлением
        types = filtered['type'].dropna().unique()


        for t in filtered['type'].dropna().unique():
            self.comboBox_type_koeff.addItem(str(t))
        # Устанавливаем первый тип и запускаем обработчик
        if types.size > 0:
            self.comboBox_type_koeff.setCurrentIndex(0)  # устанавливаем первый элемент явно
            selected_type = self.comboBox_type_koeff.currentText()
            self.on_type_selected(selected_type)  # вручную вызываем обработчик
        

    def on_type_selected(self, selected_type):
        if not hasattr(self, 'filtered_reg_coeff'):
            return

        row = self.filtered_reg_coeff[self.filtered_reg_coeff['type'] == selected_type]

        if row.empty:
            self.lineEdit_reg_koeff.setText("0")
            self.label_reg_koeff.setText("Тип не найден")
            return

        coeff = row.iloc[0]['coff']
        self.lineEdit_reg_koeff.setText(f"{coeff:.3f}")
        self.label_reg_koeff.setText(f"{selected_type}")
        self.reg_coeff = coeff
        self.recalculate_all()

    def set_stat_koeff(self):
        df_stat = self.data_service.load_stat_koeff()
        result = df_stat['Коэфф'].prod()
        date = df_stat['Дата'].tail(1).values[0]
        self.lineEdit_stat_koeff.setText(f"{result:.3f}")
        self.label_stat_koeff.setText(f"Коэффициент Госкомстата с  01.04.2004 по {date}")
        self.stat_coeff = result
        self.recalculate_all()
   
    def wrap_text(self, text, max_length=40):
        if len(text) <= max_length:
            return text
        # Найти ближайший пробел к max_length
        nearest_space = text.rfind(' ', 0, max_length)
        if nearest_space == -1:
            nearest_space = max_length
        return text[:nearest_space] + '\n' + text[nearest_space+1:]

    
    def populate_wear_table(self, df):
        


        row_count = len(df) + 1
        col_count = len(df.columns)
        self.tableWidget_wear.horizontalHeader().setStretchLastSection(True)
        

        self.tableWidget_wear.setRowCount(row_count)
        self.tableWidget_wear.setColumnCount(col_count)
        # Исходные названия
        headers = list(df.columns)

        # Заменяем на более читаемые с переносами строк
        renamed_headers = []
        for h in headers:
            if h == "Поправка к удельным весам %":
                renamed_headers.append("Поправка к\nудельным весам %")
            elif h == "Физический износ %":
                renamed_headers.append("Физический\nизнос %")
            else:
                renamed_headers.append(h)

        self.tableWidget_wear.setHorizontalHeaderLabels(renamed_headers)

        
        

        for row_idx, row in enumerate(df.itertuples(index=False)):
            max_lines = 1

            for col_idx, value in enumerate(row):
                display_value = str(value)
                if df.columns[col_idx] == "Конструкции":
                    display_value = self.wrap_text(display_value)
                    max_lines = value.count("\n") + 1  # учитываем количество строк

                item = QTableWidgetItem(display_value)
                if col_idx in [2, 3]:  # Колонки с редактируемыми значениями
                    # Если значение пустое или не число, инициализируем как 0.0
                    if not value or not str(value).replace('.', '', 1).isdigit():
                        value = 0.0
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tableWidget_wear.setItem(row_idx, col_idx, item)
            base_height = 25  # можно подогнать под стиль приложения
            self.tableWidget_wear.setRowHeight(row_idx, base_height * max_lines)
        self.add_total_row(df)
        self.tableWidget_wear.itemChanged.connect(self.update_total_row)
        self.update_total_row()
        self.tableWidget_wear.resizeColumnsToContents()

    def add_total_row(self, df):
        row_idx = self.tableWidget_wear.rowCount() - 1
        for col in range(self.tableWidget_wear.columnCount()):
            item = QTableWidgetItem()
            if col == 0:
                item.setText("ВСЕГО")
            item.setFlags(Qt.ItemIsEnabled)  # ❗ Только отображение, без редактирования и выделения
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.tableWidget_wear.setItem(row_idx, col, item)

        self.update_total_row()



    def update_total_row(self):
        self.recalculate_all()

        

    def load_structural_elements(self, building_id):
        df = self.data_service.structural_elements()
        if df is None or df.empty:
            QMessageBox.warning(self.parent, "Ошибка", "Нет данных по конструктивным элементам.")
            return

        if building_id not in df.index:
            QMessageBox.warning(self.parent, "Ошибка", f"Нет данных для ID: {building_id}")
            return
        df_filtered = df[df.index == building_id][["Конструкции", "Доля %"]].copy()

        # Удалим возможную колонку "Описание" или другие лишние
        df_filtered = df_filtered.loc[:, ["Конструкции", "Доля %"]]

        # Добавим и упорядочим колонки
        df_filtered["Поправка к удельным весам %"] = 0.0
        df_filtered["Физический износ %"] = 0.0
        df_filtered = df_filtered[["Конструкции", "Доля %", "Поправка к удельным весам %", "Физический износ %"]]
        return df_filtered
        
    def handle_key_press(self, event):
        """Обрабатывает нажатие клавиши Enter и стрелок для перемещения по ячейкам."""
        current_row = self.tableWidget_wear.currentRow()
        current_column = self.tableWidget_wear.currentColumn()

        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Переход вниз на одну строку
            next_row = current_row + 1
            if next_row < self.tableWidget_wear.rowCount():
                self.tableWidget_wear.setCurrentCell(next_row, current_column)
                self.tableWidget_wear.editItem(self.tableWidget_wear.item(next_row, current_column))
        elif event.key() == Qt.Key_Up:
            # Переход на строку выше
            prev_row = max(0, current_row - 1)
            self.tableWidget_wear.setCurrentCell(prev_row, current_column)
            self.tableWidget_wear.editItem(self.tableWidget_wear.item(prev_row, current_column))
        elif event.key() == Qt.Key_Down:
            # Переход на строку ниже
            next_row = min(self.tableWidget_wear.rowCount() - 1, current_row + 1)
            self.tableWidget_wear.setCurrentCell(next_row, current_column)
            self.tableWidget_wear.editItem(self.tableWidget_wear.item(next_row, current_column))
        elif event.key() == Qt.Key_Left:
            # Переход влево
            prev_col = max(0, current_column - 1)
            self.tableWidget_wear.setCurrentCell(current_row, prev_col)
            self.tableWidget_wear.editItem(self.tableWidget_wear.item(current_row, prev_col))
        elif event.key() == Qt.Key_Right:
            # Переход вправо
            next_col = min(self.tableWidget_wear.columnCount() - 1, current_column + 1)
            self.tableWidget_wear.setCurrentCell(current_row, next_col)
            self.tableWidget_wear.editItem(self.tableWidget_wear.item(current_row, next_col))
        else:
            # Стандартное поведение для редактирования
            QWidget.keyPressEvent(self.tableWidget_wear, event)



    def set_wear_labelline(self):
        
        self.wear_price = (self.wear_percent / 100) * self.replacement_cost
        avg_wear_line = self.wear_price
        avg_wear_label = self.wear_percent
        self.label_wear.setText(f"Физический износ {avg_wear_label:.2f} %")
        self.lineEdit_wear.setText(f"{avg_wear_line:,.2f}")

        


    def calculate_replacement_cost(self):
        required_attrs = ['total_ukup', 'unit_value', 'reg_coeff', 'stat_coeff', 'developer', 'inconsistency']
        missing = [attr for attr in required_attrs if not hasattr(self, attr)]
        if missing:
            self.replacement_cost = 0.0
            return

        try:
            self.replacement_cost = (
                self.total_ukup * self.sesmos * self.territorial *
                float(self.unit_value) *
                self.reg_coeff *
                self.stat_coeff *
                (1+ (self.developer / 100)) *
                self.inconsistency
            )
        except Exception as e:
            self.replacement_cost = 0.0



   
    def finalize_replacement_cost(self):
        
        self.calculate_replacement_cost()
        self.set_wear_labelline()
        self.final_cost = self.replacement_cost - self.wear_price
        # self.label_final_cost.setText(f"{self.final_cost:,.2f}")
        self.lineEdit_final_cost.setText(f"{self.final_cost:,.2f}")
    
    
    def calculate_inconsistency_and_wear(self):
        row_idx = self.tableWidget_wear.rowCount() - 1
        total_share = 0
        total_adjustment = 0
        weighted_wear_sum = 0

        for row in range(row_idx):
            try:
                share = self.tableWidget_wear.item(row, 1)
                adjustment = self.tableWidget_wear.item(row, 2)
                wear = self.tableWidget_wear.item(row, 3)

                share_value = float(share.text()) if share and share.text() else 0.0
                adjustment_value = float(adjustment.text()) if adjustment and adjustment.text() else 0.0
                wear_value = float(wear.text()) if wear and wear.text() else 0.0

                total_share += share_value
                total_adjustment += adjustment_value
                weighted_wear_sum += (wear_value * share_value) / 100
            except Exception:
                continue

        self.inconsistency = (total_share - total_adjustment) / 100
        self.wear_percent = weighted_wear_sum
        self.lineEdit_inconsistency.setText(str(self.inconsistency))

        # Запишем итоговую строку в таблицу
        self.tableWidget_wear.blockSignals(True)
        self.tableWidget_wear.setItem(row_idx, 1, QTableWidgetItem(str(round(total_share, 2))))
        self.tableWidget_wear.setItem(row_idx, 2, QTableWidgetItem(str(round(total_adjustment, 2))))
        self.tableWidget_wear.setItem(row_idx, 3, QTableWidgetItem(str(round(weighted_wear_sum, 2))))
        self.tableWidget_wear.blockSignals(False)


    def recalculate_all(self):
        self.calculate_inconsistency_and_wear()
        self.update_corrected_price()
        self.calculate_replacement_cost()
        self.set_wear_labelline()

        self.final_cost = self.replacement_cost - self.wear_price
        self.lineEdit_final_cost.setText(f"{self.final_cost:,.2f}")

    

# ДОБАВЛЕНИЕ ЛИТЕРА В ТАБЛИЦУ

    def on_accept(self):
        table = self.parent.tableWidget_liter_list

        def format_number(value):
            return f"{int(round(value)):,}".replace(",", " ")

        liter_data = self.collect_data()

        # Обновляем существующий литер, если активен
        if self.parent.active_liter_number is not None:
            updated = False
            for idx, liter in enumerate(self.parent.main_window.saved_liters):
                if liter["number"] == self.parent.active_liter_number:
                    liter_data["number"] = self.parent.active_liter_number
                    self.parent.main_window.saved_liters[idx] = liter_data
                    updated = True
                    break

            # Обновляем строку в таблице
            for row in range(table.rowCount()):
                item = table.item(row, 0)
                if item and int(item.text()) == self.parent.active_liter_number:
                    table.setItem(row, 1, QTableWidgetItem(liter_data["building_type"]))
                    table.setItem(row, 2, QTableWidgetItem(format_number(self.replacement_cost)))
                    table.setItem(row, 3, QTableWidgetItem(format_number(self.wear_price)))
                    table.setItem(row, 4, QTableWidgetItem(format_number(self.final_cost)))
                    break

            if not updated:
                print("⚠️ Не удалось обновить литер – не найден по номеру.")
        else:
            # Добавляем как новый литер
            max_number = 0
            for row in range(table.rowCount()):
                item = table.item(row, 0)  # Столбец "№"
                if item and item.text().isdigit():
                    max_number = max(max_number, int(item.text()))
            new_number = max_number + 1

            row_position = table.rowCount()
            table.insertRow(row_position)

            table.setItem(row_position, 0, QTableWidgetItem(str(new_number)))
            table.setItem(row_position, 1, QTableWidgetItem(liter_data["building_type"]))
            table.setItem(row_position, 2, QTableWidgetItem(format_number(self.replacement_cost)))
            table.setItem(row_position, 3, QTableWidgetItem(format_number(self.wear_price)))
            table.setItem(row_position, 4, QTableWidgetItem(format_number(self.final_cost)))

            if hasattr(self.parent, 'main_window') and self.parent.main_window:
                liter_data["number"] = new_number
                self.parent.main_window.saved_liters.append(liter_data)
        # 👇 Обновим строку "ВСЕГО"
        if hasattr(self.parent, "add_total_row") and hasattr(self.parent, "update_total_row"):
            # Удалим старую строку "ВСЕГО", если есть
            table = self.parent.tableWidget_liter_list
            if table.rowCount() > 0 and table.item(table.rowCount() - 1, 0).text() == "ВСЕГО":
                table.removeRow(table.rowCount() - 1)
            self.parent.add_total_row()
            self.parent.update_total_row()

        self.valuation_window.save_report()
                # ⬇️ Очистка полей Площадь, Высота, Объём и скрытие кнопки
        self.parent.lineEdit_square.clear()
        self.parent.lineEdit_height.clear()
        self.parent.lineEdit_volume.clear()
        self.parent.pushButton_deviations_wear.setVisible(False)
        self.parent.pushButton_choose_analog.setVisible(False)

        self.accept()
        # self.parent.update_total_row()
    # СОБИРАЕМ ДАННЫЕ ИЗ ДИАЛОГА

    def collect_data(self):
        """Собирает все данные из диалога для сериализации в liter"""
        # Конструктивные элементы (таблица wear)
        wear_data = []
        for row in range(self.tableWidget_wear.rowCount() - 1):  # exclude "ВСЕГО"
            row_data = {}
            for col in range(self.tableWidget_wear.columnCount()):
                item = self.tableWidget_wear.item(row, col)
                header = self.tableWidget_wear.horizontalHeaderItem(col).text()
                row_data[header] = item.text() if item else ""
            wear_data.append(row_data)
        # Добавим applied_improvements — список применённых инженерных улучшений
       

        data = {
            "building_type": self.parent.label_building_choose.text().strip(),
            "sesmos": float(self.lineEdit_sesmos.text().replace(",", ".").strip() or 0),
            "replacement_cost": self.replacement_cost,
            "wear_price": self.wear_price,
            "final_cost": self.final_cost,
            "corrected_price": getattr(self, "total_ukup", 0),
            "unit": self.lineEdit_unit.text().strip(),
            "unit_type": self.label_unit.text(),
            "reg_coeff": self.reg_coeff,
            "stat_coeff": self.stat_coeff,
            "developer_percent": self.developer,
            "inconsistency": getattr(self, "inconsistency", 0),
            "wear_percent": getattr(self, "wear_percent", 0),
            "facade_corrected_price": getattr(self, "facade_corrected_price", 0),
            "height_corrected_price": getattr(self, "high_corrected_price", 0),
            "improvement_correction": getattr(self, "improvement_correction", 0),
            "deviation_correction": getattr(self, "deviation_correction", 0),
            "structural_elements": wear_data,
            "reg_coeff_type": self.comboBox_type_koeff.currentText(),
            "facade_type": self.comboBox_facade.currentText(),
            "stat_koeff_label": self.label_stat_koeff.text()
        }
        _, applied_improvements = self.apply_improvements_logic(self.building_id, price_per_m2=0.0)
        price_str = self.parent.label_price_result.text().replace("Стоимость за м² по УКУП:", "").strip().split()[0]
        try:
            base_price = float(price_str.replace(" ", "").replace(",", ""))
        except:
            base_price = 0

        data["improvement_details"] = [
            {
                "name": name,
                "correction_percent": correction,
                "correction_value": round(base_price * correction, 2)
            }
            for name, correction in applied_improvements
        ]

                
        # Сохраняем отмеченные чекбоксы отклонений
        if hasattr(self, 'deviation_checkboxes'):
            data["deviation_details"] = []
            for name, (checkbox, value) in self.deviation_checkboxes.items():
                data["deviation_details"].append({
                    "name": name,
                    "value": value,
                    "selected": checkbox.isChecked()
                })
       
        base_data = self.parent.collect_liter_base_data()
        data.update(base_data)

        self.wear_dialog_data = data
        return data


    # ЗАГРУЖАЕМ ДАННЫЕ В ДИАЛОГ
    def load_data(self, data: dict):
        """Загружает данные в диалог из сохранённого литера"""
        # Загрузка базовых коэффициентов и цен
        self.replacement_cost = data.get("replacement_cost", 0)
        self.wear_price = data.get("wear_price", 0)
        self.final_cost = data.get("final_cost", 0)
        self.total_ukup = data.get("corrected_price", 0)
        self.sesmos = data.get("sesmos", 0)
        self.lineEdit_unit.setText(data.get("unit", ""))
        self.label_unit.setText(data.get("unit_type", ""))
        self.reg_coeff = data.get("reg_coeff", 1)
        self.stat_coeff = data.get("stat_coeff", 1)
        self.developer = data.get("developer_percent", 0)
        self.inconsistency = data.get("inconsistency", 0)
        self.wear_percent = data.get("wear_percent", 0)
        self.facade_corrected_price = data.get("facade_corrected_price", 0)
        self.high_corrected_price = data.get("height_corrected_price", 0)
        self.improvement_correction = data.get("improvement_correction", 0)
        self.deviation_correction = data.get("deviation_correction", 0)

        # Установка типов коэффициентов и фасада
        self.comboBox_type_koeff.setCurrentText(data.get("reg_coeff_type", ""))
        self.comboBox_facade.setCurrentText(data.get("facade_type", ""))
        self.label_stat_koeff.setText(data.get("stat_koeff_label", ""))

        # Заполнение таблицы конструктивных элементов
        wear_data = data.get("structural_elements", [])
        self.tableWidget_wear.setRowCount(len(wear_data) + 1)  # +1 для строки ВСЕГО
        headers = [
            "Конструкции", "Доля %", 
            "Поправка к удельным весам %", 
            "Физический износ %"
        ]
        self.tableWidget_wear.setColumnCount(len(headers))
        self.tableWidget_wear.setHorizontalHeaderLabels([
            "Конструкции", "Доля %",
            "Поправка к\nудельным весам %",
            "Физический\nизнос %"
        ])
        for row_idx, row_data in enumerate(wear_data):
            max_lines = 1
            for col_idx, header in enumerate(headers):
                value = row_data.get(header, "")
                if header == "Конструкции":
                    value = self.wrap_text(str(value), max_length=40)
                    max_lines = value.count("\n") + 1  # учитываем количество строк

                item = QTableWidgetItem(str(value))
                if col_idx in [2, 3]:  # Эти колонки редактируемые
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.tableWidget_wear.setItem(row_idx, col_idx, item)
            base_height = 25  # можно подогнать под стиль приложения
            self.tableWidget_wear.setRowHeight(row_idx, base_height * max_lines)
        self.tableWidget_wear.resizeColumnsToContents()

        for row_idx, row_data in enumerate(wear_data):
            for col_idx in range(self.tableWidget_wear.columnCount()):
                header = self.tableWidget_wear.horizontalHeaderItem(col_idx).text()
                item_text = row_data.get(header, "")
                item = QTableWidgetItem(item_text)
                self.tableWidget_wear.setItem(row_idx, col_idx, item)
        # Восстановление применённых улучшений
        improvement_details = data.get("improvement_details", [])
        if improvement_details:
            # Можно вывести в текстовое поле, таблицу или отладочный лог
            details_text = ""
            for item in improvement_details:
                name = item.get("name", "")
                percent = item.get("correction_percent", 0)
                value = item.get("correction_value", 0)
                details_text += f"{name}: {percent:+.3%} ({value:,.2f} сум)\n"
            
            # Пример: если у тебя есть QTextEdit или QLabel
            if hasattr(self, "textEdit_improvements"):
                self.textEdit_improvements.setPlainText(details_text)
            elif hasattr(self, "label_improvements"):
                self.label_improvements.setText(details_text)
            

        # Восстановление чекбоксов отклонений
        deviation_details = data.get("deviation_details", [])
        if deviation_details:
            if self.label_injener_correct.layout() is None:
                self.label_injener_correct.setLayout(QVBoxLayout())
            layout = self.label_injener_correct.layout()
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                layout.removeWidget(widget)
                widget.setParent(None)
            self.deviation_checkboxes = {}
            for item in deviation_details:
                checkbox = QCheckBox(f"{item['name']}: {item['value']:+.2f} сум")
                checkbox.setChecked(item['selected'])
                checkbox.stateChanged.connect(self.update_selected_deviations)
                layout.addWidget(checkbox)
                self.deviation_checkboxes[item['name']] = (checkbox, item['value'])
            self.label_deviation_total = QLabel("Суммарная корректировка: 0.00 сум")
            layout.addWidget(self.label_deviation_total)
            self.update_selected_deviations()
        self.tableWidget_wear.resizeColumnsToContents()

        self.recalculate_all()
