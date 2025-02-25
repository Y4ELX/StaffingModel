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


def calculate_tactics_data(tactic, fte_overdemand):
    if tactic["name"] != "FTE":
        tactic["daily_income_work"] = fte_overdemand
    
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
        "time_to_hire": tactic["time_to_hire"],
        "cost_to_hire": tactic["cost_to_hire"],
        "set_up_time": tactic["set_up_time"],
        "cost_to_set_up": tactic["cost_to_set_up"],
        "training_time": tactic["training_time"],
        "no_of_trainers": tactic["no_of_trainers"],
        "daily_cost_per_trainer": tactic["daily_cost_per_trainer"],
        "no_of_trainees_per_session": tactic["no_of_trainees_per_session"],
        "training_cost_per_individual": round(training_cost_per_individual, 2),
        "total_onboarding_cost_per_employee": round(total_onboarding_cost_per_employee, 2),
        "startup_time_days": startup_time_days,
        
        "throughput_initial": tactic["throughput_initial"],
        "throughput_final": tactic["throughput_final"],
        "time_to_100_productivity": tactic["time_to_100_productivity"],
        "daily_productivity_increase": round(daily_productivity_increase, 2),
        "final_daily_throughput": round(final_daily_throughput, 2),
        "average_daily_throughput": round(average_daily_throughput, 2),
        
        "initial_quality": tactic["initial_quality"],
        "final_quality": tactic["final_quality"],
        "time_to_100_quality": tactic["time_to_100_quality"],
        "daily_quality_increase": round(daily_quality_increase),
        "final_daily_quality": round(final_daily_quality, 2),
        "average_daily_quality": round(average_daily_quality),
        
        "max_no_employees": tactic["max_no_employees"],
        "absentism_rate": tactic["absentism_rate"],
        "amount_of_needed_employees": amount_of_needed_employees,
        "throughput": throughput,
        
        "employee_cost": tactic["employee_cost"],
        "daily_supervision_cost": tactic["daily_supervision_cost"],
        "contract_cost": tactic["contract_cost"],
        "oversight_cost": round(oversight_cost, 2),
        "total_daily_cost_per_employee": round(total_daily_cost_per_employee, 2),
        
        "over_demand": overdemand,
        "reduction_on_backlog": reduction_on_backlog,
        "backlog": backlog,
        
        "processed_transactions": processed_transactions,
        "total_cost": round(total_cost, 2),
        "unit_cost": unit_cost
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
selected_tactics = ["FTE", "OT", "CT1", "CT2", "CT3", "Temps", "RP1", "RP2"]
tactics = [create_tactic(name, configurations[name]) for name in selected_tactics]

data = {"backlog": tactics[0]["backlog"], "Daily": tactics[0]["daily_income_work"], "summary": {}, "detail": {}}
fte_overdemand = 0
total_cost = 0

for tactic in tactics:
    tactic_data = {}
    for t in range(1, tactic["recovery_time_final"] + 1):
        tactic["recovery_time"] = t
        result = calculate_tactics_data(tactic, fte_overdemand)
        tactic_data[t] = result
        total_cost += result["total_cost"]
        if tactic["name"] == "FTE" and t == tactic["recovery_time_final"]:
            fte_overdemand = result["over_demand"]
    data["detail"][tactic["name"]] = tactic_data

for i in range(1, tactics[0]["recovery_time_final"] + 1):
    total_transactions_FTE = (tactics[0]["daily_income_work"] * i) + tactics[0]["backlog"]
    total_cost_day = sum(tactic_data.get(i, {}).get("total_cost", 0) for tactic_data in data["detail"].values())
    total_unit_cost_day = total_cost_day / total_transactions_FTE if total_transactions_FTE > 0 else 0
    data["summary"][str(i)] = {"total_transactions_summ": total_transactions_FTE, "total_cost_summ": total_cost_day, "total_unit_cost_summ": total_unit_cost_day}

with open("tactics_results.json", "w") as f:
    json.dump(data, f, indent=4, default=decimal_to_float)

print("JSON generado exitosamente.")
