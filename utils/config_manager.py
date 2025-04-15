import json
import os

class ConfigManager:
    def __init__(self):
        self.config_file = "config/settings.json"
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)  # settings.json'dan okuyor
        except Exception as e:
            print(f"Config okuma hatası: {str(e)}")
            return {}

    def save_config(self):
        """Ayarları kaydet"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Config kaydetme hatası: {str(e)}")
            return False

    def get_column_mapping(self, excel_column):
        """Excel sütunu için görünen isim ve görünürlük ayarını al"""
        mappings = self.config.get("datasource", {}).get("column_mappings", {})
        return mappings.get(excel_column, {
            "display_name": excel_column,
            "visible": True
        })

    def update_datasource(self, new_settings):
        """Veri kaynağı ayarlarını güncelle"""
        self.config["datasource"] = new_settings
        return self.save_config()
