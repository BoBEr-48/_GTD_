import numpy as np
from typing import Optional, Any
import pint

# Импортируем единый реестр
from main_folder.base_classes.base_thermodynamic import ureg

class MechanicalPort:
    """
    Механический порт (Вал).
    Передает механическую энергию между узлами двигателя.
    
    Основные параметры:
    - power: Мощность (N или P) [Ватт, кВт]
    - rpm: Частота вращения (n)[об/мин]
    - torque: Крутящий момент (M_k) [Н*м]
    """

    def __init__(self, 
                 name: str = "Main_Shaft",
                 power: Optional[pint.Quantity[Any]] = None, 
                 rpm: Optional[pint.Quantity[Any]] = None):
        self.name = name
        self._power = power
        self._rpm = rpm

    # --- СВОЙСТВО: МОЩНОСТЬ ---
    @property
    def power(self) -> Optional[pint.Quantity[Any]]:
        return self._power

    @power.setter
    def power(self, value: pint.Quantity[Any]):
        # Проверяем, что передана именно мощность (Ватты)
        if not value.check('[mass] * [length]**2 / [time]**3'):
            raise pint.DimensionalityError(value.units, ureg.watt, 
                                           extra_msg=" Ожидалась размерность мощности (например, ureg.watt или ureg.kW)")
        self._power = value

    # --- СВОЙСТВО: ОБОРОТЫ ---
    @property
    def rpm(self) -> Optional[pint.Quantity[Any]]:
        return self._rpm

    @rpm.setter
    def rpm(self, value: pint.Quantity[Any]):
        # Проверяем, что передана частота (об/мин или Гц)
        if not value.check('1 / [time]'):
            raise pint.DimensionalityError(value.units, ureg.rpm, 
                                           extra_msg=" Ожидалась размерность частоты (например, ureg.rpm)")
        self._rpm = value

    # --- СВОЙСТВО: КРУТЯЩИЙ МОМЕНТ (Вычисляемое) ---
    @property
    def torque(self) -> Optional[pint.Quantity[Any]]:
        """
        Вычисляет крутящий момент, если известны мощность и обороты.
        M_k = N / omega
        """
        if self._power is not None and self._rpm is not None:
            # Переводим обороты в радианы в секунду (угловую скорость)
            # pint автоматически конвертирует rpm в rad/s, если попросить
            omega = self._rpm.to(ureg.radian / ureg.second)
            
            # Считаем момент и приводим к Ньютон-метрам
            calc_torque = (self._power / omega).to(ureg.newton * ureg.meter)
            return calc_torque
        return None

    def __repr__(self):
        """Красивый вывод состояния порта для отладки"""
        p_str = f"{self._power.to(ureg.kW):.2f}" if self._power else "None"
        r_str = f"{self._rpm.to(ureg.rpm):.0f}" if self._rpm else "None"
        t_str = f"{self.torque:.2f}" if self.torque else "None"
        
        return f"<MechanicalPort '{self.name}': Power={p_str}, RPM={r_str}, Torque={t_str}>"