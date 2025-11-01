from __future__ import annotations

from typing import List, Optional, Dict, Any

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.retrievers import (
    EnsembleRetriever,
)
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from db.document_loader import DocumentLoader


from langchain_openai import OpenAIEmbeddings


class RetrievalSystem:

    def __init__(
        self,
        data_dir: str,
        llm: Optional[BaseChatModel] = None,
        embedding_function=OpenAIEmbeddings(model="text-embedding-3-large"),
    ):
        self._retriever = None
        self._bm25_retriever = None
        self._ensemble_retriever = None
        self._vector_store_retriever = None
        self._llm = llm

        self.vector_store = None
        self.data_dir = data_dir
        self.embedding_function = embedding_function
        self.initialize_vector_database()
        self.initialize_retriever()

    @property
    def documents(self) -> List[Document]:
        loader = DocumentLoader(self.data_dir)
        return loader.load_documents()

    @property
    def retriever(self):
        return self._retriever

    def query_vector_store(self, query: str, **kwargs) -> List[Document]:
        """Query the vector store for similar documents to the given query text."""
        return self.retriever.invoke(input=query, **kwargs)

    def initialize_vector_database(self) -> None:
        """Load documents, create embeddings."""
        self.vector_store = Chroma.from_documents(
            self.documents,
            self.embedding_function,
            persist_directory="data/chroma",
        )

    def initialize_retriever(
        self,
        k: int = 6,
        score_threshold: float | None = 0.6,
        metadata_filter: dict | None = None,
        fetch_k_multiplier: int = 4,
        lambda_mult: float = 0.7,
    ):
        """
        Initializes the object with a specified vector store and retriever for handling
        document embeddings. The retriever is configured to retrieve the most relevant
        documents using MMR (Maximum Marginal Relevance) for better diversity.

        Parameters:
            k: int
                Number of top relevant documents to retrieve. Defaults to 6.

            score_threshold: float
                Threshold for similarity scores. Only documents with a similarity
                score equal to or greater than this value will be retrieved.

            metadata_filter: dict | None
               Metadata filtering for selective document retrieval.

            fetch_k_multiplier: int
                Multiplier for fetch_k in MMR (fetch_k = k * fetch_k_multiplier).
                Higher values provide more candidates for diversity. Defaults to 4.

            lambda_mult: float
                MMR lambda parameter (0-1). Higher values favor relevance (0.7),
                lower values favor diversity (0.3). Defaults to 0.7.
        """
        # Initialize the (Sparse) BM25 retriever and (Dense) Chroma retriever.
        self._bm25_retriever = BM25Retriever.from_documents(self.documents)
        # Retrieve the top K documents with the highest similarity.
        self._bm25_retriever.k = 3

        # Configure retriever with MMR and score threshold
        if score_threshold is not None:
            self._vector_store_retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    "k": k,
                    "score_threshold": score_threshold,
                    "filter": metadata_filter,
                },
            )
        else:
            # Use MMR (Maximum Marginal Relevance) for better diversity
            self._vector_store_retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": k,
                    "fetch_k": k * fetch_k_multiplier,  # Fetch more candidates for MMR
                    "lambda_mult": lambda_mult,  # Balance between relevance and diversity
                    "filter": metadata_filter,
                },
            )

        # initialize the ensemble retriever
        self._ensemble_retriever = EnsembleRetriever(
            retrievers=[self._bm25_retriever, self._vector_store_retriever],
            weights=[0.7, 0.3],
        )

        self._retriever = self._ensemble_retriever


class DocumentSearchInput(BaseModel):
    """Input schema for document search."""

    query: str = Field(description="Search query to find relevant documents")
    k: int = Field(
        default=6, description="Number of documents to retrieve", ge=1, le=20
    )
    score_threshold: Optional[float] = Field(
        default=None, description="Minimum similarity score threshold (0-1)", ge=0, le=1
    )


class DocumentSearchResult(BaseModel):
    """Output schema for document search results."""

    content: str = Field(description="Document content")
    metadata: Dict[str, Any] = Field(description="Document metadata")
    similarity_score: Optional[float] = Field(
        description="Similarity score (0-1, higher is better)", ge=0, le=1
    )


def document_search_impl(inputs: Optional[Dict[str, Any]] = None, **kwargs: Any) -> List[DocumentSearchResult]:
    """
    Search for relevant documents using the retrieval system.

    Args:
        inputs: Dictionary containing search parameters (can be provided as a single dict positional argument)
        **kwargs: Alternative way to pass individual parameters

    Returns:
        List of relevant documents with metadata and scores
    """
    # Support both a single dict argument and keyword arguments
    merged_inputs: Dict[str, Any] = {}
    if inputs is not None:
        if not isinstance(inputs, dict):
            raise TypeError("inputs must be a dict if provided")
        merged_inputs.update(inputs)
    if kwargs:
        merged_inputs.update(kwargs)

    # Parse inputs
    search_input = DocumentSearchInput(**merged_inputs)

    # Initialize retrieval system (assuming data directory)
    data_dir = "data/documents"  # Default data directory
    retrieval_system = RetrievalSystem(data_dir=data_dir)

    # Query the retrieval system
    documents = retrieval_system.query_vector_store(
        query=search_input.query, k=search_input.k
    )

    # Format results
    results = []
    for doc in documents:
        # Extract similarity score if available
        similarity_score = None
        if hasattr(doc, "metadata") and "score" in doc.metadata:
            similarity_score = doc.metadata["score"]

        result = DocumentSearchResult(
            content=doc.page_content,
            metadata=doc.metadata or {},
            similarity_score=similarity_score,
        )
        results.append(result)

    return results


# Create the LangChain tool
document_search_tool = StructuredTool.from_function(
    func=document_search_impl,
    name="document_search",
    description="""Search for relevant documents using semantic similarity and BM25 retrieval.
    
    This tool can find documents based on:
    - Natural language queries
    - Semantic similarity using embeddings
    - BM25 keyword matching
    - Configurable similarity thresholds
    
    The tool uses a hybrid retrieval approach combining dense vector search
    with sparse keyword matching for comprehensive document discovery.
    
    Returns up to 20 documents with relevance scores and metadata.""",
    args_schema=DocumentSearchInput,
)
