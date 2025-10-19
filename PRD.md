# Product Requirements Document: OpenAI RAG System

## 1. Product Overview

### 1.1 Purpose

The OpenAI RAG (Retrieval-Augmented Generation) System is a Python-based application that enables users to query their local document collections using natural language. The system combines document retrieval with OpenAI's language models to provide accurate, context-aware answers based on the user's own documents.

### 1.2 Target Users

- **Developers**: Building knowledge-based applications and custom Q&A systems
- **Business**: Organizations needing to query proprietary documents and knowledge bases
- **Organizations**: Companies wanting to implement document-based AI assistants

### 1.3 Value Proposition

Query local documents with natural language instead of manually searching through documents or relying on generic AI responses. Users receive answers grounded in their specific document collection, reducing hallucinations and ensuring factual accuracy.

## 2. Core Features

### 2.1 Document Management

- **Document Loading**: Automatically loads all `.txt` files from the `data/documents/` directory
- **Text Chunking**: Splits documents into manageable chunks (default 1000 characters) for efficient processing
- **File Format**: Currently supports plain text files (.txt)

### 2.2 Embedding System

- **OpenAI Integration**: Uses OpenAI's `text-embedding-3-large` model for creating vector embeddings
- **Batch Processing**: Processes multiple documents and creates embeddings for each chunk
- **Vector Storage**: Stores embeddings in memory using NumPy arrays

### 2.3 Retrieval System

- **Similarity Search**: Uses cosine similarity to find relevant document chunks
- **Top-K Retrieval**: Returns the 3 most relevant chunks by default (configurable)
- **Ranking**: Sorts results by relevance score

### 2.4 Question Answering

- **Natural Language Queries**: Accepts questions in plain English
- **Context-Aware Responses**: Uses retrieved chunks as context for GPT-4o
- **Model Configuration**: Powered by `gpt-4o` with Top-p=0 and Temperature=0.7

## 3. Technical Architecture

### 3.1 Components

- **`DocumentLoader`**: Handles file I/O and document ingestion from `data/documents/`
- **`TextProcessor`**: Manages text chunking with configurable chunk sizes (default: 1000 chars)
- **`EmbeddingsManager`**: Interfaces with OpenAI's embedding API using `text-embedding-3-large`
- **`RetrievalSystem`**: Implements cosine similarity search and top-k ranking
- **`RAGSystem`**: Orchestrates all components into a unified system

### 3.2 Dependencies

- `openai`: OpenAI API client for embeddings and chat completions
- `python-dotenv`: Environment variable management
- `langchain-huggingface`: Additional language model support

### 3.3 Configuration

- Environment variables managed via `.env` file
- Required: `OPENAI_API_KEY`

### 3.4 Data Flow

1. Documents loaded from `data/documents/` → `DocumentLoader`
2. Text chunked (1000 chars) → `TextProcessor`
3. Chunks embedded using `text-embedding-3-large` → `EmbeddingsManager`
4. User query embedded → `EmbeddingsManager`
5. Similar chunks retrieved (top-3) → `RetrievalSystem`
6. Context + query sent to `gpt-4o` → Response generated

## 4. Current Limitations

### 4.1 Performance Issues

- Large documents may take significant time to process due to API rate limits
- High memory usage with extensive document collections
- No caching mechanism for embeddings (reprocesses on each run)

### 4.2 Feature Limitations

- Limited to text files only (.txt)
- In-memory storage only (no persistence layer)
- No error handling for API failures
- Sequential embedding creation (no batching optimization)

### 4.3 Scalability Constraints

- In-memory storage limits maximum document size
- No database integration for production use
- No multi-user support or access control

## 5. Future Enhancements

### 5.1 Priority 1 (Essential)

- **Embedding Caching**: Store embeddings to disk to avoid reprocessing
- **Multiple File Formats**: Support PDF, DOCX, Markdown, etc.
- **Error Handling**: Robust error handling for API failures and network issues
- **Batch Embedding**: Process multiple chunks in single API call

### 5.2 Priority 2 (Important)

- **Vector Database**: Integrate with ChromaDB for production use
- **Configurable Parameters**: Expose chunk size, top-k, models as config options
- **Document Metadata**: Track source files and citations

### 5.3 Priority 3 (Nice-to-Have)

- **Advanced Chunking**: Semantic chunking instead of fixed-size
- **Unit & Integration Testing**: Comprehensive test suite

## 6. Success Metrics

### 6.1 Quality Metrics

- **Accuracy**: % of correct factual responses (human-audited)
- **Hallucination Rate**: % of responses containing inventions or unverifiable data
- **Context Relevance**: % of responses properly grounded in retrieved documents

### 6.2 Performance Metrics

- **Latency**: Average response time (target < 2s for internal processing, < 5s total)

### 6.3 Business Metrics

- **Tool Usage**: % of interactions where the LLM called deterministic tools
- **Conversion Proxy**: Contact requests/leads generated per session
- **Conversation Completion Rate**: User satisfied vs. drop-offs
- **Cost Metrics**: Tokens per session, cost per session

## 7. Technical Requirements

### 7.1 Environment

- Python 3.8+
- OpenAI API key with sufficient credits
- Unix-based system
- Adequate RAM for document collection size

### 7.2 API Requirements

- Access to OpenAI's embedding API (`text-embedding-3-large`)
- Access to GPT-4o API (or fallback to GPT-3.5)
- Sufficient API rate limits for expected usage

## 8. Security & Privacy

### 8.1 Current State

- No data encryption at rest
- Documents processed via OpenAI API (subject to OpenAI's privacy policy)

### 8.2 Recommendations

- Implement local encryption for sensitive documents
- Consider self-hosted embedding models for private data
- Add access control for multi-user scenarios
- Audit logging for document access and queries
- Data retention policies for document storage

## 9. Documentation & Support

### 9.1 Current Documentation

- Empty README file

### 9.2 Needed Documentation

- Simple architecture diagram
- Troubleshooting guide
- Deployment instructions

_This PRD is based on the current scope and should be updated as the product evolves._
