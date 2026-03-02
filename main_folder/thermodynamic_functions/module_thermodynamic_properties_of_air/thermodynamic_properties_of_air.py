# Импортируем родительский класс из корня проекта
from main_folder.base_classes.base_thermodynamic import BaseGasFromCSV

class AirPropertiesMatrix(BaseGasFromCSV):
    """Модуль Воздуха. Вся логика унаследована от BaseGasFromCSV."""
    
    def __init__(self, csv_file_path: str):
        # Просто передаем родительскому классу путь и константы воздуха
        super().__init__(csv_file_path, R_val=0.2881, mu_val=28.86)