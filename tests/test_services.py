import unittest
import sys
import os

# Add the project root to the Python path to allow importing 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services import (
    calculate_base_salary,
    calculate_performance_bonus,
    calculate_lti_and_cash,
    calculate_total_compensation,
    BASE_SALARY_PARAMS, # Import for checking roles
    LTI_RULES
)

class TestCompensationCalculations(unittest.TestCase):

    def test_calculate_base_salary_normal(self):
        # Mid-level, standard calculation within cap
        result = calculate_base_salary("Mid-level", 10_000_000, 80_000)
        # Potential = 75k + (10m * 1%) = 75k + 100k = 175k
        # Cap: 80k * 0.85 = 68k, 80k * 1.15 = 92k
        # Result should be capped at 92k
        self.assertAlmostEqual(result, 92000.00)

    def test_calculate_base_salary_upper_cap(self):
        # Executive, potential salary exceeds upper cap
        result = calculate_base_salary("Executive", 20_000_000, 250_000)
        # Potential = 150k + (20m * 2%) = 150k + 400k = 550k
        # Cap: 250k * 0.85 = 212.5k, 250k * 1.15 = 287.5k
        # Result should be capped at 287.5k (matches example)
        self.assertAlmostEqual(result, 287500.00)

    def test_calculate_base_salary_lower_cap(self):
        # Senior, potential salary below lower cap (e.g., revenue dropped)
        result = calculate_base_salary("Senior", 1_000_000, 150_000)
        # Potential = 100k + (1m * 1.5%) = 100k + 15k = 115k
        # Cap: 150k * 0.85 = 127.5k, 150k * 1.15 = 172.5k
        # Result should be capped at 127.5k
        self.assertAlmostEqual(result, 127500.00)

    def test_calculate_base_salary_invalid_role(self):
        with self.assertRaisesRegex(ValueError, "Invalid role level: Manager"):
            calculate_base_salary("Manager", 10_000_000, 100_000)

    def test_calculate_performance_bonus(self):
        base = 100_000
        target_bonus, perf_bonus = calculate_performance_bonus(base, "Senior", 1.1)
        # Target % for Senior = 100% => Target Amount = 100k * 1.0 = 100k
        # Perf Bonus = 100k * 1.1 = 110k
        self.assertAlmostEqual(target_bonus, 100000.00)
        self.assertAlmostEqual(perf_bonus, 110000.00)

    def test_calculate_performance_bonus_zero_multiplier(self):
        base = 80_000
        target_bonus, perf_bonus = calculate_performance_bonus(base, "Mid-level", 0.0)
        # Target % for Mid = 60% => Target Amount = 80k * 0.6 = 48k
        # Perf Bonus = 48k * 0.0 = 0
        self.assertAlmostEqual(target_bonus, 48000.00)
        self.assertAlmostEqual(perf_bonus, 0.00)

    def test_calculate_performance_bonus_invalid_role(self):
         with self.assertRaisesRegex(ValueError, "Invalid role level: Intern"):
            calculate_performance_bonus(50000, "Intern", 1.0)

    def test_calculate_lti_and_cash_executive(self):
        perf_bonus = 431250.00
        target_bonus = 359375.00 # Needed for equity calc
        role = "Executive"
        rules = LTI_RULES[role]
        result = calculate_lti_and_cash(perf_bonus, target_bonus, role)

        expected_deferred = perf_bonus * rules["deferral_pct"] # 431250 * 0.40 = 172500
        expected_fund = perf_bonus * rules["fund_investment_pct"] # 431250 * 0.20 = 86250
        expected_equity = target_bonus * rules["equity_factor"] # 359375 * 0.50 = 179687.50
        expected_cash = perf_bonus - expected_deferred - expected_fund # 431250 - 172500 - 86250 = 172500

        self.assertAlmostEqual(result["deferred_cash"], expected_deferred)
        self.assertAlmostEqual(result["fund_investment_amount"], expected_fund)
        self.assertAlmostEqual(result["equity_award_value"], expected_equity)
        self.assertAlmostEqual(result["immediate_cash_bonus"], expected_cash)

    def test_calculate_lti_and_cash_junior(self):
        perf_bonus = 20000.00
        target_bonus = 15000.00
        role = "Junior"
        rules = LTI_RULES[role]
        result = calculate_lti_and_cash(perf_bonus, target_bonus, role)

        expected_deferred = perf_bonus * rules["deferral_pct"] # 20000 * 0.10 = 2000
        expected_fund = perf_bonus * rules["fund_investment_pct"] # 20000 * 0.05 = 1000
        expected_equity = 0 # Junior not eligible
        expected_cash = perf_bonus - expected_deferred - expected_fund # 20000 - 2000 - 1000 = 17000

        self.assertAlmostEqual(result["deferred_cash"], expected_deferred)
        self.assertAlmostEqual(result["fund_investment_amount"], expected_fund)
        self.assertAlmostEqual(result["equity_award_value"], expected_equity)
        self.assertAlmostEqual(result["immediate_cash_bonus"], expected_cash)

    def test_calculate_lti_invalid_role(self):
        with self.assertRaisesRegex(ValueError, "Invalid role level: Contractor"):
             calculate_lti_and_cash(50000, 40000, "Contractor")

    def test_calculate_total_compensation_example(self):
        # The main example from the prompt
        result = calculate_total_compensation(
            role_level="Executive",
            team_revenue=20_000_000,
            last_years_salary=250_000,
            performance_multiplier=1.2
        )
        self.assertNotIn("error", result) # Check calculation was successful
        self.assertAlmostEqual(result["calculated_base_salary"], 287500.00)
        self.assertAlmostEqual(result["target_bonus_amount"], 359375.00)
        self.assertAlmostEqual(result["performance_bonus"], 431250.00)
        self.assertAlmostEqual(result["lti_breakdown"]["deferred_cash"], 172500.00)
        self.assertAlmostEqual(result["lti_breakdown"]["equity_award_value"], 179687.50)
        self.assertAlmostEqual(result["lti_breakdown"]["fund_investment_amount"], 86250.00)
        self.assertAlmostEqual(result["immediate_cash_bonus"], 172500.00)

    def test_calculate_total_compensation_invalid_role_error(self):
         result = calculate_total_compensation(
            role_level="Supervisor",
            team_revenue=5_000_000,
            last_years_salary=90_000,
            performance_multiplier=1.0
        )
         self.assertIn("error", result)
         self.assertEqual(result["error"], "Invalid role level: Supervisor")

if __name__ == '__main__':
    unittest.main()
