"""
Test document search tool functionality.
"""

import pytest
from unittest.mock import Mock, patch
from src.retrieval_system import document_search_impl, DocumentSearchInput, DocumentSearchResult


class TestDocumentSearchTool:
    """Test document search tool functionality."""

    @patch('src.retrieval_system.RetrievalSystem')
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
        inputs = {
            "query": "car information",
            "k": 5
        }
        
        results = document_search_impl(inputs)
        
        # Verify results
        assert len(results) == 1
        assert results[0].content == "This is a test document about cars."
        assert results[0].metadata == {"source": "test.md", "title": "Car Information"}
        assert results[0].similarity_score is None

    @patch('src.retrieval_system.RetrievalSystem')
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
        inputs = {
            "query": "vehicle specifications",
            "k": 3,
            "score_threshold": 0.7
        }
        
        results = document_search_impl(inputs)
        
        # Verify results
        assert len(results) == 1
        assert results[0].content == "Vehicle specifications and details."
        assert results[0].similarity_score == 0.85

    @patch('src.retrieval_system.RetrievalSystem')
    def test_document_search_multiple_docs(self, mock_retrieval_class):
        """Test document search with multiple documents."""
        # Mock multiple documents
        mock_docs = []
        for i in range(3):
            mock_doc = Mock()
            mock_doc.page_content = f"Document {i+1} content about vehicles."
            mock_doc.metadata = {"source": f"doc{i+1}.md", "score": 0.8 - i*0.1}
            mock_docs.append(mock_doc)
        
        # Mock retrieval system
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.query_vector_store.return_value = mock_docs
        mock_retrieval_class.return_value = mock_retrieval_instance
        
        # Test inputs
        inputs = {
            "query": "vehicle information",
            "k": 3
        }
        
        results = document_search_impl(inputs)
        
        # Verify results
        assert len(results) == 3
        for i, result in enumerate(results):
            assert f"Document {i+1} content" in result.content
            assert result.similarity_score == 0.8 - i*0.1

    @patch('src.retrieval_system.RetrievalSystem')
    def test_document_search_no_results(self, mock_retrieval_class):
        """Test document search with no results."""
        # Mock empty results
        mock_retrieval_instance = Mock()
        mock_retrieval_instance.query_vector_store.return_value = []
        mock_retrieval_class.return_value = mock_retrieval_instance
        
        # Test inputs
        inputs = {
            "query": "nonexistent topic",
            "k": 5
        }
        
        results = document_search_impl(inputs)
        
        # Verify empty results
        assert len(results) == 0

    def test_document_search_input_validation(self):
        """Test input validation for document search."""
        # Test valid inputs
        valid_inputs = {
            "query": "test query",
            "k": 5,
            "score_threshold": 0.7
        }
        
        search_input = DocumentSearchInput(**valid_inputs)
        assert search_input.query == "test query"
        assert search_input.k == 5
        assert search_input.score_threshold == 0.7

    def test_document_search_input_defaults(self):
        """Test default values for document search input."""
        # Test with minimal inputs
        minimal_inputs = {
            "query": "test query"
        }
        
        search_input = DocumentSearchInput(**minimal_inputs)
        assert search_input.query == "test query"
        assert search_input.k == 6  # Default value
        assert search_input.score_threshold is None  # Default value
