import os
from main_folder.base_classes.base_thermodynamic import ureg

# Импорт БД, Портов и Узлов
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_air.thermodynamic_properties_of_air import AirPropertiesMatrix
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort
from main_folder.structural_layer.nodes.boundary.inlet_device import InletDeviceNode
from main_folder.structural_layer.nodes.routing.duct import DuctNode
from main_folder.structural_layer.nodes.boundary.outlet_device import OutletDeviceNode

def main():
    print("=== ТЕСТ: ЦЕПОЧКА ВхУ -> КАНАЛ -> СОПЛО ===")

    # 1. База данных
    base_dir = os.path.dirname(os.path.abspath(__file__))
    air_csv = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties", "table_air.csv")
    air_model = AirPropertiesMatrix(air_csv)

    # 2. Создаем Порты (Узлы связи)
    port_atm    = ThermogasdynamicPort("0_Атмосфера", air_model, G=50.0 * (ureg.kg / ureg.s))
    port_inlet  = ThermogasdynamicPort("1_За_ВхУ", air_model, G=0 * (ureg.kg / ureg.s)) # G обновится автоматически
    port_duct   = ThermogasdynamicPort("2_За_Каналом", air_model, G=0 * (ureg.kg / ureg.s))
    port_nozzle = ThermogasdynamicPort("3_Срез_Сопла", air_model, G=0 * (ureg.kg / ureg.s))

    # Задаем условия полета (Высота ~0 м, скорость М = 0.8)
    P_ambient = 101.325 * ureg.kPa
    port_atm.T_stat = 288.15 * ureg.K
    port_atm.P_stat = P_ambient

    # 3. Собираем Узлы двигателя
    inlet = InletDeviceNode(
        name="Воздухозаборник",
        port_in=port_atm, port_out=port_inlet,
        M_flight=0.8, sigma=0.98
    )

    # Длинный извилистый трубопровод (например, внешний контур ТРДД)
    duct = DuctNode(
        name="Канал наружного контура",
        port_in=port_inlet, port_out=port_duct,
        sigma=0.95  # Потеряли 5% давления на трение
    )

    nozzle = OutletDeviceNode(
        name="Сужающееся сопло",
        port_in=port_duct, port_out=port_nozzle,
        P_ambient=P_ambient, sigma=0.99,
        device_type="convergent"
    )

    # 4. ЗАПУСКАЕМ РАСЧЕТ ПО ЦЕПОЧКЕ
    print("\n--- СТАРТ РАСЧЕТА ---")
    inlet.calculate()
    duct.calculate()
    nozzle.calculate()

    # 5. Вывод результатов
    print("\n--- ИТОГОВОЕ СОСТОЯНИЕ ГАЗА НА СРЕЗЕ СОПЛА ---")
    print(port_nozzle)
    
    print(f"\nРеактивная тяга холодной струи: {nozzle.thrust.to(ureg.kN):.2f}")

if __name__ == "__main__":
    main()