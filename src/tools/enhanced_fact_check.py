"""
Enhanced fact-checking tool integration for LangChain.

This module provides a comprehensive fact-checking tool that integrates
with the existing LangChain tool registry and provides enhanced functionality.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from .fact_checker import FactChecker


class EnhancedFactCheckInput(BaseModel):
    """Enhanced input schema for fact-checking with more options."""

    response_text: str = Field(
        description="Text containing vehicle information to verify"
    )
    source_records: Optional[List[int]] = Field(
        default=None, description="Specific stock IDs to check against (if known)"
    )
    check_price: Optional[bool] = Field(
        default=True, description="Whether to verify price information"
    )
    check_specs: Optional[bool] = Field(
        default=True, description="Whether to verify vehicle specifications"
    )
    check_features: Optional[bool] = Field(
        default=True, description="Whether to verify feature information"
    )
    price_tolerance: Optional[float] = Field(
        default=0.001, description="Price tolerance for verification (0.1% = 0.001)"
    )


class EnhancedFactCheckResult(BaseModel):
    """Enhanced result of fact-checking verification."""

    is_accurate: bool = Field(description="Overall accuracy of the information")
    verified_facts: List[str] = Field(description="Facts that were verified as correct")
    discrepancies: List[str] = Field(description="Facts that don't match the database")
    warnings: List[str] = Field(description="Potential issues or missing information")
    confidence_score: float = Field(
        description="Confidence in the verification (0-1)", ge=0, le=1
    )
    claims_found: int = Field(description="Number of claims extracted from text")
    validation_details: Dict[str, Any] = Field(
        description="Detailed validation results for each claim"
    )


def enhanced_fact_check_impl(inputs: Dict[str, Any]) -> EnhancedFactCheckResult:
    """
    Enhanced fact-checking implementation using the new FactChecker class.

    Args:
        inputs: Dictionary of fact-checking inputs

    Returns:
        Enhanced fact-checking result
    """
    # Parse inputs
    check_input = EnhancedFactCheckInput(**inputs)

    # Create fact checker with custom tolerance
    fact_checker = FactChecker()
    fact_checker.price_tolerance = check_input.price_tolerance

    # Verify the text using the enhanced fact checker
    verification_results = fact_checker.verify_text(check_input.response_text)

    # Process results into the expected format
    verified_facts = []
    discrepancies = []
    warnings = []

    for verification in verification_results["verifications"]:
        claim = verification["claim"]

        if verification.get("valid", False):
            if claim["type"] == "stock_id":
                verified_facts.append(f"Stock ID {claim['value']} exists in database")
            elif claim["type"] == "price":
                verified_facts.append(f"Price ${claim['value']:,.2f} is accurate")
            elif claim["type"] == "vehicle_mention":
                vehicle_info = claim["value"]
                verified_facts.append(
                    f"Vehicle {vehicle_info['make']} {vehicle_info['model']} {vehicle_info['year']} exists"
                )
            elif claim["type"] == "mileage":
                verified_facts.append(f"Mileage {claim['value']:,} km is accurate")
        else:
            error_msg = verification.get("error", "Unknown error")
            discrepancies.append(f"Claim '{claim['original_text']}': {error_msg}")

        # Add warnings
        if "warning" in verification:
            warnings.append(
                f"Claim '{claim['original_text']}': {verification['warning']}"
            )

    # Calculate overall accuracy
    total_claims = verification_results["claims_found"]
    valid_claims = verification_results["valid_claims"]

    if total_claims == 0:
        confidence_score = 1.0  # No claims to verify
        is_accurate = True
    else:
        confidence_score = valid_claims / total_claims
        is_accurate = len(discrepancies) == 0 and confidence_score > 0.7

    # Add warnings for low confidence
    if confidence_score < 0.5 and total_claims > 0:
        warnings.append("Low confidence in verification - multiple vehicles may match")

    if not is_accurate and confidence_score > 0.5:
        warnings.append("Some information doesn't match the database")

    return EnhancedFactCheckResult(
        is_accurate=is_accurate,
        verified_facts=verified_facts,
        discrepancies=discrepancies,
        warnings=warnings,
        confidence_score=confidence_score,
        claims_found=total_claims,
        validation_details=verification_results,
    )


# Create the enhanced LangChain tool
enhanced_fact_check_tool = Tool(
    name="enhanced_fact_check",
    func=enhanced_fact_check_impl,
    description="""Enhanced vehicle information verification against the database.
    
    This tool provides comprehensive fact-checking capabilities:
    - Extracts vehicle details (price, year, mileage, make, model, features) from text
    - Verifies information against the vehicle database with configurable tolerance
    - Identifies discrepancies and missing information
    - Provides detailed confidence scores and validation results
    - Supports custom price tolerance settings
    
    Features:
    - Stock ID verification
    - Price verification with configurable tolerance (default 0.1%)
    - Vehicle specification verification
    - Feature availability checking
    - Comprehensive error reporting
    
    Useful for fact-checking responses before sending them to customers
    or verifying information from external sources.""",
    args_schema=EnhancedFactCheckInput,
)


def create_validated_rag_tool(
    llm, retriever, enable_fact_checking: bool = True
) -> Tool:
    """
    Create a LangChain tool that wraps the ValidatedRAGChain.

    Args:
        llm: Language model for generation
        retriever: Retriever for document retrieval
        enable_fact_checking: Whether to enable fact-checking

    Returns:
        LangChain Tool instance
    """
    # Create fact checker if enabled
    fact_checker = FactChecker() if enable_fact_checking else None

    # Create the validated RAG chain
    rag_chain = create_validated_rag_chain(
        llm=llm,
        retriever=retriever,
        fact_checker=fact_checker,
        enable_fact_checking=enable_fact_checking,
    )

    def rag_tool_func(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Function wrapper for the RAG chain."""
        question = inputs.get("question", "")
        return rag_chain.run(question)

    return Tool(
        name="validated_rag",
        func=rag_tool_func,
        description="""Validated RAG system for vehicle recommendations with fact-checking.
        
        This tool provides:
        - Retrieval-augmented generation for vehicle recommendations
        - Automatic fact-checking of generated responses
        - Guardrailed prompts to prevent hallucinations
        - Comprehensive validation results
        
        Input: Question about vehicles
        Output: Validated response with fact-checking results""",
        args_schema=type(
            "RAGInput",
            (BaseModel,),
            {"question": Field(description="Question about vehicles to answer")},
        ),
    )


# Export tools and utilities
__all__ = [
    "EnhancedFactCheckInput",
    "EnhancedFactCheckResult",
    "enhanced_fact_check_impl",
    "enhanced_fact_check_tool",
    "create_validated_rag_tool",
]
