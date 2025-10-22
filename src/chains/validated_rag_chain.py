"""
Validated RAG Chain implementation with fact-checking integration.

This module provides a custom LangChain-compatible chain that combines
retrieval, generation, and fact-checking in a single pipeline.
"""

from typing import Dict, Any, List, Optional, Union
from langchain_core.language_models import BaseLanguageModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain.chains import LLMChain

from .prompts import vehicle_rag_prompt, VEHICLE_RAG_CHAT_PROMPT
from ..tools.fact_checker import FactChecker


class ValidatedRAGChain:
    """
    A RAG chain that validates generated responses against the database.

    This chain combines retrieval, generation, and fact-checking to ensure
    that LLM responses are accurate and grounded in the provided context.
    """

    def __init__(
        self,
        llm: BaseLanguageModel,
        retriever: BaseRetriever,
        fact_checker: Optional[FactChecker] = None,
        use_chat_prompt: bool = True,
        enable_fact_checking: bool = True,
    ):
        """
        Initialize the ValidatedRAGChain.

        Args:
            llm: Language model for generation
            retriever: Retriever for document retrieval
            fact_checker: FactChecker instance for validation
            use_chat_prompt: Whether to use chat prompt format
            enable_fact_checking: Whether to enable fact-checking
        """
        self.llm = llm
        self.retriever = retriever
        self.fact_checker = fact_checker
        self.use_chat_prompt = use_chat_prompt
        self.enable_fact_checking = enable_fact_checking

        # Set up the prompt
        if use_chat_prompt:
            self.prompt = VEHICLE_RAG_CHAT_PROMPT
        else:
            self.prompt = vehicle_rag_prompt

    def _retrieve_context(self, question: str) -> tuple[List[Document], str]:
        """
        Retrieve relevant documents and format as context.

        Args:
            question: User question

        Returns:
            Tuple of (documents, formatted_context)
        """
        # Retrieve relevant documents
        documents = self.retriever.invoke(question)

        # Format context from documents
        context_parts = []
        for doc in documents:
            # Include document content and metadata
            content = doc.page_content
            metadata = doc.metadata

            # Add stock_id if available
            if "stock_id" in metadata:
                content = f"[Stock ID: {metadata['stock_id']}] {content}"

            context_parts.append(content)

        formatted_context = "\n\n".join(context_parts)

        return documents, formatted_context

    def _generate_response(self, context: str, question: str) -> str:
        """
        Generate response using the LLM and prompt.

        Args:
            context: Retrieved context
            question: User question

        Returns:
            Generated response text
        """
        if self.use_chat_prompt:
            # Use chat prompt format
            messages = self.prompt.format_messages(context=context, question=question)
            response = self.llm.invoke(messages)

            # Extract content from response
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)
        else:
            # Use regular prompt format
            chain = LLMChain(llm=self.llm, prompt=self.prompt)
            response = chain.run(context=context, question=question)
            return response

    def _validate_response(self, response: str, context: str) -> Dict[str, Any]:
        """
        Validate the generated response using fact-checking.

        Args:
            response: Generated response text
            context: Retrieved context

        Returns:
            Validation results
        """
        if not self.enable_fact_checking or not self.fact_checker:
            return {
                "validated": True,
                "fact_check_results": [],
                "validation_summary": "Fact-checking disabled",
            }

        # Use the fact checker to validate the response
        validation_results = self.fact_checker.verify_text(response)

        return {
            "validated": validation_results["valid"],
            "fact_check_results": validation_results["verifications"],
            "validation_summary": validation_results["summary"],
            "claims_found": validation_results["claims_found"],
            "valid_claims": validation_results["valid_claims"],
            "invalid_claims": validation_results["invalid_claims"],
        }

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the chain with input data.

        Args:
            inputs: Dictionary containing 'question' key

        Returns:
            Dictionary with response, documents, and validation results
        """
        question = inputs.get("question", "")

        if not question:
            raise ValueError("Question is required")

        # Step 1: Retrieve context
        documents, context = self._retrieve_context(question)

        # Step 2: Generate response
        response = self._generate_response(context, question)

        # Step 3: Validate response (if enabled)
        validation_results = self._validate_response(response, context)

        # Return comprehensive results
        return {
            "question": question,
            "response": response,
            "context": context,
            "source_documents": documents,
            "validation_results": validation_results,
            "metadata": {
                "num_documents": len(documents),
                "context_length": len(context),
                "response_length": len(response),
                "fact_checking_enabled": self.enable_fact_checking,
            },
        }

    def run(self, question: str) -> Dict[str, Any]:
        """
        Run the chain with a question string.

        Args:
            question: User question

        Returns:
            Dictionary with response and validation results
        """
        return self.invoke({"question": question})

    def __call__(self, inputs: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make the chain callable.

        Args:
            inputs: Question string or input dictionary

        Returns:
            Chain results
        """
        if isinstance(inputs, str):
            return self.run(inputs)
        else:
            return self.invoke(inputs)


def create_validated_rag_chain(
    llm: BaseLanguageModel,
    retriever: BaseRetriever,
    fact_checker: Optional[FactChecker] = None,
    use_chat_prompt: bool = True,
    enable_fact_checking: bool = True,
) -> ValidatedRAGChain:
    """
    Factory function to create a ValidatedRAGChain.

    Args:
        llm: Language model for generation
        retriever: Retriever for document retrieval
        fact_checker: FactChecker instance for validation
        use_chat_prompt: Whether to use chat prompt format
        enable_fact_checking: Whether to enable fact-checking

    Returns:
        Configured ValidatedRAGChain instance
    """
    return ValidatedRAGChain(
        llm=llm,
        retriever=retriever,
        fact_checker=fact_checker,
        use_chat_prompt=use_chat_prompt,
        enable_fact_checking=enable_fact_checking,
    )


# Export the main class and factory function
__all__ = ["ValidatedRAGChain", "create_validated_rag_chain"]
