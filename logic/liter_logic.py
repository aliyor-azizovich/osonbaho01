
from logic.data_entry import DataEntryForm

class LiterFilterService:
    def __init__(self, data_service=None):
        self.data_service = data_service or DataEntryForm()

    def get_unique_buildings(self):
        df = self.data_service.ukup()
        if df is not None and 'Здание и сооружение' in df.columns:
            return df['Здание и сооружение'].dropna().unique().tolist()
        return []
    
    def get_filtered_ukup(self, selected_building_type):
        df = self.data_service.ukup()
        if df is not None and 'Здание и сооружение' in df.columns:
            return df[df['Здание и сооружение'] == selected_building_type]
        return df.iloc[0:0]  # Пустой DataFrame
    
    def description(self):
        return self.data_service.description()