from PyQt5.QtWidgets import (QWidget, QAbstractItemView, QHeaderView, QTableWidget, QPushButton, QLabel,
                            QDialog, QMessageBox, QTableWidgetItem, QLineEdit, QComboBox, QTextBrowser)
from PyQt5 import uic
import os

from PyQt5.QtGui import QFont
from ui.cost_method_dialogs.building_choose import BuildingChooseDialog
from ui.cost_method_dialogs.deviations_and_wear_dialog import DeviationsAndWearDialog

from logic.data_entry import DataEntryForm
from PyQt5.QtCore import QDate, Qt
import json
import pandas as pd
from functools import partial
from logic.paths import get_ui_path

import traceback



class UkupWidget(QWidget):
    def __init__(self, parent=None, main_window=None, valuation_window = None):
        super().__init__(parent)
        self.main_window = main_window
        self.valuation_window = valuation_window     

        uic.loadUi(get_ui_path("ukup_window.ui"), self)

        

        
        self.data_service = DataEntryForm()
        self.liter_list = [] 
        
        self.filters_initialized = False


        self.active_liter_number = None

        self.auto_applied_filters = {}


       
       


        # Найти элементы UI
        self.label_square = self.findChild(QLabel, 'label_square')
        self.label_height = self.findChild(QLabel, 'label_height')
        self.label_volume = self.findChild(QLabel, 'label_volume')
        self.label_length = self.findChild(QLabel, 'label_length')
        self.label_floors = self.findChild(QLabel, 'label_floors')
        self.label_wall_material = self.findChild(QLabel, 'label_wall_material')
        self.label_roof = self.findChild(QLabel, 'label_roof')
        self.label_foundation = self.findChild(QLabel, 'label_foundation')
        self.label_label_overlap = self.findChild(QLabel, 'label_overlap')
        self.label_decoration = self.findChild(QLabel, 'label_decoration')
        self.label_junction = self.findChild(QLabel, 'label_junction')
        self.label_coating = self.findChild(QLabel, 'label_coating')
        self.label_wall_thickness = self.findChild(QLabel, 'label_wall_thickness')
        self.label_price_result = self.findChild(QLabel, 'label_price_result')
        self.label_selected_analog_index = self.findChild(QLabel, 'label_selected_analog_index')



        self.lineEdit_square = self.findChild(QLineEdit, 'lineEdit_square')
        self.lineEdit_height = self.findChild(QLineEdit, 'lineEdit_height')
        self.lineEdit_volume = self.findChild(QLineEdit, 'lineEdit_volume')

        self.lineEdit_length = self.findChild(QLineEdit, 'lineEdit_length')

        self.comboBox_floor = self.findChild(QComboBox, 'comboBox_floor')
        self.comboBox_wall_material = self.findChild(QComboBox, 'comboBox_wall_material')
        self.comboBox_roof = self.findChild(QComboBox, 'comboBox_roof')
        self.comboBox_foundation = self.findChild(QComboBox, 'comboBox_foundation')
        self.comboBox_overlap = self.findChild(QComboBox, 'comboBox_overlap')
        self.comboBox_decoration = self.findChild(QComboBox, 'comboBox_decoration')
        self.comboBox_junction = self.findChild(QComboBox, 'comboBox_junction')
        self.comboBox_coating = self.findChild(QComboBox, 'comboBox_coating')
        self.comboBox_wall_thickness = self.findChild(QComboBox, 'comboBox_wall_thickness')
        self.comboBox_wall_height = self.findChild(QComboBox, "comboBox_wall_height")


        self.combo_boxes = {
            "Этажность": self.comboBox_floor,
            "Материал стен": self.comboBox_wall_material,
            "Кровля": self.comboBox_roof,
            "Фундаменты": self.comboBox_foundation,
            "Перекрытие": self.comboBox_overlap,
            "Отделка": self.comboBox_decoration,
            "Примыкание": self.comboBox_junction,
            "Полы": self.comboBox_coating,
            "Толщина стен": self.comboBox_wall_thickness,
            "Высота стен": self.comboBox_wall_height
            
        }

       


        self.textBrowser_analog = self.findChild(QTextBrowser, 'textBrowser_analog')


        self.pushButton_addLiter = self.findChild(QWidget, "pushButton_addLiter")
        self.pushButton_liter_dublicate = self.findChild(QWidget, "pushButton_liter_dublicate")
        self.pushButton_liter_dublicate.clicked.connect(self.duplicate_selected_liter)

        self.pushButton_liter_delete = self.findChild(QWidget, "pushButton_liter_delete")
        self.pushButton_liter_delete.clicked.connect(self.delete_checked_liters)

        self.pushButton_building_choose = self.findChild(QPushButton, "pushButton_building_choose")
        self.pushButton_edit = self.findChild(QWidget, "pushButton_edit")
        self.pushButton_edit.clicked.connect(self.enable_liter_editing)

        self.pushButton_save = self.findChild(QWidget, 'pushButton_save')
        self.label_building_choose = self.findChild(QWidget, "label_building_choose")
        self.pushButton_deviations_wear = self.findChild(QPushButton, 'pushButton_deviations_wear')
        self.pushButton_deviations_wear.setVisible(False)
        self.pushButton_choose_analog = self.findChild(QPushButton, 'pushButton_choose_analog')
        self.pushButton_choose_analog.setVisible(False)
        self.pushButton_choose_analog.clicked.connect(self.on_choose_analog_clicked)
        self.pushButton_deviations_wear.clicked.connect(self.open_deviation)
        self.tableWidget_liter_list = self.findChild(QTableWidget, "TableWidget_liter_list")
        self.tableWidget_liter_list.setColumnCount(5)
        headers = ["№", "Здание",
                  "Восстановительная\nстоимость здания",
                  "Усреднённый\nизнос",
                  "Оценочная\nстоимость"

        ]
        self.tableWidget_liter_list.setHorizontalHeaderLabels(headers)
        

        header = self.tableWidget_liter_list.horizontalHeader()
        self.tableWidget_liter_list.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tableWidget_liter_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget_liter_list.setSelectionBehavior(QTableWidget.SelectRows) 
        self.tableWidget_liter_list.setSelectionMode(QAbstractItemView.SingleSelection) 
        
        self.tableWidget_liter_list.cellClicked.connect(self.load_liter_to_ui)


        self.pushButton_next = self.findChild(QPushButton, 'pushButton_next')
        self.pushButton_next.clicked.connect(self.switch_to_land)
       
        
       
        self.pushButton_building_choose.clicked.connect(self.choose_building)

        self.lineEdit_square.textChanged.connect(self.calculate_weight)
        self.lineEdit_height.textChanged.connect(self.calculate_weight)
        self.lineEdit_volume.setReadOnly(True)
    
        self.lineEdit_square.textChanged.connect(self.check_to_activate_filters)
        self.lineEdit_height.textChanged.connect(self.check_to_activate_filters)
        self.lineEdit_length.textChanged.connect(self.check_to_activate_filters)
        
       
    
    def choose_building(self):
        self.reset_ui()
        dialog = BuildingChooseDialog(self)
        if dialog.exec_():
            selected_building = dialog.selected_building_type
            self.label_building_choose.setText(selected_building)
            self.df_filtered_original = self.get_filtered_ukup(selected_building)
            self.df_filtered = self.df_filtered_original.copy()
            self.filters_initialized = False
            self.apply_field_availability()
            self.check_to_activate_filters()  

        self.active_liter_number = None

    
    
    def get_filtered_ukup(self, selected_building_type):
        df = self.data_service.ukup()
        if df is not None and 'Здание и сооружение' in df.columns:
            return df[df['Здание и сооружение'] == selected_building_type]
        return df.iloc[0:0]
                

    def apply_field_availability(self):
        df = self.df_filtered_original
        if df is None or df.empty:
            return

        if df['Объём до м3'].notna().any():
            self.lineEdit_square.setDisabled(False)
            self.lineEdit_height.setDisabled(False)
            self.lineEdit_volume.setDisabled(False)
        elif df['Площадь до м2'].notna().any():
            self.lineEdit_square.setDisabled(False)
            if df['Высота'].notna().any() or self.label_building_choose.text().strip() == "Жилой дом":
                self.lineEdit_height.setDisabled(False)
        elif df['Протяженность'].notna().any():
            self.lineEdit_length.setDisabled(False)



   
    def check_to_activate_filters(self):
       
        excluded_types = ["Жилой щитовой дом", "Тандыр", "Гараж подземный"]
        if self.label_building_choose.text().strip() in excluded_types:
            self.pushButton_choose_analog.setVisible(True)
            return

        if self.check_required_inputs_filled():
            self.setup_initial_ui()
        elif self.is_single_row_without_inputs():
            self.setup_initial_ui()





    

    def check_required_inputs_filled(self):
        required_fields = [self.lineEdit_square, self.lineEdit_height, self.lineEdit_length]
        for field in required_fields:
            if field.isEnabled() and not field.text().strip():
                return False
        return True

    def check_all_required_inputs_and_combos_filled(self):
        
        for field in [self.lineEdit_square, self.lineEdit_height, self.lineEdit_length]:
            if field.isEnabled() and not field.text().strip():
                return False

        
        for combo in self.combo_boxes.values():
            if combo.isEnabled() and (combo.currentText() == "Выберите из списка" or not combo.currentText().strip()):
                return False

        return True


    def calculate_weight(self):
        try:
            square = float(self.lineEdit_square.text().replace(',', '.')) if self.lineEdit_square.isEnabled() else 0
            high = float(self.lineEdit_height.text().replace(',', '.')) if self.lineEdit_height.isEnabled() else 0
            weight = square * high
            self.lineEdit_volume.setText(str(round(weight, 2)))
        except ValueError:
            self.lineEdit_volume.setText('0')
        
            
    
    
    def setup_initial_ui(self):
        if self.is_single_row_without_inputs():
            self.pushButton_choose_analog.setVisible(True)
            return

        if self.filters_initialized:
            return
        if not self.check_required_inputs_filled():
            return

        self.filters_initialized = True
        self.df_filtered = self.df_filtered_original.copy()

        for combo in self.combo_boxes.values():
            combo.setDisabled(True)
            combo.clear()

        for column, combo in self.combo_boxes.items():
            
            unique_vals = self.df_filtered[column].dropna().unique()
            if len(unique_vals) == 0:
                combo.setDisabled(True)
            elif len(unique_vals) == 1:
                selected_value = unique_vals[0]
                self.df_filtered = self.df_filtered[self.df_filtered[column] == selected_value]
                self.auto_applied_filters[column] = str(selected_value)  # ← сохраняем
                combo.setDisabled(True)

            else:
                combo.setDisabled(False)
                combo.addItem("Выберите из списка")
                combo.addItems(map(str, unique_vals))
                try:
                    combo.currentIndexChanged.disconnect()
                except TypeError:
                    pass
                combo.currentIndexChanged.connect(partial(self.on_combo_changed, column, combo))
                break
        should_show = self.should_show_choose_analog_button()
        self.pushButton_choose_analog.setVisible(should_show)
        
                
    def on_combo_changed(self, column, combo):
        selected_value = combo.currentText()
        if selected_value == "Выберите из списка":
            return

        applied_filters = {}
        for col, cb in self.combo_boxes.items():
            if cb.isEnabled() and cb.currentText() != "Выберите из списка":
                applied_filters[col] = cb.currentText()
            if col == column:
                break

        self.df_filtered = self.df_filtered_original.copy()
        for col, value in applied_filters.items():
            col_dtype = self.df_filtered[col].dtype
            try:
                if pd.api.types.is_numeric_dtype(col_dtype):
                    value = float(value)
                    if col_dtype == int:
                        value = int(value)
            except ValueError:
                pass 
            
            self.df_filtered = self.df_filtered[self.df_filtered[col] == value]

            if self.df_filtered.empty:
                QMessageBox.warning(self, "Ошибка", f"Нет данных для фильтра: {col} = {value}")
                return

        columns = list(self.combo_boxes.keys())
        index = columns.index(column)
        for col in columns[index + 1:]:
            cb = self.combo_boxes[col]
            cb.blockSignals(True)
            cb.clear()
            cb.setDisabled(True)
            cb.blockSignals(False)

        for col in columns[index + 1:]:
            cb = self.combo_boxes[col]
            unique_vals = self.df_filtered[col].dropna().unique()
           

            if len(unique_vals) > 1:
                cb.addItem("Выберите из списка")
                cb.addItems(map(str, unique_vals))
                cb.setCurrentIndex(0)
                cb.setDisabled(False)
                cb.currentIndexChanged.connect(partial(self.on_combo_changed, col, cb))
                break
        should_show = self.should_show_choose_analog_button()
        self.pushButton_choose_analog.setVisible(should_show)
      

        

    
    def get_target_volume(self):
        try:
            return float(self.lineEdit_volume.text().replace(',', '.'))
        except ValueError:
            return None

    def get_target_area(self):
        try:
            return float(self.lineEdit_square.text().replace(',', '.'))
        except ValueError:
            return None



    def fill_combobox_options(self):
        for column, combo in self.combo_boxes.items():
            if column not in self.df_filtered.columns:
                combo.clear()
                combo.setDisabled(True)
                continue

            unique_vals = self.df_filtered[column].dropna().unique()
            combo.blockSignals(True)
            current_value = combo.currentText()
            combo.clear()

            if len(unique_vals) == 0:
                combo.addItem("Нет данных")
                combo.setDisabled(True)
            else:
                combo.addItem("Выберите из списка")
                combo.addItems(map(str, unique_vals))
                combo.setDisabled(False)

              
                index = combo.findText(current_value)
                if index >= 0:
                    combo.setCurrentIndex(index)
                else:
                    combo.setCurrentIndex(0)

            combo.blockSignals(False)






    def get_selected_price_per_m2(self):
       
        
        if not hasattr(self, "df_filtered"):
            
            self.label_price_result.setText("Цена не определена")
            return None

        if self.df_filtered is None:
            
            self.label_price_result.setText("Цена не определена")
            return None

        
        if len(self.df_filtered) == 1:
            row = self.df_filtered.iloc[0]
            

            if "Стоимость" in row:
               
                if pd.notna(row["Стоимость"]):
                    price = float(row["Стоимость"])
                    self.label_price_result.setText(f"{round(price, 2)} сум")
                    return price
                

        self.label_price_result.setText("Цена не определена")
        return None




    def apply_final_volume_area_filter(self, target_volume=None, target_area=None):
        """Последняя фильтрация аналогов по объему или площади"""
        if hasattr(self, 'df_filtered') and len(self.df_filtered) > 1:
            if target_volume is not None and 'Объём до м3' in self.df_filtered.columns:
                df_sorted = self.df_filtered[self.df_filtered['Объём до м3'].notna()].sort_values('Объём до м3')
                for _, row in df_sorted.iterrows():
                    if target_volume <= row['Объём до м3']:
                        self.df_filtered = pd.DataFrame([row])
                        return
                if not df_sorted.empty:
                    self.df_filtered = pd.DataFrame([df_sorted.iloc[-1]])

            elif target_area is not None and 'Площадь до м2' in self.df_filtered.columns:
                df_sorted = self.df_filtered[self.df_filtered['Площадь до м2'].notna()].sort_values('Площадь до м2')
                for _, row in df_sorted.iterrows():
                    if target_area <= row['Площадь до м2']:
                        self.df_filtered = pd.DataFrame([row])
                        return
                if not df_sorted.empty:
                    self.df_filtered = pd.DataFrame([df_sorted.iloc[-1]])








    def reset_ui(self):
        for line_edit in [self.lineEdit_square, self.lineEdit_height, self.lineEdit_length]:
            try:
                line_edit.textChanged.disconnect()
            except TypeError:
                pass
        for combo in self.combo_boxes.values():
            try:
                combo.currentIndexChanged.disconnect()
            except TypeError:
                pass
            combo.blockSignals(True)
            combo.clear()
            combo.setDisabled(True)
            combo.blockSignals(False)

        for line_edit in [self.lineEdit_square, self.lineEdit_height, self.lineEdit_volume, self.lineEdit_length]:
            line_edit.clear()
            line_edit.setDisabled(True)

        self.textBrowser_analog.clear()
        self.label_price_result.setText("")
        self.label_building_choose.setText("")
        self.df_filtered = pd.DataFrame()
        self.df_filtered_original = pd.DataFrame()
        self.filters_initialized = False

        self.lineEdit_square.textChanged.connect(self.calculate_weight)
        self.lineEdit_height.textChanged.connect(self.calculate_weight)
        self.lineEdit_square.textChanged.connect(self.check_to_activate_filters)
        self.lineEdit_height.textChanged.connect(self.check_to_activate_filters)
        self.lineEdit_length.textChanged.connect(self.check_to_activate_filters)
        self.pushButton_choose_analog.setVisible(False)
        self.pushButton_deviations_wear.setVisible(False)



    def on_choose_analog_clicked(self):
        target_volume = self.get_target_volume()
        target_area = self.get_target_area()

        if target_volume and self.df_filtered['Объём до м3'].notna().any():
            self.apply_final_volume_area_filter(target_volume=target_volume)
        elif target_area and self.df_filtered['Площадь до м2'].notna().any():
            self.apply_final_volume_area_filter(target_area=target_area)

        self.get_selected_price_per_m2()
        if len(self.df_filtered) == 1:
            selected_index = self.df_filtered.index[0]
            self.selected_analog_index = selected_index
            
        df_description = self.data_service.description()
        if df_description is not None and selected_index in df_description.index:
            row = df_description.loc[selected_index]
            description = row.get("Описание", "нет данных")
            table_num = row.get("Таблица", "нет данных")

            html = f"""
            <div align="center">
                <h2><b>Описание выбранного аналога:</b></h2>
                <p style="font-size:10pt; font-weight:bold; margin-top:20px;">{description}</p>
            </div>
            <div align="right" style="margin-top:20px;">
                <span style="font-size:10pt;"><b>Таблица № {table_num}</b></span>
            </div>
            """
            self.textBrowser_analog.setHtml(html)
        else:
            self.textBrowser_analog.setText("Нет описания для выбранного аналога.")
        if self.label_selected_analog_index is not None and hasattr(self, "selected_analog_index"):
            self.label_selected_analog_index.setText(str(self.selected_analog_index))


        self.pushButton_deviations_wear.setVisible(True)


    def should_show_choose_analog_button(self):
        

        # Условие 1: Только один аналог — фильтрация не требуется
        if hasattr(self, 'df_filtered_original') and len(self.df_filtered_original) == 1:
            return True

        # Условие 2: Все обязательные поля и комбобоксы заполнены
        if self.check_all_required_inputs_and_combos_filled():
            return True

        # Условие 3: Ни одно из полей square/height/length не активно
        if not any([
            self.lineEdit_square.isEnabled(),
            self.lineEdit_height.isEnabled(),
            self.lineEdit_length.isEnabled()
        ]):
            return True

        return False



    def is_single_row_without_inputs(self):
       
        if hasattr(self, 'df_filtered_original') and len(self.df_filtered_original) == 1:
            # Если все поля единиц измерения отключены
            no_inputs_required = all([
                not self.lineEdit_square.isEnabled(),
                not self.lineEdit_height.isEnabled(),
                not self.lineEdit_length.isEnabled()
            ])
            return no_inputs_required
        return False



