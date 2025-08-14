from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QComboBox
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


class MethodRejectionDialog(QDialog):
    def __init__(self, parent=None, valuation_window=None):
        super().__init__(parent)
        self.valuation_window = valuation_window

        uic.loadUi(get_ui_path("method__dialog.ui"), self)

        
        self.label_method_rejection = self.findChild(QLabel, "label_method_rejection")
        self.comboBox_reason = self.findChild(QComboBox, "comboBox_reason")
        self.pushButton_ok = self.findChild(QPushButton, "pushButton_ok")
        self.pushButton_exit = self.findChild(QPushButton, "pushButton_exit")
        self.pushButton_ok.clicked.connect(self.accept_if_valid)
        self.pushButton_exit.clicked.connect(self.reject)

        report_number = valuation_window.report_number_input.text().strip()
        self.cost_reasons = ["Объект не достроен", "Индивидуальное архитектурное решение"]
        self.comparative_reason = ["Нет рыночных данных", "Нетипичный объект"]
        report_path = valuation_window.main_window.report_manager.get_report_path(report_number)

        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

            
        self.agreement = report_data.get("agreement", {})
        self.use_cost = self.agreement.get("use_cost", False)
        self.use_comparative = self.agreement.get("use_comparative", False)
        self.template_map = {
            "Нет рыночных данных": "result_3.docx",
            "Индивидуальное архитектурное решение": "result_2.docx",
            "Объект не достроен": "result_1.docx",
            "Нетипичный объект": "result_4.docx"
        }
        self.set_rejection_label()
        self.populate_reason_combobox()


    def populate_reason_combobox(self):
        self.comboBox_reason.clear()  # очищаем список

        if not self.use_cost:
            self.comboBox_reason.addItems(self.cost_reasons)
        elif not self.use_comparative:
            self.comboBox_reason.addItems(self.comparative_reason)


    def set_rejection_label(self):
        self.label_method_rejection.clear()

        if not self.use_cost and not self.use_comparative:
            self.label_method_rejection.setText("Отказ от затратного и сравнительного подходов")
        elif not self.use_cost:
            self.label_method_rejection.setText("Отказ от затратного подхода")
        elif not self.use_comparative:
            self.label_method_rejection.setText("Отказ от сравнительного подхода")


   


    def accept_if_valid(self):
        reason_text = self.comboBox_reason.currentText().strip()
        if not reason_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите причину отказа.")
            return
        self.selected_template = self.template_map.get(reason_text, "result.docx")
       
        self.accept()

