"""
Pydantic data models for LangChain tools.

This module contains all the Pydantic BaseModel schemas used
as input/output schemas for the LangChain tools.
"""

from typing import Optional
from pydantic import BaseModel, Field


class FinanceCalculatorArgs(BaseModel):
    """
    Input schema for the enhanced finance calculator tool.

    This tool calculates financing options for multiple loan terms
    with a fixed 10% annual interest rate.
    """

    price: float = Field(description="Vehicle price in USD", gt=0, example=25000.0)

    down_payment: float = Field(
        description="Down payment amount in USD", ge=0, example=5000.0
    )

    return_schedule: bool = Field(
        default=False,
        description="If true, return the full monthly amortization schedule for the 3-year term",
        example=False,
    )

    class Config:
        json_schema_extra = {
            "example": {
                "price": 25000.0,
                "down_payment": 5000.0,
                "return_schedule": False,
            }
        }
