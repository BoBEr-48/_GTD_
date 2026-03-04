from main_folder.structural_layer.nodes.base_node import BaseEngineNode
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort
from main_folder.base_classes.base_thermodynamic import ureg

class DuctNode(BaseEngineNode):
    """
    Узел переходного канала (трубопровод, газовод, канал наружного контура).
    Моделирует течение газа без теплообмена с внешней средой (адиабатное) и без совершения механической работы.
    Учитывает гидравлические потери полного давления на трение и местные сопротивления.
    """
    def __init__(self, 
                 name: str, 
                 port_in: ThermogasdynamicPort, 
                 port_out: ThermogasdynamicPort,
                 sigma: float):
        super().__init__(name, port_in, port_out)
        
        # Пользовательский параметр - коэффициент сохранения полного давления
        if sigma <= 0.0 or sigma > 1.0:
            raise ValueError(f"[{self.name}] Коэффициент восстановления давления (sigma) должен быть в пределах (0; 1]. Задано: {sigma}")
        self.sigma = sigma

    def calculate(self):
        """Расчет изменения параметров потока в канале."""
        
        if self.port_in.T_star is None or self.port_in.P_star is None:
            raise ValueError(f"[{self.name}] Входной порт {self.port_in.name} не имеет параметров торможения (T*, P*)!")

        # 1. ТЕРМОДИНАМИКА КАНАЛА
        # Так как канал не подводит тепло и не совершает работу, энтальпия торможения (а значит и T*) сохраняется.
        T_out_star = self.port_in.T_star
        
        # Полное давление падает из-за трения
        P_out_star = self.port_in.P_star * self.sigma

        # 2. СИНХРОНИЗАЦИЯ ПАРАМЕТРОВ ПОТОКА
        # Убеждаемся, что выходной порт унаследовал массовый расход и состав газа из входного
        self.port_out.G = self.port_in.G
        self.port_out.alpha = self.port_in.alpha
        self.port_out.fluid = self.port_in.fluid

        # 3. ОБНОВЛЕНИЕ ПОРТА
        self.port_out.set_total_state(T_star=T_out_star, P_star=P_out_star)
        
        # Информационный вывод
        pressure_loss_pct = (1.0 - self.sigma) * 100
        print(f"[УЗЕЛ: {self.name}] Расчет завершен.")
        print(f"   -> Температура сохранена : T* = {T_out_star.magnitude:.2f} K")
        print(f"   -> Потеря полного давления: {pressure_loss_pct:.2f}% (P* на выходе: {P_out_star.to(ureg.kPa).magnitude:.1f} kPa)")