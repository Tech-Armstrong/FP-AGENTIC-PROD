"""
Standard External Tools - Web Search Integration

What this file does:
This script configures standard external tools for the financial planning system.
Currently provides Tavily-powered web search capability for agents.

What this file contains:
- tavily_tool: TavilySearchResults instance configured with API key for web research and information retrieval
"""

from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv
import os

load_dotenv()
TAVILY_API_KEY=os.getenv('TAVILY_API_KEY')
# Initialize Tavily search tool
tavily_tool = TavilySearchResults(max_results=10, api_key=TAVILY_API_KEY)
