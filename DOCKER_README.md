# Docker Setup for Commercial Agent

This document explains how to run the Commercial Agent using Docker.

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. **Environment variables** configured (see below)

## Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration (optional, defaults are provided)
DATABASE_URL=postgresql://postgres:password@db:5432/commercial_agent
```

## Quick Start

### Option 1: Using Docker directly (Recommended)

1. **Build the image:**
   ```bash
   docker build -t commercial-agent .
   ```

2. **Run with environment variables:**
   ```bash
   docker run -p 5000:5000 \
     -e TWILIO_ACCOUNT_SID=your_sid \
     -e TWILIO_AUTH_TOKEN=your_token \
     -e TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890 \
     -e OPENAI_API_KEY=your_openai_key \
     commercial-agent
   ```

### Option 2: Using Docker Compose

1. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

2. **Build and start the services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - WhatsApp webhook: `http://localhost:5000/whatsapp/webhook`
   - Health check: `http://localhost:5000/health`
   - API docs: `http://localhost:5000/docs`

## What Happens During Startup

1. **CSV Ingestion**: The container first runs the CSV ingestion script to populate the database with vehicle data
2. **Database Setup**: Creates necessary tables and indexes
3. **WhatsApp Server**: Starts the FastAPI server with WhatsApp webhook endpoints

## Container Features

- **Automatic CSV Ingestion**: Runs `scripts/ingest_csv.py` on startup
- **Health Checks**: Built-in health monitoring
- **Error Handling**: Fails fast if CSV ingestion fails
- **Logging**: Comprehensive logging to stdout and files
- **Database Integration**: PostgreSQL with persistent volumes

## Troubleshooting

### CSV Ingestion Fails
- Check that `data/sample_vehicles.csv` exists
- Verify database connection
- Check logs: `docker-compose logs commercial-agent`

### WhatsApp Webhook Issues
- Ensure Twilio webhook URL points to: `http://your-domain:5000/whatsapp/webhook`
- Verify Twilio credentials are correct
- Check that the server is accessible from the internet

### Database Connection Issues
- Ensure PostgreSQL container is running: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify environment variables

## Development

### Accessing the Database
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d commercial_agent

# Or use a GUI tool with:
# Host: localhost
# Port: 5432
# Database: commercial_agent
# Username: postgres
# Password: password
```

## Production Deployment

For production deployment:

1. **Use environment-specific configuration**
2. **Set up proper secrets management**
3. **Configure reverse proxy (nginx)**
4. **Set up SSL/TLS certificates**
5. **Configure monitoring and alerting**
6. **Use production database with proper backup strategy**

## API Endpoints

- `GET /health` - Health check
- `POST /whatsapp/webhook` - WhatsApp webhook (Twilio)
- `GET /whatsapp/webhook` - WhatsApp webhook verification
- `POST /send-message` - Send WhatsApp message via API
- `GET /docs` - API documentation (Swagger)
- `GET /redoc` - Alternative API documentation
