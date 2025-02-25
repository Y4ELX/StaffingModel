class Tactic:
    
    def __init__(self, name, config):
        self.name = name
        self.recovery_time = config.get("recovery_time", 1)
        self.recovery_time_final = config.get("recovery_time_final", 100)
        self.time_to_hire = config.get("time_to_hire", 0)
        self.cost_to_hire = config.get("cost_to_hire", 0)
        self.set_up_time = config.get("set_up_time", 0)
        self.cost_to_set_up = config.get("cost_to_set_up", 0)
        self.training_time = config.get("training_time", 0)
        self.no_of_trainers = config.get("no_of_trainers", 0)
        self.daily_cost_per_trainer = config.get("daily_cost_per_trainer", 0)
        self.no_of_trainees_per_session = config.get(
            "no_of_trainees_per_session", 10
        )
        self.throughput_initial = config.get("throughput_initial", 69)
        self.throughput_final = config.get("throughput_final", 69)
        self.time_to_100_productivity = config.get(
            "time_to_100_productivity", 1
        )
        self.initial_quality = config.get("initial_quality", 100)
        self.final_quality = config.get("final_quality", 100)
        self.time_to_100_quality = config.get("time_to_100_quality", 10)
        self.max_no_employees = config.get("max_no_employees", 39)
        self.absentism_rate = config.get("absentism_rate", 15)
        self.employee_cost = config.get("employee_cost", 166)
        self.daily_supervision_cost = config.get("daily_supervision_cost", 16)
        self.contract_cost = config.get("contract_cost", 0)
        self.throughput_acum = 0
        self.reduction_backlog_acum = 0
        self.final_quality_acum = 0
        self.final_throughput_acum = 0

    FTE_overdemand = 0

    def calculate_tactics_data(self):
        if self.name != "FTE":
            self.daily_income_work = Tactic.FTE_overdemand
        startup_time_days = (
            self.time_to_hire + self.set_up_time + self.training_time
        )
        daily_productivity_increase = (
            self.throughput_final - self.throughput_initial
        ) / self.time_to_100_productivity
        final_daily_throughput = min(
            self.throughput_initial
            + (daily_productivity_increase * self.recovery_time),
            self.throughput_final,
        )
        self.final_throughput_acum += final_daily_throughput
        average_daily_throughput = (
            self.final_throughput_acum / self.recovery_time
            if self.recovery_time > 0
            else 0
        )
        daily_quality_increase = (
            (self.final_quality - self.initial_quality)
            / self.time_to_100_quality
            / 100
        )
        final_daily_quality = min(
            self.initial_quality
            + (daily_quality_increase * self.recovery_time),
            self.final_quality,
        )
        self.final_quality_acum += final_daily_quality
        average_daily_quality = (
            self.final_quality_acum / self.recovery_time
            if self.recovery_time > 0
            else 0
        )
        amount_of_needed_employees = (
            self.max_no_employees
            if self.max_no_employees < 9999
            else round(
                ((self.daily_income_work * self.recovery_time) + self.backlog)
                / (
                    average_daily_throughput
                    * (1 - self.absentism_rate / 100)
                    * self.recovery_time
                )
            )
        )
        training_cost_per_individual = (
            self.training_time
            * self.no_of_trainers
            * self.daily_cost_per_trainer
            / max(
                1,
                min(
                    amount_of_needed_employees, self.no_of_trainees_per_session
                ),
            )
        )
        total_onboarding_cost_per_employee = (
            self.cost_to_hire
            + self.cost_to_set_up
            + (self.training_time * self.employee_cost)
            + training_cost_per_individual
        )
        throughput = (
            0
            if startup_time_days >= self.recovery_time
            else round(
                average_daily_throughput
                * amount_of_needed_employees
                * (1 - self.absentism_rate / 100)
            )
        )
        self.throughput_acum += throughput
        oversight_cost = (
            self.daily_cost_per_trainer * (1 - average_daily_quality) / 2
            if average_daily_quality < 0.9
            else 0
        )
        total_daily_cost_per_employee = (
            self.employee_cost
            + self.daily_supervision_cost
            + self.contract_cost
            + oversight_cost
            if throughput > 0
            else 0
        )
        overdemand = max(0, self.daily_income_work - throughput)
        reduction_on_backlog = max(0, throughput - self.daily_income_work)
        backlog = (
            max(0, self.backlog - reduction_on_backlog)
            if overdemand == 0
            else self.backlog
        )
        processed_transactions = (
            self.throughput_acum
            if self.daily_income_work > 0 or self.backlog > 0
            else 0
        )
        total_cost = (
            self.recovery_time
            * total_daily_cost_per_employee
            * amount_of_needed_employees
        ) + (total_onboarding_cost_per_employee * amount_of_needed_employees)
        if self.name != "FTE":
            unit_cost = (
                total_cost / processed_transactions
                if processed_transactions > 0
                else 0
            )
        else:
            unit_cost = (
                total_cost / self.throughput_acum
                if self.throughput_acum > 0
                else 0
            )
        if (
            self.name == "FTE"
            and self.recovery_time == self.recovery_time_final
        ):
            Tactic.FTE_overdemand = overdemand

        return {
            "daily_income_work": self.daily_income_work,
            "backlog": self.backlog,
            "recovery_time": self.recovery_time,
            "time_to_hire_days": self.time_to_hire,
            "cost_to_hire": self.cost_to_hire,
            "set_up_time_days": self.set_up_time,
            "cost_to_set_up": self.cost_to_set_up,
            "training_time_days": self.training_time,
            "no_of_trainers": self.no_of_trainers,
            "daily_cost_per_trainer": self.daily_cost_per_trainer,
            "no_of_trainees_per_session": self.no_of_trainees_per_session,
            "training_cost_individual": training_cost_per_individual,
            "total_onboarding_cost_per_employee": total_onboarding_cost_per_employee,
            "startup_time_days": startup_time_days,
            "throughput_day_initial": self.throughput_initial,
            "throughput_day_final": self.throughput_final,
            "time_to_100_productivity_days": self.time_to_100_productivity,
            "daily_productivity_increase": daily_productivity_increase,
            "final_daily_throughput": final_daily_throughput,
            "average_daily_throughput": average_daily_throughput,
            "initial_quality": self.initial_quality,
            "final_quality": self.final_quality,
            "time_to_100_quality_days": self.time_to_100_quality,
            "daily_quality_increase": daily_quality_increase,
            "final_daily_quality": final_daily_quality,
            "average_daily_quality": average_daily_quality,
            "max_no_employees": self.max_no_employees,
            "absentism_rate": self.absentism_rate,
            "amount_of_needed_employees": amount_of_needed_employees,
            "throughput": throughput,
            "employee_cost": self.employee_cost,
            "daily_supervision_cost": self.daily_supervision_cost,
            "contract_cost": self.contract_cost,
            "oversight_cost": oversight_cost,
            "total_daily_cost_per_employee": total_daily_cost_per_employee,
            "over_demand": overdemand,
            "reduction_on_backlog": reduction_on_backlog,
            "backlog": backlog,
            "processed_transactions": processed_transactions,
            "total_cost": total_cost,
            "unit_cost": unit_cost,
        }