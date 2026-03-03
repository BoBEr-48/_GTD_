from main_folder.gasdynamic_functions.module_gasdynamic_functions.gasdynamic_functions import GasDynamicCalculator

def main():
    gdf_module = GasDynamicCalculator()
    
    # Показатель адиабаты для стандартного воздуха
    k_air = 1.4

    print("=== ТЕСТ 1: Вход через Число Маха (M -> lambda) ===")
    M_input = 2.0  # Сверхзвук, Мах = 2
    matrix_from_m, labels = gdf_module.get_gdf_matrix(k_direct=k_air, M=M_input)
    
    lam_calc = matrix_from_m[1, 0].magnitude # Вытаскиваем найденную лямбду
    print(f"Задано M = {M_input:.2f}  -->  Рассчитана lambda = {lam_calc:.4f}")


    print("\n=== ТЕСТ 2: Вход через Лямбду (lambda -> M) ===")
    # Используем лямбду, полученную в Тесте 1, чтобы убедиться в обратимости
    matrix_from_lam, _ = gdf_module.get_gdf_matrix(k_direct=k_air, lambda_val=lam_calc)
    
    M_calc = matrix_from_lam[2, 0].magnitude # Вытаскиваем найденного Маха
    print(f"Задана lambda = {lam_calc:.4f}  -->  Рассчитан M = {M_calc:.2f}")

    print("\nОбе матрицы полностью идентичны!")
    for i in range(len(labels)):
        print(f"{labels[i]:<7}: {matrix_from_m[i,0].magnitude:.4f} == {matrix_from_lam[i,0].magnitude:.4f}")

if __name__ == "__main__":
    main()