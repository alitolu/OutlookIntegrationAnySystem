from typing import Dict, Any
from .excel_helper import ExcelHelper 
from .mssql_helper import MSSQLHelper
from .data_source import DataSource

class DataSourceFactory:
    @staticmethod
    def create_data_source(config: Dict[str, Any]) -> DataSource:
        """Veri kaynağı oluşturucu"""
        try:
            if not config or "datasource" not in config:
                return ExcelHelper("data/_main.xlsx", config)
            source_type = config.get("datasource", {}).get("type", "excel").lower()
            if source_type == "mssql":
                return MSSQLHelper(config)  # MSSQL seçildiyse MSSQLHelper oluştur
            if source_type == "excel":
                excel_file = config.get("datasource", {}).get("excel_file", "data/_main.xlsx")
                return ExcelHelper(excel_file, config)
            else:
                print(f"Desteklenmeyen veri kaynağı tipi: {source_type}, Excel kullanılacak")
                return ExcelHelper("data/_main.xlsx", config)
        except Exception as e:
            print(f"Veri kaynağı oluşturma hatası: {str(e)}")
            return ExcelHelper("data/_main.xlsx", config)
