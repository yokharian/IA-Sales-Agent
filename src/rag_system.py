import os
from typing import List, Optional

from langchain_core.documents import Document

from .document_loader import DocumentLoader
from .retrieval_system import RetrievalSystem


class RAGSystem:
    """
    Retrieval-Augmented Generation system that
    Loads documents and Builds embeddings
    """

    def __init__(self, data_dir: str = "data/documents", model: Optional[str] = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")

        self.loader = DocumentLoader(data_dir)
        self.retrieval_system: Optional[RetrievalSystem] = None

        self.initialize_system()

    def initialize_system(self) -> None:
        """Load documents, create embeddings, and initialize the retrieval system."""
        documents = self.loader.load_documents()
        self.retrieval_system = RetrievalSystem(documents)

    @staticmethod
    def _build_knowledge_base(docs: List[Document]) -> str:
        """Construct a textual knowledge base by joining document contents."""
        return "\n\n".join(
            doc.page_content
            for doc in docs
            if doc is not None and getattr(doc, "page_content", None)
        )

    def obtain_knowledge_base(self, query: str) -> str:
        """Query the vector store and return a concatenated context string."""
        if not self.retrieval_system:
            raise RuntimeError("Retrieval system is not initialized.")
        docs: List[Document] = self.retrieval_system.query_vector_store(query, k=2)
        return self._build_knowledge_base(docs)
