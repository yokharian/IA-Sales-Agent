#!/usr/bin/env python3
"""
WhatsApp Server for Vehicle Assistant.

This is a simplified version that only uses catalog search
and doesn't require the document search tool.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from agent import chat

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class SendMessageRequest(BaseModel):
    to_number: str
    message: str


class HealthResponse(BaseModel):
    status: str
    service: str


class WhatsAppVehicleAssistant:
    """WhatsApp Vehicle Assistant using the full AI agent."""

    def __init__(self):
        """Initialize the WhatsApp assistant."""

        try:
            self.twilio_client = Client(
                os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN")
            )
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise

    def send_whatsapp_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """Send a WhatsApp message using Twilio."""
        if not self.twilio_client:
            return {"success": False, "error": "Twilio client not initialized"}

        try:
            from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
            if not from_number:
                return {
                    "success": False,
                    "error": "Twilio WhatsApp number not configured",
                }

            # Ensure the number has the correct format
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            if not from_number.startswith("whatsapp:"):
                from_number = f"whatsapp:{from_number}"

            message_obj = self.twilio_client.messages.create(
                from_=from_number, body=message, to=to_number
            )

            logger.info(f"WhatsApp message sent successfully. SID: {message_obj.sid}")
            return {
                "success": True,
                "sid": message_obj.sid,
                "status": message_obj.status,
            }

        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return {"success": False, "error": str(e)}

    def handle_whatsapp_message(self, from_number: str, message_body: str) -> str:
        """Handle incoming WhatsApp messages and generate responses."""
        try:
            logger.info(f"Received WhatsApp message from {from_number}: {message_body}")
            response = self._handle_with_ai_agent(message_body)

            # Format the response for WhatsApp (limit length)
            if len(response) > 1600:  # WhatsApp has message limits
                response = response[:1600] + "...\n\n[Respuesta truncada]"

            logger.info(
                f"Sending WhatsApp response to {from_number}: {response[:100]}..."
            )
            return response

        except Exception as e:
            error_msg = f"Error procesando mensaje: {str(e)}"
            logger.error(error_msg)
            return error_msg

    @staticmethod
    def _handle_with_ai_agent(message: str) -> str:
        """Handle message using the AI agent."""
        try:
            result = chat(message)
            if result["success"]:
                return str(result["response"])
            else:
                return f"Lo siento, ocurrió un error: {result.get('error', 'Error desconocido')}"
        
        except Exception as e:
            return f"Lo siento, ocurrió un error: {str(e)}"


def create_fastapi_app() -> FastAPI:
    """Create FastAPI application for WhatsApp webhook handling."""
    app = FastAPI(
        title="WhatsApp Vehicle Assistant",
        description="AI-powered vehicle search via WhatsApp using Twilio",
        version="1.0.0",
    )

    @app.post("/whatsapp/webhook")
    async def whatsapp_webhook(request: Request):
        """Handle incoming WhatsApp messages via webhook."""
        try:
            # Parse form data from Twilio
            form_data = await request.form()
            message_body = form_data.get("Body", "")
            from_number = form_data.get("From", "")

            if not message_body or not from_number:
                logger.warning("Received empty message or sender")
                return Response("OK", status_code=200)

            # Clean the phone number
            from_number = from_number.replace("whatsapp:", "")

            # Get global assistant instance
            global assistant
            if not assistant:
                assistant = WhatsAppVehicleAssistant()

            # Handle the message and get response
            response_text = assistant.handle_whatsapp_message(from_number, message_body)

            # Create TwiML response
            twiml_response = MessagingResponse()
            twiml_response.message(response_text)

            return Response(content=str(twiml_response), media_type="text/xml")

        except Exception as e:
            logger.error(f"Error handling WhatsApp webhook: {e}")
            twiml_response = MessagingResponse()
            twiml_response.message("Lo siento, ocurrió un error procesando tu mensaje.")
            return Response(content=str(twiml_response), media_type="text/xml")

    @app.get("/whatsapp/webhook")
    async def whatsapp_webhook_verify(request: Request):
        """Handle WhatsApp webhook verification."""
        return request.query_params.get("hub.challenge", "")

    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(status="healthy", service="whatsapp-vehicle-assistant")

    @app.post("/send-message")
    async def send_message(request_data: SendMessageRequest):
        """Send a WhatsApp message via API."""
        try:
            global assistant
            if not assistant:
                assistant = WhatsAppVehicleAssistant()

            result = assistant.send_whatsapp_message(
                request_data.to_number, request_data.message
            )
            return result

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return app


def start_whatsapp_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Start the WhatsApp webhook server."""
    import uvicorn

    app = create_fastapi_app()

    print(f"🚀 Starting WhatsApp Vehicle Assistant Server (FastAPI)")
    print(f"📍 Server: http://{host}:{port}")
    print(f"🔗 Webhook URL: http://{host}:{port}/whatsapp/webhook")
    print(f"❤️  Health Check: http://{host}:{port}/health")
    print(f"📤 Send Message API: http://{host}:{port}/send-message")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"🔧 ReDoc Documentation: http://{host}:{port}/redoc")
    print()
    print("Configure your Twilio WhatsApp webhook to point to the webhook URL above.")
    print("Make sure to set the following environment variables:")
    print("- TWILIO_ACCOUNT_SID")
    print("- TWILIO_AUTH_TOKEN")
    print("- TWILIO_WHATSAPP_NUMBER")
    print("- OPENAI_API_KEY")
    print()

    uvicorn.run(app, host=host, port=port, log_level="debug" if debug else "info")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WhatsApp Vehicle Assistant Server")

    parser.add_argument("--host", default="0.0.0.0", help="Host for WhatsApp server")
    parser.add_argument(
        "--port", type=int, default=5000, help="Port for WhatsApp server"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    start_whatsapp_server(host=args.host, port=args.port, debug=args.debug)
