#!/usr/bin/env python3
"""
AI Agent with ReAct using LangChain.

This module creates an intelligent agent that can help users with vehicle searches
and document queries using the ReAct (Reasoning and Acting) framework.
"""

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

# Import our custom tools
from tools.catalog_search import catalog_search_tool
from tools.document_search import document_search_tool

# Prompts estandarizados
SYSTEM_PROMPT = """Eres un asistente virtual especializado en búsqueda de vehículos y atención al cliente para una empresa automotriz. 

HERRAMIENTAS DISPONIBLES:
- 'catalog_search': úsala para encontrar vehículos según los criterios del usuario (marca, modelo, año, precio, tipo de combustible, etc.), incluso si hay errores ortográficos.
- 'document_search': úsala únicamente para responder preguntas sobre la empresa (sedes, servicios, cultura, propuesta de valor). No la uses para preguntas sobre vehículos.

INSTRUCCIONES:
1. Si el usuario solicita ayuda para encontrar un coche, usa 'catalog_search' y muestra los resultados más relevantes. No justifiques tus recomendaciones.
2. Si el usuario pregunta sobre la empresa, usa 'document_search' para obtener la información correspondiente.
3. Si no encuentras una respuesta clara en el catálogo o documentos, responde de forma transparente diciendo: "Lo siento, no tengo esa información disponible en este momento."
4. Evita inventar información. Responde siempre con precisión, manteniendo un tono profesional y alineado con la cultura de la empresa."""

ROLE_PROMPT = "Actúa como un agente comercial de Kavak que asiste al cliente durante su proceso de búsqueda y responde preguntas generales sobre la empresa."

CONTEXT_PROMPT = """CONTEXTO OPERACIONAL:
- Canal: WhatsApp conversacional
- Audiencia: Clientes potenciales interesados en comprar vehículos o conocer más sobre la empresa
- Limitaciones: Conocimiento limitado al catálogo disponible y documentos proporcionados internamente
- Comportamiento: Comprender entradas con errores o expresiones vagas, responder de forma directa en lo comercial y cordial en lo informativo"""

FULL_PROMPT = SYSTEM_PROMPT + "\n" + ROLE_PROMPT + "\n" + CONTEXT_PROMPT


class VehicleAssistantAgent:
    """
    AI Agent for vehicle search and document queries using LangChain agents.

    This agent can:
    - Search vehicle catalogs with fuzzy matching
    - Find relevant documents using semantic search
    - Provide intelligent recommendations based on user preferences
    - Handle complex multi-step queries
    """

    def __init__(self, llm: Optional[BaseChatModel] = None, verbose: bool = True):
        """
        Initialize the Vehicle Assistant Agent.

        Args:
            llm: Language model to use (defaults to GPT-4)
            verbose: Whether to show agent reasoning steps
        """
        self.llm = llm or self._get_llm
        self.verbose = verbose

        # Initialize tools
        self.tools = [catalog_search_tool, document_search_tool]

        # Create the agent
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=FULL_PROMPT,
            debug=self.verbose,
        )

    @property
    def _get_llm(self) -> BaseChatModel:
        """Get default language model."""
        return ChatOpenAI(model="gpt-4o", temperature=0.1, max_tokens=2000)

    def chat(self, message: str) -> Dict[str, Any]:
        """
        Chat with the agent.

        Args:
            message: User message/query

        Returns:
            Dictionary containing response and metadata
        """
        try:
            # Prepare input for the agent
            inputs = {"messages": [{"role": "user", "content": message}]}

            # Get the response
            response = self.agent.invoke(inputs)

            # Extract the final message content
            messages = response.get("messages", [])
            if messages:
                final_message = messages[-1]
                if hasattr(final_message, "content"):
                    content = final_message.content
                else:
                    content = str(final_message)
            else:
                content = "I couldn't generate a response."

            return {"response": content, "messages": messages, "success": True}
        except Exception as e:
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "messages": [],
                "success": False,
                "error": str(e),
            }
