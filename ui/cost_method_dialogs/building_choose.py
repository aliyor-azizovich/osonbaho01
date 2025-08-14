from PyQt5.QtWidgets import QDialog, QGridLayout, QCheckBox, QPushButton, QLabel, QGroupBox, QMessageBox
from PyQt5 import uic
from PyQt5.QtCore import Qt
import os
from logic.data_entry import DataEntryForm
from logic.paths import get_ui_path
from PyQt5.QtGui import QIcon

class BuildingChooseDialog(QDialog):
    def __init__(self, parent=None, data_service=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("cost_method_dialogs/building_choose_dialog.ui"), self)

        self.setWindowTitle("Выбор типа строения")
        
        self.setWindowIcon(QIcon("icon.ico"))  
        self.data_service = data_service or DataEntryForm()
        self.selected_building_type = None
        self.checkboxes = []

        
        self.label_title = self.findChild(QLabel, "label_title")

        
        # Подключаем кнопку
        self.pushButton_agree = self.findChild(QPushButton, "pushButton_agree")
        self.pushButton_agree.clicked.connect(self.accept_selection)
        groupbox = self.findChild(QGroupBox, "groupBox_buildings")
        self.layout_checkboxes = self.findChild(QGridLayout, "gridLayout_for_checkboxes")
        self.layout_checkboxes.setSpacing(10)
        self.layout_checkboxes.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 6px;
                font-size: 13px;
                color: #5c4033;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #bfa07a;
                background-color: #fffaf0;
                border-radius: 3px;
            }

            QCheckBox::indicator:hover {
                border: 1px solid #a07d5e;
                background-color: #f9f0df;
            }

            QCheckBox::indicator:checked {
                image: url(:/qt-project.org/styles/commonstyle/images/checkbox_checked.png);
                background-color: #d2b48c;
                border: 1px solid #a07d5e;
            }

            QCheckBox::indicator:disabled {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
            }
            """)

        

        

        self.load_building_types()

    def load_building_types(self):
        """Заполняет чекбоксы уникальными типами зданий"""
        buildings = self.get_unique_buildings()
        row, col, max_rows = 0, 0, 7
        for building in buildings:
            cb = QCheckBox(building)
            self.layout_checkboxes.addWidget(cb, row, col, alignment=Qt.AlignLeft)
            cb.clicked.connect(self.single_selection)  # Только один чекбокс
            self.checkboxes.append(cb)
            row += 1
            if row >= max_rows:
                row, col = 0, col + 1
        columns = (len(buildings) + max_rows - 1) // max_rows  # кол-во колонок
        for i in range(columns):
            self.layout_checkboxes.setColumnStretch(i, 1)

    def single_selection(self):
        """Обеспечиваем выбор только одного чекбокса"""
        sender = self.sender()
        for cb in self.checkboxes:
            if cb != sender:
                cb.setChecked(False)

    def accept_selection(self):
        selected = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите тип здания!")
            return
        self.selected_building_type = selected[0]
        self.accept()

    def get_unique_buildings(self):
        df = self.data_service.ukup()
        if df is not None and 'Здание и сооружение' in df.columns:
            return df['Здание и сооружение'].dropna().unique().tolist()
        return []
