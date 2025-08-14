import os
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QPushButton, QHeaderView
from PyQt5.uic import loadUi
from PyQt5.QtCore import QTimer
from logic.paths import get_ui_path



class DescriptionDialog(QDialog):
    def __init__(self, analog_id, df_description, parent=None):
        super().__init__(parent)
        loadUi(get_ui_path("pages/description.ui"), self)

        df_filtered = df_description[df_description.index == analog_id]
        self.pushButton_close = self.findChild(QPushButton, "pushButton_close")
        self.pushButton_close.clicked.connect(self.close)

        if not df_filtered.empty:
            self.label_description.setText(f"Аналог ID: {analog_id}")

            self.tableView_description.setRowCount(df_filtered.shape[0])
            self.tableView_description.setColumnCount(df_filtered.shape[1])
            self.tableView_description.setHorizontalHeaderLabels(df_filtered.columns.tolist())

            for row in range(df_filtered.shape[0]):
                for col in range(df_filtered.shape[1]):
                    value = df_filtered.iat[row, col]
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() ^ 2)  # делаем ячейки нередактируемыми
                    self.tableView_description.setItem(row, col, item)

            header = self.tableView_description.horizontalHeader()
            header.setStretchLastSection(False)  # мы сами задаем ширину вручную
            header.setSectionResizeMode(QHeaderView.Fixed)  # отключаем авторастяжение

            # Подгонка высоты строк под содержимое
            self.tableView_description.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

            # Отложенное задание ширины колонок, когда окно уже отрисовано
            QTimer.singleShot(0, self.adjust_column_widths)
        else:
            self.label_description.setText(f"Нет описания для ID: {analog_id}")
            self.tableView_description.setRowCount(0)

    def adjust_column_widths(self):
        total_width = self.tableView_description.viewport().width()
        self.tableView_description.setColumnWidth(0, int(total_width * 0.85))
        self.tableView_description.setColumnWidth(1, int(total_width * 0.15))
