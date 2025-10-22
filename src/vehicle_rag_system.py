"""
Integration example for ValidatedRAGChain with fact-checking.

This module demonstrates how to integrate the ValidatedRAGChain with
the existing vehicle search system and fact-checking capabilities.
"""

from typing import Optional
from langchain_core.language_models import BaseLanguageModel

from .search.engine import VehicleSearchEngine
from .chains.validated_rag_chain import create_validated_rag_chain
from .tools.fact_checker import FactChecker
from .db.database import get_session_sync


class VehicleRAGSystem:
    """
    Complete RAG system for vehicle recommendations with fact-checking.

    This class integrates the vehicle search engine with the validated RAG chain
    to provide comprehensive vehicle recommendations with automatic fact-checking.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        persist_directory: str = "./data/chroma",
        enable_fact_checking: bool = True,
    ):
        """
        Initialize the VehicleRAGSystem.

        Args:
            llm: Language model for generation
            persist_directory: Directory for ChromaDB persistence
            enable_fact_checking: Whether to enable fact-checking
        """
        self.llm = llm
        self.enable_fact_checking = enable_fact_checking

        # Initialize search engine
        self.search_engine = VehicleSearchEngine(persist_directory)

        # Create fact checker if enabled
        self.fact_checker = FactChecker() if enable_fact_checking else None

        # Initialize RAG chain
        self.rag_chain = None
        self._initialize_rag_chain()

    def _initialize_rag_chain(self):
        """Initialize the validated RAG chain."""
        if not self.search_engine.vector_store:
            raise ValueError("Search index not built. Call build_index() first.")

        # Create a retriever from the search engine
        retriever = self.search_engine.vector_store.as_retriever(search_kwargs={"k": 5})

        # Create the validated RAG chain
        self.rag_chain = create_validated_rag_chain(
            llm=self.llm,
            retriever=retriever,
            fact_checker=self.fact_checker,
            enable_fact_checking=self.enable_fact_checking,
        )

    def build_index(self):
        """Build the search index."""
        self.search_engine.build_index()
        self._initialize_rag_chain()

    def query(self, question: str) -> dict:
        """
        Query the RAG system with fact-checking.

        Args:
            question: User question about vehicles

        Returns:
            Dictionary with response and validation results
        """
        if not self.rag_chain:
            raise ValueError("RAG chain not initialized. Call build_index() first.")

        return self.rag_chain.run(question)

    def fact_check_text(self, text: str) -> dict:
        """
        Fact-check a piece of text against the database.

        Args:
            text: Text to fact-check

        Returns:
            Fact-checking results
        """
        if not self.fact_checker:
            return {"validated": True, "message": "Fact-checking disabled"}

        return self.fact_checker.verify_text(text)

    def search_vehicles(self, query: str, k: int = 5) -> list:
        """
        Search for vehicles using the hybrid search engine.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results
        """
        return self.search_engine.search(query, k)


def create_vehicle_rag_system(
    llm: BaseLanguageModel,
    persist_directory: str = "./data/chroma",
    enable_fact_checking: bool = True,
) -> VehicleRAGSystem:
    """
    Factory function to create a VehicleRAGSystem.

    Args:
        llm: Language model for generation
        persist_directory: Directory for ChromaDB persistence
        enable_fact_checking: Whether to enable fact-checking

    Returns:
        Configured VehicleRAGSystem instance
    """
    return VehicleRAGSystem(
        llm=llm,
        persist_directory=persist_directory,
        enable_fact_checking=enable_fact_checking,
    )


# Example usage function
def example_usage():
    """
    Example of how to use the VehicleRAGSystem.
    """
    # This would be used with an actual LLM
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(model="gpt-3.5-turbo")

    # Create the RAG system
    # rag_system = create_vehicle_rag_system(llm)

    # Build the index
    # rag_system.build_index()

    # Query the system
    # result = rag_system.query("Find me a Toyota Camry under $30,000")
    # print(f"Response: {result['response']}")
    # print(f"Validated: {result['validation_results']['validated']}")

    # Fact-check some text
    # fact_check_result = rag_system.fact_check_text(
    #     "The Toyota Camry stock ID 12345 costs $25,000"
    # )
    # print(f"Fact-check result: {fact_check_result}")

    pass


if __name__ == "__main__":
    example_usage()
