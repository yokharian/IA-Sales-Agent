#!/usr/bin/env python3
"""
AI Agent with ReAct using LangChain.

This module creates an intelligent agent that can help users with vehicle searches
and document queries using the ReAct (Reasoning and Acting) framework.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

# Import our custom tools
from tools.catalog_search import catalog_search_tool
from tools.document_search import document_search_tool

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """You are a helpful AI assistant specialized in vehicle searches and automotive information.

You have access to the following tools:
- catalog_search: Search the vehicle catalog with advanced filtering and fuzzy matching
- document_search: Search for relevant documents using semantic similarity

When users ask about vehicles:
1. Use catalog_search to find vehicles matching their criteria
2. Use document_search to find relevant documentation or information
3. Provide helpful recommendations based on the results
4. Handle typos and fuzzy matching gracefully
5. Explain your reasoning when making recommendations

Always be helpful, accurate, and provide detailed information about the vehicles you find."""


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
        self.llm = llm or self._get_default_llm()
        self.verbose = verbose

        # Initialize tools
        self.tools = [catalog_search_tool, document_search_tool]

        # Store system prompt
        self.system_prompt = SYSTEM_PROMPT

        # Create the agent
        self.agent = create_agent(
            model="openai:gpt-4o",
            tools=self.tools,
            system_prompt=self.system_prompt,
            debug=self.verbose,
        )

    def _get_default_llm(self) -> BaseChatModel:
        """Get default language model."""
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
            )

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
