
from PyQt5 import uic
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QTableWidgetItem
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from logic.koefs_logic import KoefsService
import os
from PyQt5.QtCore import Qt
from logic.paths import get_ui_path, get_project_dir

class KoefsWidget(QWidget):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        uic.loadUi(get_ui_path("koefs.ui"), self)

        self.main_window = main_window
        self.service = KoefsService()

        if self.main_window:
            self.main_window.comboBox_oblast.currentIndexChanged.connect(self.load_table_data)
            self.main_window.comboBox_rayon.currentIndexChanged.connect(self.load_table_data)

        self.load_table_data()

    def load_table_data(self):
        oblast_name = self.main_window.comboBox_oblast.currentText() if self.main_window else ""
        rayon_name = self.main_window.comboBox_rayon.currentText() if self.main_window else ""
        df_stat, final_data = self.service.get_filtered_stat_and_regional(oblast_name, rayon_name)

        if df_stat is not None and final_data is not None:
            self.display_table(df_stat, self.tableView_stat)
            self.display_table(final_data, self.tableView_regional)

    def display_table(self, dataframe, table_view):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(dataframe.columns.tolist())

        for row in dataframe.itertuples(index=False):
            model.appendRow([QStandardItem(str(item)) for item in row])

        table_view.setModel(model)
        table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)


    def collect_koefs_data(self):
        """Сохраняет данные только из tableView_stat"""
        data = {"koefs_table": []}

        model = self.tableView_stat.model()
        if not model:
            return data

        rows = model.rowCount()
        cols = model.columnCount()

        for row in range(rows):
            row_data = []
            for col in range(cols):
                index = model.index(row, col)
                row_data.append(index.data() if index.isValid() else "")
            data["koefs_table"].append(row_data)

        return data


    def load_koefs_data(self, data: dict):
        """Восстанавливает данные только в tableView_stat"""
        table_data = data.get("koefs_table", [])
        if not table_data:
            return

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Дата", "Коэфф"])

        for row_data in table_data:
            items = [QStandardItem(str(val)) for val in row_data]
            for item in items:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            model.appendRow(items)

        self.tableView_stat.setModel(model)
        self.tableView_stat.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView_stat.setEditTriggers(QAbstractItemView.NoEditTriggers)
