"""
Tools registry for LangChain vehicle search and recommendations.

This module provides a centralized registry of all available tools
for the vehicle recommendation system.
"""

from typing import List
from langchain_core.tools import Tool

from .catalog_search import catalog_search_tool
from .finance_calculation import finance_calculation_tool
from .fact_check import fact_check_tool
from .finance_calculator_tool import finance_calc_tool

# Registry of all available tools
AVAILABLE_TOOLS: List[Tool] = [
    catalog_search_tool,
    finance_calculation_tool,
    fact_check_tool,
    finance_calc_tool,  # Enhanced finance calculator with multiple terms
]

# Tool name to tool mapping for easy lookup
TOOL_MAP = {tool.name: tool for tool in AVAILABLE_TOOLS}


def get_tool(name: str) -> Tool:
    """
    Get a specific tool by name.

    Args:
        name: Tool name

    Returns:
        Tool instance

    Raises:
        KeyError: If tool name not found
    """
    if name not in TOOL_MAP:
        available_names = list(TOOL_MAP.keys())
        raise KeyError(f"Tool '{name}' not found. Available tools: {available_names}")

    return TOOL_MAP[name]


def get_all_tools() -> List[Tool]:
    """
    Get all available tools.

    Returns:
        List of all tool instances
    """
    return AVAILABLE_TOOLS.copy()


def get_tool_names() -> List[str]:
    """
    Get names of all available tools.

    Returns:
        List of tool names
    """
    return list(TOOL_MAP.keys())
