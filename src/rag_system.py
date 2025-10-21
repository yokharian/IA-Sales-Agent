from typing import Optional

from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.retrievers import (
    ContextualCompressionRetriever,
)
from langchain_classic.retrievers.document_compressors import (
    EmbeddingsFilter,
    DocumentCompressorPipeline,
    LLMChainExtractor,
)
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import CharacterTextSplitter

from settings import EMBEDDING_FUNCTION, SYSTEM_PROMPT
from .document_loader import DocumentLoader
from .retrieval_system import RetrievalSystem


class RAGSystem:
    """
    Retrieval-Augmented Generation system that
    Loads documents and Builds embeddings
    """

    def __init__(
        self,
        data_dir: str,
        llm: Optional[BaseChatModel] = None,
        embedding_function=EMBEDDING_FUNCTION,
        system_prompt=SYSTEM_PROMPT,
    ):
        self.retrieval_system: Optional[RetrievalSystem] = None
        self.embedding_function = embedding_function
        self.initialize_vector_database(data_dir)
        self._llm = llm
        self.system_prompt = system_prompt

    def initialize_vector_database(self, data_dir) -> None:
        """Load documents, create embeddings."""
        loader = DocumentLoader(data_dir)
        documents = loader.load_documents()
        self.retrieval_system = RetrievalSystem(
            documents=documents,
            embedding_function=self.embedding_function,
            score_threshold=None,
        )

    @property
    def retriever(self):
        return self.retrieval_system.retriever

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

        # 4. Generate DocumentCompressorPipeline object using splitter, redundant_filter, relevant_filter, and LLMChainExtractor
        pipeline_compressor = DocumentCompressorPipeline(transformers=transformers)

        # 5. Use pipeline_compressor as the base_compressor and retriever as the base_retriever to initialize ContextualCompressionRetriever
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor,
            base_retriever=self.retriever,
        )
        return compression_retriever

    def query(self, query: str, llm: Optional[BaseChatModel] = None):

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}"),
            ]
        )
        qa_chain = create_stuff_documents_chain(llm, prompt)
        chain = create_retrieval_chain(self.retriever, qa_chain)

        return chain.invoke({"input": query})
