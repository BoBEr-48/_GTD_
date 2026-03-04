from main_folder.base_classes.base_thermodynamic import ureg
from main_folder.structural_layer.ports.mechanical_port import MechanicalPort

def main():
    print("=== ТЕСТ МЕХАНИЧЕСКОГО ПОРТА ===")

    # 1. Создаем пустой вал (например, вал между турбиной низкого давления и вентилятором)
    fan_shaft = MechanicalPort(name="LPT_to_Fan_Shaft")
    print(f"Изначально: {fan_shaft}")

    # 2. Допустим, Турбина посчитала свою работу и передала мощность на вал (15 Мегаватт)
    fan_shaft.power = 15 * ureg.megawatt
    
    # Задаем обороты ротора низкого давления (3000 об/мин)
    fan_shaft.rpm = 3000 * ureg.rpm

    print(f"\nПосле расчета турбины: {fan_shaft}")

    # 3. Компрессор/Вентилятор запрашивает мощность с вала для своих расчетов
    power_for_compressor = fan_shaft.power.to(ureg.kW)
    print(f"\nМощность, доступная вентилятору: {power_for_compressor:.2f}")
    
    # 4. Порт сам посчитал крутящий момент (полезно для расчетов на прочность вала)
    print(f"Крутящий момент на валу: {fan_shaft.torque:.2f}")

    # 5. Проверка безопасности размерностей (защита от дурака)
    print("\nПроверка защиты типов:")
    try:
        fan_shaft.power = 500 * ureg.kelvin # Пытаемся передать температуру вместо Ватт
    except Exception as e:
        print(f"ОШИБКА ПОЙМАНА УСПЕШНО:\n{e}")

if __name__ == "__main__":
    main()