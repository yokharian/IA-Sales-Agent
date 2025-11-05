#!/usr/bin/env python3
"""
AI Agent with ReAct using LangChain.

This module creates an intelligent agent that can help users with vehicle searches
and document queries using the ReAct (Reasoning and Acting) framework.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from src.agent import chat

DEMO_PROMPTS = (
    "¿Qué documentos necesito para comprar un auto en Kavak?",
    "quiero comprar un coche BMW",
    "¿hay devolución?",
    "busco onda o bolbo baratos",
    "¿Dónde están las sedes de kavak?",
    "¿En qué año se fundó kavak?",
    "wolksvagen del año",
    "nasda y nisan con el menor km",
    "¿Cómo funciona el plan de pago a meses?",
)


def interactive_chat(verbose: bool = False):
    """Start an interactive chat session."""
    print("🚗 Vehicle Assistant Agent - Interactive Mode")
    print("=" * 50)
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye! 👋")
                break

            if not user_input:
                continue

            print("🤖 Assistant: ", end="", flush=True)
            result = chat(user_input)

            if result["success"]:
                print( str(result["response"]))
            else:
                print(f"Lo siento, ocurrió un error: {result.get('error', 'Error desconocido')}")
            print()

        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")


def demo_agent(verbose: bool = False):
    """Demonstrate the agent capabilities."""
    print("🚗 Vehicle Assistant Agent Demo")
    print("=" * 50)

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OpenAI API key not found. exiting...")
        print("To use the full agent, set OPENAI_API_KEY environment variable.")
        return  # exit safely

    try:

        # Demo queries
        for i, query in enumerate(DEMO_PROMPTS, 1):
            print(f"\n🔍 Demo {i}: {query}")
            print("-" * 50)

            result = chat(query)

            if result["success"]:
                print(f"✅ Response: {result['response']}")
                if result.get("messages"):
                    print(f"📝 Messages: {len(result['messages'])}")
            else:
                print(f"❌ Error: {result['response']}")

            print()

    except Exception as e:
        print(f"❌ Error creating agent: {e}")


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
        demo_agent(args.verbose)
    elif args.mode == "interactive":
        interactive_chat(args.verbose)
