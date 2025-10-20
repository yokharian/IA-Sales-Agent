from src.rag_system import RAGSystem
from src.document_loader import DocumentLoader
from pprint import pprint


assert len(DocumentLoader("data/documents").load_documents()) == 6

# Initialize the RAG system
rag = RAGSystem()

knowledge_base = rag.obtain_knowledge_base(query="What is the Beta Eco Initiative?")
pprint(knowledge_base)
