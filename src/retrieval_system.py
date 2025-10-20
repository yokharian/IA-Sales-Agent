from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


def faiss_vector_store(documents: List[Document]):
    # Set up the embedding model
    embeddings_model = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        encode_kwargs={"normalize_embeddings": True},
    )

    # Create FAISS index from documents
    return FAISS.from_documents(documents, embeddings_model)


class RetrievalSystem:
    """Retrieval system backed by a FAISS vector store."""

    def __init__(self, embeddings: List[Document]):
        self.vector_store = faiss_vector_store(embeddings)

    def query_vector_store(self, query_text: str, k: int = 2):
        """Query the vector store for similar documents to the given query text."""
        output = self.vector_store.similarity_search_with_relevance_scores(
            query=query_text,
            k=k,
        )
        return output
