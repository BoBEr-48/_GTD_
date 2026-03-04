import numpy as np
import pint
from typing import Optional

# Импорт базовых классов и инструментов
from main_folder.structural_layer.nodes.base_node import BaseEngineNode
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort
from main_folder.gasdynamic_functions.module_gasdynamic_functions.gasdynamic_functions import GasDynamicCalculator
from main_folder.base_classes.base_thermodynamic import ureg

class OutletDeviceNode(BaseEngineNode):
    """
    Узел Выходного Устройства (Сопло / Диффузор).
    Выполняет расширение газа до атмосферного давления (или до критического).
    Рассчитывает скорость истечения и реактивную тягу.
    
    Типы (device_type):
    - 'convergent' : Сужающееся сопло (возможен режим неполного расширения, M <= 1)
    - 'laval'      : Сверхзвуковое сопло Лаваля (полное расширение, M >= 1)
    - 'diffuser'   : Выхлопной диффузор (для ТВаД/ТВД, сброс скорости)
    """

    def __init__(self, 
                 name: str, 
                 port_in: ThermogasdynamicPort, 
                 port_out: ThermogasdynamicPort,
                 P_ambient: pint.Quantity,
                 sigma: float,
                 device_type: str = "convergent"):
        super().__init__(name, port_in, port_out)
        
        self.P_ambient = P_ambient # Давление окружающей среды
        self.device_type = device_type
        self.gdf_calc = GasDynamicCalculator()

        if sigma <= 0.0 or sigma > 1.0:
            raise ValueError(f"[{self.name}] Коэффициент sigma должен быть в пределах (0; 1].")
        self.sigma = sigma
        
        # Вычисляемые параметры узла
        self.thrust: Optional[pint.Quantity] = None # Тяга

    def calculate(self):
        """Расчет расширения газа в выходном устройстве."""
        
        if self.port_in.T_star is None or self.port_in.P_star is None:
            raise ValueError(f"[{self.name}] Входной порт не имеет параметров торможения!")

        # 1. ПОЛНЫЕ ПАРАМЕТРЫ ЗА СОПЛОМ
        # Процесс адиабатный, полная температура сохраняется. Давление падает на величину sigma
        T_out_star = self.port_in.T_star
        P_out_star = self.port_in.P_star * self.sigma

        # Обновляем выходной порт (записываем полные параметры)
        self.port_out.set_total_state(T_star=T_out_star, P_star=P_out_star)

        # 2. ПОКАЗАТЕЛЬ АДИАБАТЫ (берем из уже обновленного выходного порта)
        k = self.port_out.k
        if k is None:
            raise RuntimeError("Ошибка вычисления показателя адиабаты k.")

        # 3. КРИТИЧЕСКИЙ ПЕРЕПАД ДАВЛЕНИЙ
        # Формула: pi_cr = ((k+1)/2) ^ (k/(k-1))
        pi_cr = ((k + 1) / 2) ** (k / (k - 1))
        
        # Располагаемый перепад давлений
        pi_available = (P_out_star / self.P_ambient).magnitude

        # 4. ЛОГИКА РАСШИРЕНИЯ (в зависимости от типа сопла)
        M_out = 0.0
        P_out_static = self.P_ambient # По умолчанию считаем, что расширились до атмосферы

        if self.device_type == 'convergent':
            # Сужающееся сопло не может расширить газ быстрее скорости звука (Мах <= 1)
            if pi_available >= pi_cr:
                # Режим ЗАПИРАНИЯ (Неполное расширение)
                M_out = 1.0
                P_out_static = P_out_star / pi_cr # Статическое давление на срезе БОЛЬШЕ атмосферного
            else:
                # Докритический режим (Полное расширение)
                pi_gdf = (self.P_ambient / P_out_star).magnitude
                gdf_mat, _ = self.gdf_calc.get_gdf_matrix(k_direct=k, pi=pi_gdf, regime='subsonic')
                M_out = gdf_mat[2, 0].magnitude
                P_out_static = self.P_ambient

        elif self.device_type == 'laval':
            # Сопло Лаваля проектируется для ПОЛНОГО расширения до атмосферы
            pi_gdf = (self.P_ambient / P_out_star).magnitude
            # Если перепад больше критического - режим сверхзвуковой
            regime = 'supersonic' if pi_available > pi_cr else 'subsonic'
            gdf_mat, _ = self.gdf_calc.get_gdf_matrix(k_direct=k, pi=pi_gdf, regime=regime)
            M_out = gdf_mat[2, 0].magnitude
            P_out_static = self.P_ambient

        elif self.device_type == 'diffuser':
            # Диффузор тормозит поток, давление равно атмосферному
            pi_gdf = (self.P_ambient / P_out_star).magnitude
            gdf_mat, _ = self.gdf_calc.get_gdf_matrix(k_direct=k, pi=pi_gdf, regime='subsonic')
            M_out = gdf_mat[2, 0].magnitude
            P_out_static = self.P_ambient
            
        else:
            raise ValueError(f"[{self.name}] Неизвестный тип выходного устройства: {self.device_type}")

        # 5. ПЕРЕДАЧА КИНЕМАТИКИ В ПОРТ
        # Так как порт сам умеет считать статику по Маху, просто передаем ему Мах!
        self.port_out.add_kinematics_by_mach(M=M_out)
        
        # Корректируем P_stat принудительно (из-за возможных погрешностей округления)
        self.port_out.P_stat = P_out_static

        # 6. РАСЧЕТ ТЯГИ (R = G * c + F * (P_stat - P_H))
        momentum_thrust = self.port_out.G * self.port_out.c
        pressure_thrust = self.port_out.F * (self.port_out.P_stat - self.P_ambient)
        
        self.thrust = (momentum_thrust + pressure_thrust).to(ureg.newton)

        # Вывод результатов
        print(f"[УЗЕЛ: {self.name}] Расчет завершен (Тип: {self.device_type}).")
        print(f"   -> Перепад давлений: располагаемый = {pi_available:.2f} | критический = {pi_cr:.2f}")
        print(f"   -> Срез сопла      : M = {M_out:.3f}, Скорость c = {self.port_out.c:.1f}")
        print(f"   -> Стат. давление  : P = {self.port_out.P_stat.to(ureg.kPa):.1f} (Атмосфера: {self.P_ambient.to(ureg.kPa):.1f})")
        print(f"   -> РЕАКТИВНАЯ ТЯГА : {self.thrust.to(ureg.kN):.2f}")