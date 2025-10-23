# PRD: Document Search Tool

**Version:** 1.0  
**Date:** October 23, 2025  
**Tool:** `document_search_tool`

---

## 1. Overview

LangChain tool for semantic document search using RAG (Retrieval-Augmented Generation). Enables finding relevant information through vector similarity.

### Purpose
- Search information in documentation (.txt, .md)
- Semantic similarity search with embeddings
- Return relevant chunks with context
- Prevent AI agent hallucinations

---

## 2. Technical Capabilities

### Vector Search
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2` (384 dims)
- **Vector Store:** ChromaDB (persisted to disk)
- **Similarity:** Cosine similarity with normalized embeddings
- **Performance:** <200ms per search

### Document Processing
| Parameter | Value | Description |
|-----------|-------|-------------|
| Chunk size | 500 chars | Fragment size |
| Chunk overlap | 100 chars | Overlap between chunks |
| Top-K | 3 (default) | Number of results |
| File types | .txt, .md | Supported formats |

---

## 3. Schemas

### Input Schema
- `query`: str (Required) - Natural language query
- `k`: int (Default: 3) - Number of chunks to return

### Output Schema
- `content`: str - Chunk text content
- `metadata`: Dict - Source filename, chunk index
- `score`: float - Similarity score (0-1, higher is better)

**Return Type:** List of DocumentResult (0-K items)

---

## 4. Usage Examples

### Typical Queries
| Query | Use Case |
|-------|----------|
| "What documents do I need to buy a car?" | Purchase requirements |
| "How does Kavak's financing work?" | Financing information |
| "vehicle maintenance information" | Maintenance |
| "How does the warranty work?" | Warranty policies |

---

## 5. Data Flow

```
1. User Query (natural language)
   ↓
2. Agent → document_search_tool
   ↓
3. Load documents from data/documents/
   ↓
4. Chunk documents (500/100)
   ↓
5. Generate embeddings (HuggingFace)
   ↓
6. Store in ChromaDB
   ↓
7. Embed query
   ↓
8. Similarity search (top-K)
   ↓
9. Format as DocumentResult[]
   ↓
10. Return to agent
```

---

## 6. Implementation Details

### Document Loading
- Uses `DocumentLoader` from `db.document_loader`
- Loads from `data/documents/` directory
- Supports .txt and .md files
- Skips hidden files

### Text Chunking
- Uses `RecursiveCharacterTextSplitter` from LangChain
- Chunk size: 500 characters
- Overlap: 100 characters
- Preserves document structure

### Vector Store
- ChromaDB for persistence
- Persisted to `data/chroma/`
- Normalized embeddings for better similarity
- Metadata includes source filename and chunk index

---

## 7. Document Structure

### Directory Layout
```
data/documents/
├── kavak.md              # Info about Kavak
├── financing.md          # Financing plans
├── requirements.txt      # Purchase requirements
└── warranty.md           # Warranty information
```

### Metadata
- `source`: Document filename
- `chunk_index`: Position in document
- `chunk_size`: Size of chunk
- `total_chunks`: Total chunks in document

---

## 8. Performance Targets (TBD)

| Metric | Target |
|---------|--------|
| Document loading | <2s (first time) |
| Embedding generation | <1s per document |
| Vector search | <200ms |
| Total tool latency | <500ms (cached) |
| Relevance accuracy | >85% |

---

## 9. Error Handling

### Error Cases
1. **No documents found:** Return empty list
2. **Invalid query:** Pydantic validation error
3. **ChromaDB error:** Log error, return empty list
4. **Embedding error:** Fallback to empty results

---

## 10. ChromaDB Storage

### Collection Schema
- `id`: Unique chunk identifier
- `embedding`: 384-dimensional vector
- `document`: Chunk text content
- `metadata`: Source filename, chunk index

### Persistence Structure
```
data/chroma/
├── chroma.sqlite3        # Metadata database
└── [collection-id]/      # Vector data
    ├── data_level0.bin
    ├── header.bin
    └── link_lists.bin
```

---

## 11. Current Limitations

- Only .txt and .md supported
- No support for PDF, DOCX
- Duplicates if documents are re-ingested
- No incremental updates
- No embedding caching
- No metadata filtering

---

## 12. Embedding Model

### all-MiniLM-L6-v2
- **Provider:** HuggingFace sentence-transformers
- **Dimensions:** 384
- **Max sequence length:** 256 tokens
- **Performance:** 14,200 sentences/sec (GPU)
- **Size:** ~80MB
- **License:** Apache 2.0

**Advantages:**
- Fast and efficient
- Good quality for Spanish/English
- Runs on CPU
- Open source

**Disadvantages:**
- Limited to 256 tokens per chunk
- Not optimized for automotive domain

---

## 13. Document Guidelines

### Recommended Format
- Clear document titles
- Hierarchical structure with headers
- Short paragraphs (<500 characters)
- Bullet points for lists
- Keywords for better search

### Best Practices
1. Use markdown headers (# ## ###)
2. Keep paragraphs concise
3. Avoid complex tables
4. Include relevant keywords
5. Structure content logically

---

## 14. Testing Strategy

### Unit Tests
- Document loading
- Semantic search accuracy
- Result relevance ranking
- Metadata integrity

### Integration Tests
- End-to-end document search with agent
- Query-response accuracy
- Error handling scenarios

---

**File:** `src/tools/document_search.py`  
**Storage:** ChromaDB in `data/chroma/`  
**Documents:** `data/documents/`  
**Testing:** `tests/test_document_search_tool.py`
