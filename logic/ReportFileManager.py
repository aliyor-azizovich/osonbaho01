import json
import os
from logic.paths import get_reports_dir, get_report_file_path
import re

class ReportFileManager:
    def __init__(self):
        self.reports_dir = get_reports_dir()

    def get_report_path(self, report_number):
        """Возвращает путь к файлу отчёта"""
        return get_report_file_path(report_number)


    def create_report_file(self, report_number):
        # Очистим строку от недопустимых символов
        report_number = str(report_number).strip()

        # Только латиница, цифры, тире, подчёркивание
        report_number = re.sub(r'[^\w\-]', '_', report_number)

        report_path = get_report_file_path(report_number)
        reports_dir = os.path.dirname(report_path)
        os.makedirs(reports_dir, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as file:
            json.dump({}, file, ensure_ascii=False, indent=4)


    def save_report_data(self, report_number, data):
        """Сохраняет данные отчёта в JSON-файл"""
        try:
            report_path = self.get_report_path(report_number)
            with open(report_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def load_report_data(self, report_number):
        """Загружает данные отчёта из JSON-файла"""
        try:
            report_path = self.get_report_path(report_number)
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as file:
                    return json.load(file)
            return {}
        except Exception:
            return {}
