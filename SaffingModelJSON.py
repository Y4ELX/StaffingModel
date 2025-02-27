import json
from decimal import Decimal, localcontext, ROUND_HALF_UP


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not serializable")


def create_tactic(name, config):
    return {
        "name": name,
        **config,
        "throughput_acum": 0,
        "reduction_backlog_acum": 0,
        "final_quality_acum": 0,
        "final_throughput_acum": 0,
    }


def calculate_tactics_data(tactic, fte_overdemand, fte_backlog):
    if tactic["name"] != "FTE":
        tactic["daily_income_work"] = fte_overdemand
        tactic["backlog"] = fte_backlog
    
    startup_time_days = tactic["time_to_hire"] + tactic["set_up_time"] + tactic["training_time"]
    daily_productivity_increase = (tactic["throughput_final"] - tactic["throughput_initial"]) / tactic["time_to_100_productivity"]
    
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        final_daily_throughput = Decimal(min(tactic["throughput_initial"] + (daily_productivity_increase * tactic["recovery_time"]), tactic["throughput_final"]))
        final_daily_throughput = final_daily_throughput.to_integral_value()
    
    tactic["final_throughput_acum"] += final_daily_throughput
    average_daily_throughput = round(tactic["final_throughput_acum"] / tactic["recovery_time"]) if tactic["recovery_time"] > 0 else 0
    
    daily_quality_increase = (tactic["final_quality"] - tactic["initial_quality"]) / tactic["time_to_100_quality"]
    final_daily_quality = min(round(tactic["initial_quality"] + (daily_quality_increase * tactic["recovery_time"])), tactic["final_quality"])
    tactic["final_quality_acum"] += final_daily_quality
    average_daily_quality = tactic["final_quality_acum"] / tactic["recovery_time"] if tactic["recovery_time"] > 0 else 0
    
    amount_of_needed_employees = min(tactic["max_no_employees"], round(((tactic["daily_income_work"] * tactic["recovery_time"]) + tactic["backlog"]) / (average_daily_throughput * (1 - tactic["absentism_rate"] / 100) * tactic["recovery_time"])))
    
    training_cost_per_individual = (tactic["training_time"] * tactic["no_of_trainers"] * tactic["daily_cost_per_trainer"]) / max(1, min(amount_of_needed_employees, tactic["no_of_trainees_per_session"]))
    total_onboarding_cost_per_employee = tactic["cost_to_hire"] + tactic["cost_to_set_up"] + (tactic["training_time"] * tactic["employee_cost"]) + training_cost_per_individual
    
    throughput = 0 if startup_time_days >= tactic["recovery_time"] else round(average_daily_throughput * amount_of_needed_employees * (1 - tactic["absentism_rate"] / 100))
    tactic["throughput_acum"] += throughput
    
    oversight_cost = tactic["daily_cost_per_trainer"] * (1 - average_daily_quality) / 2 if average_daily_quality < 0.9 else 0
    total_daily_cost_per_employee = tactic["employee_cost"] + tactic["daily_supervision_cost"] + tactic["contract_cost"] + oversight_cost if throughput > 0 else 0
    
    if tactic["daily_income_work"] > throughput:
        overdemand = tactic["daily_income_work"] - throughput
    else:
        overdemand = 0
    reduction_on_backlog = max(0, throughput - tactic["daily_income_work"])
    backlog = max(0, tactic["backlog"] - reduction_on_backlog) if overdemand == 0 else tactic["backlog"]
    
    processed_transactions = tactic["throughput_acum"] if tactic["daily_income_work"] > 0 or tactic["backlog"] > 0 else 0
    total_cost = (tactic["recovery_time"] * total_daily_cost_per_employee * amount_of_needed_employees) + (total_onboarding_cost_per_employee * amount_of_needed_employees)
    
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        unit_cost = Decimal(total_cost / processed_transactions).quantize(Decimal('0.01')) if processed_transactions > 0 else 0
      
    return {
        "daily_income_work": tactic["daily_income_work"],
        "over_demand": overdemand,
        "backlog": backlog,
        "processed_transactions": processed_transactions,
        "total_cost": total_cost,
        "unit_cost": unit_cost,
    }


