"""
Fact-checking tool for vehicle information verification.

This module provides LangChain-compatible tools for verifying
vehicle information against the database to ensure accuracy.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from sqlmodel import Session, select
import re

from models.vehicle import Vehicle
from db.database import get_session_sync


class FactCheckInput(BaseModel):
    """Input schema for fact-checking."""

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


class FactCheckResult(BaseModel):
    """Result of fact-checking verification."""

    is_accurate: bool = Field(description="Overall accuracy of the information")
    verified_facts: List[str] = Field(description="Facts that were verified as correct")
    discrepancies: List[str] = Field(description="Facts that don't match the database")
    warnings: List[str] = Field(description="Potential issues or missing information")
    confidence_score: float = Field(
        description="Confidence in the verification (0-1)", ge=0, le=1
    )


def extract_vehicle_info(text: str) -> Dict[str, Any]:
    """
    Extract vehicle information from text using regex patterns.

    Args:
        text: Text to extract information from

    Returns:
        Dictionary of extracted information
    """
    info = {}

    # Extract price (various formats)
    price_patterns = [
        r"\$([0-9,]+(?:\.[0-9]{2})?)",
        r"([0-9,]+(?:\.[0-9]{2})?)\s*dollars?",
        r"price[:\s]*\$?([0-9,]+(?:\.[0-9]{2})?)",
    ]

    for pattern in price_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(",", "")
            try:
                info["price"] = float(price_str)
                break
            except ValueError:
                continue

    # Extract year
    year_match = re.search(r"\b(19|20)\d{2}\b", text)
    if year_match:
        info["year"] = int(year_match.group())

    # Extract mileage
    mileage_patterns = [
        r"(\d{1,3}(?:,\d{3})*)\s*km",
        r"(\d{1,3}(?:,\d{3})*)\s*kilometers?",
        r"mileage[:\s]*(\d{1,3}(?:,\d{3})*)",
    ]

    for pattern in mileage_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            mileage_str = match.group(1).replace(",", "")
            try:
                info["km"] = int(mileage_str)
                break
            except ValueError:
                continue

    # Extract make and model
    make_model_patterns = [
        r"(toyota|honda|ford|chevrolet|nissan|bmw|mercedes|audi|volkswagen|hyundai|kia|mazda|subaru|lexus|acura|infiniti|volvo|jaguar|land rover|porsche|ferrari|lamborghini|bentley|rolls royce|mclaren|aston martin|maserati|alfa romeo|fiat|jeep|dodge|chrysler|ram|gmc|cadillac|lincoln|buick|genesis)\s+([a-zA-Z0-9\s]+)",
    ]

    for pattern in make_model_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info["make"] = match.group(1).lower()
            info["model"] = match.group(2).strip().lower()
            break

    # Extract features
    feature_keywords = [
        "bluetooth",
        "car play",
        "android auto",
        "air conditioning",
        "power steering",
        "power windows",
        "central locking",
        "alarm",
        "radio",
        "cd player",
        "usb",
        "aux",
        "navigation",
        "gps",
        "backup camera",
        "parking sensors",
        "cruise control",
        "leather seats",
        "heated seats",
        "sunroof",
        "moonroof",
        "automatic transmission",
        "manual transmission",
        "all wheel drive",
        "four wheel drive",
        "abs",
        "airbags",
    ]

    features = []
    for feature in feature_keywords:
        if re.search(r"\b" + re.escape(feature) + r"\b", text, re.IGNORECASE):
            features.append(feature.lower().replace(" ", "_"))

    if features:
        info["features"] = features

    return info


def verify_against_database(
    extracted_info: Dict[str, Any], source_records: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Verify extracted information against the database.

    Args:
        extracted_info: Information extracted from text
        source_records: Specific stock IDs to check

    Returns:
        Verification results
    """
    with get_session_sync() as session:
        # Build query
        query = select(Vehicle)

        if source_records:
            query = query.where(Vehicle.stock_id.in_(source_records))
        else:
            # Filter by extracted criteria
            if "make" in extracted_info:
                query = query.where(Vehicle.make.ilike(f"%{extracted_info['make']}%"))
            if "model" in extracted_info:
                query = query.where(Vehicle.model.ilike(f"%{extracted_info['model']}%"))
            if "year" in extracted_info:
                query = query.where(Vehicle.year == extracted_info["year"])

        vehicles = list(session.exec(query))

    if not vehicles:
        return {"matches": [], "best_match": None, "confidence": 0.0}

    # Score matches based on extracted information
    scored_matches = []

    for vehicle in vehicles:
        score = 0.0
        total_checks = 0

        # Check price
        if "price" in extracted_info:
            total_checks += 1
            price_diff = abs(vehicle.price - extracted_info["price"])
            if price_diff < 100:  # Within $100
                score += 1.0
            elif price_diff < 1000:  # Within $1000
                score += 0.5

        # Check year
        if "year" in extracted_info:
            total_checks += 1
            if vehicle.year == extracted_info["year"]:
                score += 1.0

        # Check mileage
        if "km" in extracted_info:
            total_checks += 1
            km_diff = abs(vehicle.km - extracted_info["km"])
            if km_diff < 1000:  # Within 1000 km
                score += 1.0
            elif km_diff < 10000:  # Within 10000 km
                score += 0.5

        # Check features
        if "features" in extracted_info and vehicle.features:
            total_checks += 1
            matched_features = 0
            for feature in extracted_info["features"]:
                if vehicle.features.get(feature, False):
                    matched_features += 1

            if extracted_info["features"]:
                feature_score = matched_features / len(extracted_info["features"])
                score += feature_score

        # Calculate confidence
        confidence = score / total_checks if total_checks > 0 else 0.0

        scored_matches.append(
            {"vehicle": vehicle, "score": score, "confidence": confidence}
        )

    # Sort by confidence
    scored_matches.sort(key=lambda x: x["confidence"], reverse=True)

    return {
        "matches": scored_matches,
        "best_match": scored_matches[0] if scored_matches else None,
        "confidence": scored_matches[0]["confidence"] if scored_matches else 0.0,
    }


