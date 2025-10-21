"""
Vehicle Search Engine for semantic and hybrid search capabilities.

This module provides a comprehensive search system that combines:
- Vector embeddings for semantic similarity
- BM25 for keyword matching
- Fuzzy matching for typo tolerance
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from rapidfuzz import fuzz, process
import numpy as np

from models.vehicle import Vehicle
from db.database import get_session_sync


class VehicleSearchEngine:
    """
    Hybrid search engine for vehicle recommendations.

    Combines semantic search (vector embeddings), keyword search (BM25),
    and fuzzy matching for robust vehicle discovery with typo tolerance.
    """

    def __init__(self, persist_directory: str = "./data/chroma"):
        """
        Initialize the search engine.

        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Initialize search components
        self.vector_store: Optional[Chroma] = None
        self.bm25_retriever: Optional[BM25Retriever] = None
        self.vehicles_corpus: List[str] = []
        self.vehicles_metadata: List[Dict[str, Any]] = []

        # Load existing index if available
        self._load_existing_index()

    def _load_existing_index(self) -> None:
        """Load existing ChromaDB index if it exists."""
        if os.path.exists(self.persist_directory):
            try:
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
                print(f"Loaded existing vector index from {self.persist_directory}")
            except Exception as e:
                print(f"Warning: Could not load existing index: {e}")
                self.vector_store = None

    def _prepare_documents(self) -> List[Document]:
        """
        Prepare vehicle documents for indexing.

        Returns:
            List of Document objects with formatted text and metadata
        """
        documents = []

        with get_session_sync() as session:
            from sqlmodel import select

            statement = select(Vehicle)
            vehicles = list(session.exec(statement))

        for vehicle in vehicles:
            # Format vehicle description
            text_parts = [
                vehicle.make,
                vehicle.model,
                vehicle.version or "",
                str(vehicle.year),
                f"{vehicle.km}km",
            ]

            # Add active features
            if vehicle.features:
                active_features = [k for k, v in vehicle.features.items() if v]
                if active_features:
                    text_parts.append(" ".join(active_features))

            # Create search text
            search_text = " ".join(text_parts).strip()

            # Create document with flattened metadata for ChromaDB
            metadata = {
                "stock_id": vehicle.stock_id,
                "make": vehicle.make,
                "model": vehicle.model,
                "year": vehicle.year,
                "price": vehicle.price,
                "km": vehicle.km,
                "version": vehicle.version or "",
            }

            # Add features as individual boolean fields
            if vehicle.features:
                for feature, enabled in vehicle.features.items():
                    metadata[f"feature_{feature}"] = enabled

            doc = Document(page_content=search_text, metadata=metadata)
            documents.append(doc)

            # Store for fuzzy search
            self.vehicles_corpus.append(search_text)
            self.vehicles_metadata.append(
                {
                    "stock_id": vehicle.stock_id,
                    "text": search_text,
                    "make": vehicle.make,
                    "model": vehicle.model,
                }
            )

        return documents

    def build_index(self) -> None:
        """Build the search index from vehicle data."""
        print("Building search index...")

        # Prepare documents
        documents = self._prepare_documents()

        if not documents:
            print("No vehicles found to index")
            return

        # Build ChromaDB vector store
        self.vector_store = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )

        # Build BM25 retriever
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        self.bm25_retriever.k = 10  # Retrieve top 10 for reranking

        print(f"Index built successfully with {len(documents)} vehicles")
        print(f"Vector store persisted to {self.persist_directory}")

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        if max_score == min_score:
            return [1.0] * len(scores)

        return [(score - min_score) / (max_score - min_score) for score in scores]

    def _combine_scores(
        self, vector_results: List, bm25_results: List, fuzzy_results: List
    ) -> List[Dict[str, Any]]:
        """
        Combine results from different search methods with weighted scoring.

        Args:
            vector_results: Results from vector search
            bm25_results: Results from BM25 search
            fuzzy_results: Results from fuzzy search

        Returns:
            Combined and scored results
        """
        # Create a mapping of stock_id to combined score
        combined_scores = {}

        # Process vector results (weight: 0.5)
        if vector_results:
            vector_scores = [result[1] for result in vector_results]  # Extract scores
            normalized_vector = self._normalize_scores(vector_scores)

            for i, (doc, score) in enumerate(vector_results):
                stock_id = doc.metadata["stock_id"]
                combined_scores[stock_id] = {
                    "vehicle": doc,
                    "vector_score": normalized_vector[i],
                    "bm25_score": 0.0,
                    "fuzzy_score": 0.0,
                    "combined_score": 0.0,
                }

        # Process BM25 results (weight: 0.25)
        if bm25_results:
            bm25_scores = [doc.metadata.get("score", 0) for doc in bm25_results]
            normalized_bm25 = self._normalize_scores(bm25_scores)

            for i, doc in enumerate(bm25_results):
                stock_id = doc.metadata["stock_id"]
                if stock_id in combined_scores:
                    combined_scores[stock_id]["bm25_score"] = normalized_bm25[i]
                else:
                    combined_scores[stock_id] = {
                        "vehicle": doc,
                        "vector_score": 0.0,
                        "bm25_score": normalized_bm25[i],
                        "fuzzy_score": 0.0,
                        "combined_score": 0.0,
                    }

        # Process fuzzy results (weight: 0.25)
        if fuzzy_results:
            fuzzy_scores = [result[1] for result in fuzzy_results]  # Extract scores
            normalized_fuzzy = self._normalize_scores(fuzzy_scores)

            for i, (text, score, metadata) in enumerate(fuzzy_results):
                stock_id = metadata["stock_id"]
                if stock_id in combined_scores:
                    combined_scores[stock_id]["fuzzy_score"] = normalized_fuzzy[i]
                else:
                    # Create a mock document for fuzzy-only results
                    doc = Document(page_content=text, metadata=metadata)
                    combined_scores[stock_id] = {
                        "vehicle": doc,
                        "vector_score": 0.0,
                        "bm25_score": 0.0,
                        "fuzzy_score": normalized_fuzzy[i],
                        "combined_score": 0.0,
                    }

        # Calculate combined scores
        for result in combined_scores.values():
            result["combined_score"] = (
                0.5 * result["vector_score"]
                + 0.25 * result["bm25_score"]
                + 0.25 * result["fuzzy_score"]
            )

        return list(combined_scores.values())

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform hybrid search across all search methods.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results with combined scores
        """
        if not self.vector_store or not self.bm25_retriever:
            raise ValueError("Search index not built. Call build_index() first.")

        # Vector search
        vector_results = []
        if self.vector_store:
            vector_docs = self.vector_store.similarity_search_with_score(query, k=k * 2)
            vector_results = [
                (doc, 1 - score) for doc, score in vector_docs
            ]  # Convert distance to similarity

        # BM25 search
        bm25_results = []
        if self.bm25_retriever:
            bm25_docs = self.bm25_retriever.invoke(query)
            bm25_results = bm25_docs

        # Fuzzy search
        fuzzy_results = []
        if self.vehicles_corpus:
            fuzzy_matches = process.extract(
                query, self.vehicles_corpus, scorer=fuzz.token_set_ratio, limit=k * 2
            )
            fuzzy_results = [
                (text, score, self.vehicles_metadata[i])
                for i, (text, score, _) in enumerate(fuzzy_matches)
            ]

        # Combine and rerank results
        combined_results = self._combine_scores(
            vector_results, bm25_results, fuzzy_results
        )

        # Sort by combined score and return top k
        sorted_results = sorted(
            combined_results, key=lambda x: x["combined_score"], reverse=True
        )

        return sorted_results[:k]

    def get_vehicle_by_stock_id(self, stock_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific vehicle by stock_id.

        Args:
            stock_id: Vehicle stock ID

        Returns:
            Vehicle data if found, None otherwise
        """
        for metadata in self.vehicles_metadata:
            if metadata["stock_id"] == stock_id:
                return metadata
        return None