# Configuración de tácticas
configurations = {
    "FTE": {
        "daily_income_work": 3200, "backlog": 8000, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 0, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0,
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0,
        "no_of_trainees_per_session": 10, "throughput_initial": 69, "throughput_final": 69,
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100,
        "time_to_100_quality": 10, "max_no_employees": 39, "absentism_rate": 15,
        "employee_cost": 166, "daily_supervision_cost": 16, "contract_cost": 0},
    "OT": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 0, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 34, "throughput_final": 34, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 20, "absentism_rate": 0, 
        "employee_cost": 125, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "CT1": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 0, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 80, "throughput_final": 80, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 5, "absentism_rate": 5, 
        "employee_cost": 130, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "CT2": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 0, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 75, "throughput_final": 75, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 5, "absentism_rate": 5, 
        "employee_cost": 130, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "CT3": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 5, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 69, "throughput_final": 69, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 5, "absentism_rate": 5, 
        "employee_cost": 130, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "CT4": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 5, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 69, "throughput_final": 69, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 5, "absentism_rate": 5, 
        "employee_cost": 130, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "Temps": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 5, "cost_to_hire": 0, "set_up_time": 10, "cost_to_set_up": 0, 
        "training_time": 5, "no_of_trainers": 2, "daily_cost_per_trainer": 166, 
        "no_of_trainees_per_session": 5, "throughput_initial": 20, "throughput_final": 69, 
        "time_to_100_productivity": 240, "initial_quality": 50, "final_quality": 100, 
        "time_to_100_quality": 240, "max_no_employees": 9999, "absentism_rate": 15, 
        "employee_cost": 130, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "RP1": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 0, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 60, "throughput_final": 69, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 5, "absentism_rate": 15, 
        "employee_cost": 166, "daily_supervision_cost": 16, "contract_cost": 0
    },
    "RP2": {
        "daily_income_work": 0, "backlog": 0, "recovery_time": 1, "recovery_time_final": 100,
        "time_to_hire": 0, "cost_to_hire": 0, "set_up_time": 0, "cost_to_set_up": 0, 
        "training_time": 0, "no_of_trainers": 0, "daily_cost_per_trainer": 0, 
        "no_of_trainees_per_session": 10, "throughput_initial": 60, "throughput_final": 69, 
        "time_to_100_productivity": 1, "initial_quality": 100, "final_quality": 100, 
        "time_to_100_quality": 1, "max_no_employees": 5, "absentism_rate": 15, 
        "employee_cost": 166, "daily_supervision_cost": 16, "contract_cost": 0
    }
}

# Crear tácticas
selected_tactics = ["FTE", "OT", "CT1", "CT2", "CT3", "CT4", "Temps", "RP1", "RP2"]
tactics = [create_tactic(name, configurations[name]) for name in selected_tactics]

num_tactics = len(tactics)
max_recovery_days = max(tactic["recovery_time_final"] for tactic in tactics)

data = {"backlog": tactics[0]["backlog"], "Daily": tactics[0]["daily_income_work"], "summary": {}, "detail": {}}
fte_overdemand = 0
fte_backlog = 0
total_cost = 0
tacticProcTr = [0] * len(tactics)
tacticTotal = [0] * len(tactics)
tacticUnit = [0] * len(tactics)
tacticUnitPT = [[0 for _ in range(max_recovery_days)] for _ in range(num_tactics)]
tacticTotalPT = [[0 for _ in range(max_recovery_days)] for _ in range(num_tactics)]
tacticBacklog = [[0 for _ in range(max_recovery_days)] for _ in range(num_tactics)]
totalPerRecovery = [0] * max_recovery_days
minUnitCostIndex = 0
conclusions = [[0 for _ in range(max_recovery_days)] for _ in range(num_tactics)]

