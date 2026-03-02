import os
import sys

# Импортируем единый реестр размерностей
from main_folder.base_classes.base_thermodynamic import ureg

# Импортируем расчетные модули
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_air.thermodynamic_properties_of_air import AirPropertiesMatrix
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_clear_combustion_products.thermodynamic_properties_of_clear_combustion_products import ClearCombustionPropertiesMatrix
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_combustion_products.thermodynamic_properties_of_combustion_products import CombustionMixturePropertiesMatrix

def print_matrix(title: str, matrix, labels):
    """Красивый табличный вывод матрицы"""
    print(f"\n{title}")
    print("-" * 45)
    for i in range(len(labels)):
        print(f"| {labels[i]:<4} | {matrix[i, 0]:.4f}")
    print("-" * 45)

def ask_parameter():
    """Интерактивное меню выбора входного параметра"""
    while True:
        print("\nВыберите входной параметр для расчета:")
        print("  1 -> Температура (T) [К]")
        print("  2 -> Изобарная теплоемкость (cp) [кДж/(кг·К)]")
        print("  3 -> Энтальпия (h) [кДж/кг]")
        print("  4 -> Энтропия (s0) [кДж/(кг·К)]")
        
        choice = input("Ваш выбор (1-4): ").strip()
        
        if choice not in['1', '2', '3', '4']:
            print("[ОШИБКА] Пожалуйста, введите цифру от 1 до 4.")
            continue
            
        try:
            val_str = input("Введите числовое значение параметра (например, 1200.5): ").strip()
            # Заменяем запятую на точку, если пользователь ошибся при вводе
            val_str = val_str.replace(',', '.')
            val = float(val_str)
        except ValueError:
            print("[ОШИБКА] Введено некорректное число. Попробуйте снова.")
            continue

        # Оборачиваем введенное число в правильную единицу измерения
        if choice == '1':
            return {'T': val * ureg.kelvin}, f"T = {val} K"
        elif choice == '2':
            return {'cp': val * (ureg.kilojoule / (ureg.kilogram * ureg.kelvin))}, f"cp = {val} кДж/(кг·К)"
        elif choice == '3':
            return {'h': val * (ureg.kilojoule / ureg.kilogram)}, f"h = {val} кДж/кг"
        elif choice == '4':
            return {'s0': val * (ureg.kilojoule / (ureg.kilogram * ureg.kelvin))}, f"s0 = {val} кДж/(кг·К)"

def main():
    print("=" * 60)
    print(" ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ ТЕРМОДИНАМИЧЕСКИХ МОДУЛЕЙ ")
    print("=" * 60)

    # --- Подготовка путей ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tables_dir = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties")
    
    air_csv = os.path.join(tables_dir, "table_air.csv")
    prod_csv = os.path.join(tables_dir, "table_clear_combustion_products.csv")

    if not os.path.exists(air_csv) or not os.path.exists(prod_csv):
        print(f"\n[ФАТАЛЬНАЯ ОШИБКА] CSV файлы не найдены в:\n{tables_dir}")
        sys.exit(1)

    # =======================================================
    # ТЕСТ 1: ВОЗДУХ
    # =======================================================
    print("\n\n" + "#"*50)
    print(">>> ИССЛЕДОВАНИЕ 1: ВОЗДУХ (AirPropertiesMatrix)")
    print("#"*50)
    air_module = AirPropertiesMatrix(air_csv)
    
    kwargs, param_desc = ask_parameter()
    try:
        # Распаковываем словарь kwargs: если выбрали 1, передастся T=1200*ureg.kelvin
        matrix, labels = air_module.get_full_matrix(**kwargs)
        print_matrix(f"Результат для ВОЗДУХА при {param_desc}", matrix, labels)
    except ValueError as e:
        print(f"\n[ОШИБКА РАСЧЕТА] {e}")


    # =======================================================
    # ТЕСТ 2: ЧИСТЫЕ ПРОДУКТЫ СГОРАНИЯ (alpha = 1)
    # =======================================================
    print("\n\n" + "#"*50)
    print(">>> ИССЛЕДОВАНИЕ 2: ЧИСТЫЕ ПРОДУКТЫ СГОРАНИЯ (alpha=1)")
    print("#"*50)
    prod_module = ClearCombustionPropertiesMatrix(prod_csv)
    
    kwargs, param_desc = ask_parameter()
    try:
        matrix, labels = prod_module.get_full_matrix(**kwargs)
        print_matrix(f"Результат для ЧИСТЫХ ПС при {param_desc}", matrix, labels)
    except ValueError as e:
        print(f"\n[ОШИБКА РАСЧЕТА] {e}")


    # =======================================================
    # ТЕСТ 3: СМЕСЬ ПРОДУКТОВ СГОРАНИЯ (alpha > 1)
    # =======================================================
    print("\n\n" + "#"*50)
    print(">>> ИССЛЕДОВАНИЕ 3: СМЕСЬ ГАЗОВ (Реальные продукты сгорания)")
    print("#"*50)
    mix_module = CombustionMixturePropertiesMatrix(air_csv, prod_csv)
    
    # Спрашиваем коэффициент избытка воздуха
    while True:
        try:
            alpha_str = input("\nВведите коэффициент избытка воздуха (alpha >= 1.0), например 2.5: ").strip()
            alpha_str = alpha_str.replace(',', '.')
            alpha_val = float(alpha_str)
            if alpha_val < 1.0:
                print("Значение alpha должно быть больше или равно 1.0!")
                continue
            break
        except ValueError:
            print("[ОШИБКА] Введите корректное число.")

    # Спрашиваем термодинамический параметр
    kwargs, param_desc = ask_parameter()
    try:
        # Передаем alpha и распаковываем словарь kwargs
        matrix, labels = mix_module.get_full_matrix(alpha=alpha_val, **kwargs)
        print_matrix(f"Результат для СМЕСИ при alpha={alpha_val} и {param_desc}", matrix, labels)
    except ValueError as e:
        print(f"\n[ОШИБКА РАСЧЕТА] {e}")

    print("\n" + "=" * 60)
    print(" ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО ")
    print("=" * 60)

if __name__ == "__main__":
    main()