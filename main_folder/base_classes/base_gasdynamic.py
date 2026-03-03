import numpy as np
from scipy.optimize import brentq
from typing import Tuple, List, Optional, Any

# Импортируем единый реестр из соседнего базового класса
from main_folder.base_classes.base_thermodynamic import ureg

class BaseGasDynamic:
    """
    Базовый класс газодинамических функций.
    Строгое соответствие уравнениям газовой динамики (ГДФ).
    Все параметры безразмерные.
    """
    
    ureg = ureg 

    @staticmethod
    def lambda_max(k: float) -> float:
        """
        Максимальный коэффициент скорости (истечение в вакуум, T=0).
        Формула: lam_max = sqrt((k + 1) / (k - 1))
        """
        return np.sqrt((k + 1) / (k - 1))

    # =========================================================
    # ФУНДАМЕНТАЛЬНАЯ СВЯЗЬ: ЧИСЛО МАХА (M) <---> ЛЯМБДА (lam)
    # =========================================================
    
    @staticmethod
    def M_to_lambda(k: float, M: float) -> float:
        """
        Перевод числа Маха (M) в коэффициент скорости (lambda).
        Формула: lambda = sqrt([((k+1)/2) * M^2] / [1 + ((k-1)/2) * M^2] )
        """
        if np.isinf(M):
            return BaseGasDynamic.lambda_max(k)
        
        num = ((k + 1) / 2) * (M ** 2)
        den = 1 + ((k - 1) / 2) * (M ** 2)
        return np.sqrt(num / den)

    @staticmethod
    def lambda_to_M(k: float, lam: float) -> float:
        """
        Перевод коэффициента скорости (lambda) в число Маха (M).
        Формула: M = sqrt([2/(k+1) * lam^2] / [1 - ((k-1)/(k+1)) * lam^2] )
        """
        l_max = BaseGasDynamic.lambda_max(k)
        if lam >= l_max:
            return np.inf # При истечении в вакуум Мах стремится к бесконечности
            
        tau = BaseGasDynamic.calc_tau(k, lam)
        return np.sqrt((2 / (k + 1)) * (lam ** 2) / tau)

    # =========================================================
    # ПРЯМЫЕ ГАЗОДИНАМИЧЕСКИЕ ФУНКЦИИ (от lambda)
    # =========================================================

    @staticmethod
    def calc_tau(k: float, lam: float) -> float:
        """Функция температур: tau = T / T*"""
        if lam > BaseGasDynamic.lambda_max(k):
            raise ValueError(f"lambda ({lam}) превышает предел lambda_max")
        return 1.0 - ((k - 1) / (k + 1)) * (lam ** 2)

    @staticmethod
    def calc_pi(k: float, lam: float) -> float:
        """Функция давлений: pi = P / P*"""
        tau = BaseGasDynamic.calc_tau(k, lam)
        return tau ** (k / (k - 1))

    @staticmethod
    def calc_eps(k: float, lam: float) -> float:
        """Функция плотностей: eps = rho / rho*"""
        tau = BaseGasDynamic.calc_tau(k, lam)
        return tau ** (1 / (k - 1))

    @staticmethod
    def calc_q(k: float, lam: float) -> float:
        """Функция приведенного расхода: q = (rho * c) / (rho_cr * a_cr)"""
        eps = BaseGasDynamic.calc_eps(k, lam)
        return lam * eps * (((k + 1) / 2) ** (1 / (k - 1)))

    # =========================================================
    # РЕШАТЕЛЬ ОБРАТНЫХ ЗАДАЧ (Поиск lambda)
    # =========================================================

    def solve_lambda(self, k: float, param_name: str, param_val: float, regime: str = 'subsonic') -> float:
        """Аналитическое и численное нахождение lambda по любому известному параметру ГДФ"""
        
        if param_name == 'lambda_val':
            return param_val
            
        elif param_name == 'M':
            # ИСПОЛЬЗУЕМ СТРОГУЮ ТЕОРЕТИЧЕСКУЮ ФУНКЦИЮ
            return self.M_to_lambda(k, param_val)
            
        elif param_name == 'tau':
            return np.sqrt(((k + 1) / (k - 1)) * (1 - param_val))
            
        elif param_name == 'pi':
            tau_val = param_val ** ((k - 1) / k)
            return self.solve_lambda(k, 'tau', tau_val)
            
        elif param_name == 'eps':
            tau_val = param_val ** (k - 1)
            return self.solve_lambda(k, 'tau', tau_val)
            
        elif param_name == 'q':
            if param_val > 1.0:
                raise ValueError(f"Приведенный расход q не может быть > 1.0 (получено {param_val})")
            if np.isclose(param_val, 1.0):
                return 1.0 # Критическое сечение
                
            def obj_q(lam_est): 
                return self.calc_q(k, lam_est) - param_val
                
            l_max = self.lambda_max(k)
            
            # Численный поиск с учетом режима течения
            if regime == 'subsonic':
                return brentq(obj_q, 1e-6, 1.0)
            elif regime == 'supersonic':
                return brentq(obj_q, 1.0, l_max - 1e-6)
            else:
                raise ValueError("Режим 'regime' должен быть 'subsonic' или 'supersonic'")
        else:
            raise ValueError(f"Неизвестный параметр ГДФ: {param_name}")

    def _build_gdf_matrix(self, k: float, lam: float) -> Tuple[np.ndarray, List[str]]:
        """Универсальный упаковщик в матрицу 7x1"""
        labels =['k', 'lambda', 'M', 'tau', 'pi', 'eps', 'q']
        dimless = self.ureg.dimensionless
        
        data =[
            k * dimless,
            lam * dimless,
            self.lambda_to_M(k, lam) * dimless,  # <-- Вызов строгой функции связи
            self.calc_tau(k, lam) * dimless,
            self.calc_pi(k, lam) * dimless,
            self.calc_eps(k, lam) * dimless,
            self.calc_q(k, lam) * dimless
        ]
        
        return np.array(data, dtype=object).reshape(7, 1), labels