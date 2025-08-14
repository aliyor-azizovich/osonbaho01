import os
import sys

def is_frozen():
    return getattr(sys, 'frozen', False)

def get_base_dir():
    # Путь к папке, где лежит .exe или main.py
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Папка, где будут храниться пользовательские файлы, JSON и т.п.
def get_project_dir():
    return os.path.join(os.path.expanduser("~"), "AppData", "Local", "OsonBaho")

# --- UI ---
def get_ui_path(filename):
    return os.path.join(get_base_dir(), "ui", filename)

# --- Logic ---
def get_logic_path(filename):
    return os.path.join(get_base_dir(), "logic", filename)

# --- Data: stat_koeff, data.pkg ---
def get_stat_koeff_path():
    return os.path.join(get_base_dir(), "stat_koeff.xlsx")

def get_data_pkg_path():
    return os.path.join(get_base_dir(), "data.pkg")

# --- Reports (внешняя папка рядом с exe) ---
def get_reports_templates_dir():
    return os.path.join(get_base_dir(), "reports")

# --- Research (внешняя папка рядом с exe) ---
def get_research_dir():
    return os.path.join(get_base_dir(), "research") 

# --- JSON отчёты пользователя ---
def get_reports_dir():
    return os.path.join(get_project_dir(), "reports")

def get_report_file_path(report_number):
    return os.path.join(get_reports_dir(), f"report_{report_number}.json")

# --- Settings / Registry ---
def get_settings_path():
    return os.path.join(get_project_dir(), "settings.json")

def get_registry_path():
    return os.path.join(get_project_dir(), "report_registry.json")

def get_rent_temp_path():
    return os.path.join(get_base_dir(), "rent_temp.csv") 

def get_province_choose_path():
    return os.path.join(get_base_dir(), "province_choose.xlsx")

def get_regional_coff_path():
    return os.path.join(get_base_dir(), "regional_coff.xlsx")

def get_rent_analyze_path():
    return os.path.join(get_base_dir(), "rent_analyze.xlsx")

def get_rent_2025_path():
    return os.path.join(get_base_dir(), "rent_min_2025.xlsx")

def get_sesmos_path():
    return os.path.join(get_base_dir(), "sesmos.xlsx")  # или .csv, если у тебя .csv

def get_territorial_correction_path():
    return os.path.join(get_base_dir(), "territorial correction.xlsx")
