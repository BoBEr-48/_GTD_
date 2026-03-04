import numpy as np
import pint
from typing import Optional, Any

# Импорт единого реестра и модуля газодинамики
from main_folder.base_classes.base_thermodynamic import ureg
from main_folder.gasdynamic_functions.module_gasdynamic_functions.gasdynamic_functions import GasDynamicCalculator

class ThermogasdynamicPort:
    """
    Термогазодинамический порт (Сечение двигателя).
    Хранит параметры рабочего тела, полные и статические параметры потока, а также кинематику.
    """

    def __init__(self, name: str, fluid_module: Any, G: pint.Quantity[Any], alpha: float = 1.0):
        self.name = name
        self.fluid = fluid_module  # Ссылка на модуль расчета (Воздух, ЧПС или Смесь)
        self.G = G                 # Массовый расход
        self.alpha = alpha         # Коэф-нт избытка воздуха (имеет смысл для смесей)
        
        self.gdf_calc = GasDynamicCalculator()

        # Полные параметры (Торможения)
        self.T_star: Optional[pint.Quantity] = None
        self.P_star: Optional[pint.Quantity] = None
        self.h_star: Optional[pint.Quantity] = None
        self.s0_star: Optional[pint.Quantity] = None
        self.cp_star: Optional[pint.Quantity] = None
        self.R: Optional[pint.Quantity] = None
        self.mu: Optional[pint.Quantity] = None
        self.k: Optional[float] = None  # Показатель адиабаты

        # Статические параметры
        self.T_stat: Optional[pint.Quantity] = None
        self.P_stat: Optional[pint.Quantity] = None
        self.h_stat: Optional[pint.Quantity] = None
        self.rho: Optional[pint.Quantity] = None
        
        # Кинематика и Геометрия
        self.M: Optional[float] = None
        self.lam: Optional[float] = None
        self.q: Optional[float] = None
        self.c: Optional[pint.Quantity] = None # Скорость потока
        self.F: Optional[pint.Quantity] = None # Площадь сечения

    def _get_thermo_matrix_safe(self, **kwargs) -> np.ndarray:
        """
        Полиморфный вызов: модули Воздуха не принимают alpha, 
        а модуль Смеси требует alpha. Этот метод сам понимает, как обращаться к базе.
        """
        try:
            # Пытаемся передать alpha (для смесей)
            matrix, _ = self.fluid.get_full_matrix(alpha=self.alpha, **kwargs)
        except TypeError:
            # Если выдало ошибку, значит это чистый газ (Воздух/ЧПС), которому alpha не нужен
            matrix, _ = self.fluid.get_full_matrix(**kwargs)
        return matrix

    def set_total_state(self, T_star: pint.Quantity, P_star: pint.Quantity):
        """
        Устанавливает параметры заторможенного потока (0D расчет).
        """
        self.T_star = T_star
        self.P_star = P_star
        
        # Вызываем термодинамику
        matrix = self._get_thermo_matrix_safe(T=self.T_star)
        
        # Извлекаем данные
        self.cp_star = matrix[1, 0]
        self.h_star = matrix[2, 0]
        self.s0_star = matrix[3, 0]
        self.R = matrix[4, 0]
        self.mu = matrix[5, 0]
        
        # Считаем показатель адиабаты: k = cp / (cp - R)
        cp_val = self.cp_star.magnitude
        R_val = self.R.to(self.cp_star.units).magnitude # Приводим к одним единицам
        self.k = cp_val / (cp_val - R_val)

    def add_kinematics_by_mach(self, M: float):
        """
        Рассчитывает статику и площади по заданному числу Маха (1D расчет).
        Требует, чтобы до этого были заданы полные параметры.
        """
        if self.T_star is None or self.P_star is None:
            raise ValueError("Сначала задайте полные параметры через set_total_state!")

        self.M = M
        
        # 1. Газодинамика: получаем tau, pi, lam
        gdf_mat, _ = self.gdf_calc.get_gdf_matrix(k_direct=self.k, M=self.M)
        self.lam = gdf_mat[1, 0].magnitude
        tau = gdf_mat[3, 0].magnitude
        pi = gdf_mat[4, 0].magnitude
        self.q = gdf_mat[6, 0].magnitude

        # 2. Статика: T = T* * tau, P = P* * pi
        self.T_stat = self.T_star * tau
        self.P_stat = self.P_star * pi
        
        # Энтальпию статики берем из термодинамики
        stat_matrix = self._get_thermo_matrix_safe(T=self.T_stat)
        self.h_stat = stat_matrix[2, 0]

        # 3. Плотность: rho = P / (R * T)
        self.rho = (self.P_stat / (self.R * self.T_stat)).to(ureg.kilogram / ureg.meter**3)

        # 4. Скорость звука и скорость потока: a = sqrt(k*R*T)
        # pint автоматически извлечет корень и мы переведем в м/с
        a_sound = np.sqrt(self.k * self.R * self.T_stat).to(ureg.meter / ureg.second)
        self.c = self.M * a_sound

        # 5. Площадь сечения: F = G / (rho * c)
        self.F = (self.G / (self.rho * self.c)).to(ureg.meter**2)

    def __repr__(self):
        """
        Информативный вывод состояния порта
        """
        T_s = f"{self.T_star.to(ureg.kelvin).magnitude:.1f} K" if self.T_star else "None"
        P_s = f"{self.P_star.to(ureg.kilopascal).magnitude:.1f} kPa" if self.P_star else "None"
        G_val = f"{self.G.to(ureg.kilogram/ureg.second).magnitude:.2f} kg/s" if self.G else "None"
        k_val = f"{self.k:.4f}" if self.k is not None else "None"
        
        header = f"<Port '{self.name}' | Fluid: {self.fluid.__class__.__name__} | G: {G_val} | alpha: {self.alpha}>\n"
        totals = f"  Total[T*: {T_s}, P*: {P_s}, k: {k_val}]\n"
        
        if self.M is not None:
            M_val = f"{self.M:.3f}"
            c_val = f"{self.c.magnitude:.1f} m/s"
            F_val = f"{self.F.to(ureg.cm**2).magnitude:.1f} cm2"
            T_st = f"{self.T_stat.to(ureg.kelvin).magnitude:.1f} K"
            P_st = f"{self.P_stat.to(ureg.kilopascal).magnitude:.1f} kPa"
            statics = f"  Static[T: {T_st}, P: {P_st}, M: {M_val}, c: {c_val}, Area: {F_val}]"
        else:
            statics = "  Static [Not calculated yet]"
            
        return header + totals + statics