# Product Requirements Document: Commercial Agent

**Version:** 2.0  
**Date:** October 23, 2025  
**Status:** Active Development

---

## Executive Summary

Commercial Agent is an AI-powered vehicle sales assistant that combines intelligent conversation, semantic search, and structured data retrieval to help customers find and learn about vehicles. Built with LangChain's ReAct framework, it provides WhatsApp integration, fuzzy matching for typo tolerance, and comprehensive vehicle catalog search capabilities.

---

## 1. Product Overview

### 1.1 Purpose

Deliver an intelligent, conversational AI agent that:
- Helps customers discover vehicles from a catalog with natural language queries
- Handles typos and fuzzy inputs gracefully (e.g., "toyata" → "toyota")
- Provides accurate, verifiable information from documents using RAG
- Integrates seamlessly with WhatsApp for real-world customer engagement
- Minimizes hallucinations through structured tool calls

### 1.2 Target Users

- **Primary**: Car buyers interacting via WhatsApp
- **Secondary**: Sales teams using the system for customer support
- **Tertiary**: Developers integrating the system into existing platforms

### 1.3 Value Proposition

- **Customer Experience**: Natural, conversational vehicle search in Spanish/English
- **Accuracy**: Structured database queries prevent AI hallucinations
- **Accessibility**: WhatsApp integration reaches customers where they are
- **Scalability**: Serverless-ready FastAPI architecture
- **Maintainability**: Clean separation of tools, agents, and data layers

---

## 2. Technical Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   WhatsApp   │  │     CLI      │  │   FastAPI    │       │
│  │   (Twilio)   │  │   Terminal   │  │     Docs     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer (LangChain)                  │
│  ┌────────────────────────────────────────────────────┐     │
│  │  VehicleAssistantAgent (ReAct Framework)           │     │
│  │  - Intent understanding                            │     │
│  │  - Tool selection & invocation                     │     │
│  │  - Response synthesis                              │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│   catalog_search_tool   │  │  document_search_tool   │
│                         │  │                         │
│  - Fuzzy make/model     │  │  - Semantic search      │
│  - Price/feature filter │  │  - RAG retrieval        │
│  - PostgreSQL queries   │  │  - ChromaDB vectors     │
└─────────────────────────┘  └─────────────────────────┘
                │                       │
                ▼                       ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│   PostgreSQL Database   │  │   ChromaDB VectorStore  │
│                         │  │                         │
│  - Vehicle catalog      │  │  - Document embeddings  │
│  - SQLModel ORM         │  │  - HuggingFace vectors  │
└─────────────────────────┘  └─────────────────────────┘
```

### 2.2 Data Flow

#### Vehicle Search Flow
```
1. User: "busco un Toyota con bluetooth bajo 300k"
   ↓
2. Agent: Analyzes intent → select catalog_search_tool
   ↓
3. Tool: Fuzzy match "Toyota" → apply filters → query PostgreSQL
   ↓
4. Database: Returns matching vehicles (stock_id, price, features, etc.)
   ↓
5. Tool: Formats results as VehicleResult objects
   ↓
6. Agent: Synthesizes natural response
   ↓
7. User: Receives: "Encontré 3 vehículos Toyota con Bluetooth..."
```

#### Document Search Flow
```
1. User: "¿Qué documentos necesito para comprar?"
   ↓
2. Agent: Analyzes intent → select document_search_tool
   ↓
3. Tool: Embeds query → semantic search in ChromaDB
   ↓
4. VectorStore: Returns top-K similar document chunks
   ↓
5. Tool: Formats as DocumentResult with content & metadata
   ↓
6. Agent: Synthesizes answer from retrieved context
   ↓
