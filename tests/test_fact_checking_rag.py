"""
Tests for the fact-checking and RAG integration system.

This module provides comprehensive tests for the FactChecker class,
ValidatedRAGChain, and integration components.
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from src.tools.fact_checker import FactChecker
from src.chains.validated_rag_chain import ValidatedRAGChain, create_validated_rag_chain
from src.tools.enhanced_fact_check import (
    enhanced_fact_check_impl,
    EnhancedFactCheckInput,
)
from src.models.vehicle import Vehicle


class TestFactChecker:
    """Test cases for the FactChecker class."""

    def test_extract_claims_stock_id(self):
        """Test extraction of stock IDs from text."""
        fact_checker = FactChecker()

        text = "I'm interested in stock 12345 and also stock #67890"
        claims = fact_checker.extract_claims(text)

        assert len(claims) == 2
        assert claims[0]["type"] == "stock_id"
        assert claims[0]["value"] == 12345
        assert claims[1]["type"] == "stock_id"
        assert claims[1]["value"] == 67890

    def test_extract_claims_price(self):
        """Test extraction of prices from text."""
        fact_checker = FactChecker()

        text = "The price is $25,000 and also 30000 dollars"
        claims = fact_checker.extract_claims(text)

        assert len(claims) == 2
        assert claims[0]["type"] == "price"
        assert claims[0]["value"] == 25000.0
        assert claims[1]["type"] == "price"
        assert claims[1]["value"] == 30000.0

    def test_extract_claims_vehicle_mention(self):
        """Test extraction of vehicle mentions."""
        fact_checker = FactChecker()

        text = "I want a Toyota Camry 2020"
        claims = fact_checker.extract_claims(text)

        assert len(claims) == 1
        assert claims[0]["type"] == "vehicle_mention"
        assert claims[0]["value"]["make"] == "toyota"
        assert claims[0]["value"]["model"] == "camry"
        assert claims[0]["value"]["year"] == 2020

    def test_extract_claims_mileage(self):
        """Test extraction of mileage information."""
        fact_checker = FactChecker()

        text = "The car has 50,000 km mileage"
        claims = fact_checker.extract_claims(text)

        assert len(claims) == 1
        assert claims[0]["type"] == "mileage"
        assert claims[0]["value"] == 50000

    @patch("src.tools.fact_checker.get_session_sync")
    def test_verify_stock_id_valid(self, mock_get_session):
        """Test verification of valid stock ID."""
        # Mock database session
        mock_session = Mock()
        mock_vehicle = Vehicle(
            stock_id=12345,
            make="Toyota",
            model="Camry",
            year=2020,
            price=25000.0,
            km=50000,
        )
        mock_session.exec.return_value.first.return_value = mock_vehicle
        mock_get_session.return_value = mock_session

        fact_checker = FactChecker()
        claim = {"type": "stock_id", "value": 12345}

        result = fact_checker.verify_claim(claim)

        assert result["valid"] is True
        assert result["actual_data"]["stock_id"] == 12345
        assert result["actual_data"]["make"] == "Toyota"

    @patch("src.tools.fact_checker.get_session_sync")
    def test_verify_stock_id_invalid(self, mock_get_session):
        """Test verification of invalid stock ID."""
        # Mock database session
        mock_session = Mock()
        mock_session.exec.return_value.first.return_value = None
        mock_get_session.return_value = mock_session

        fact_checker = FactChecker()
        claim = {"type": "stock_id", "value": 99999}

        result = fact_checker.verify_claim(claim)

        assert result["valid"] is False
        assert "not found" in result["error"]

    def test_verify_text_comprehensive(self):
        """Test comprehensive text verification."""
        fact_checker = FactChecker()

        text = (
            "I'm interested in stock 12345 Toyota Camry 2020 for $25,000 with 50,000 km"
        )

        with patch("src.tools.fact_checker.get_session_sync") as mock_get_session:
            # Mock database session
            mock_session = Mock()
            mock_vehicle = Vehicle(
                stock_id=12345,
                make="Toyota",
                model="Camry",
                year=2020,
                price=25000.0,
                km=50000,
            )
            mock_session.exec.return_value.first.return_value = mock_vehicle
            mock_get_session.return_value = mock_session

            result = fact_checker.verify_text(text)

            assert result["claims_found"] > 0
            assert "verifications" in result


class TestValidatedRAGChain:
    """Test cases for the ValidatedRAGChain class."""

    def test_initialization(self):
        """Test ValidatedRAGChain initialization."""
        mock_llm = Mock()
        mock_retriever = Mock()
        mock_fact_checker = Mock()

        chain = ValidatedRAGChain(
            llm=mock_llm, retriever=mock_retriever, fact_checker=mock_fact_checker
        )

        assert chain.llm == mock_llm
        assert chain.retriever == mock_retriever
        assert chain.fact_checker == mock_fact_checker

    def test_retrieve_context(self):
        """Test context retrieval."""
        mock_llm = Mock()
        mock_retriever = Mock()

        # Mock documents
        mock_docs = [
            Mock(page_content="Toyota Camry 2020", metadata={"stock_id": 12345}),
            Mock(page_content="Honda Civic 2019", metadata={"stock_id": 67890}),
        ]
        mock_retriever.invoke.return_value = mock_docs

        chain = ValidatedRAGChain(mock_llm, mock_retriever)
        documents, context = chain._retrieve_context("test question")

        assert len(documents) == 2
        assert "[Stock ID: 12345]" in context
        assert "[Stock ID: 67890]" in context

    def test_generate_response(self):
        """Test response generation."""
        mock_llm = Mock()
        mock_retriever = Mock()

        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "This is a test response"
        mock_llm.invoke.return_value = mock_response

        chain = ValidatedRAGChain(mock_llm, mock_retriever, use_chat_prompt=True)
        response = chain._generate_response("test context", "test question")

        assert response == "This is a test response"

    def test_validate_response(self):
        """Test response validation."""
        mock_llm = Mock()
        mock_retriever = Mock()
        mock_fact_checker = Mock()

        # Mock fact checker response
        mock_fact_checker.verify_text.return_value = {
            "valid": True,
            "verifications": [],
            "summary": "All claims valid",
        }

        chain = ValidatedRAGChain(
            mock_llm, mock_retriever, mock_fact_checker, enable_fact_checking=True
        )

        result = chain._validate_response("test response", "test context")

        assert result["validated"] is True
        assert result["validation_summary"] == "All claims valid"

    def test_invoke_complete_flow(self):
        """Test complete invoke flow."""
        mock_llm = Mock()
        mock_retriever = Mock()
        mock_fact_checker = Mock()

        # Mock documents
        mock_docs = [
            Mock(page_content="Toyota Camry 2020", metadata={"stock_id": 12345})
        ]
        mock_retriever.invoke.return_value = mock_docs

        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "The Toyota Camry 2020 is available"
        mock_llm.invoke.return_value = mock_response

        # Mock fact checker
        mock_fact_checker.verify_text.return_value = {
            "valid": True,
            "verifications": [],
            "summary": "All claims valid",
        }

        chain = ValidatedRAGChain(
            mock_llm, mock_retriever, mock_fact_checker, enable_fact_checking=True
        )

        result = chain.invoke({"question": "Find me a Toyota Camry"})

        assert "response" in result
        assert "source_documents" in result
        assert "validation_results" in result
        assert result["validation_results"]["validated"] is True


class TestEnhancedFactCheck:
    """Test cases for the enhanced fact-checking tool."""

    def test_enhanced_fact_check_impl(self):
        """Test the enhanced fact-checking implementation."""
        inputs = {
            "response_text": "The Toyota Camry stock 12345 costs $25,000",
            "check_price": True,
            "check_specs": True,
            "price_tolerance": 0.001,
        }

        with patch(
            "src.tools.enhanced_fact_check.FactChecker"
        ) as mock_fact_checker_class:
            mock_fact_checker = Mock()
            mock_fact_checker_class.return_value = mock_fact_checker

            # Mock verification results
            mock_fact_checker.verify_text.return_value = {
                "valid": True,
                "verifications": [
                    {
                        "claim": {
                            "type": "stock_id",
                            "value": 12345,
                            "original_text": "stock 12345",
                        },
                        "valid": True,
                    },
                    {
                        "claim": {
                            "type": "price",
                            "value": 25000.0,
                            "original_text": "$25,000",
                        },
                        "valid": True,
                    },
                ],
                "summary": "All claims valid",
                "claims_found": 2,
                "valid_claims": 2,
                "invalid_claims": 0,
            }

            result = enhanced_fact_check_impl(inputs)

            assert result.is_accurate is True
            assert result.confidence_score == 1.0
            assert result.claims_found == 2

    def test_enhanced_fact_check_input_validation(self):
        """Test input validation for enhanced fact-checking."""
        # Test valid input
        valid_input = EnhancedFactCheckInput(
            response_text="Test text", check_price=True, price_tolerance=0.001
        )
        assert valid_input.response_text == "Test text"
        assert valid_input.check_price is True
        assert valid_input.price_tolerance == 0.001


if __name__ == "__main__":
    pytest.main([__file__])
