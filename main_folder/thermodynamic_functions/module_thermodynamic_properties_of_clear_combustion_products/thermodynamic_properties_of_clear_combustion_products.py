from main_folder.base_classes.base_thermodynamic import BaseGasFromCSV

class ClearCombustionPropertiesMatrix(BaseGasFromCSV):
    """Модуль Чистых продуктов сгорания. Вся логика унаследована."""
    
    def __init__(self, csv_file_path: str):
        # Константы для продуктов сгорания метана
        super().__init__(csv_file_path, R_val=0.3007, mu_val=27.65)