#  DEVIATIONS AND WEAR

    def open_deviation(self):
        if not self.label_building_choose.text().strip():
            QMessageBox.warning(self, "Ошибка", "Сначала выберите тип здания.")
            return

        dialog = DeviationsAndWearDialog(
            parent=self,
            valuation_window=self.valuation_window
        )

        if self.active_liter_number is not None:
            
            existing = next((l for l in self.main_window.saved_liters
                            if l["number"] == self.active_liter_number), None)
            if existing:
                dialog.load_data(existing)

        dialog.exec_()


# СОХРАНЯЕМ ДАННЫЕ

    def collect_liter_base_data(self):
        """Собирает базовые параметры литера из UkupWidget"""
        measurements = {
            "square": self.lineEdit_square.text().strip() if self.lineEdit_square.isEnabled() else "",
            "height": self.lineEdit_height.text().strip() if self.lineEdit_height.isEnabled() else "",
            "volume": self.lineEdit_volume.text().strip() if self.lineEdit_volume.isEnabled() else "",
            "length": self.lineEdit_length.text().strip() if self.lineEdit_length.isEnabled() else "",
            "ukup_price_label": self.label_price_result.text().strip()
        }

        filters = {}
        for name, combo in self.combo_boxes.items():
            text = combo.currentText()
            if text and text != "Выберите из списка":
                filters[name] = text

        # Добавляем автоматические фильтры, если их нет
        for name, val in getattr(self, "auto_applied_filters", {}).items():
            if name not in filters:
                filters[name] = val



        analog_description = self.textBrowser_analog.toHtml().strip()
        analog_index_text = self.label_selected_analog_index.text().strip()
        analog_index = int(analog_index_text) if analog_index_text.isdigit() else None
        return {
            "building_type": self.label_building_choose.text().strip(),
            "measurements": measurements,
            "filters": filters,
            "analog_description_html": analog_description,
            "analog_index": analog_index
        }

       

        


