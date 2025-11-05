#!/usr/bin/env python3
"""
AI Agent for vehicle search and document queries using LangChain agents
using the ReAct (Reasoning and Acting) framework.

This agent can:
- Search vehicle catalogs with fuzzy matching
- Find relevant documents using semantic search
- Provide intelligent recommendations based on user preferences
- Handle complex multi-step queries
"""
from os import getenv
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig

# Load environment variables
load_dotenv()

import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from tools.catalog_search import catalog_search_tool
from tools.document_search import document_search_tool

# Prompts estandarizados
SYSTEM_PROMPT = """Eres un asistente virtual especializado en búsqueda de vehículos y atención al cliente para una empresa automotriz que actúa como agente comercial de Kavak. Asistes al cliente en su búsqueda y respondes preguntas generales sobre la empresa, siempre usando solo las herramientas disponibles.

HERRAMIENTAS DISPONIBLES:
- 'catalog_search': úsala para encontrar vehículos según los criterios del usuario, incluso con errores ortográficos, emplea la entrada del usuario directamente, sin modificarla o corregirla previamente.
- 'document_search': utilízala únicamente para responder sobre la empresa (sedes, servicios, cultura, propuesta de valor). No la uses para preguntas sobre vehículos.

INSTRUCCIONES:
1. Si el usuario pide ayuda para encontrar un coche, usa solo 'catalog_search' y muestra los resultados más relevantes. No justifiques recomendaciones.
2. Si pregunta sobre la empresa, usa solo 'document_search' para obtener la información.
3. Si no encuentras respuesta clara en catálogo o documentos, responde: "Lo siento, no tengo esa información disponible en este momento."
4. Si el mensaje es muy vago y no puedes determinar la petición, solicita amablemente que vuelva a intentarlo o dé más detalles.
5. Si no estás seguro de la intención del usuario, mantén la conversación activa de manera servicial: haz una pregunta de confirmación para entender mejor la solicitud, ofrece opciones relevantes relacionadas con vehículos o con la empresa, y muestra disposición para ayudar con sugerencias que puedan orientar al usuario.
6. Nunca inventes información; responde solo con datos confirmados por tus herramientas, manteniendo un tono profesional y alineado a la cultura de la empresa.

CONTEXTO OPERACIONAL:
- Canal: WhatsApp conversacional
- Audiencia: Clientes potenciales interesados en comprar vehículos o conocer más sobre la empresa
- Comportamiento: Comprender entradas con errores o expresiones vagas y responder de forma directa en lo comercial y cordial en lo informativo."""

standard_model = ChatOpenAI(model="gpt-4o", temperature=0.1, max_tokens=2000)
efficient_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, max_tokens=2000)

# Initialize tools
tools = [catalog_search_tool, document_search_tool]
config: RunnableConfig = {"configurable": {"thread_id": "1"}}

# Create the agent
agent = create_agent(
    name="commercial-agent",
    model=standard_model,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    debug={'false':False,'true':True,}.get(getenv('verbose','false'),),
    # checkpointer=InMemorySaver(),
)


def chat(message: str) -> Dict[str, Any]:
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
        response = agent.invoke(inputs)
        
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
