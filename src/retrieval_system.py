from __future__ import annotations

from typing import List

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.retrievers import (
    EnsembleRetriever,
)
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


class RetrievalSystem:
    """Retrieval system backed by a Chroma vector store."""

    def __init__(
        self,
        documents: List[Document],
        embedding_function,
        k: int = 6,
        fetch_k: int = 40,
        lambda_mult: float = 0.5,
        score_threshold: float | None = 0.6,
        metadata_filter: dict | None = None,
    ):
        """
        Initializes the object with a specified vector store and retriever for handling
        document embeddings. The retriever is configured to retrieve the most relevant
        documents based on similarity score with a threshold.

        Parameters:
            documents: List[Document]
                A list of document embeddings to be stored in the vector store.

            k: int
                Number of top relevant documents to retrieve. Defaults to 3.

            score_threshold: float
                Threshold for similarity scores. Only documents with a similarity
                score equal to or greater than this value will be retrieved.

            fetch_k: int
                Number of documents initially retrieved during an MMR search (default: 20 ).

            lambda_mult: float
                Controls diversity in MMR results (0 = maximum diversity, 1 = maximum relevance, default: 0.5 ).

            metadata_filter: dict | None
               Metadata filtering for selective document retrieval.
        """
        # Construir Chroma directamente desde documentos con persistencia en disco
        self.vector_store = Chroma.from_documents(
            documents,
            embedding_function,
            persist_directory="data/chroma",
        )
        # Initialize the (Sparse) BM25 retriever and (Dense) Chroma retriever.
        self.bm25_retriever = BM25Retriever.from_documents(documents)
        # Retrieve the top K documents with the highest similarity.
        self.bm25_retriever.k = 3

        # Configurar retriever con MMR y umbral de puntuación
        search_kwargs = {"k": k, "fetch_k": fetch_k, "lambda_mult": lambda_mult}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter

        # Usa "similarity" o "mmr" (recomendado). Para umbral, usa el retriever de score_threshold.
        if score_threshold is not None:
            self.basic_retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    **search_kwargs,
                    "score_threshold": score_threshold,
                },
            )
        else:
            self.basic_retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs=search_kwargs,
            )

        # initialize the ensemble retriever
        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self.bm25_retriever, self.basic_retriever], weights=[0.5, 0.5]
        )

        self._retriever = self.ensemble_retriever

    @property
    def retriever(self):
        return self._retriever

    def query_vector_store(self, query: str, **kwargs) -> List[Document]:
        """Query the vector store for similar documents to the given query text."""
        return self.ensemble_retriever.invoke(input=query, **kwargs)