# Загружаем данные обратно на страницу
    def load_liters_to_table(self, liters_list):
        # Удаляем строку "ВСЕГО", если она есть
        for row in range(self.tableWidget_liter_list.rowCount()):
            item = self.tableWidget_liter_list.item(row, 0)
            if item and item.text().strip().upper() == "ВСЕГО":
                self.tableWidget_liter_list.removeRow(row)
                break

        self.tableWidget_liter_list.setRowCount(0)

        for liter in liters_list:
            row_position = self.tableWidget_liter_list.rowCount()
            self.tableWidget_liter_list.insertRow(row_position)

            self.tableWidget_liter_list.setItem(row_position, 0, QTableWidgetItem(str(liter["number"])))
            self.tableWidget_liter_list.setItem(row_position, 1, QTableWidgetItem(liter["building_type"]))
            self.tableWidget_liter_list.setItem(row_position, 2, QTableWidgetItem(f"{int(round(liter['replacement_cost'])):,}".replace(",", " ")))
            self.tableWidget_liter_list.setItem(row_position, 3, QTableWidgetItem(f"{int(round(liter['wear_price'])):,}".replace(",", " ")))
            self.tableWidget_liter_list.setItem(row_position, 4, QTableWidgetItem(f"{int(round(liter['final_cost'])):,}".replace(",", " ")))

        self.add_total_row()
        self.update_total_row()

    
    def restore_filter_values(self, filters_dict):
       
        self.df_filtered = self.df_filtered_original.copy()

        for column, combo in self.combo_boxes.items():
            combo.blockSignals(True)
            combo.clear()
            combo.setDisabled(True)
            combo.blockSignals(False)

        for column, combo in self.combo_boxes.items():
            if column not in self.df_filtered.columns:
                continue

            value = filters_dict.get(column)
            if value is None:
                continue

            
            self.df_filtered = self.df_filtered[self.df_filtered[column] == value]

           
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Выберите из списка")
            unique_vals = self.df_filtered_original[column].dropna().unique()
            combo.addItems(map(str, unique_vals))
            idx = combo.findText(value)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.setDisabled(False)
            combo.blockSignals(False)



    def restore_price_label(self, price_text):
        
        self.label_price_result.setText(price_text)


    def load_liter_to_ui(self, row, column):
        item = self.tableWidget_liter_list.item(row, 0)
        if item and item.text().strip().upper() == "ВСЕГО":
            return  
        try:
            liter_number = int(self.tableWidget_liter_list.item(row, 0).text())
            selected_liter = next(l for l in self.main_window.saved_liters if l["number"] == liter_number)
        except Exception:
            return

        building_type = selected_liter["building_type"]
        self.label_building_choose.setText(building_type)

        # Подготовка UI под тип здания
        self.df_filtered_original = self.get_filtered_ukup(building_type)
        self.df_filtered = self.df_filtered_original.copy()
        self.apply_field_availability()
        self.setup_initial_ui()
        self.restore_filter_values(selected_liter.get("filters", {}))

        # Устанавливаем измерения
        measurements = selected_liter.get("measurements", {})
        if self.lineEdit_square.isEnabled():
            self.lineEdit_square.setText(str(measurements.get("square", "")))
        if self.lineEdit_height.isEnabled():
            self.lineEdit_height.setText(str(measurements.get("height", "")))
        if self.lineEdit_volume.isEnabled():
            self.lineEdit_volume.setText(str(measurements.get("volume", "")))
        if self.lineEdit_length.isEnabled():
            self.lineEdit_length.setText(str(measurements.get("length", "")))

        # Восстановление цены аналога
        price_text = selected_liter.get("measurements", {}).get("ukup_price_label", "")
        if price_text:
            self.label_price_result.setText(price_text)

        # Восстановление описания аналога
        analog_description = selected_liter.get("analog_description_html", "")
        if analog_description:
            self.textBrowser_analog.setHtml(analog_description)
        else:
            self.textBrowser_analog.clear()
            
        analog_index = selected_liter.get("analog_index")
        self.selected_analog_index = analog_index
        self.label_selected_analog_index.setText(str(analog_index) if analog_index is not None else "")
        
        self.calculate_weight()
        self.check_to_activate_filters()
        # Заблокировать все поля и комбобоксы
        for line_edit in [self.lineEdit_square, self.lineEdit_height, self.lineEdit_volume, self.lineEdit_length]:
            line_edit.setDisabled(True)

        for combo in self.combo_boxes.values():
            combo.setDisabled(True)
        self.active_liter_number = liter_number
        # Скрыть кнопку выбора аналога и показать кнопку отклонений
        self.pushButton_choose_analog.setVisible(False)
        self.pushButton_deviations_wear.setVisible(False)
       
       


