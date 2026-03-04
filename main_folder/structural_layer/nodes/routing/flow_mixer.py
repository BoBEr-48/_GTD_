import numpy as np
import pint
from main_folder.structural_layer.nodes.base_node import BaseEngineNode
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort
from main_folder.base_classes.base_thermodynamic import ureg

class FlowMixerNode(BaseEngineNode):
    """
    Узел Камеры смешения.
    Объединяет два потока (например, из внутреннего и наружного контуров) в один.
    Рассчитывает усредненную энтальпию, давление и итоговый состав газа (alpha).
    """
    def __init__(self, 
                 name: str, 
                 port_in_hot: ThermogasdynamicPort,   # Вход 1 (Горячий контур / Внутренний)
                 port_in_cold: ThermogasdynamicPort,  # Вход 2 (Холодный контур / Наружный)
                 port_out: ThermogasdynamicPort,      # Выход (Смешанный поток)
                 sigma_mix: float):                   # Коэф. сохранения полного давления при смешении
        # В базовый класс передаем основной (горячий) порт как port_in
        super().__init__(name, port_in_hot, port_out)
        self.port_in_cold = port_in_cold
        
        if sigma_mix <= 0.0 or sigma_mix > 1.0:
            raise ValueError(f"[{self.name}] Коэффициент sigma_mix должен быть в пределах (0; 1].")
        self.sigma_mix = sigma_mix

    def _get_fuel_mass_flow(self, G: pint.Quantity, alpha: float, L0: float) -> pint.Quantity:
        """Вспомогательный метод: вычисляет массовый расход чистого топлива в потоке"""
        # Если alpha очень большой (например 1000) - это чистый воздух, топлива нет
        if alpha > 500:
            return 0.0 * (ureg.kilogram / ureg.second)
        return G / (1.0 + alpha * L0)

    def calculate(self):
        """Расчет термодинамики смешения двух потоков."""
        
        # Проверки наличия данных
        if self.port_in.h_star is None or self.port_in_cold.h_star is None:
            raise ValueError(f"[{self.name}] Входные порты должны иметь рассчитанную полную энтальпию (h*)!")

        # 1. БАЛАНС МАССЫ
        G1 = self.port_in.G
        G2 = self.port_in_cold.G
        G_mix = G1 + G2
        
        # Записываем расход в выходной порт
        self.port_out.G = G_mix

        # 2. БАЛАНС ЭНЕРГИИ (Энтальпийное смешение)
        h1_star = self.port_in.h_star
        h2_star = self.port_in_cold.h_star
        
        # Средневзвешенная энтальпия
        h_mix_star = (G1 * h1_star + G2 * h2_star) / G_mix

        # 3. БАЛАНС СОСТАВА ГАЗА (Расчет итогового alpha)
        # Получаем L0 из модуля (или задаем стандартный 17.12 для метана)
        L0 = getattr(self.port_out.fluid, 'L0', 17.12)
        
        Gf_1 = self._get_fuel_mass_flow(G1, self.port_in.alpha, L0)
        Gf_2 = self._get_fuel_mass_flow(G2, self.port_in_cold.alpha, L0)
        Gf_mix = Gf_1 + Gf_2
        
        if Gf_mix.magnitude == 0:
            alpha_mix = 1000.0  # Смешались два потока чистого воздуха
        else:
            # alpha = G_air / (G_fuel * L0) = (G_total - G_fuel) / (G_fuel * L0)
            alpha_mix = ((G_mix - Gf_mix) / (Gf_mix * L0)).magnitude
            
        self.port_out.alpha = alpha_mix

        # 4. ПОЛНОЕ ДАВЛЕНИЕ (Упрощенная 0D модель)
        P1_star = self.port_in.P_star
        P2_star = self.port_in_cold.P_star
        
        # Усредняем давление по массе и применяем потери на вихреобразование (sigma)
        P_mix_avg = (G1 * P1_star + G2 * P2_star) / G_mix
        P_mix_star = P_mix_avg * self.sigma_mix

        # 5. ОПРЕДЕЛЕНИЕ ТЕМПЕРАТУРЫ (Решение обратной задачи)
        # Зная энтальпию h_mix_star и новый состав alpha_mix, находим T_mix_star
        matrix_mix, _ = self.port_out.fluid.get_full_matrix(alpha=alpha_mix, h=h_mix_star)
        T_mix_star = matrix_mix[0, 0]

        # 6. ОБНОВЛЕНИЕ ПОРТА
        self.port_out.set_total_state(T_star=T_mix_star, P_star=P_mix_star)
        
        print(f"[УЗЕЛ: {self.name}] Смешение завершено.")
        print(f"   -> Соотношение расходов G2/G1 (Степень двухконтурности): {(G2/G1).magnitude:.2f}")
        print(f"   -> Итоговая температура: T* = {T_mix_star.magnitude:.2f} K")
        print(f"   -> Итоговый состав     : alpha = {alpha_mix:.3f}")