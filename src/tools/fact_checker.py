"""
Enhanced FactChecker class for validating LLM responses against the database.

This module provides a comprehensive fact-checking system that extracts
factual claims from text and verifies them against the vehicle database.
"""

import re
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select

from models.vehicle import Vehicle
from db.database import get_session_sync


class FactChecker:
    """
    Enhanced fact-checking system for vehicle information validation.

    Extracts factual claims from text using regex patterns and verifies
    them against the PostgreSQL database with configurable tolerance.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the FactChecker.

        Args:
            db_session: Database session. If None, will create one as needed.
        """
        self.session = db_session
        self.price_tolerance = 0.001  # 0.1% tolerance for price verification

    def _get_session(self) -> Session:
        """Get database session, creating one if needed."""
        if self.session is None:
            return get_session_sync()
        return self.session

    def extract_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract factual claims from text using regex patterns.

        Args:
            text: Text to extract claims from

        Returns:
            List of claim dictionaries with type, value, and position
        """
        claims = []

        # Extract stock IDs (5-6 digits, optionally prefixed with "stock" or "#")
        stock_pattern = r"stock[\s#]*(\d{5,6})"
        stock_matches = re.finditer(stock_pattern, text, re.IGNORECASE)

        for match in stock_matches:
            claims.append(
                {
                    "type": "stock_id",
                    "value": int(match.group(1)),
                    "text_position": match.start(),
                    "original_text": match.group(0),
                }
            )

        # Extract prices (various formats)
        price_patterns = [
            r"\$?([\d,]+\.?\d*)\s*(?:k|mil|thousand|dollars?)?",
            r"price[:\s]*\$?([\d,]+\.?\d*)",
            r"cost[:\s]*\$?([\d,]+\.?\d*)",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:k|mil|thousand)?",
        ]

        for pattern in price_patterns:
            price_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in price_matches:
                price_str = match.group(1).replace(",", "")
                try:
                    price_value = float(price_str)
                    # Skip very small numbers that are likely not prices
                    if price_value >= 100:
                        claims.append(
                            {
                                "type": "price",
                                "value": price_value,
                                "text_position": match.start(),
                                "original_text": match.group(0),
                            }
                        )
                except ValueError:
                    continue

        # Extract vehicle mentions (make model year pattern)
        vehicle_pattern = r"(\w+)\s+(\w+)\s+(20\d{2})"
        vehicle_matches = re.finditer(vehicle_pattern, text, re.IGNORECASE)

        for match in vehicle_matches:
            claims.append(
                {
                    "type": "vehicle_mention",
                    "value": {
                        "make": match.group(1).lower(),
                        "model": match.group(2).lower(),
                        "year": int(match.group(3)),
                    },
                    "text_position": match.start(),
                    "original_text": match.group(0),
                }
            )

        # Extract mileage/kilometer mentions
        mileage_patterns = [
            r"(\d{1,3}(?:,\d{3})*)\s*km",
            r"(\d{1,3}(?:,\d{3})*)\s*kilometers?",
            r"mileage[:\s]*(\d{1,3}(?:,\d{3})*)",
            r"(\d{1,3}(?:,\d{3})*)\s*miles?",
        ]

        for pattern in mileage_patterns:
            mileage_matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in mileage_matches:
                mileage_str = match.group(1).replace(",", "")
                try:
                    mileage_value = int(mileage_str)
                    claims.append(
                        {
                            "type": "mileage",
                            "value": mileage_value,
                            "text_position": match.start(),
                            "original_text": match.group(0),
                        }
                    )
                except ValueError:
                    continue

        return claims

    def verify_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a single claim against the database.

        Args:
            claim: Claim dictionary from extract_claims

        Returns:
            Verification result dictionary
        """
        session = self._get_session()

        try:
            if claim["type"] == "stock_id":
                return self._verify_stock_id(claim, session)
            elif claim["type"] == "price":
                return self._verify_price(claim, session)
            elif claim["type"] == "vehicle_mention":
                return self._verify_vehicle_mention(claim, session)
            elif claim["type"] == "mileage":
                return self._verify_mileage(claim, session)
            else:
                return {
                    "valid": True,
                    "warning": f'Unknown claim type: {claim["type"]}',
                }
        except Exception as e:
            return {"valid": False, "error": f"Verification failed: {str(e)}"}

    def _verify_stock_id(
        self, claim: Dict[str, Any], session: Session
    ) -> Dict[str, Any]:
        """Verify stock ID claim."""
        stock_id = claim["value"]

        statement = select(Vehicle).where(Vehicle.stock_id == stock_id)
        vehicle = session.exec(statement).first()

        if not vehicle:
            return {
                "valid": False,
                "error": f"Stock ID {stock_id} not found in database",
            }

        return {
            "valid": True,
            "actual_data": {
                "stock_id": vehicle.stock_id,
                "price": vehicle.price,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year,
                "km": vehicle.km,
            },
        }

    def _verify_price(self, claim: Dict[str, Any], session: Session) -> Dict[str, Any]:
        """Verify price claim by finding nearby context."""
        claimed_price = claim["value"]

        # Try to find a nearby stock ID in the text
        nearby_stock_id = self._find_nearby_stock_id(claim)

        if nearby_stock_id:
            statement = select(Vehicle).where(Vehicle.stock_id == nearby_stock_id)
            vehicle = session.exec(statement).first()

            if vehicle:
                price_diff = abs(vehicle.price - claimed_price) / vehicle.price
                return {
                    "valid": price_diff <= self.price_tolerance,
                    "actual_price": vehicle.price,
                    "claimed_price": claimed_price,
                    "difference_pct": price_diff * 100,
                    "stock_id": vehicle.stock_id,
                }

        # If no specific vehicle found, check if price is reasonable
        # by looking for vehicles in similar price range
        statement = select(Vehicle).where(
            Vehicle.price.between(
                claimed_price * 0.9, claimed_price * 1.1  # 10% tolerance
            )
        )
        similar_vehicles = list(session.exec(statement))

        if similar_vehicles:
            return {
                "valid": True,
                "warning": f"Price ${claimed_price:,.2f} is in reasonable range but no specific vehicle context found",
                "similar_vehicles_count": len(similar_vehicles),
            }
        else:
            return {
                "valid": False,
                "error": f"Price ${claimed_price:,.2f} not found in database and no similar vehicles exist",
            }

    def _verify_vehicle_mention(
        self, claim: Dict[str, Any], session: Session
    ) -> Dict[str, Any]:
        """Verify vehicle mention (make, model, year)."""
        make = claim["value"]["make"]
        model = claim["value"]["model"]
        year = claim["value"]["year"]

        statement = select(Vehicle).where(
            Vehicle.make.ilike(f"%{make}%"),
            Vehicle.model.ilike(f"%{model}%"),
            Vehicle.year == year,
        )
        vehicles = list(session.exec(statement))

        if not vehicles:
            return {
                "valid": False,
                "error": f"No vehicle found matching {make} {model} {year}",
            }

        return {
            "valid": True,
            "actual_data": {
                "matches": len(vehicles),
                "vehicles": [
                    {
                        "stock_id": v.stock_id,
                        "make": v.make,
                        "model": v.model,
                        "year": v.year,
                        "price": v.price,
                    }
                    for v in vehicles[:3]  # Limit to first 3 matches
                ],
            },
        }

    def _verify_mileage(
        self, claim: Dict[str, Any], session: Session
    ) -> Dict[str, Any]:
        """Verify mileage claim."""
        claimed_mileage = claim["value"]

        # Try to find nearby stock ID
        nearby_stock_id = self._find_nearby_stock_id(claim)

        if nearby_stock_id:
            statement = select(Vehicle).where(Vehicle.stock_id == nearby_stock_id)
            vehicle = session.exec(statement).first()

            if vehicle:
                mileage_diff = abs(vehicle.km - claimed_mileage) / vehicle.km
                return {
                    "valid": mileage_diff <= 0.01,  # 1% tolerance for mileage
                    "actual_mileage": vehicle.km,
                    "claimed_mileage": claimed_mileage,
                    "difference_pct": mileage_diff * 100,
                    "stock_id": vehicle.stock_id,
                }

        # Check if mileage is in reasonable range
        statement = select(Vehicle).where(
            Vehicle.km.between(claimed_mileage * 0.9, claimed_mileage * 1.1)
        )
        similar_vehicles = list(session.exec(statement))

        if similar_vehicles:
            return {
                "valid": True,
                "warning": f"Mileage {claimed_mileage:,} km is in reasonable range but no specific vehicle context found",
                "similar_vehicles_count": len(similar_vehicles),
            }
        else:
            return {
                "valid": False,
                "error": f"Mileage {claimed_mileage:,} km not found in database",
            }

    def _find_nearby_stock_id(self, claim: Dict[str, Any]) -> Optional[int]:
        """
        Find a stock ID mentioned near the current claim in the text.

        This is a simplified implementation. In a real scenario, you might
        want to use more sophisticated NLP techniques to find context.
        """
        # This would need access to the original text and position
        # For now, return None - this would be enhanced in a full implementation
        return None

    def verify_text(self, text: str) -> Dict[str, Any]:
        """
        Verify all claims in a text against the database.

        Args:
            text: Text to verify

        Returns:
            Comprehensive verification results
        """
        claims = self.extract_claims(text)

        if not claims:
            return {
                "valid": True,
                "claims_found": 0,
                "verifications": [],
                "summary": "No verifiable claims found in text",
            }

        verifications = []
        valid_count = 0
        invalid_count = 0

        for claim in claims:
            verification = self.verify_claim(claim)
            verification["claim"] = claim
            verifications.append(verification)

            if verification.get("valid", False):
                valid_count += 1
            else:
                invalid_count += 1

        return {
            "valid": invalid_count == 0,
            "claims_found": len(claims),
            "valid_claims": valid_count,
            "invalid_claims": invalid_count,
            "verifications": verifications,
            "summary": f"Found {len(claims)} claims: {valid_count} valid, {invalid_count} invalid",
        }
