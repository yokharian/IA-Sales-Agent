"""
Enhanced Finance Calculator Tool for LangChain.

This module provides a comprehensive financing calculator that computes
monthly payments and amortization schedules for multiple loan terms
with a fixed 10% annual interest rate.
"""

from decimal import Decimal
from typing import Dict, Any, List
from langchain_core.tools import StructuredTool

from .finance_calculator_logic import FinanceCalculator
from .data_models import FinanceCalculatorArgs


def _run_finance_calculator(
    price: float, down_payment: float, return_schedule: bool = False
) -> str:
    """
    Calculate vehicle financing options for multiple loan terms.

    This function provides comprehensive financing calculations with:
    - Fixed 10% annual interest rate
    - Multiple loan terms (3, 4, 5, 6 years)
    - Optional detailed amortization schedule
    - Precise decimal arithmetic

    Args:
        price: Vehicle price in USD
        down_payment: Down payment amount in USD
        return_schedule: If True, include detailed amortization schedule

    Returns:
        Formatted string with financing options and summary table

    Raises:
        ValueError: If inputs are invalid
    """
    # Validate inputs
    FinanceCalculator.validate_inputs(price, down_payment)

    # Calculate principal amount
    principal = Decimal(str(price - down_payment))

    if principal <= 0:
        return (
            f"💰 **Financing Summary**\n\n"
            f"Vehicle Price: ${price:,.2f}\n"
            f"Down Payment: ${down_payment:,.2f}\n"
            f"Principal Financed: $0.00\n\n"
            f"✅ **No financing needed!** Your down payment covers the full vehicle price.\n"
        )

    # Calculate all loan terms
    terms_results = FinanceCalculator.calculate_all_terms(principal)

    # Format summary table
    summary_lines = [
        "💰 **Financing Summary**",
        "",
        f"Vehicle Price: ${price:,.2f}",
        f"Down Payment: ${down_payment:,.2f}",
        f"Principal Financed: ${principal:,.2f}",
        f"Annual Interest Rate: 10.0%",
        "",
        "📊 **Loan Terms Comparison**",
        "",
        "| Term | Monthly Payment | Total Paid | Interest Paid |",
        "|------|----------------|------------|---------------|",
    ]

    # Add each term to the table
    for term in terms_results:
        summary_lines.append(
            f"| {term['term_years']} years | "
            f"${term['monthly_payment']:,.2f} | "
            f"${term['total_paid']:,.2f} | "
            f"${term['interest_paid']:,.2f} |"
        )

    summary_lines.extend(["", "💡 **Recommendations:**", ""])

    # Add recommendations based on the results
    shortest_term = terms_results[0]  # 3 years
    longest_term = terms_results[-1]  # 6 years

    # Down payment analysis
    down_payment_percent = (down_payment / price) * 100
    if down_payment_percent >= 20:
        summary_lines.append(
            f"✅ Excellent down payment of {down_payment_percent:.1f}%!"
        )
    elif down_payment_percent >= 10:
        summary_lines.append(f"👍 Good down payment of {down_payment_percent:.1f}%")
    else:
        summary_lines.append(
            f"💭 Consider increasing down payment from {down_payment_percent:.1f}% to 20%+"
        )

    # Payment analysis
    monthly_payment_3yr = shortest_term["monthly_payment"]
    monthly_payment_6yr = longest_term["monthly_payment"]

    summary_lines.append(
        f"📈 3-year term: ${monthly_payment_3yr:,.2f}/month (saves ${longest_term['interest_paid'] - shortest_term['interest_paid']:,.2f} in interest)"
    )
    summary_lines.append(
        f"📉 6-year term: ${monthly_payment_6yr:,.2f}/month (${monthly_payment_6yr - monthly_payment_3yr:,.2f} less per month)"
    )

    # Interest analysis
    interest_savings = longest_term["interest_paid"] - shortest_term["interest_paid"]
    summary_lines.append(
        f"💰 You'll save ${interest_savings:,.2f} in interest with the 3-year term"
    )

    # Add amortization schedule if requested
    if return_schedule:
        summary_lines.extend(
            [
                "",
                "📋 **Detailed Amortization Schedule (3-Year Term)**",
                "",
                "| Month | Payment | Principal | Interest | Balance |",
                "|-------|---------|-----------|----------|---------|",
            ]
        )

        # Generate amortization schedule for 3-year term (36 months)
        monthly_payment_3yr_decimal = Decimal(str(monthly_payment_3yr))
        schedule = FinanceCalculator.generate_amortization_schedule(
            principal, monthly_payment_3yr_decimal, 36
        )

        # Add first 12 months and last 3 months for brevity
        for i, entry in enumerate(schedule):
            if i < 12 or i >= len(schedule) - 3:  # First 12 and last 3 months
                summary_lines.append(
                    f"| {entry['month']:2d} | "
                    f"${entry['payment']:8.2f} | "
                    f"${entry['principal']:9.2f} | "
                    f"${entry['interest']:8.2f} | "
                    f"${entry['balance']:7.2f} |"
                )
            elif i == 12:
                summary_lines.append(
                    "| ... | ... | ... | ... | ... |"
                )  # Ellipsis for middle months

    return "\n".join(summary_lines)


# Create the LangChain tool
finance_calc_tool = StructuredTool.from_function(
    func=_run_finance_calculator,
    name="finance_calculator",
    description="""Calculate comprehensive vehicle financing options with multiple loan terms.
    
    This tool provides detailed financing calculations with:
    - Fixed 10% annual interest rate
    - Multiple loan terms: 3, 4, 5, and 6 years
    - Comparison table showing monthly payments and total costs
    - Optional detailed amortization schedule
    - Personalized recommendations
    
    Perfect for helping customers understand their financing options
    and make informed decisions about loan terms.""",
    args_schema=FinanceCalculatorArgs,
)
