from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains import create_retrieval_chain
from langchain_openai import ChatOpenAI

from src.rag_system import RAGSystem

LLM = ChatOpenAI(model="gpt-4o", temperature=0)
LLM_TURBO = ChatOpenAI(model="gpt-4o-turbo", temperature=0)


DATA_DIR = "data/documents"
QUERY = "What is the Beta Eco Initiative?"

# Initialize the RAG system
rag = RAGSystem(DATA_DIR)
respuesta = rag.query(QUERY)

print(respuesta)
