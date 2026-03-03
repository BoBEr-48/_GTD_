import numpy as np
from typing import Optional, Tuple, List, Any

# Импорт базового класса
from main_folder.base_classes.base_gasdynamic import BaseGasDynamic

class GasDynamicCalculator(BaseGasDynamic):
    """
    Рабочий модуль газодинамических функций.
    Интегрируется с матрицами термодинамического модуля (ТДФ) для получения 'k'.
    """

    def __init__(self):
        super().__init__()

    def _extract_k_from_tdf_matrix(self, tdf_matrix: np.ndarray) -> float:
        """Извлечение k из ТДФ матрицы: k = cp / (cp - R)"""
        cp_val = tdf_matrix[1, 0].magnitude
        R_val = tdf_matrix[4, 0].magnitude
        return cp_val / (cp_val - R_val)

    def get_gdf_matrix(self, 
                       tdf_matrix: Optional[np.ndarray] = None, 
                       k_direct: Optional[float] = None,
                       lambda_val: Optional[float] = None,
                       M: Optional[float] = None,
                       tau: Optional[float] = None,
                       pi: Optional[float] = None,
                       eps: Optional[float] = None,
                       q: Optional[float] = None,
                       regime: str = 'subsonic') -> Tuple[np.ndarray, List[str]]:
        """
        Главный метод расчета. 
        Принимает либо tdf_matrix, либо k_direct.
        Плюс ОДИН кинематический параметр.
        """
        # 1. Определяем показатель адиабаты
        if tdf_matrix is not None:
            k_val = self._extract_k_from_tdf_matrix(tdf_matrix)
        elif k_direct is not None:
            k_val = k_direct
        else:
            raise ValueError("Передайте либо tdf_matrix, либо k_direct")

        # 2. Определяем, какой параметр передан
        gdf_inputs = {'lambda_val': lambda_val, 'M': M, 'tau': tau, 'pi': pi, 'eps': eps, 'q': q}
        provided = {name: val for name, val in gdf_inputs.items() if val is not None}
        
        if len(provided) != 1:
            raise ValueError(f"Ожидался строго 1 газодинамический параметр, получено {len(provided)}")
            
        param_name, param_val = list(provided.items())[0]

        # 3. Решаем задачу: находим lambda (а через нее все остальное)
        lam_solved = self.solve_lambda(k_val, param_name, param_val, regime)

        # 4. Собираем матрицу
        return self._build_gdf_matrix(k_val, lam_solved)