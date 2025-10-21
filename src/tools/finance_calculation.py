"""
Finance calculation tool for vehicle financing.

This module provides LangChain-compatible tools for calculating
vehicle financing options including monthly payments and amortization schedules.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
import math


class FinanceCalculationInput(BaseModel):
    """Input schema for finance calculations."""

    price: float = Field(description="Vehicle price in USD", gt=0)
    down_payment: float = Field(description="Down payment amount in USD", ge=0)
    term_years: int = Field(description="Loan term in years", ge=1, le=10)
    interest_rate: Optional[float] = Field(
        default=5.5,
        description="Annual interest rate as percentage (e.g., 5.5 for 5.5%)",
        ge=0,
        le=50,
    )
    include_amortization: Optional[bool] = Field(
        default=False, description="Whether to include detailed amortization schedule"
    )


class PaymentBreakdown(BaseModel):
    """Monthly payment breakdown."""

    monthly_payment: float = Field(description="Monthly payment amount")
    total_interest: float = Field(description="Total interest over loan term")
    total_payments: float = Field(description="Total amount paid over loan term")
    principal_amount: float = Field(description="Principal amount financed")


class AmortizationEntry(BaseModel):
    """Single entry in amortization schedule."""

    month: int = Field(description="Month number")
    payment: float = Field(description="Monthly payment amount")
    principal: float = Field(description="Principal portion of payment")
    interest: float = Field(description="Interest portion of payment")
    balance: float = Field(description="Remaining balance")


class FinanceCalculationResult(BaseModel):
    """Complete finance calculation result."""

    payment_breakdown: PaymentBreakdown = Field(description="Payment summary")
    amortization_schedule: Optional[List[AmortizationEntry]] = Field(
        default=None, description="Detailed monthly payment breakdown"
    )
    recommendations: List[str] = Field(description="Financial recommendations")


def calculate_monthly_payment(
    principal: float, annual_rate: float, years: int
) -> float:
    """
    Calculate monthly payment using standard loan formula.

    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate as decimal (e.g., 0.055 for 5.5%)
        years: Loan term in years

    Returns:
        Monthly payment amount
    """
    if annual_rate == 0:
        return principal / (years * 12)

    monthly_rate = annual_rate / 12
    num_payments = years * 12

    monthly_payment = (
        principal
        * (monthly_rate * (1 + monthly_rate) ** num_payments)
        / ((1 + monthly_rate) ** num_payments - 1)
    )

    return monthly_payment


def generate_amortization_schedule(
    principal: float, monthly_rate: float, monthly_payment: float, num_payments: int
) -> List[AmortizationEntry]:
    """
    Generate detailed amortization schedule.

    Args:
        principal: Loan principal amount
        monthly_rate: Monthly interest rate as decimal
        monthly_payment: Monthly payment amount
        num_payments: Total number of payments

    Returns:
        List of amortization entries
    """
    schedule = []
    balance = principal

    for month in range(1, num_payments + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment

        # Adjust final payment if needed
        if principal_payment > balance:
            principal_payment = balance
            monthly_payment = principal_payment + interest_payment

        balance -= principal_payment

        entry = AmortizationEntry(
            month=month,
            payment=monthly_payment,
            principal=principal_payment,
            interest=interest_payment,
            balance=max(0, balance),
        )
        schedule.append(entry)

        if balance <= 0:
            break

    return schedule


def generate_recommendations(
    price: float, down_payment: float, monthly_payment: float, total_interest: float
) -> List[str]:
    """
    Generate financial recommendations based on the calculation.

    Args:
        price: Vehicle price
        down_payment: Down payment amount
        monthly_payment: Monthly payment
        total_interest: Total interest over loan term

    Returns:
        List of recommendation strings
    """
    recommendations = []

    # Down payment analysis
    down_payment_percent = (down_payment / price) * 100
    if down_payment_percent < 10:
        recommendations.append(
            f"Consider increasing down payment from {down_payment_percent:.1f}% to 20%+ "
            "to reduce monthly payments and total interest"
        )
    elif down_payment_percent >= 20:
        recommendations.append(
            f"Excellent down payment of {down_payment_percent:.1f}% - this will "
            "significantly reduce your monthly payment and total interest"
        )

    # Monthly payment analysis
    if monthly_payment > price * 0.05:  # More than 5% of vehicle price
        recommendations.append(
            f"Monthly payment of ${monthly_payment:,.2f} is relatively high. "
            "Consider a longer term or larger down payment if possible"
        )
    elif monthly_payment < price * 0.02:  # Less than 2% of vehicle price
        recommendations.append(
            f"Monthly payment of ${monthly_payment:,.2f} is very manageable. "
            "This is a good financing option"
        )

    # Interest analysis
    interest_percent = (total_interest / price) * 100
    if interest_percent > 20:
        recommendations.append(
            f"Total interest of ${total_interest:,.2f} ({interest_percent:.1f}% of vehicle price) "
            "is quite high. Consider shopping for better rates or increasing down payment"
        )
    elif interest_percent < 10:
        recommendations.append(
            f"Total interest of ${total_interest:,.2f} ({interest_percent:.1f}% of vehicle price) "
            "is very reasonable for this loan term"
        )

    # General advice
    if down_payment_percent < 20 and monthly_payment > price * 0.04:
        recommendations.append(
            "Consider saving more for a larger down payment to improve your loan terms"
        )

    return recommendations


def finance_calculation_impl(inputs: Dict[str, Any]) -> FinanceCalculationResult:
    """
    Calculate vehicle financing options.

    Args:
        inputs: Dictionary of calculation inputs

    Returns:
        Complete finance calculation result
    """
    # Parse inputs
    calc_input = FinanceCalculationInput(**inputs)

    # Calculate principal amount
    principal = calc_input.price - calc_input.down_payment

    if principal <= 0:
        return FinanceCalculationResult(
            payment_breakdown=PaymentBreakdown(
                monthly_payment=0,
                total_interest=0,
                total_payments=calc_input.down_payment,
                principal_amount=0,
            ),
            amortization_schedule=[],
            recommendations=[
                "Down payment covers full vehicle price - no financing needed!"
            ],
        )

    # Convert interest rate to decimal
    annual_rate = calc_input.interest_rate / 100
    monthly_rate = annual_rate / 12
    num_payments = calc_input.term_years * 12

    # Calculate monthly payment
    monthly_payment = calculate_monthly_payment(
        principal, annual_rate, calc_input.term_years
    )

    # Calculate totals
    total_payments = monthly_payment * num_payments
    total_interest = total_payments - principal

    # Create payment breakdown
    payment_breakdown = PaymentBreakdown(
        monthly_payment=monthly_payment,
        total_interest=total_interest,
        total_payments=total_payments,
        principal_amount=principal,
    )

    # Generate amortization schedule if requested
    amortization_schedule = None
    if calc_input.include_amortization:
        amortization_schedule = generate_amortization_schedule(
            principal, monthly_rate, monthly_payment, num_payments
        )

    # Generate recommendations
    recommendations = generate_recommendations(
        calc_input.price, calc_input.down_payment, monthly_payment, total_interest
    )

    return FinanceCalculationResult(
        payment_breakdown=payment_breakdown,
        amortization_schedule=amortization_schedule,
        recommendations=recommendations,
    )


# Create the LangChain tool
finance_calculation_tool = Tool(
    name="finance_calculation",
    func=finance_calculation_impl,
    description="""Calculate vehicle financing options including monthly payments and amortization schedules.
    
    This tool helps customers understand the financial implications of purchasing a vehicle:
    - Calculates monthly payment based on price, down payment, term, and interest rate
    - Shows total interest and total payments over the loan term
    - Generates detailed amortization schedule showing principal/interest breakdown
    - Provides personalized financial recommendations
    
    Useful for helping customers compare different financing options and make informed decisions.""",
    args_schema=FinanceCalculationInput,
)
