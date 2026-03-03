import os
from main_folder.base_classes.base_thermodynamic import ureg

# Импорт ТДФ
from main_folder.thermodynamic_functions.module_thermodynamic_properties_of_combustion_products.thermodynamic_properties_of_combustion_products import CombustionMixturePropertiesMatrix
# Импорт ГДФ
from main_folder.gasdynamic_functions.module_gasdynamic_functions.gasdynamic_functions import GasDynamicCalculator

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    air_csv = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties", "table_air.csv")
    prod_csv = os.path.join(base_dir, "main_folder", "thermodynamic_functions", "tables_of_thermophysical_properties", "table_clear_combustion_products.csv")

    # 1. Сначала считаем ТЕРМОДИНАМИКУ (параметры торможения перед турбиной)
    print("--- 1. ТЕРМОДИНАМИКА ---")
    tdf_module = CombustionMixturePropertiesMatrix(air_csv, prod_csv)
    
    T_star = 1500 * ureg.kelvin # Температура заторможенного потока
    alpha = 2.5
    
    tdf_matrix, tdf_labels = tdf_module.get_full_matrix(alpha=alpha, T=T_star)
    print(f"k будет рассчитан из: cp = {tdf_matrix[1,0]:.4f}, R = {tdf_matrix[4,0]:.4f}")

    # 2. Теперь считаем ГАЗОДИНАМИКУ
    print("\n--- 2. ГАЗОДИНАМИКА ---")
    gdf_module = GasDynamicCalculator()

    # Сценарий А: Расчет сопла турбины (дозвук). Известно, что лямбда = 0.85
    gdf_mat_1, gdf_labels = gdf_module.get_gdf_matrix(tdf_matrix=tdf_matrix, lambda_val=0.85)
    
    print("\n[Сценарий А] Известна скорость (lambda = 0.85):")
    for i in range(len(gdf_labels)):
        print(f"| {gdf_labels[i]:<6} | {gdf_mat_1[i, 0]:.4f}")

    # Сценарий Б: Решение уравнения неразрывности
    # Известен расход q = 0.5. Найти число Маха (сверхзвуковое течение)
    q_target = 0.5
    gdf_mat_2, _ = gdf_module.get_gdf_matrix(tdf_matrix=tdf_matrix, q=q_target, regime='supersonic')
    
    print(f"\n[Сценарий Б] Известен расход q = {q_target} (Сверхзвук):")
    print(f"| lambda | {gdf_mat_2[1, 0]:.4f}")
    print(f"| Мах M  | {gdf_mat_2[2, 0]:.4f}")

if __name__ == "__main__":
    main()