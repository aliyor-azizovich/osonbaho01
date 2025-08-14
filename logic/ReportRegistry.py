import os
import json
from datetime import datetime
from logic.paths import get_registry_path
from logic.paths import get_report_file_path



class ReportRegistry:
    def __init__(self, project_dir=None):
        self.registry_path = get_registry_path()

        if not os.path.exists(self.registry_path):
            with open(self.registry_path, "w", encoding="utf-8") as file:
                json.dump({"reports": []}, file, ensure_ascii=False, indent=4)

    def load_registry(self):
        try:
            with open(self.registry_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
                if not content:
                    raise ValueError("Файл реестра пуст")
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return {"reports": []}

    def remove_report(self, report_number):
        data = self.load_registry()
        reports = data.get("reports", [])

        updated_reports = [r for r in reports if str(r.get("report_number")) != str(report_number)]

        if len(reports) == len(updated_reports):
            raise ValueError(f"Отчёт №{report_number} не найден в реестре.")

        data["reports"] = updated_reports

        try:
            with open(self.registry_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception as e:
            raise ValueError(f"Ошибка при сохранении реестра: {str(e)}")

        report_path = get_report_file_path(report_number)
        if os.path.exists(report_path):
            try:
                os.remove(report_path)
            except:
                pass

    def add_report(self, report_number, reg_number, report_date, owner_name, buyer_name, adress, valuation_cost="Оценка не окончена"):
        data = self.load_registry()

        new_report = {
            "report_number": report_number,
            "reg_number": reg_number,
            "report_date": report_date,
            "last_change_date": datetime.now().strftime("%Y-%m-%d"),
            "owner_name": owner_name,
            "buyer_name": buyer_name,
            "adress": adress,
            "valuation_cost": valuation_cost,
            "file_path": f"reports/report_{report_number}.json"
        }

        data["reports"].append(new_report)

        with open(self.registry_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def update_report(self, report_number, reg_number, report_date, last_change_date, owner_name, buyer_name, adress, valuation_cost="Оценка не окончена"):
        try:
            with open(self.registry_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            updated = False
            for report in data.get("reports", []):
                if report.get("report_number") == report_number:
                    report['reg_number'] = reg_number
                    report["report_date"] = report_date
                    report["last_change_date"] = last_change_date
                    report["owner_name"] = owner_name
                    report["buyer_name"] = buyer_name
                    report["adress"] = adress
                    report["valuation_cost"] = valuation_cost
                    updated = True
                    break

            if not updated:
                new_report = {
                    "report_number": report_number,
                    "reg_number": reg_number,
                    "report_date": report_date,
                    "last_change_date": last_change_date,
                    "owner_name": owner_name,
                    "buyer_name": buyer_name,
                    "adress": adress,
                    "valuation_cost": valuation_cost
                }
                data["reports"].append(new_report)

            with open(self.registry_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def get_report_data(self, report_number):
        try:
            with open(self.registry_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            for report in data.get("reports", []):
                if report["report_number"] == str(report_number):
                    return report

            return None
        except Exception:
            return None
