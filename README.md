# Demo-Agent

**Project Overview**
This project implements an AI-powered command-line agent using Model Context Protocol (MCP)
and Ollama (Mistral 7B). The agent dynamically selects and executes tools based on user input
using a ReAct-style reasoning loop.

**Architecture**
User → LLM (Mistral via Ollama) → JSON Decision → MCP Tool Server → Tool Execution → Final
Response

**Project Structure**
agent_fun.py → AI agent with ReAct loop and JSON parsing
server_fun.py → FastMCP tool server exposing weather, books, jokes, etc.

**Available Tools**
• get_weather(latitude, longitude) – Fetches real-time weather via Open-Meteo API.
• book_recs(topic, limit) – Returns book suggestions via Open Library.
• random_joke() – Safe single-line joke from JokeAPI.
• random_dog() – Random dog image URL.
• trivia() – Multiple-choice trivia question.

**Setup Instructions**
1. Install dependencies:
 pip install mcp ollama requests
2. Install and run Ollama:
 ollama pull mistral:7b
3. Run the agent:
 python agent_fun.py

**Example Usage**
What’s the temperature at (37.7749, -122.4194)?
Recommend books about automation testing
Tell me a joke
Give me trivia

**Key Features**
• Strict JSON-based tool invocation
• Safe JSON extraction from LLM output
• Async MCP client-server architecture
• Dynamic tool discovery
• Clean CLI-based interaction

**Future Improvements**
• City name to latitude/longitude conversion
• Memory support for conversation history
• Streaming responses
• Tool schema validation
• Improved output formatting
