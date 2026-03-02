import numpy as np
from scipy.optimize import brentq
from typing import Optional, Any, Tuple, List

# Импортируем базовый класс и классы-компоненты
from main_folder.base_classes.base_thermodynamic import BaseThermoModel
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_air.thermodynamic_properties_of_air import AirPropertiesMatrix
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_clear_combustion_products.thermodynamic_properties_of_clear_combustion_products import ClearCombustionPropertiesMatrix

class CombustionMixturePropertiesMatrix(BaseThermoModel):
    
    def __init__(self, air_csv_path: str, clear_prod_csv_path: str):
        super().__init__() # Подтягиваем ureg и размерности из родителя
        
        self.air_mod = AirPropertiesMatrix(air_csv_path)
        self.prod_mod = ClearCombustionPropertiesMatrix(clear_prod_csv_path)

        self.L0 = 17.12

    def _get_mix_props_at_T(self, T_val: float, alpha: float):
        if alpha < 1.0: raise ValueError("alpha >= 1.0")

        # Получаем численные значения
        cp_a = float(self.air_mod._f_cp(T_val))
        h_a  = float(self.air_mod._f_h(T_val))
        s0_a = float(self.air_mod._f_s0(T_val))
        mu_a = self.air_mod.mu_val
        R_a  = self.air_mod.R_val

        cp_c = float(self.prod_mod._f_cp(T_val))
        h_c  = float(self.prod_mod._f_h(T_val))
        s0_c = float(self.prod_mod._f_s0(T_val))
        mu_c = self.prod_mod.mu_val
        R_c  = self.prod_mod.R_val

        # Вспомогательный коэф-нт q
        q = (mu_c / mu_a) * (self.L0 / (self.L0 + 1.0))
        
        # Объемные доли
        r_air = (q * (alpha - 1.0)) / (1.0 + q * (alpha - 1.0))
        r_ccp = 1.0 - r_air

        # Молекулярная масса смеси
        mu_mix = r_air * mu_a + r_ccp * mu_c

        # ИСПРАВЛЕНИЕ ФИЗИКИ: Переход к массовым долям
        g_air = (r_air * mu_a) / mu_mix
        g_ccp = (r_ccp * mu_c) / mu_mix

        # Удельные (массовые) свойства считаются по массовым долям
        cp_mix = g_air * cp_a + g_ccp * cp_c
        h_mix  = g_air * h_a  + g_ccp * h_c
        s0_mix = g_air * s0_a + g_ccp * s0_c
        R_mix  = g_air * R_a  + g_ccp * R_c

        return cp_mix, h_mix, s0_mix, R_mix, mu_mix

    def get_full_matrix(self, alpha: float, T=None, cp=None, h=None, s0=None) -> Tuple[np.ndarray, List[str]]:
        inputs = {'T': T, 'cp': cp, 'h': h, 's0': s0}
        provided = {k: v for k, v in inputs.items() if v is not None}
        if len(provided) != 1: raise ValueError("Нужен ровно 1 параметр помимо alpha")
            
        key, val = list(provided.items())[0]
        T_min, T_max = 200.0, 2200.0 # Ограничил экстраполяцию для надежности

        if key == 'T':
            T_val = val.to(self._u_T).magnitude
        elif key == 'h':
            target_h = val.to(self._u_h).magnitude
            T_val = brentq(lambda t: self._get_mix_props_at_T(t, alpha)[1] - target_h, T_min, T_max)
        elif key == 's0':
            target_s0 = val.to(self._u_s0).magnitude
            T_val = brentq(lambda t: self._get_mix_props_at_T(t, alpha)[2] - target_s0, T_min, T_max)
        elif key == 'cp':
            target_cp = val.to(self._u_cp).magnitude
            T_val = brentq(lambda t: self._get_mix_props_at_T(t, alpha)[0] - target_cp, T_min, T_max)

        # Рассчитываем и пакуем через унаследованный метод _build_matrix
        cp_m, h_m, s0_m, R_m, mu_m = self._get_mix_props_at_T(T_val, alpha)
        return self._build_matrix(T_val, cp_m, h_m, s0_m, R_m, mu_m)