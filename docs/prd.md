# Product Requirements Document: Local RAG Helper (ChromaDB + HuggingFace)

## 1. Product Overview

### 1.1 Purpose

Provide a simple, local-first helper to retrieve the most relevant context from a user's document collection. The system builds embeddings using a local HuggingFace model and performs similarity search with ChromaDB to return the top matching chunks for a query. It intentionally does not call an LLM to generate answers; instead it returns the concatenated relevant context.

### 1.2 Target Users

- Developers who need a minimal, inspectable RAG building block
- Teams who want local context retrieval without external API calls
- Users preparing context to feed into their own LLM pipelines

### 1.3 Value Proposition

- Fast, local similarity search over your files
- No API keys required for core functionality
- Small, focused codebase built with LangChain primitives

## 2. Core Features

### 2.1 Document Management

- Loads `.txt` and `.md` files from `data/documents/`
- Deterministic file ordering and hidden file skipping
- Chunking via RecursiveCharacterTextSplitter (default: 500 chars, overlap: 100)

### 2.2 Embedding System

- HuggingFace embeddings: `all-MiniLM-L6-v2`
- Normalized embeddings for better cosine similarity behavior

### 2.3 Retrieval System

- ChromaDB collection persisted on disk at `data/chroma`
- Top-K retrieval (default K=2) with relevance scores

### 2.4 Output

- Returns a concatenated context string from the top-K chunks
- Intended to be piped into any downstream LLM if desired

## 3. Technical Architecture

### 3.1 Components

- `DocumentLoader`: File I/O and text chunking
- `RetrievalSystem`: ChromaDB store + similarity search
- `RAGSystem`: Orchestrates loading, indexing, and querying; exposes `obtain_knowledge_base(query)`

### 3.2 Dependencies

- `chromadb` for vector storage
- `langchain`, `langchain-community`, `langchain-huggingface`, `langchain-text-splitters`, `langchain-core`
- `numpy`

### 3.3 Configuration

- Optional: `OPENAI_MODEL` is read by `RAGSystem` but not required nor used for any API calls
- Data directory configurable via `RAGSystem(data_dir=...)`

### 3.4 Data Flow

1. Read files from `data/documents/` → `DocumentLoader`
2. Split into chunks (500/100) → `DocumentLoader`
3. Build ChromaDB collection with HuggingFace embeddings (persisted to `data/chroma`) → `RetrievalSystem`
4. Query similarity search (top-2) → `RetrievalSystem`
5. Concatenate selected chunks → `RAGSystem.obtain_knowledge_base`

## 4. Current Limitations

- ChromaDB collection persisted on disk at `data/chroma` (index grows with corpus; no deduplication across runs)
- No embedding caching
- No multi-user or access control features
- Does not generate natural-language answers (context only)

## 5. Future Enhancements

- Configurable persistence directory and collection management (prevent duplicates, custom collection names)
- Configurable chunking and retrieval parameters via config file / CLI
- Support for more input formats (PDF, DOCX) via LangChain loaders
- Optional LLM answering module using the retrieved context

## 6. Success Metrics

- Relevance quality (human-rated) of returned context
- End-to-end latency of loading + search on typical corpora
- Ease of integration into downstream pipelines

## 7. Technical Requirements

- Python 3.8+
- Network access to download HuggingFace model files on first run (if not cached)
- Sufficient RAM for the size of your corpus

## 8. Security & Privacy

- No external API calls for core retrieval
- Documents are processed locally
- Users should manage sensitive data according to their environment policies

## 9. Documentation & Support

- See README.md for setup and usage
- PRs/issues welcome to extend loaders, persistence, and configuration

_This PRD reflects the current implementation and should evolve with the product._
