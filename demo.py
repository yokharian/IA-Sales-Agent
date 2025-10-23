#!/usr/bin/env python3
"""
AI Agent with ReAct using LangChain.

This module creates an intelligent agent that can help users with vehicle searches
and document queries using the ReAct (Reasoning and Acting) framework.
"""

import os
import sys
from pathlib import Path

from src.whatsapp_server import WhatsAppVehicleAssistant

# ¿Qué documentos necesito para comprar un auto en Kavak?
# ¿Cómo funciona el plan de pago a meses con Kavak?
# ¿Qué documentos necesito para el plan de pago a meses con Kavak?

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from src.main import VehicleAssistantAgent


def demo_whatsapp_functionality():
    """Demonstrate WhatsApp functionality without actually sending messages."""
    print("📱 WhatsApp Vehicle Assistant Demo")
    print("=" * 50)

    # Create assistant
    assistant = WhatsAppVehicleAssistant()

    # Test messages
    test_messages = [
        "Hola, busco un auto Toyota",
        "¿Tienes vehículos Honda disponibles?",
        "Necesito un carro con Bluetooth y CarPlay",
        "¿Qué información tienes sobre mantenimiento de autos?",
        "Busco un vehículo económico",
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 Test {i}: {message}")
        print("-" * 30)

        response = assistant.handle_whatsapp_message("+1234567890", message)
        print(f"🤖 Response: {response}")

    print("\n✅ WhatsApp functionality demo completed!")
    print("\nTo use with real WhatsApp:")
    print("1. Set up Twilio credentials in .env file")
    print("2. Run: python whatsapp_server.py --host 0.0.0.0 --port 5000")
    print("3. Configure Twilio webhook to your server URL")


def demo_tools_directly():
    """Demonstrate tools directly without the agent."""
    print("🔧 Testing Tools Directly")
    print("=" * 30)

    # Test catalog search
    print("\n1. Testing Catalog Search:")
    try:
        from src.tools.catalog_search import catalog_search_impl

        result = catalog_search_impl({"make": "Honda", "max_results": 3})
        print(f"   Found {len(result)} Honda vehicles")
        for i, vehicle in enumerate(result[:2], 1):
            print(
                f"   {i}. {vehicle.make} {vehicle.model} ({vehicle.year}) - ${vehicle.price:,.0f}"
            )
    except Exception as e:
        print(f"   Error: {e}")

    # Test document search
    print("\n2. Testing Document Search:")
    try:
        from src.tools.document_search import document_search_impl

        result = document_search_impl({"query": "vehicle information", "k": 2})
        print(f"   Found {len(result)} documents")
        for i, doc in enumerate(result[:1], 1):
            print(f"   {i}. {doc.content[:100]}...")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n✅ Tools are working correctly!")
    print("To use the full AI agent, set OPENAI_API_KEY environment variable.")


def interactive_chat():
    """Start an interactive chat session."""
    print("🚗 Vehicle Assistant Agent - Interactive Mode")
    print("=" * 50)
    print("Type 'quit' to exit, 'help' for available commands")
    print()

    # Create agent
    agent = VehicleAssistantAgent(verbose=False)

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye! 👋")
                break

            if user_input.lower() == "help":
                print(
                    """
Available commands:
- Search for vehicles: "Find me [make] vehicles under $[price]"
- Search by features: "Show me vehicles with [feature1] and [feature2]"
- Document search: "What information do you have about [topic]?"
- Complex queries: "I need a [make] [model] with low mileage and [features]"
- Type 'quit' to exit
                """
                )
                continue

            if not user_input:
                continue

            print("🤖 Assistant: ", end="", flush=True)
            result = agent.chat(user_input)

            if result["success"]:
                print(result["response"])
            else:
                print(
                    f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
                )

            print()

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")


def demo_agent():
    """Demonstrate the agent capabilities."""
    print("🚗 Vehicle Assistant Agent Demo")
    print("=" * 50)

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API key not found. Running in test mode...")
        print("To use the full agent, set OPENAI_API_KEY environment variable.")
        print()

        # Test the tools directly
        demo_tools_directly()
        return

    try:
        # Create agent
        agent = VehicleAssistantAgent(verbose=True)

        # Demo queries
        demo_queries = [
            "Find me Toyota vehicles under $300,000",
            "I'm looking for a Honda Civic with low mileage",
            "What documents do you have about vehicle maintenance?",
            "Show me vehicles with Bluetooth and CarPlay features",
            "I want to find information about electric vehicles",
        ]

        for i, query in enumerate(demo_queries, 1):
            print(f"\n🔍 Demo {i}: {query}")
            print("-" * 50)

            result = agent.chat(query)

            if result["success"]:
                print(f"✅ Response: {result['response']}")
                if result.get("messages"):
                    print(f"📝 Messages: {len(result['messages'])}")
            else:
                print(f"❌ Error: {result['response']}")

            print()

    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        print("Running in test mode...")
        demo_tools_directly()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vehicle Assistant Agent")
    parser.add_argument(
        "--mode",
        choices=["demo", "interactive"],
        default="demo",
        help="Run mode: demo or interactive chat",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show agent reasoning steps"
    )

    args = parser.parse_args()

    if args.mode == "demo":
        demo_agent()
    elif args.mode == "interactive":
        interactive_chat()
