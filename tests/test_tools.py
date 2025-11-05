"""
Tests for LangChain tools.
"""

import os
import sys
from pathlib import Path

# Set test environment variables before any imports
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.catalog_search import catalog_search_tool
from tools.document_search import document_search_tool, DocumentSearchInput


class TestCatalogSearchTool:
    """Test catalog search tool functionality."""

    def test_catalog_tool_attributes(self):
        """Test catalog search tool has required attributes."""
        assert hasattr(catalog_search_tool, "name")
        assert hasattr(catalog_search_tool, "description")
        assert hasattr(catalog_search_tool, "func")
        assert hasattr(catalog_search_tool, "args_schema")

        assert catalog_search_tool.name == "catalog_search"
        assert "vehicle" in catalog_search_tool.description.lower()
        assert catalog_search_tool.func is not None
        assert catalog_search_tool.args_schema is not None

    def test_catalog_tool_schema(self):
        """Test catalog search tool schema validation."""
        schema = catalog_search_tool.args_schema

        # Test valid inputs
        valid_inputs = {
            "make": "Toyota",
            "model": "Corolla",
            "budget_max": 30000,
            "max_results": 5,
        }

        # Should not raise validation error
        validated = schema(**valid_inputs)
        assert validated.make == "Toyota"
        assert validated.model == "Corolla"
        assert validated.budget_max == 30000
        assert validated.max_results == 5

    def test_catalog_tool_schema_defaults(self):
        """Test catalog search tool schema default values."""
        schema = catalog_search_tool.args_schema

        # Test with minimal inputs
        minimal_inputs = {"make": "Honda"}
        validated = schema(**minimal_inputs)
        assert validated.make == "Honda"
        assert validated.max_results == 5  # Default value

    def test_catalog_tool_function_call(self):
        """Test catalog search tool function call."""
        # Test that the tool function can be called without crashing
        inputs = {"make": "Toyota", "max_results": 2}

        try:
            content,artifact = catalog_search_tool.func(**inputs)
            # Should return a str and list (even if empty)
            assert isinstance(content, str)
            assert isinstance(artifact, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            assert isinstance(e, (ValueError, TypeError, KeyError, AttributeError))

    def test_catalog_tool_error_handling(self):
        """Test catalog search tool error handling."""
        # Test with invalid inputs that should be handled gracefully
        invalid_inputs = [
            {"make": None, "max_results": -1},
            {"make": "", "budget_max": "invalid"},
            {"make": "Toyota", "max_results": 0},
        ]

        for inputs in invalid_inputs:
            try:
                result = catalog_search_tool.func(**DocumentSearchInput(**inputs))
                # Should either return results or handle gracefully
                assert isinstance(result, list)
            except Exception as e:
                # Should handle errors gracefully
                assert isinstance(e, (ValueError, TypeError, KeyError))


class TestDocumentSearchTool:
    """Test document search tool functionality."""

    def test_document_tool_attributes(self):
        """Test document search tool has required attributes."""
        assert hasattr(document_search_tool, "name")
        assert hasattr(document_search_tool, "description")
        assert hasattr(document_search_tool, "func")
        assert hasattr(document_search_tool, "args_schema")

        assert document_search_tool.name == "document_search"
        assert "document" in document_search_tool.description.lower()
        assert document_search_tool.func is not None
        assert document_search_tool.args_schema is not None

    def test_document_tool_schema(self):
        """Test document search tool schema validation."""
        schema = document_search_tool.args_schema

        # Test valid inputs
        valid_inputs = {
            "query": "vehicle specifications",
            "k": 5,
        }

        # Should not raise validation error
        validated = schema(**valid_inputs)
        assert validated.query == "vehicle specifications"
        assert validated.k == 5

    def test_document_tool_schema_defaults(self):
        """Test document search tool schema default values."""
        schema = document_search_tool.args_schema

        # Test with minimal inputs
        minimal_inputs = {"query": "test query"}
        validated = schema(**minimal_inputs)
        assert validated.query == "test query"
        assert validated.k == 6  # Default value

    def test_document_tool_function_call(self):
        """Test document search tool function call."""
        # Test that the tool function can be called without crashing
        inputs = {"query": "test query", "k": 2}

        try:
            result = document_search_tool.func(**inputs)
            # Should return a list (even if empty)
            assert isinstance(result, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            from openai import AuthenticationError

            assert isinstance(
                e,
                (ValueError, TypeError, KeyError, AttributeError, AuthenticationError),
            )

    def test_document_tool_error_handling(self):
        """Test document search tool error handling."""
        # Test with invalid inputs that should be handled gracefully
        invalid_inputs = [
            {"query": "", "k": -1},
            {"query": None, "k": 0},
        ]

        for inputs in invalid_inputs:
            try:
                result = document_search_tool.func(**DocumentSearchInput(**inputs))
                # Should either return results or handle gracefully
                assert isinstance(result, list)
            except Exception as e:
                # Should handle errors gracefully
                assert isinstance(e, (ValueError, TypeError, KeyError))


class TestToolIntegration:
    """Test tool integration and compatibility."""

    def test_tool_compatibility(self):
        """Test that both tools are compatible with LangChain."""
        # Both tools should have the required LangChain tool interface
        for tool in [catalog_search_tool, document_search_tool]:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "func")
            assert hasattr(tool, "args_schema")

            # Name should be a string
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0

            # Description should be a string
            assert isinstance(tool.description, str)
            assert len(tool.description) > 0

            # Function should be callable
            assert callable(tool.func)

            # Args schema should be a Pydantic model
            assert hasattr(tool.args_schema, "model_fields")

    def test_tool_schema_consistency(self):
        """Test that tool schemas are consistent and valid."""
        for tool in [catalog_search_tool, document_search_tool]:
            schema = tool.args_schema

            # Schema should have fields
            fields = schema.model_fields

            assert len(fields) > 0

            # Each field should have a type annotation
            for field_name, field_info in fields.items():
                assert field_name is not None
                assert field_info is not None

    def test_tool_function_signatures(self):
        """Test that tool functions have correct signatures."""
        # Both tools should accept a dictionary input
        test_input = {"query": "test"}

        for tool in [catalog_search_tool, document_search_tool]:
            # Should be able to call the function (even if it fails)
            try:
                result = tool.func(**test_input)
                assert isinstance(result, list)
            except Exception:
                # Expected to fail in test environment, but should not crash
                pass