7. User: Receives: "Para comprar necesitas: [lista de documentos]"
```

---

## 3. Core Features

### 3.1 Vehicle Catalog Search

**Tool:** `catalog_search_tool`

**Capabilities:**
- Fuzzy matching for make/model (80% similarity threshold)
- Budget filtering (min/max price)
- Mileage filtering (max kilometers)
- Feature filtering (Bluetooth, CarPlay, etc.)
- Sorting options (price, year, mileage)
- Returns up to 20 results per query

**See:** [catalog_search_prd.md](catalog_search_prd.md) for detailed specifications

### 3.2 Document Search

**Tool:** `document_search_tool`

**Capabilities:**
- Semantic similarity search using HuggingFace embeddings
- Returns top-K most relevant document chunks
- Includes source metadata (filename, chunk index)
- Supports .txt and .md files
- Normalized embeddings for better cosine similarity

**See:** [document_search_prd.md](document_search_prd.md) for detailed specifications

### 3.3 CSV Data Ingestion

**Script:** `scripts/ingest_csv.py`

**Capabilities:**
- Batch processing with configurable batch size
- Data normalization (lowercase, accent removal)
- Boolean field mapping (Sí/No → True/False)
- Comprehensive error logging
- SQLModel-based type safety

**See:** [csv_ingestion.md](csv_ingestion.md) for detailed guide

### 3.4 WhatsApp Integration

**Server:** `src/whatsapp_server.py` (FastAPI)

**Capabilities:**
- Bidirectional WhatsApp messaging via Twilio
- Webhook handling for incoming messages
- TwiML response generation
- Message length management (1600 char limit)
- Health check endpoint

**See:** [whatsapp_setup.md](whatsapp_setup.md) for setup guide

### 3.5 AI Agent

**Class:** `VehicleAssistantAgent`

**Framework:** LangChain ReAct (Reasoning and Acting)

**Model:** OpenAI GPT-4 (configurable)

**Features:**
- ReAct reasoning: Step-by-step problem solving
- Tool selection: Automatic tool choice
- Multi-turn conversations: Context maintenance
- Error recovery: Graceful failure handling
- Multilingual: Spanish and English support

**See:** [agents.md](agents.md) for agent development guidelines

---

## 5. Success Metrics (TBD)

### 5.1 Accuracy Metrics

- **Fuzzy Match Precision**: >95% correct make/model resolution
- **Search Relevance**: >90% user satisfaction on vehicle results
- **Document Relevance**: >85% answer accuracy from RAG retrieval
- **Hallucination Rate**: <1% (prevented by structured tools)

### 5.2 Performance Metrics

- **Response Time**: <3s end-to-end (95th percentile)
- **Tool Invocation Success**: >99%
- **Database Query Success**: >99.9%
- **WhatsApp Delivery Rate**: >98%

### 5.3 Usage Metrics

- **Daily Active Users**: Track via WhatsApp message volume
- **Queries per Session**: Measure engagement depth
- **Tool Usage Distribution**: catalog_search vs document_search
- **Error Rate**: Track tool failures and agent errors

---

## 6. Current Limitations

### 6.1 Known Issues

- **ChromaDB Duplicates**: Repeated document ingestion creates duplicate chunks
- **No Conversation Memory**: Each query is stateless
- **Limited Feature Extraction**: Only Bluetooth and CarPlay in sample data
- **Single Language Model**: No fallback if OpenAI unavailable

### 6.2 Scope Exclusions (MVP)

- Finance calculator (monthly payment, interest)
- Image recognition (vehicle photos)
- Voice message support
- Multi-user conversation tracking
- Advanced recommendation ranking (ML-based)
- Integration with external CRM systems

---

## 7. Testing Strategy

### 7.1 Unit Tests

- CSV parsing and normalization
- Fuzzy matching algorithms
- Data access layer (DAO)
- Tool input/output schemas
- Pydantic model validation

### 7.2 Integration Tests

- End-to-end agent workflows
- Tool invocation and response handling
- Database queries and transactions
- WhatsApp message flow (mocked Twilio)

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM Hallucinations | High | Use structured tools; prevent free-form assertions |
| Poor Fuzzy Matches | Medium | Combine token-based + semantic similarity |
| Database Downtime | High | Connection pooling; retry logic; fallback mode |
| Twilio Rate Limits | Medium | Queue messages; respect rate limits |
| Cost Overruns (OpenAI) | Medium | Monitor usage; implement caching |
| Data Privacy Issues | High | No PII logging; secure credential management |

---

## 9. Acceptance Criteria (TBD)

### 9.1 Vehicle Search

✅ System ingests and indexes all CSV rows  
✅ Query "busco Touareg 2018 con bluetooth y presupuesto 500k" returns stock_id 243587 in top-3  
✅ Fuzzy match "toyata" → "toyota" with >90% accuracy  
✅ Filter by price, km, and features returns correct results  
✅ Sorting by price/year/km works correctly  

### 9.2 Document Search

✅ RAG retrieval returns relevant chunks for "¿Qué documentos necesito?"  
✅ Semantic search accuracy >85% on test queries  
✅ Top-K results include source metadata  

### 9.3 WhatsApp Integration

✅ Webhook receives and processes incoming messages  
✅ Agent responds with relevant vehicle information  
✅ Messages respect 1600 character limit  
✅ Health check endpoint returns 200 OK  

### 9.4 Agent Behavior

✅ ReAct agent selects appropriate tools  
✅ Multi-step reasoning works correctly  
✅ Error recovery graceful (tool failures don't crash agent)  
✅ Bilingual support (Spanish and English)  

---

## 10. Glossary

- **ReAct**: Reasoning and Acting framework for LLM agents
- **RAG**: Retrieval-Augmented Generation (semantic search + LLM)
- **Fuzzy Matching**: Approximate string matching with typo tolerance
- **Tool**: LangChain-compatible function that agent can invoke
- **TwiML**: Twilio Markup Language for message responses
- **DAO**: Data Access Object (database abstraction layer)
- **Vector Store**: Database for storing and querying embeddings

---

## Appendix: Example Queries

### Spanish Queries
- "Hola, busco un auto Toyota"
- "¿Tienes vehículos Honda disponibles?"
- "Necesito un carro con Bluetooth y CarPlay"
- "Busco un vehículo económico bajo 200 mil pesos"
- "¿Qué documentos necesito para comprar un auto en Kavak?"

### English Queries
- "Find me Toyota vehicles under $300,000"
- "I'm looking for a Honda Civic with low mileage"
- "Show me vehicles with Bluetooth and CarPlay features"
- "What's available in my budget of $250k?"

---

**Document Status**: Living document, updated as features are implemented  
**Last Updated**: October 23, 2025
