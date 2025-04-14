# Core calculation logic will go here
import math

# Constants for calculation rules (based on provided tables)
BASE_SALARY_PARAMS = {
    "Junior": {"fixed_floor": 50000, "revenue_factor": 0.005},
    "Mid-level": {"fixed_floor": 75000, "revenue_factor": 0.010},
    "Senior": {"fixed_floor": 100000, "revenue_factor": 0.015},
    "Executive": {"fixed_floor": 150000, "revenue_factor": 0.020},
}

TARGET_BONUS_PERCENT = {
    "Junior": 0.30,
    "Mid-level": 0.60,
    "Senior": 1.00,
    "Executive": 1.25,
}

LTI_RULES = {
    "Junior": {"deferral_pct": 0.10, "equity_eligible": False, "equity_factor": 0.0, "fund_investment_pct": 0.05},
    "Mid-level": {"deferral_pct": 0.20, "equity_eligible": True, "equity_factor": 0.25, "fund_investment_pct": 0.10},
    "Senior": {"deferral_pct": 0.30, "equity_eligible": True, "equity_factor": 0.40, "fund_investment_pct": 0.15},
    "Executive": {"deferral_pct": 0.40, "equity_eligible": True, "equity_factor": 0.50, "fund_investment_pct": 0.20},
}

SALARY_CAP_LOWER_BOUND = 0.85
SALARY_CAP_UPPER_BOUND = 1.15

def calculate_base_salary(role_level: str, team_revenue: float, last_years_salary: float) -> float:
    """Calculates the revenue-linked base salary with YoY cap."""
    params = BASE_SALARY_PARAMS.get(role_level)
    if not params:
        raise ValueError(f"Invalid role level: {role_level}")

    potential_salary = params["fixed_floor"] + (team_revenue * params["revenue_factor"])

    # Apply the +/- 15% year-over-year cap
    lower_cap = last_years_salary * SALARY_CAP_LOWER_BOUND
    upper_cap = last_years_salary * SALARY_CAP_UPPER_BOUND

    calculated_base = max(lower_cap, min(potential_salary, upper_cap))

    return round(calculated_base, 2)

def calculate_performance_bonus(calculated_base_salary: float, role_level: str, performance_multiplier: float) -> tuple[float, float]:
    """Calculates the target bonus amount and the final performance bonus."""
    target_pct = TARGET_BONUS_PERCENT.get(role_level)
    if target_pct is None:
        raise ValueError(f"Invalid role level: {role_level}")

    target_bonus_amount = calculated_base_salary * target_pct
    performance_bonus = target_bonus_amount * performance_multiplier

    return round(target_bonus_amount, 2), round(performance_bonus, 2)

# --- Optional: Performance Multiplier Calculation (as described in Step 2.2) ---
# def calculate_performance_multiplier(scores: dict) -> float:
#     """Calculates the multiplier based on weighted scores."""
#     # Example weights (adjust as needed)
#     weights = {
#         'absolute_return_score': 0.20,
#         'relative_perf_score': 0.50,
#         'risk_adjusted_score': 0.30,
#         # 'client_satisfaction_score': 0.0 # Example if added
#     }
#     weighted_score = sum(scores.get(k, 0) * w for k, w in weights.items())
#
#     # Map score to multiplier (example mapping)
#     if weighted_score < 2.5:
#         return 0.8
#     elif 2.5 <= weighted_score < 3.5:
#         return 1.0
#     elif 3.5 <= weighted_score < 4.5:
#         return 1.1
#     else: # >= 4.5
#         return 1.2
# -----------------------------------------------------------------------------

def calculate_lti_and_cash(performance_bonus: float, target_bonus_amount: float, role_level: str) -> dict:
    """Calculates LTI components and immediate cash bonus."""
    rules = LTI_RULES.get(role_level)
    if not rules:
        raise ValueError(f"Invalid role level: {role_level}")

    deferred_cash = performance_bonus * rules["deferral_pct"]
    fund_investment_amount = performance_bonus * rules["fund_investment_pct"]

    equity_award_value = 0.0
    if rules["equity_eligible"]:
        equity_award_value = target_bonus_amount * rules["equity_factor"]

    # Assumption: Fund Investment comes out of the total performance bonus
    immediate_cash_bonus = performance_bonus - deferred_cash - fund_investment_amount

    return {
        "deferred_cash": round(deferred_cash, 2),
        "equity_award_value": round(equity_award_value, 2),
        "fund_investment_amount": round(fund_investment_amount, 2),
        "immediate_cash_bonus": round(immediate_cash_bonus, 2)
    }

def calculate_total_compensation(role_level: str, team_revenue: float, last_years_salary: float, performance_multiplier: float) -> dict:
    """Orchestrates the full compensation calculation."""
    try:
        base_salary = calculate_base_salary(role_level, team_revenue, last_years_salary)
        target_bonus, perf_bonus = calculate_performance_bonus(base_salary, role_level, performance_multiplier)
        lti_components = calculate_lti_and_cash(perf_bonus, target_bonus, role_level)

        return {
            "calculated_base_salary": base_salary,
            "target_bonus_amount": target_bonus,
            "performance_bonus": perf_bonus,
            "lti_breakdown": {
                "deferred_cash": lti_components["deferred_cash"],
                "equity_award_value": lti_components["equity_award_value"],
                "fund_investment_amount": lti_components["fund_investment_amount"]
            },
            "immediate_cash_bonus": lti_components["immediate_cash_bonus"]
        }
    except ValueError as e:
        # Handle specific errors like invalid role level
        return {"error": str(e)}
    except Exception as e:
        # General error handling
        # Log the error in a real application: logging.exception("Calculation error")
        return {"error": "An unexpected error occurred during calculation."} 
