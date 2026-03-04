from abc import ABC, abstractmethod
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort

class BaseEngineNode(ABC):
    """
    Абстрактный базовый класс для всех узлов газотурбинного двигателя.
    Обеспечивает наличие входа, выхода и метода calculate().
    """
    def __init__(self, name: str, port_in: ThermogasdynamicPort, port_out: ThermogasdynamicPort):
        self.name = name
        self.port_in = port_in
        self.port_out = port_out

    @abstractmethod
    def calculate(self):
        """
        Главный метод расчета узла.
        Должен брать данные из port_in, производить вычисления и заполнять port_out.
        """
        pass