for i, tactic in enumerate(tactics):
    tactic_data = {}
    total_cost = 0

    for t in range(1, tactic["recovery_time_final"] + 1):
        tactic["recovery_time"] = t
        result = calculate_tactics_data(tactic, fte_overdemand, fte_backlog)
        tactic_data[t] = result
        total_cost += result["total_cost"]

        if tactic["name"] == "FTE" and t == tactic["recovery_time_final"]:
            fte_overdemand = result["over_demand"]
            fte_backlog = result["backlog"]
            
        tacticUnitPT[i][t - 1] = result["unit_cost"]
        tacticTotalPT[i][t - 1] = result["total_cost"]
        tacticBacklog[i][t - 1] = result["backlog"]
        
    tacticProcTr[i] = result["processed_transactions"]
    tacticTotal[i] = result["total_cost"]
    
    # print(f"Total Cost of {tactic['name']}: {tacticTotal[i]}")
    # print(f"Unit Cost of {tactic['name']}: {tacticUnit[i]}")
    
    data["detail"][tactic["name"]] = tactic_data
    
print(f"Total Cost of all tactics: {tacticTotalPT}")

ignored_tactics = [0]

for i in range(9):
    if i in ignored_tactics:
        continue
    
    for j in range(max_recovery_days):
        if tacticUnitPT[i][j] > 0 and i not in ignored_tactics:
            print(f"Total cost tactica: {tacticTotalPT[i][j]}")
            ignored_tactics.append(i)

for i in range(9):
    for j in range(max_recovery_days):
        if j == 6:
            print(f"Total fsdfsdfd of {tactics[i]['name']} in day {j + 1}: {tacticTotalPT[i][j]}")
        
ignored_tactics = []
        
for i in range(max_recovery_days):  # Iterar sobre los días de recuperación
          
    for j in range(9):  # Iterar sobre las tácticas
        if j not in ignored_tactics and tacticUnitPT[j][i] > 0:  # Verificar si la táctica no está ignorada y tiene un costo unitario positivo
            if j == 0:
                if tacticBacklog[j][i] > : #pendienteeeeAAAAAAAAAAAAAAA
            totalPerRecovery[i] += tacticTotalPT[j][i]
            ignored_tactics.append(j)
    ignored_tactics = []

            
print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
print(f"Total cost per recovery: {totalPerRecovery}")

tacticTotalSummary = [0] * 9
# Calcular Total Tactica 1 Summary (FTE)
tacticTotalSummary[0] = tacticTotal[0]

# Calcular Total Tactica 2 Summary (Min Unit Cost Tactic)
filtered_units = [cost for cost in tacticUnit[1:] if cost > 0]
if filtered_units:
    minUnitCost = min(filtered_units)  
    minUnitCostIndex = tacticUnit.index(minUnitCost)  
    tacticTotalSummary[1] = tacticTotal[minUnitCostIndex]
else:
    minUnitCostIndex = -1
 
# Calcular Total Tactica 3 Summary
# Volver a calcualar calculated_tactics_data pero todas las tacticas tendran el daily incoming work del tactic[minUnitCostIndex] y guardar todos los datos del result en un arreglo llamado tacticsResultsSumm2

for i in range(1, tactics[0]["recovery_time_final"] + 1):
    total_transactions_FTE = (tactics[0]["daily_income_work"] * i) + tactics[0]["backlog"]
    total_cost_day = sum(tactic_data.get(i, {}).get("total_cost", 0) for tactic_data in data["detail"].values())
    total_unit_cost_day = total_cost_day / total_transactions_FTE if total_transactions_FTE > 0 else 0
    data["summary"][str(i)] = {
            "total_transactions_summ": total_transactions_FTE,
            "total_cost_summ": total_cost_day,  # Pendiente
            "total_unit_cost_summ": total_unit_cost_day  # Pendiente
        }

with open("tactics_results.json", "w") as f:
    json.dump(data, f, indent=4, default=decimal_to_float)

print("JSON generado exitosamente.")