# УДАЛЯЕМ ЛИТЕР
    def delete_checked_liters(self):
        table = self.tableWidget_liter_list
        if table.rowCount() == 0:
            return

        current_row = table.currentRow()
        if current_row == -1:
            QMessageBox.information(self, "Удаление", "Выберите литер для удаления.")
            return

        try:
            number_item = table.item(current_row, 0) 
            if number_item is None:
                raise ValueError("Не удалось получить номер литера.")

            number_to_delete = int(number_item.text())
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить выбранный литер.")
            return

        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить литер №{number_to_delete}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

       
        self.main_window.saved_liters = [
            liter for liter in self.main_window.saved_liters
            if liter["number"] != number_to_delete
        ]

        # Переупорядочим номера литеров (1, 2, 3, …)
        for idx, liter in enumerate(self.main_window.saved_liters, start=1):
            liter["number"] = idx

        # Обновим таблицу
        self.load_liters_to_table(self.main_window.saved_liters)

        QMessageBox.information(self, "Удалено", f"Литер №{number_to_delete} успешно удалён.")
        self.valuation_window.save_report()


    # Редактируем литер
    def enable_liter_editing(self):
        # Активируем только те поля, которые разрешены для этого типа здания
        self.apply_field_availability()

        # Повторно включим комбобоксы, если это возможно
        for name, combo in self.combo_boxes.items():
            if name in self.df_filtered.columns:
                unique_vals = self.df_filtered[name].dropna().unique()
                if len(unique_vals) > 1:
                    combo.setDisabled(False)
        self.pushButton_deviations_wear.setVisible(True)
    
    
    
    # ДУБЛИРУЕМ ЛИТЕР


    def duplicate_selected_liter(self):
        table = self.tableWidget_liter_list
        row = table.currentRow()
        if row == -1:
            QMessageBox.information(self, "Дублирование", "Выберите литер для дублирования.")
            return

        try:
            selected_number = int(table.item(row, 0).text())
            original_liter = next(l for l in self.main_window.saved_liters if l["number"] == selected_number)
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти выбранный литер.")
            return

        # Копируем литер
        duplicated_liter = original_liter.copy()

        # Присваиваем новый номер
        existing_numbers = [l["number"] for l in self.main_window.saved_liters]
        new_number = max(existing_numbers) + 1 if existing_numbers else 1
        duplicated_liter["number"] = new_number

        # Добавляем в список
        self.main_window.saved_liters.append(duplicated_liter)

        # Обновляем таблицу и выделяем новый литер
        self.load_liters_to_table(self.main_window.saved_liters)
        for i in range(table.rowCount()):
            num_item = table.item(i, 0)
            if num_item and int(num_item.text()) == new_number:
                table.selectRow(i)
                self.load_liter_to_ui(i, 0)
                break

        # Сохраняем отчёт

        QMessageBox.information(self, "Готово", f"Литер №{new_number} успешно продублирован.")

        self.valuation_window.save_report()


    def add_total_row(self):
        row_idx = self.tableWidget_liter_list.rowCount()
        self.tableWidget_liter_list.insertRow(row_idx)

        font = self.tableWidget_liter_list.font()
        font.setBold(True)

        for col in range(self.tableWidget_liter_list.columnCount()):
            if col == 0:
                item = QTableWidgetItem("ВСЕГО")
            else:
                item = QTableWidgetItem("") 

            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setFont(font)
            self.tableWidget_liter_list.setItem(row_idx, col, item)



    def update_total_row(self):
        row_idx = self.tableWidget_liter_list.rowCount() - 1
        total_replacement_cost = 0
        total_wear = 0
        total_final_cost = 0

        for row in range(row_idx): 
            try:
                replacement = self.tableWidget_liter_list.item(row, 2)
                wear = self.tableWidget_liter_list.item(row, 3)
                final = self.tableWidget_liter_list.item(row, 4)

                replacement_cost = float(replacement.text().replace(" ", "")) if replacement and replacement.text() else 0.0
                wear_value = float(wear.text().replace(" ", "")) if wear and wear.text() else 0.0
                final_cost = float(final.text().replace(" ", "")) if final and final.text() else 0.0

                total_replacement_cost += replacement_cost
                total_wear += wear_value
                total_final_cost += final_cost
            except (ValueError, AttributeError):
                continue

        def format_number(n): return f"{round(n, 2):,}".replace(",", " ")

        font = self.tableWidget_liter_list.font()
        font.setBold(True)

        # Итоговые значения
        for col, value in zip([2, 3, 4], [total_replacement_cost, total_wear, total_final_cost]):
            item = QTableWidgetItem(format_number(value))
            item.setFont(font)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.tableWidget_liter_list.setItem(row_idx, col, item)


            



    def switch_to_land(self):
            """Переключает на вкладку оценка земельного участка"""
            
            index = self.valuation_window.cost_tab.indexOf(self.valuation_window.land_tab)
            if index != -1:
                # Устанавливаем текущую вкладку
                self.valuation_window.cost_tab.setCurrentIndex(index)
            self.valuation_window.save_report()