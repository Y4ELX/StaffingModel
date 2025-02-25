import json
from Tactic import Tactic


def calculate_fsm(incoming:int, backlog:int, tactics:list[Tactic], max_recovery_time:int = 100):

    selected_tactics = [tactic.name for tactic in tactics]

    # Variables para acumular el costo total
    total_cost = 0
    data = {
        "summary": {},
        "detail": {},
    }
    overdemand = 0
    for tactic in tactics:
        tactic_data = {}
        for tactic.recovery_time in range(1, tactic.recovery_time_final + 1):
            result = tactic.calculate_tactics_data(overdemand)
            tactic_data[tactic.recovery_time] = result
            total_cost += result["total_cost"]

        data["detail"][tactic.name] = tactic_data

    # Añadir el resumen con la nueva estructura
    for i in range(1, tactics[0].recovery_time_final + 1):
        # Calcular el total de transacciones para FTE
        total_transactions_FTE = (tactics[0].daily_income_work * i) + tactics[
            0
        ].backlog

        # Calcular total transactions y total cost para todas las tácticas seleccionadas
        total_transactions_day = total_transactions_FTE  # FTE es el único que determina total transactions
        total_cost_day = sum(
            tactic_data.get(i, {}).get("total_cost", 0)
            for tactic_data in data["detail"].values()
        )
        total_unit_cost_day = (
            total_cost_day / total_transactions_day
            if total_transactions_day > 0
            else 0
        )

        # Añadir al resumen con la estructura solicitada
        data["summary"][str(i)] = {
            "tota_transactions_summ": total_transactions_day,
            "total_cost_summ": total_cost_day,
            "total_unit_cost summ": total_unit_cost_day,
        }
        return data

def main():
    incoming = 3200
    backlog = 8000
    from input import configurations
    tactics = [Tactic(name, **config) for name, config in configurations.items()]
    data = calculate_fsm(incoming, backlog, tactics)
    with open("tactics_results.json", "w") as f:
        json.dump(data, f, indent=4)

    print("JSON generado exitosamente.")

if __name__ == "__main__":
    main()
