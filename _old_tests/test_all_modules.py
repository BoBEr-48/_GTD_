import os
import sys

# 1. Импорт единого реестра размерностей
from main_folder.base_classes.base_thermodynamic import ureg

# 2. Импорт всех трех расчетных модулей
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_air.thermodynamic_properties_of_air import AirPropertiesMatrix
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_clear_combustion_products.thermodynamic_properties_of_clear_combustion_products import ClearCombustionPropertiesMatrix
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_combustion_products.thermodynamic_properties_of_combustion_products import CombustionMixturePropertiesMatrix

def print_matrix(title: str, matrix, labels):
    """Вспомогательная функция для красивого табличного вывода"""
    print(f"\n{title}")
    print("-" * 45)
    for i in range(len(labels)):
        print(f"| {labels[i]:<3} | {matrix[i, 0]:.4f}")
    print("-" * 45)

def main():
    print("=" * 65)
    print(" ЗАПУСК ТЕСТИРОВАНИЯ ТЕРМОДИНАМИЧЕСКИХ МОДУЛЕЙ ")
    print("=" * 65)

    # --- ШАГ 1: Построение путей к CSV файлам ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    tables_dir = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties")
    
    # Имена файлов взяты строго из вашего struct.json
    air_csv_path = os.path.join(tables_dir, "table_air.csv")
    prod_csv_path = os.path.join(tables_dir, "table_clear_combustion_products.csv")

    if not os.path.exists(air_csv_path) or not os.path.exists(prod_csv_path):
        print(f"[ОШИБКА] CSV файлы не найдены в папке {tables_dir}")
        sys.exit(1)

    # --- ШАГ 2: Тест модуля 1 (ВОЗДУХ) ---
    print("\n>>> ИНИЦИАЛИЗАЦИЯ: Модуль Воздуха...")
    air_module = AirPropertiesMatrix(air_csv_path)
    
    # 2.1 Прямая задача
    T_air_in = 288.15 * ureg.kelvin
    mat_air_1, labels_air = air_module.get_full_matrix(T=T_air_in)
    print_matrix("Воздух (Прямая задача: T = 288.15 K)", mat_air_1, labels_air)

    # 2.2 Обратная задача
    h_air_in = 500.0 * ureg.kilojoule / ureg.kilogram
    mat_air_2, _ = air_module.get_full_matrix(h=h_air_in)
    print(f"[Обратная задача Воздух] При h = {h_air_in} -> Найдена T = {mat_air_2[0, 0]:.2f}")


    # --- ШАГ 3: Тест модуля 2 (ЧИСТЫЕ ПРОДУКТЫ, alpha=1) ---
    print("\n\n>>> ИНИЦИАЛИЗАЦИЯ: Модуль Чистых продуктов сгорания...")
    prod_module = ClearCombustionPropertiesMatrix(prod_csv_path)

    # 3.1 Прямая задача
    T_prod_in = 1200.0 * ureg.kelvin
    mat_prod_1, labels_prod = prod_module.get_full_matrix(T=T_prod_in)
    print_matrix("Чистые ПС (Прямая задача: T = 1200 K)", mat_prod_1, labels_prod)

    # 3.2 Обратная задача
    s0_prod_in = 8.5 * ureg.kilojoule / (ureg.kilogram * ureg.kelvin)
    mat_prod_2, _ = prod_module.get_full_matrix(s0=s0_prod_in)
    print(f"[Обратная задача ЧПС] При s0 = {s0_prod_in} -> Найдена T = {mat_prod_2[0, 0]:.2f}")


    # --- ШАГ 4: Тест модуля 3 (СМЕСЬ, alpha > 1) ---
    print("\n\n>>> ИНИЦИАЛИЗАЦИЯ: Модуль Смеси (Реальные продукты сгорания)...")
    # Модуль сам внутри создаст объекты воздуха и ЧПС
    mix_module = CombustionMixturePropertiesMatrix(air_csv_path, prod_csv_path)
    
    alpha_test = 2.5
    print(f"Установлен коэффициент избытка воздуха: alpha = {alpha_test}")

    # 4.1 Прямая задача
    T_mix_in = 1600.0 * ureg.kelvin
    mat_mix_1, labels_mix = mix_module.get_full_matrix(alpha=alpha_test, T=T_mix_in)
    print_matrix(f"Смесь (Прямая задача: T = 1600 K, alpha = {alpha_test})", mat_mix_1, labels_mix)

    # 4.2 Обратная задача (например, расчет температуры за турбиной по изобарной теплоемкости)
    cp_mix_in = 1.15 * ureg.kilojoule / (ureg.kilogram * ureg.kelvin)
    mat_mix_2, _ = mix_module.get_full_matrix(alpha=alpha_test, cp=cp_mix_in)
    print(f"[Обратная задача Смесь] При cp = {cp_mix_in} -> Найдена T = {mat_mix_2[0, 0]:.2f}")

    print("\n" + "=" * 65)
    print(" ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ! ")
    print("=" * 65)

if __name__ == "__main__":
    main()