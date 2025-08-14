
from logic.data_entry import DataEntryForm

class KoefsService:
    def __init__(self, data_service=None):
        self.data_service = data_service or DataEntryForm()

    def get_filtered_stat_and_regional(self, oblast_name, rayon_name):
        df_stat = self.data_service.load_stat_koeff()
        df_regional = self.data_service.load_regional_coff()
        df_territorial = self.data_service.territorial_correction()

        if df_stat.empty or df_regional is None or df_territorial is None:
            return None, None

        # Находим region_id по названию области
        region_row = df_territorial.loc[df_territorial['region'] == oblast_name]
        if region_row.empty:
            return None, None
        region_id = region_row['region_id'].values[0]

        # Фильтрация региональных коэффициентов
        filtered_data = df_regional[df_regional['region_id'] == region_id]
        matched_data = filtered_data[filtered_data['type'] == rayon_name]
        final_data = matched_data if not matched_data.empty else filtered_data

        return df_stat, final_data