def fact_check_impl(inputs: Dict[str, Any]) -> FactCheckResult:
    """
    Verify vehicle information against the database.

    Args:
        inputs: Dictionary of fact-checking inputs

    Returns:
        Fact-checking result
    """
    # Parse inputs
    check_input = FactCheckInput(**inputs)

    # Extract information from text
    extracted_info = extract_vehicle_info(check_input.response_text)

    if not extracted_info:
        return FactCheckResult(
            is_accurate=False,
            verified_facts=[],
            discrepancies=["No vehicle information found in the text"],
            warnings=["Unable to extract vehicle details for verification"],
            confidence_score=0.0,
        )

    # Verify against database
    verification = verify_against_database(extracted_info, check_input.source_records)

    verified_facts = []
    discrepancies = []
    warnings = []

    if verification["best_match"]:
        vehicle = verification["best_match"]["vehicle"]
        confidence = verification["best_match"]["confidence"]

        # Check specific facts
        if check_input.check_price and "price" in extracted_info:
            price_diff = abs(vehicle.price - extracted_info["price"])
            if price_diff < 100:
                verified_facts.append(
                    f"Price ${extracted_info['price']:,.2f} is accurate"
                )
            else:
                discrepancies.append(
                    f"Price ${extracted_info['price']:,.2f} doesn't match database "
                    f"(${vehicle.price:,.2f})"
                )

        if check_input.check_specs:
            if "year" in extracted_info and vehicle.year == extracted_info["year"]:
                verified_facts.append(f"Year {extracted_info['year']} is correct")
            elif "year" in extracted_info:
                discrepancies.append(
                    f"Year {extracted_info['year']} doesn't match database ({vehicle.year})"
                )

            if "km" in extracted_info:
                km_diff = abs(vehicle.km - extracted_info["km"])
                if km_diff < 1000:
                    verified_facts.append(
                        f"Mileage {extracted_info['km']:,} km is accurate"
                    )
                else:
                    discrepancies.append(
                        f"Mileage {extracted_info['km']:,} km doesn't match database "
                        f"({vehicle.km:,} km)"
                    )

        if (
            check_input.check_features
            and "features" in extracted_info
            and vehicle.features
        ):
            matched_features = []
            missing_features = []

            for feature in extracted_info["features"]:
                if vehicle.features.get(feature, False):
                    matched_features.append(feature)
                else:
                    missing_features.append(feature)

            if matched_features:
                verified_facts.append(
                    f"Features {', '.join(matched_features)} are available"
                )

            if missing_features:
                discrepancies.append(
                    f"Features {', '.join(missing_features)} are not available on this vehicle"
                )

        # Overall assessment
        is_accurate = len(discrepancies) == 0 and confidence > 0.7

        if confidence < 0.5:
            warnings.append(
                "Low confidence in verification - multiple vehicles may match"
            )

        if not is_accurate and confidence > 0.5:
            warnings.append("Some information doesn't match the database")

    else:
        discrepancies.append("No matching vehicle found in database")
        warnings.append("Unable to verify information - no matching records")
        confidence = 0.0
        is_accurate = False

    return FactCheckResult(
        is_accurate=is_accurate,
        verified_facts=verified_facts,
        discrepancies=discrepancies,
        warnings=warnings,
        confidence_score=confidence,
    )


# Create the LangChain tool
fact_check_tool = Tool(
    name="fact_check",
    func=fact_check_impl,
    description="""Verify vehicle information against the database to ensure accuracy.
    
    This tool helps ensure that vehicle information provided to customers is accurate:
    - Extracts vehicle details (price, year, mileage, make, model, features) from text
    - Verifies information against the vehicle database
    - Identifies discrepancies and missing information
    - Provides confidence scores for verification results
    
    Useful for fact-checking responses before sending them to customers
    or verifying information from external sources.""",
    args_schema=FactCheckInput,
)
