import os
from main_folder.base_classes.base_thermodynamic import ureg

# Импортируем порт и модуль газовой смеси
from main_folder.structural_layer.ports.thermogasdynamic_port import ThermogasdynamicPort
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_combustion_products.thermodynamic_properties_of_combustion_products import CombustionMixturePropertiesMatrix

def main():
    print("=== ТЕСТ ТЕРМОГАЗОДИНАМИЧЕСКОГО ПОРТА ===")

    # 1. Подготовка базы данных
    base_dir = os.path.dirname(os.path.abspath(__file__))
    air_csv = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties", "table_air.csv")
    prod_csv = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties", "table_clear_combustion_products.csv")

    gas_mixture = CombustionMixturePropertiesMatrix(air_csv, prod_csv)

    # 2. Создаем порт (Сечение перед турбиной)
    # Расход 50 кг/с, избыток воздуха 2.5
    turbine_inlet = ThermogasdynamicPort(
        name="Turbine_Inlet_Section",
        fluid_module=gas_mixture,
        G=50.0 * (ureg.kilogram / ureg.second),
        alpha=2.5
    )

    # 3. ЭТАП ЗАВЯЗКИ (0D): Задаем параметры торможения
    # Температура 1500 К, Давление 10 Атмосфер (1 Мегапаскаль)
    turbine_inlet.set_total_state(
        T_star=1500 * ureg.kelvin,
        P_star=1.0 * ureg.megapascal
    )
    
    print("\n--- После расчета параметров торможения ---")
    print(turbine_inlet)
    print(f"Энтальпия торможения h*: {turbine_inlet.h_star:.2f}")

    # 4. ЭТАП 1D РАСЧЕТА: Профилирование сечения
    # Допустим, мы хотим, чтобы в этом сечении число Маха было M = 0.4
    turbine_inlet.add_kinematics_by_mach(M=0.4)

    print("\n--- После расчета кинематики и статики ---")
    print(turbine_inlet)
    
    print("\n[Анализ результатов]")
    print(f"Плотность газа: {turbine_inlet.rho:.2f}")
    print(f"Скорость потока: {turbine_inlet.c:.2f}")
    print(f"Требуемая площадь проходного сечения: {turbine_inlet.F.to(ureg.cm**2):.1f}")

if __name__ == "__main__":
    main()