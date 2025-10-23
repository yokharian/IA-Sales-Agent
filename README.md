# 🚗 Commercial Agent - AI Vehicle Sales Assistant

An intelligent AI-powered vehicle sales assistant with WhatsApp integration, vector search capabilities, and fuzzy matching. Built with LangChain, PostgreSQL, and ChromaDB for production-ready automotive e-commerce.

![diagram.svg](docs/diagram.svg)

## 🌟 Features

- 🤖 **AI-Powered Agent**: ReAct framework with LangChain for intelligent conversations
- 📱 **WhatsApp Integration**: Bidirectional communication via Twilio
- 🔍 **Smart Vehicle Search**: Fuzzy matching with typo tolerance (rapidfuzz)
- 📄 **Document Search**: RAG-powered semantic search for automotive documentation
- 💾 **PostgreSQL Backend**: Robust vehicle catalog with SQLModel
- 🎯 **Feature Filtering**: Search by features, price, mileage, make, and model
- 🌐 **FastAPI Server**: Production-ready webhook handling

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+ (optional, for vehicle catalog)
- Twilio account (optional, for WhatsApp)
- OpenAI API key (for AI agent)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd commercial-agent
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

5. **Initialize the database (optional):**
   ```bash
   createdb commercial_agent
   python scripts/ingest_csv.py data/sample_vehicles.csv --create-tables
   ```

6. **Run the demo:**
   ```bash
   python demo.py --mode interactive
   ```

## 📁 Project Structure

```
commercial-agent/
│
├── src/
│   ├── main.py                    # AI Agent with ReAct framework
│   ├── whatsapp_server.py         # FastAPI WhatsApp webhook server
│   ├── db/                        # Database layer
│   └── tools/                     # LangChain tools
│
├── scripts/
│   ├── ingest_csv.py              # CSV vehicle data ingestion
│   └── run_tests.sh               # Test runner
│
├── data/
│   ├── documents/                 # Documents for RAG
│   ├── sample_vehicles.csv        # Sample vehicle data
│   └── chroma/                    # ChromaDB vector store
│
├── docs/                          # Documentation
├── tests/                         # Test suite
├── demo.py                        # Interactive demo
└── requirements.txt
```

## 💻 Usage

### Interactive Chat

```bash
python demo.py --mode interactive
```

Example queries:
```
You: Find me Toyota vehicles under $300,000
You: I'm looking for a Honda with Bluetooth and CarPlay
You: ¿Tienes vehículos Volkswagen disponibles?
```

### WhatsApp Server

```bash
python src/whatsapp_server.py --host 0.0.0.0 --port 5000
```

Configure Twilio webhook URL: `http://your-server:5000/whatsapp/webhook`

### CSV Data Ingestion

```bash
python scripts/ingest_csv.py data/sample_vehicles.csv --batch-size 500 --create-tables
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with:

```bash
# OpenAI (Required)
OPENAI_API_KEY=sk-...

# Twilio (Optional, for WhatsApp)
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Database (Optional)
DATABASE_URL=postgresql://user:password@localhost:5432/commercial_agent
```

### Vector Search Settings

- **Embeddings**: HuggingFace `all-MiniLM-L6-v2`
- **Vector Store**: ChromaDB (persisted to `data/chroma/`)
- **Chunking**: 500 chars with 100 char overlap
- **Retrieval**: Top-K semantic search

### Fuzzy Matching

- **Engine**: rapidfuzz with token-based matching
- **Threshold**: 80% similarity score
- **Scope**: Make and model searches

## 🔧 How It Works

### Vehicle Search Flow
1. User query received (WhatsApp or CLI)
2. LangChain ReAct agent analyzes intent
3. Fuzzy matching normalizes make/model (handles typos)
4. PostgreSQL query filters by price, features, mileage
5. Results ranked and formatted
6. Response sent back to user

### Document Search Flow
1. Documents chunked and embedded (HuggingFace)
2. Stored in ChromaDB vector store
3. Semantic similarity search on user query
4. Relevant chunks retrieved and ranked
5. Context provided to agent for response generation

## 🧪 Testing

```bash
# Run all tests
python scripts/run_tests.sh

# Run specific test suites
pytest tests/test_catalog_search_tool.py -v
pytest tests/test_document_search_tool.py -v
```

## 📊 API Endpoints

When running the WhatsApp server:

- `POST /whatsapp/webhook` - Handle incoming WhatsApp messages
- `GET /health` - Health check endpoint
- `POST /send-message` - Send WhatsApp message programmatically
- `GET /docs` - FastAPI auto-generated documentation
- `GET /redoc` - ReDoc API documentation

## 📚 Documentation

Comprehensive documentation available in the `docs/` directory:

- [System Overview & Architecture](docs/MAIN_PRD.md)
- [AI Agent Guidelines](docs/agents.md)
- [Vehicle Catalog Search Tool](docs/catalog_search_prd.md)
- [Document Search Tool](docs/document_search_prd.md)
- [CSV Ingestion Guide](docs/csv_ingestion.md)
- [WhatsApp Setup Guide](docs/whatsapp_setup.md)
- [Documentation Index](docs/INDEX.md)

### External Resources
- [LangChain Documentation](https://python.langchain.com/docs/introduction/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Twilio WhatsApp API](https://www.twilio.com/docs/whatsapp)
- [ChromaDB Documentation](https://docs.trychroma.com/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain** for the agent framework and tool ecosystem
- **HuggingFace** for local embeddings and NLP models
- **ChromaDB** for vector storage
- **Twilio** for WhatsApp Business API
- **FastAPI** for modern API framework
- **RapidFuzz** for fuzzy matching capabilities
- The open-source community for inspiration and tools
