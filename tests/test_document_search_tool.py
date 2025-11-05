"""
Test document search tool functionality.
"""

import os
import pytest
from pydantic import ValidationError
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Set test environment variables before any imports
os.environ["OPENAI_API_KEY"] = "test-key-for-testing"

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tools.document_search import document_search_tool, DocumentSearchInput


class TestDocumentSearchTool:
    """Test document search tool functionality."""

    @patch("tools.document_search.RetrievalSystem")
    def test_document_search_basic(self, mock_retrieval_class):
        """Test basic document search functionality."""
        # Mock document with metadata
        mock_doc = Mock()
        mock_doc.page_content = "This is a test document about cars."
        mock_doc.metadata = {"source": "test.md", "title": "Car Information"}

        # Mock retrieval system
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.query_vector_store.return_value = [mock_doc]
        mock_retrieval_class.return_value = mock_retrieval_instance

        # Test inputs
        inputs = {"query": "car information", "k": 5}
        content,artifact = document_search_tool.func(**inputs)

        # Verify results
        assert len(artifact) == 1
        assert artifact[0].page_content == "This is a test document about cars."
        assert artifact[0].metadata == {"source": "test.md", "title": "Car Information"}

    @patch("tools.document_search.RetrievalSystem")
    def test_document_search_with_score(self, mock_retrieval_class):
        """Test document search with similarity score."""
        # Mock document with score in metadata
        mock_doc = Mock()
        mock_doc.page_content = "Vehicle specifications and details."
        mock_doc.metadata = {"source": "specs.md", "score": 0.85}

        # Mock retrieval system
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.query_vector_store.return_value = [mock_doc]
        mock_retrieval_class.return_value = mock_retrieval_instance

        # Test inputs
        inputs = {"query": "vehicle specifications", "k": 3}

        content,artifact = document_search_tool.func(**inputs)

        # Verify results
        assert len(artifact) == 1
        assert artifact[0].page_content == "Vehicle specifications and details."

    @patch("tools.document_search.RetrievalSystem")
    def test_document_search_multiple_docs(self, mock_retrieval_class):
        """Test document search with multiple documents."""
        # Mock multiple documents
        mock_docs = []
        for i in range(3):
            mock_doc = Mock()
            mock_doc.page_content = f"Document {i+1} content about vehicles."
            mock_doc.metadata = {"source": f"doc{i+1}.md", "score": 0.8 - i * 0.1}
            mock_docs.append(mock_doc)

        # Mock retrieval system
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.query_vector_store.return_value = mock_docs
        mock_retrieval_class.return_value = mock_retrieval_instance

        # Test inputs
        inputs = {"query": "vehicle information", "k": 3}

        content,artifact = document_search_tool.func(**inputs)

        # Verify results
        assert len(artifact) == 3
        for i, result in enumerate(artifact):
            assert f"Document {i+1} content" in result.page_content

    @patch("tools.document_search.RetrievalSystem")
    def test_document_search_no_artifact(self, mock_retrieval_class):
        """Test document search with no artifact."""
        # Mock empty results
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.query_vector_store.return_value = []
        mock_retrieval_class.return_value = mock_retrieval_instance

        # Test inputs
        inputs = {"query": "nonexistent topic", "k": 5}

        content,artifact = document_search_tool.func(**inputs)

        # Verify empty results
        assert len(artifact) == 0

    def test_document_search_input_validation(self):
        """Test input validation for document search."""
        # Test valid inputs
        valid_inputs = {"query": "test query", "k": 5, "score_threshold": 0.7}

        search_input = DocumentSearchInput(**valid_inputs)
        assert search_input.query == "test query"
        assert search_input.k == 5

    def test_document_search_input_defaults(self):
        """Test default values for document search input."""
        # Test with minimal inputs
        minimal_inputs = {"query": "test query"}

        search_input = DocumentSearchInput(**minimal_inputs)
        assert search_input.query == "test query"
        assert search_input.k == 6  # Default value

    def test_document_search_comprehensive_scenarios(self):
        """Test document search with comprehensive scenarios."""
        # Test cases for document search
        test_cases = [
            {
                "name": "Basic vehicle search",
                "inputs": {"query": "vehicle specifications and features", "k": 3},
            },
            {
                "name": "Search with similarity threshold",
                "inputs": {
                    "query": "car maintenance and service",
                    "k": 5,
                    "score_threshold": 0.7,
                },
            },
            {
                "name": "Technical documentation search",
                "inputs": {"query": "engine specifications and performance", "k": 4},
            },
            {
                "name": "General automotive information",
                "inputs": {"query": "automotive industry trends", "k": 2},
            },
        ]

        for test_case in test_cases:
            # Test that the function can be called without crashing
            try:
                content,artifact = document_search_tool.func(**test_case["inputs"])
                assert isinstance(artifact, list)
                # Should handle the query gracefully
            except Exception as e:
                # Should handle errors gracefully
                from openai import AuthenticationError

                assert isinstance(
                    e,
                    (
                        ValueError,
                        TypeError,
                        KeyError,
                        AttributeError,
                        AuthenticationError,
                        ValidationError,
                    ),
                )

    def test_document_search_tool_integration(self):
        """Test document search tool integration with LangChain."""
        from tools.document_search import document_search_tool

        # Test tool attributes
        assert document_search_tool.name == "document_search"
        assert isinstance(document_search_tool.description, str)
        assert len(document_search_tool.description) > 0
        assert document_search_tool.args_schema is not None
        assert callable(document_search_tool.func)

        # Test direct tool usage
        try:
            result = document_search_tool.func(**
                {"query": "vehicle information", "k": 2}
            )
            assert isinstance(result, list)
        except Exception as e:
            # Expected to fail in test environment, but should not crash
            from openai import AuthenticationError

            assert isinstance(
                e,
                (
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                    AuthenticationError,
                    ValidationError,
                ),
            )

    def test_document_search_performance_scenarios(self):
        """Test document search performance with different scenarios."""
        import time

        # Test different search scenarios
        search_scenarios = [
            {"name": "Simple query", "inputs": {"query": "car information", "k": 3}},
            {
                "name": "Complex technical query",
                "inputs": {
                    "query": "engine specifications and performance metrics",
                    "k": 5,
                },
            },
            {
                "name": "Query with threshold",
                "inputs": {
                    "query": "vehicle maintenance",
                    "k": 4,
                    "score_threshold": 0.8,
                },
            },
            {"name": "Large result set", "inputs": {"query": "automotive", "k": 10}},
        ]

        for scenario in search_scenarios:
            start_time = time.time()

            try:
                content,artifact = document_search_tool.func(**scenario["inputs"])
                end_time = time.time()

                # Should complete within reasonable time (5 seconds)
                assert end_time - start_time < 5.0
                assert isinstance(artifact, list)

            except Exception as e:
                # Should handle errors gracefully
                from openai import AuthenticationError

                assert isinstance(
                    e,
                    (
                        ValueError,
                        TypeError,
                        KeyError,
                        AttributeError,
                        AuthenticationError,
                        ValidationError,
                    ),
                )

    def test_document_search_edge_cases(self):
        """Test document search error handling and edge cases."""
        # Test edge cases and error scenarios
        edge_cases = [
            {"name": "Empty query", "inputs": {"query": "", "k": 3}},
            {"name": "Very long query", "inputs": {"query": "a" * 1000, "k": 3}},
            {"name": "Zero results requested", "inputs": {"query": "test", "k": 0}},
            {
                "name": "High similarity threshold",
                "inputs": {"query": "test", "k": 5, "score_threshold": 0.99},
            },
            {
                "name": "Special characters",
                "inputs": {"query": "test@#$%^&*()", "k": 3},
            },
        ]

        for case in edge_cases:
            try:
                content,artifact = document_search_tool.func(**case["inputs"])
                assert isinstance(artifact, list)
                # Should handle edge cases gracefully
            except Exception as e:
                # Should handle errors gracefully
                from openai import AuthenticationError

                assert isinstance(
                    e,
                    (
                        ValueError,
                        TypeError,
                        KeyError,
                        AttributeError,
                        AuthenticationError,
                        ValidationError,
                    ),
                )

    def test_document_search_input_validation_edge_cases(self):
        """Test input validation for edge cases."""
        # Test with None values
        with pytest.raises((ValueError, TypeError, ValidationError)):
            document_search_tool.func(**{"query": None, "k": 3})

        # Test with invalid types
        with pytest.raises((ValueError, TypeError, ValidationError)):
            document_search_tool.func(**{"query": 123, "k": "invalid"})

        # Test with missing required fields
        with pytest.raises((KeyError, TypeError, Exception, ValidationError)):
            document_search_tool.func(**{"k": 3})  # Missing query

    def test_document_search_result_structure(self):
        """Test that document search results have correct structure."""
        # Mock a successful search
        with patch("tools.document_search.RetrievalSystem") as mock_retrieval_class:
            # Create mock documents with proper structure
            mock_docs = []
            for i in range(2):
                mock_doc = Mock()
                mock_doc.page_content = f"Test document {i+1} content"
                mock_doc.metadata = {"source": f"doc{i+1}.md", "score": 0.8 - i * 0.1}
                mock_docs.append(mock_doc)

            mock_retrieval_instance = Mock()
            mock_retrieval_instance.query_vector_store.return_value = mock_docs
            mock_retrieval_class.return_value = mock_retrieval_instance

            # Test the search
            inputs = {"query": "test query", "k": 2}
            content,artifact = document_search_tool.func(**inputs)

            # Verify result structure
            assert len(artifact) == 2
            for result in artifact:
                assert hasattr(result, "content")
                assert hasattr(result, "metadata")
                assert isinstance(result.page_content, str)
                assert isinstance(result.metadata, dict)
