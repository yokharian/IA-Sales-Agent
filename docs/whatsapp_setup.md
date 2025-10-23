# WhatsApp Vehicle Assistant Setup

## Overview
This implementation provides bidirectional WhatsApp communication using Twilio and integrates with the AI vehicle assistant agent.

## Features
- 🤖 **AI-Powered Responses**: Uses LangChain agent with ReAct framework
- 📱 **WhatsApp Integration**: Bidirectional communication via Twilio
- 🔍 **Vehicle Search**: Fuzzy search with typo tolerance
- 📄 **Document Search**: Semantic document retrieval
- 🌐 **Web Server**: Flask-based webhook handling

## Setup Instructions

### 1. Environment Variables
Create a `.env` file in the project root with the following variables:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Twilio Configuration for WhatsApp
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Database Configuration (if needed)
DATABASE_URL=postgresql://user:password@localhost:5432/vehicles
```

### 2. Twilio Setup
1. Create a Twilio account at https://www.twilio.com
2. Get your Account SID and Auth Token from the Twilio Console
3. Set up WhatsApp Sandbox or get WhatsApp Business API access
4. Note your WhatsApp number (format: whatsapp:+1234567890)

### 3. Running the Application

#### Demo Mode (No API keys required)
```bash
python main.py --mode whatsapp-demo
```

#### WhatsApp Server Mode
```bash
python main.py --mode whatsapp-server --host 0.0.0.0 --port 5000
```

#### With Debug Mode
```bash
python main.py --mode whatsapp-server --debug
```

### 4. Webhook Configuration
1. Start the server: `python main.py --mode whatsapp-server`
2. Note the webhook URL: `http://your-server:5000/whatsapp/webhook`
3. Configure this URL in your Twilio WhatsApp settings
4. The server will handle incoming messages automatically

## API Endpoints

### Webhook Endpoint
- **URL**: `/whatsapp/webhook`
- **Method**: POST
- **Purpose**: Handle incoming WhatsApp messages

### Health Check
- **URL**: `/health`
- **Method**: GET
- **Purpose**: Check server status

### Send Message API
- **URL**: `/send-message`
- **Method**: POST
- **Body**: `{"to_number": "+1234567890", "message": "Hello"}`
- **Purpose**: Send WhatsApp messages programmatically

## Usage Examples

### Spanish Queries (Common for WhatsApp users)
- "Hola, busco un auto Toyota"
- "¿Tienes vehículos Honda disponibles?"
- "Necesito un carro con Bluetooth y CarPlay"
- "Busco un vehículo económico"

### English Queries
- "Find me Toyota vehicles under $300,000"
- "I'm looking for a Honda Civic with low mileage"
- "Show me vehicles with Bluetooth and CarPlay features"

## Features

### Vehicle Search Capabilities
- ✅ **Make/Model Search**: Find vehicles by manufacturer and model
- ✅ **Fuzzy Matching**: Handles typos and variations
- ✅ **Price Filtering**: Search by budget range
- ✅ **Feature Search**: Find vehicles with specific features
- ✅ **Mileage Filtering**: Search by maximum kilometers

### AI Agent Features
- ✅ **ReAct Framework**: Reasoning and Acting pattern
- ✅ **Tool Integration**: Seamlessly uses catalog and document search
- ✅ **Error Handling**: Graceful error recovery
- ✅ **Message Formatting**: Optimized for WhatsApp message limits

### WhatsApp Features
- ✅ **Bidirectional Communication**: Send and receive messages
- ✅ **Webhook Handling**: Automatic message processing
- ✅ **TwiML Responses**: Proper WhatsApp message formatting
- ✅ **Error Recovery**: Handles API failures gracefully

## Troubleshooting

### Common Issues
1. **"Twilio client not initialized"**: Check your Twilio credentials
2. **"OpenAI API key not found"**: Set OPENAI_API_KEY environment variable
3. **"Webhook not receiving messages"**: Verify webhook URL in Twilio console
4. **"Message not sending"**: Check Twilio WhatsApp number format

### Debug Mode
Enable debug mode to see detailed logs:
```bash
python main.py --mode whatsapp-server --debug
```

### Testing Without Twilio
Use the demo mode to test functionality:
```bash
python main.py --mode whatsapp-demo
```

## Security Notes
- Keep your Twilio credentials secure
- Use HTTPS in production
- Implement rate limiting for production use
- Validate incoming webhook requests

## Production Deployment
- Use a production WSGI server (gunicorn, uwsgi)
- Set up proper logging
- Implement monitoring and alerting
- Use environment-specific configuration
