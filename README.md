# Local RAG System (ChromaDB + HuggingFace)

A lightweight Python Retrieval-Augmented Generation (RAG) helper that lets you query your local document collection using natural language. It builds embeddings with HuggingFace and performs similarity search with ChromaDB to return the most relevant context for your query.

## 🌟 Features

- Document loading from a local folder (.txt and .md supported)
- Smart chunking with LangChain's RecursiveCharacterTextSplitter
- Local embeddings via HuggingFace (all-MiniLM-L6-v2)
- Fast similarity search using ChromaDB
- Minimal API surface and easy-to-read code

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd commercial-agent
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Add your documents:
   Place your `.txt` or `.md` files in the `data/documents/` directory.

5. Run a quick test:
   ```bash
   python test.py
   ```

## 📁 Project Structure

```
commercial-agent/
│
├── src/
│   ├── __init__.py
│   ├── document_loader.py    # Loads and chunks local documents
│   ├── retrieval_system.py   # ChromaDB vector store + similarity search
│   └── rag_system.py         # Orchestration and simple query interface
│
├── data/
│   └── documents/            # Place your .txt or .md files here
│
├── docs/
│   └── prd.md                # Product Requirements Document
│
├── requirements.txt
├── test.py
└── README.md
```

## 💻 Usage

Basic example to retrieve relevant context for a question:

```python
from src.rag_system import RAGSystem

# Initialize the RAG system (defaults to data/documents)
rag = RAGSystem()

# Get context for your query from top-2 similar chunks
question = "What is the Beta Eco Initiative?"
context = rag.obtain_knowledge_base(question)
print(context)
```

## ⚙️ Configuration

- Data folder: defaults to `data/documents` (can be changed via `RAGSystem(data_dir=...)`).
- Chunking: defaults to `chunk_size=500`, `chunk_overlap=100` (see DocumentLoader.load_documents).
- Embeddings: HuggingFace model `all-MiniLM-L6-v2` with normalized embeddings (see retrieval_system.py).
- Retrieval: returns top-2 most similar chunks by relevance score.

Note: An optional environment variable `OPENAI_MODEL` is read by `RAGSystem` but is not required for current functionality (no OpenAI API calls are made).

## 🔧 How It Works

1. Documents are loaded from `data/documents` (supports .txt and .md, skips hidden files)
2. Text is chunked using RecursiveCharacterTextSplitter (default 500/100)
3. Each chunk is embedded with HuggingFace (all-MiniLM-L6-v2)
4. ChromaDB performs similarity search to find the most relevant chunks for a query
5. The selected chunks are concatenated and returned as a context string

## 📊 Defaults

- Chunk size: 500 characters
- Chunk overlap: 100 characters
- Retrieval: Top-2 chunks
- Embeddings: all-MiniLM-L6-v2 (local, downloaded via HuggingFace if not cached)

## ⚠️ Current Limitations

- ChromaDB index is persisted to data/chroma; repeated runs may append duplicate chunks if documents are re-ingested
- No caching: embeddings are recreated on each run
- This repo does not generate an LLM answer; it returns the most relevant context

## 🔒 Security & Privacy

- No API keys are required for core functionality
- HuggingFace model files may be downloaded to your environment when first used
- Documents are processed locally; review your environment security for sensitive data

## 📚 Documentation

- Product Requirements Document: [docs/prd.md](docs/prd.md)
- LangChain Documentation: https://python.langchain.com/docs/introduction/

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- HuggingFace and ChromaDB for open-source tooling
- The open-source community for inspiration and utilities
