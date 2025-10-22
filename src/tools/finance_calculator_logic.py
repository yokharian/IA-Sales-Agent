"""
Core financial calculation logic for vehicle financing.

This module provides precise financial calculations using the Decimal
library to avoid floating-point errors in monetary calculations.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any


class FinanceCalculator:
    """
    Core financial calculator with fixed 10% annual interest rate.

    Uses Decimal arithmetic for precise financial calculations
    and supports multiple loan terms simultaneously.
    """

    # Fixed annual interest rate: 10%
    ANNUAL_RATE = Decimal("0.10")

    # Supported loan terms in months
    TERMS_MONTHS = [36, 48, 60, 72]  # 3, 4, 5, 6 years

    @staticmethod
    def calculate_monthly_payment(principal: Decimal, months: int) -> Decimal:
        """
        Calculate monthly payment using standard amortization formula.

        Formula: P * [r(1+r)^n] / [(1+r)^n - 1]
        Where:
        - P = principal amount
        - r = monthly interest rate
        - n = number of payments

        Args:
            principal: Loan principal amount
            months: Number of monthly payments

        Returns:
            Monthly payment amount (rounded to nearest cent)
        """
        if principal <= 0:
            return Decimal("0")

        monthly_rate = FinanceCalculator.ANNUAL_RATE / Decimal("12")

        if monthly_rate == 0:
            return (principal / months).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Calculate using amortization formula
        # P * [r(1+r)^n] / [(1+r)^n - 1]
        rate_plus_one = Decimal("1") + monthly_rate
        rate_power = rate_plus_one**months

        numerator = principal * monthly_rate * rate_power
        denominator = rate_power - Decimal("1")

        payment = numerator / denominator

        return payment.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def generate_amortization_schedule(
        principal: Decimal, monthly_payment: Decimal, months: int
    ) -> List[Dict[str, Any]]:
        """
        Generate detailed amortization schedule.

        Args:
            principal: Loan principal amount
            monthly_payment: Monthly payment amount
            months: Number of monthly payments

        Returns:
            List of monthly payment breakdowns
        """
        schedule = []
        balance = principal
        monthly_rate = FinanceCalculator.ANNUAL_RATE / Decimal("12")

        for month in range(1, months + 1):
            interest_payment = balance * monthly_rate
            principal_payment = monthly_payment - interest_payment

            # Adjust final payment if needed
            if principal_payment > balance:
                principal_payment = balance
                monthly_payment = principal_payment + interest_payment

            balance -= principal_payment

            schedule.append(
                {
                    "month": month,
                    "payment": float(
                        monthly_payment.quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    ),
                    "principal": float(
                        principal_payment.quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    ),
                    "interest": float(
                        interest_payment.quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    ),
                    "balance": float(
                        max(balance, Decimal("0")).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    ),
                }
            )

            if balance <= Decimal("0.01"):  # Account for rounding
                break

        return schedule

    @staticmethod
    def calculate_all_terms(principal: Decimal) -> List[Dict[str, Any]]:
        """
        Calculate financing options for all supported terms.

        Args:
            principal: Loan principal amount

        Returns:
            List of financing options for each term
        """
        results = []

        for months in FinanceCalculator.TERMS_MONTHS:
            years = months // 12
            monthly_payment = FinanceCalculator.calculate_monthly_payment(
                principal, months
            )
            total_paid = monthly_payment * months
            total_interest = total_paid - principal

            results.append(
                {
                    "term_years": years,
                    "months": months,
                    "monthly_payment": float(monthly_payment),
                    "total_paid": float(total_paid),
                    "interest_paid": float(total_interest),
                    "principal": float(principal),
                }
            )

        return results

    @staticmethod
    def format_currency(amount: Decimal) -> str:
        """
        Format decimal amount as currency string.

        Args:
            amount: Decimal amount to format

        Returns:
            Formatted currency string
        """
        return f"${amount:,.2f}"

    @staticmethod
    def validate_inputs(price: float, down_payment: float) -> None:
        """
        Validate input parameters.

        Args:
            price: Vehicle price
            down_payment: Down payment amount

        Raises:
            ValueError: If inputs are invalid
        """
        if price <= 0:
            raise ValueError("Price must be positive")

        if down_payment < 0:
            raise ValueError("Down payment cannot be negative")

        if down_payment > price:
            raise ValueError(
                f"Down payment (${down_payment:,.2f}) cannot exceed price (${price:,.2f})"
            )
