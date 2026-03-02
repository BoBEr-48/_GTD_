import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import pint
import os
from typing import Optional, Any, Tuple, List, Dict

# 1. ЕДИНЫЙ РЕЕСТР НА ВЕСЬ ПРОЕКТ
ureg = pint.UnitRegistry()
ureg.formatter.default_format = "~P"

class BaseThermoModel:
    """Самый базовый класс. Хранит единицы измерения и метод форматирования матрицы."""
    
    # Наследуем единый реестр
    ureg = ureg 

    def __init__(self):
        # Эталонные размерности
        self._u_T = self.ureg.kelvin
        self._u_cp = self.ureg.kilojoule / (self.ureg.kilogram * self.ureg.kelvin)
        self._u_h = self.ureg.kilojoule / self.ureg.kilogram
        self._u_s0 = self.ureg.kilojoule / (self.ureg.kilogram * self.ureg.kelvin)
        self._u_R = self.ureg.kilojoule / (self.ureg.kilogram * self.ureg.kelvin)
        self._u_mu = self.ureg.kilogram / self.ureg.kilomole

    def _build_matrix(self, T, cp, h, s0, R, mu) -> Tuple[np.ndarray, List[str]]:
        """Универсальный упаковщик в 6x1 матрицу для всех дочерних классов"""
        labels =['T', 'cp', 'h', 's0', 'R', 'mu']
        data =[
            T * self._u_T,
            cp * self._u_cp,
            h * self._u_h,
            s0 * self._u_s0,
            R * self._u_R,
            mu * self._u_mu
        ]
        matrix = np.array(data, dtype=object).reshape(6, 1)
        return matrix, labels


class BaseGasFromCSV(BaseThermoModel):
    """Родительский класс для Воздуха и Чистых продуктов сгорания. Берет на себя всю грязную работу."""
    
    _instances_cache: Dict[Tuple[type, str], Any] = {}

    def __new__(cls, csv_file_path: str, *args, **kwargs):
        # Singleton теперь учитывает и класс, и путь
        cache_key = (cls, csv_file_path)
        if cache_key in cls._instances_cache:
            return cls._instances_cache[cache_key]
        instance = super().__new__(cls)
        cls._instances_cache[cache_key] = instance
        return instance

    def __init__(self, csv_file_path: str, R_val: float, mu_val: float):
        if hasattr(self, 'df'): return # Защита от двойной инициализации
        
        super().__init__() # Инициализируем размерности
        
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"Файл не найден: {csv_file_path}")
            
        self.df = pd.read_csv(csv_file_path, sep=';')
        T_b, cp_b, h_b, s0_b = self.df['T_K'].values, self.df['cp'].values, self.df['h'].values, self.df['s0'].values

        # Создаем интерполяторы один раз на всех
        self._f_cp = interp1d(T_b, cp_b, kind='linear', fill_value='extrapolate')
        self._f_h  = interp1d(T_b, h_b,  kind='linear', fill_value='extrapolate')
        self._f_s0 = interp1d(T_b, s0_b, kind='linear', fill_value='extrapolate')
        self._inv_cp = interp1d(cp_b, T_b, kind='linear', fill_value='extrapolate')
        self._inv_h  = interp1d(h_b,  T_b, kind='linear', fill_value='extrapolate')
        self._inv_s0 = interp1d(s0_b, T_b, kind='linear', fill_value='extrapolate')

        self.R_val = R_val
        self.mu_val = mu_val

    def get_full_matrix(self, T: Optional[pint.Quantity[Any]] = None, cp: Optional[pint.Quantity[Any]] = None, h: Optional[pint.Quantity[Any]] = None, s0: Optional[pint.Quantity[Any]] = None) -> Tuple[np.ndarray, List[str]]:
        """Единая математика решения для табличных газов"""
        inputs = {'T': T, 'cp': cp, 'h': h, 's0': s0}
        provided = {k: v for k, v in inputs.items() if v is not None}
        if len(provided) != 1: raise ValueError("Ожидался ровно 1 аргумент")
            
        key, val = list(provided.items())[0]

        if key == 'T':   T_val = val.to(self._u_T).magnitude
        elif key == 'cp':T_val = float(self._inv_cp(val.to(self._u_cp).magnitude))
        elif key == 'h': T_val = float(self._inv_h(val.to(self._u_h).magnitude))
        elif key == 's0':T_val = float(self._inv_s0(val.to(self._u_s0).magnitude))

        return self._build_matrix(
            T=T_val,
            cp=float(self._f_cp(T_val)),
            h=float(self._f_h(T_val)),
            s0=float(self._f_s0(T_val)),
            R=self.R_val,
            mu=self.mu_val
        )