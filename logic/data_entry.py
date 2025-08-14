
import pandas as pd
from PyQt5.QtWidgets import QWidget
from logic.encrypted_loader import EncryptedDataLoader
from io import BytesIO
import pandas as pd
from logic.paths import get_stat_koeff_path, get_province_choose_path, get_regional_coff_path, get_rent_temp_path, get_rent_2025_path, get_sesmos_path, get_territorial_correction_path, get_rent_analyze_path
                        
                        

class DataEntryForm(QWidget):
    def __init__(self, parent=None):
        self.loader = EncryptedDataLoader()

        super().__init__(parent)

    def load_stat_koeff(self):
        try:
            file_path = get_stat_koeff_path()
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить stat_koeff.xlsx: {e}") 
            return pd.DataFrame()



    
    def load_regional_coff(self):
        try:
            file_path = get_regional_coff_path()
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            print(f"[ERROR] Не удалось загрузить regional_coff.xlsx: {e}")
            return pd.DataFrame()

    

   

    def ukup(self):
        try:
            return pd.read_parquet(self.loader.get("UKUP.parquet"))
        except Exception as e:
            import traceback
            with open("ukup_error.log", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
            return None

    def description(self):
        try:
            df = pd.read_parquet(self.loader.get("Description.parquet"))
            df.index = df.index.astype(int)
            return df
        except Exception:
            return None

    def structural_elements(self):
        try:
            df = pd.read_parquet(self.loader.get("structural_elements.parquet"))
            df.index = df.index.astype(int)
            return df
        except Exception:
            return None

    def Improvements(self):
        try:
            df = pd.read_parquet(self.loader.get("Improvements.parquet"))
            df.index = df.index.astype(int)
            return df
        except Exception:
            return None

    def Deviations(self):
        try:
            df = pd.read_parquet(self.loader.get("Deviations.parquet"))
            df.index = df.index.astype(int)
            return df
        except Exception:
            return None

    def facade(self):
        try:
            df = pd.read_parquet(self.loader.get("facade.parquet"))
            df.index = df.index.astype(int)
            return df
        except Exception:
            return None

    def altitude(self):
        try:
            df = pd.read_parquet(self.loader.get("altitude.parquet"))
            df.index = df.index.astype(int)
            return df
        except Exception:
            return None

    def territorial_correction(self):
        try:
            file_path = get_territorial_correction_path()
            return pd.read_excel(file_path)
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке territorial correction: {e}")
            return None

    def province_choose(self):
        try:
            file_path = get_province_choose_path()
            df = pd.read_excel(file_path, dtype={"kadastr": str})
            df["kadastr"] = df["kadastr"].str.strip().str.zfill(2)
            return df
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке province_choose: {e}")
            return None

    def rent_temp(self):
        try:
            file_path = get_rent_temp_path()
            return pd.read_csv(file_path)
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке rent_temp.csv: {e}")
            return None

    def load_rent_2025(self):
        try:
            file_path = get_rent_2025_path()
            return pd.read_excel(file_path)
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке rent_min_2025.xlsx: {e}")
            return pd.DataFrame()

    def sesmos(self):
        try:
            file_path = get_sesmos_path()
            if file_path.endswith(".csv"):
                return pd.read_csv(file_path)
            return pd.read_excel(file_path)
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке sesmos: {e}")
            return None
        
    def load_rent_analyze(self):
        try:
            file_path = get_rent_analyze_path()
            return pd.read_excel(file_path)
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке rent_analyze.xlsx: {e}")
            return pd.DataFrame()
