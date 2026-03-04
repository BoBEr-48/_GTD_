from typing import Optional
import pint

# Импортируем базовые классы и инструменты
from main_folder.structural_layer.nodes.base_node import BaseEngineNode
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort
from main_folder.gasdynamic_functions.module_gasdynamic_functions.gasdynamic_functions import GasDynamicCalculator
from main_folder.base_classes.base_thermodynamic import ureg

class InletDeviceNode(BaseEngineNode):
    """
    Узел Входного Устройства (ВхУ / Воздухозаборник).
    Обеспечивает торможение набегающего потока воздуха от статических параметров 
    атмосферы (H, M0) до полных параметров перед компрессором.
    
    Поддерживает как дозвуковые, так и сверхзвуковые режимы за счет 
    пользовательского коэффициента восстановления давления (sigma).
    """
    
    def __init__(self, 
                 name: str, 
                 port_in: ThermogasdynamicPort, 
                 port_out: ThermogasdynamicPort,
                 M_flight: float,
                 sigma: float,
                 inlet_type: str = "subsonic"):
        super().__init__(name, port_in, port_out)
        
        self.M_flight = M_flight      # Число Маха полета
        self.inlet_type = inlet_type  # Тип (для информативности: 'subsonic' или 'supersonic')
        self.gdf_calc = GasDynamicCalculator()

        # Пользовательский коэффициент сохранения полного давления
        if sigma <= 0.0 or sigma > 1.0:
            raise ValueError(f"[{self.name}] Коэффициент sigma должен быть в пределах (0; 1]. Задано: {sigma}")
        self.sigma = sigma

    def calculate(self):
        """
        Выполнение термо- и газодинамического расчета входного устройства.
        """
        # 1. Извлекаем статические параметры атмосферы из входного порта
        T_stat_H = self.port_in.T_stat
        P_stat_H = self.port_in.P_stat

        if T_stat_H is None or P_stat_H is None:
            raise ValueError(f"[{self.name}] Ошибка: В порт {self.port_in.name} не переданы статические параметры атмосферы (T_stat, P_stat).")

        # 2. Вычисляем термодинамические свойства воздуха при атмосферной температуре
        # Мы вызываем защищенный метод порта, чтобы получить матрицу 6x1
        tdf_matrix = self.port_in._get_thermo_matrix_safe(T=T_stat_H)
        
        cp_val = tdf_matrix[1, 0].magnitude
        R_val = tdf_matrix[4, 0].magnitude
        
        # Вычисляем показатель адиабаты набегающего потока
        k_val = cp_val / (cp_val - R_val)

        # 3. Газодинамика: находим газодинамические функции от числа Маха полета
        gdf_matrix, _ = self.gdf_calc.get_gdf_matrix(k_direct=k_val, M=self.M_flight)
        
        tau_val = gdf_matrix[3, 0].magnitude  # tau = T / T*
        pi_val  = gdf_matrix[4, 0].magnitude  # pi = P / P*

        # 4. ТОРМОЖЕНИЕ ПОТОКА (Расчет идеальных полных параметров)
        # Если бы потерь не было, поток затормозился бы до этих значений:
        T_star_ideal = T_stat_H / tau_val
        P_star_ideal = P_stat_H / pi_val

        # 5. УЧЕТ РЕАЛЬНЫХ ПОТЕРЬ (Применение пользовательской sigma)
        # Процесс во ВхУ считается адиабатным (без теплообмена с внешней средой), 
        # поэтому полная температура сохраняется. Падает только полное давление.
        T_star_out = T_star_ideal
        P_star_out = P_star_ideal * self.sigma

        # 6. ПЕРЕДАЧА ДАННЫХ ДАЛЬШЕ ПО ТРАКТУ
        # Обновляем выходной порт (вход в компрессор), устанавливая ему вычисленные параметры торможения.
        self.port_out.set_total_state(T_star=T_star_out, P_star=P_star_out)
        
        # Информационный вывод
        print(f"[УЗЕЛ: {self.name}] Расчет завершен ({self.inlet_type}, M={self.M_flight}).")
        print(f"   -> Набегающий поток : T_H = {T_stat_H.magnitude:.2f} K, P_H = {P_stat_H.magnitude:.2f} kPa")
        print(f"   -> Выход из ВхУ (T*): {T_star_out.magnitude:.2f} K")
        print(f"   -> Выход из ВхУ (P*): {P_star_out.to(ureg.kPa).magnitude:.2f} kPa")