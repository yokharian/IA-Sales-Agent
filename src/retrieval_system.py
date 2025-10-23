from __future__ import annotations

from typing import List
from typing import Optional

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.retrievers import (
    ContextualCompressionRetriever,
)
from langchain_classic.retrievers import (
    EnsembleRetriever,
)
from langchain_classic.retrievers.document_compressors import (
    EmbeddingsFilter,
    DocumentCompressorPipeline,
    LLMChainExtractor,
)
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_text_splitters import CharacterTextSplitter

from settings import EMBEDDING_FUNCTION, SYSTEM_PROMPT
from .document_loader import DocumentLoader


class RAGSystem:

    def __init__(
        self,
        data_dir: str,
        llm: Optional[BaseChatModel] = None,
        embedding_function=EMBEDDING_FUNCTION,
        system_prompt=SYSTEM_PROMPT,
    ):
        self._retriever = None
        self._bm25_retriever = None
        self._ensemble_retriever = None
        self._vector_store_retriever = None
        self._llm = llm

        self.vector_store = None
        self.data_dir = data_dir
        self.system_prompt = system_prompt
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
        # Initialize the (Sparse) BM25 retriever and (Dense) Chroma retriever.
        self._bm25_retriever = BM25Retriever.from_documents(self.documents)
        # Retrieve the top K documents with the highest similarity.
        self._bm25_retriever.k = 3

        # Configurar retriever con MMR y umbral de puntuación
        search_kwargs = {"k": k, "fetch_k": fetch_k, "lambda_mult": lambda_mult}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter

        if score_threshold is not None:
            self._vector_store_retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={
                    **search_kwargs,
                    "score_threshold": score_threshold,
                },
            )
        else:
            self._vector_store_retriever = self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs=search_kwargs,
            )

        # initialize the ensemble retriever
        self._ensemble_retriever = EnsembleRetriever(
            retrievers=[self._bm25_retriever, self._vector_store_retriever],
            weights=[0.7, 0.3],
        )

        self._retriever = self._ensemble_retriever

    def document_compression_retriever(self, similarity_threshold):
        splitter = CharacterTextSplitter(
            chunk_size=300, chunk_overlap=0, separator=". "
        )
        redundant_filter = EmbeddingsRedundantFilter(embeddings=self.embedding_function)
        relevant_filter = EmbeddingsFilter(
            embeddings=self.embedding_function,
            similarity_threshold=similarity_threshold,
        )

        transformers = [
            splitter,
            redundant_filter,
            relevant_filter,
        ]
        transformers += [LLMChainExtractor.from_llm(self._llm)]

        pipeline_compressor = DocumentCompressorPipeline(transformers=transformers)

        return ContextualCompressionRetriever(
            base_compressor=pipeline_compressor,
            base_retriever=self.retriever,
        )
