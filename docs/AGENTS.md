# AI Agent Development Guidelines

**Version:** 1.0  
**Last Updated:** October 23, 2025

---

## Overview

This document provides guidelines for developing, maintaining, and extending AI agents in the Commercial Agent system. It covers architecture patterns, best practices, and common scenarios.

---

## 1. Agent Architecture

### 1.1 Core Components

**VehicleAssistantAgent** is the main agent class that:
- Uses LangChain's ReAct framework (Reasoning and Acting)
- Manages tool selection and invocation
- Handles multi-step reasoning
- Synthesizes responses from tool outputs

### 1.2 Agent Responsibilities

**DO:**
- Analyze user intent
- Select appropriate tools
- Chain multiple tool calls when needed
- Provide natural language responses
- Handle errors gracefully

**DON'T:**
- Generate vehicle information without using tools
- Make assumptions about data not returned by tools
- Override tool results
- Ignore tool failures silently

---

## 2. Testing Guidelines

### 2.1 Unit Testing

**Test agent components:**
- Intent classification
- Tool selection logic
- Response formatting
- Error handling

### 2.2 Integration Testing

**Test workflows:**
- Simple single-tool queries
- Complex multi-tool queries
- Error scenarios
- Edge cases (empty results, invalid input)

### 2.3 Test Scenarios

**Essential test cases:**
```python
# Vehicle search
"Find Toyota under $300,000"
"busco Honda con bluetooth"
"¿Tienes vehículos económicos?"

# Document search
"What documents do I need to buy?"
"¿Cómo funciona el financiamiento?"
"warranty information"

# Multi-tool
"Show me Toyota vehicles and explain the buying process"

# Error cases
"Find XYZ brand" (non-existent)
"" (empty query)
"asdfghjkl" (gibberish)
```

---

## 3. Agent Extension

### 3.1 Adding New Tools

**Steps:**
1. Create tool implementation in `src/tools/`
2. Define Pydantic schemas (input/output)
3. Implement core logic
4. Add to agent's tool list
5. Update agent prompt with tool description
6. Write tests
7. Document in separate PRD

### 3.2 Tool Design Principles

**Tool should:**
- Have single, clear purpose
- Accept structured input (Pydantic)
- Return structured output (Pydantic)
- Handle errors internally
- Log failures appropriately
- Be independently testable

**Tool should NOT:**
- Call other tools directly
- Maintain state
- Generate natural language responses
- Make assumptions about agent context

---

## 4. Best Practices Summary

### DO ✅
- Use tools for all data retrieval
- Handle errors gracefully
- Provide clear, concise responses
- Test extensively
- Log appropriately
- Keep responses under 1600 chars (WhatsApp)
- Ask clarifying questions
- Validate tool inputs

### DON'T ❌
- Generate data without tools
- Ignore tool failures
- Make assumptions about missing data
- Create overly long responses
- Skip error handling
- Hard-code business logic in agent
- Mix languages inconsistently
