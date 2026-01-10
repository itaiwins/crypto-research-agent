"""
Main agent logic using the Anthropic API.

This module implements the Crypto Research Agent using Claude as the
reasoning engine. The agent can use tools to fetch price data and news,
then synthesize the information into a comprehensive research brief.

=============================================================================
ARCHITECTURE OVERVIEW (for interviewers)
=============================================================================

This file implements the "Agentic AI" pattern, where an LLM (Claude) acts as
a reasoning engine that can:
1. Understand user intent
2. Decide which tools to use
3. Execute tools and process results
4. Synthesize information into a coherent response

The key innovation is the AGENTIC LOOP (see research() method):
- We send a request to Claude with available tools
- Claude decides if it needs to call a tool
- If yes, we execute the tool and send results back
- Claude continues reasoning until it has enough info
- Finally, Claude generates the research report

This is different from simple "prompt in, text out" LLM usage because
the agent can take ACTIONS (via tools) to gather information dynamically.

=============================================================================
"""

import json
import os
from typing import Any

from anthropic import Anthropic

from .tools import (
    get_crypto_price,
    get_price_tool_definition,
    get_crypto_news,
    get_news_tool_definition,
)


# =============================================================================
# SYSTEM PROMPT
# =============================================================================
# The system prompt defines the agent's "personality" and behavior.
# This is crucial for getting consistent, high-quality outputs.
#
# Key design decisions:
# 1. Clear role definition ("professional cryptocurrency research analyst")
# 2. Explicit instructions on WHICH tools to use and WHEN
# 3. Structured output format (sections the report should include)
# 4. Guidelines for tone (objective, factual, cite numbers)
# =============================================================================

SYSTEM_PROMPT = """You are a professional cryptocurrency research analyst. Your job is to provide
comprehensive, data-driven research briefs about cryptocurrencies.

When researching a cryptocurrency, you should:
1. First fetch the current price and market data using the get_crypto_price tool
2. Then fetch recent news using the get_crypto_news tool
3. Synthesize all information into a well-structured research brief

Your research brief should include:
- **Price Analysis**: Current price, recent price changes, and market position
- **Market Overview**: Market cap, trading volume, and supply information
- **News Summary**: Key recent developments and news (summarize, don't just list)
- **Key Takeaways**: 2-3 bullet points highlighting the most important insights

Be objective and factual. Cite specific numbers from the data. If data is unavailable,
acknowledge it rather than making assumptions.

Format your response in clean markdown with clear sections."""


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================
# Tools are how the agent interacts with the outside world. Each tool has:
# 1. A name (string identifier)
# 2. A description (helps Claude understand when to use it)
# 3. An input schema (JSON Schema defining parameters)
#
# These definitions are sent to Claude so it knows what tools are available.
# =============================================================================

def get_all_tools() -> list[dict[str, Any]]:
    """
    Get all tool definitions for the agent.

    This function aggregates tool definitions from each tool module.
    The definitions follow Anthropic's tool use specification.

    Returns:
        A list of tool definitions in Anthropic's format

    Why this pattern?
        - Keeps tool definitions close to their implementations
        - Makes it easy to add/remove tools without changing agent logic
        - Each tool module is responsible for its own schema
    """
    return [
        get_price_tool_definition(),
        get_news_tool_definition(),
    ]


# =============================================================================
# TOOL EXECUTION
# =============================================================================
# This function is the "bridge" between Claude's tool requests and our
# actual Python implementations. When Claude says "call get_crypto_price
# with ticker=BTC", this function routes that to the right code.
# =============================================================================

def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> str:
    """
    Execute a tool and return its result as a string.

    This is the dispatcher that routes tool calls to their implementations.
    It acts as a bridge between Claude's tool requests and our Python code.

    Args:
        tool_name: The name of the tool to execute (matches tool definition)
        tool_input: The input parameters for the tool (parsed from Claude's request)

    Returns:
        The tool result as a JSON string (Claude expects string responses)

    Design decisions:
        - Returns JSON string so Claude can parse structured data
        - Uses a simple if/elif pattern (could use a registry for more tools)
        - Handles unknown tools gracefully with an error message
    """
    # Route to the appropriate tool implementation
    if tool_name == "get_crypto_price":
        result = get_crypto_price(tool_input["ticker"])

    elif tool_name == "get_crypto_news":
        # Use default of 5 articles if not specified
        max_articles = tool_input.get("max_articles", 5)
        result = get_crypto_news(tool_input["ticker"], max_articles)

    else:
        # Unknown tool - return error that Claude can understand
        result = {"error": f"Unknown tool: {tool_name}"}

    # Convert to JSON string for Claude to process
    # default=str handles non-serializable types like datetime
    return json.dumps(result, indent=2, default=str)


# =============================================================================
# THE AGENT CLASS
# =============================================================================
# This is the main class that orchestrates everything. It:
# 1. Manages the Anthropic API connection
# 2. Implements the agentic loop (the core innovation)
# 3. Tracks tool usage for transparency
# =============================================================================

class CryptoResearchAgent:
    """
    An AI agent that researches cryptocurrencies using Claude and various tools.

    This class implements the "agentic AI" pattern where Claude acts as a
    reasoning engine that can call tools to gather information, then synthesize
    it into a comprehensive research report.

    Architecture:
        ┌─────────────┐
        │   User      │ ──── "Research BTC" ────►
        └─────────────┘
              │
              ▼
        ┌─────────────┐
        │   Agent     │ ◄──── This class
        └─────────────┘
              │
        ┌─────┴─────┐
        ▼           ▼
    ┌───────┐  ┌───────┐
    │ Price │  │ News  │  ◄── Tools (external APIs)
    │ Tool  │  │ Tool  │
    └───────┘  └───────┘

    Attributes:
        client: The Anthropic API client for making requests to Claude
        model: The Claude model to use (e.g., claude-sonnet-4-20250514)
        detailed: Whether to request more detailed analysis

    Example:
        >>> agent = CryptoResearchAgent()
        >>> result = agent.research("BTC")
        >>> print(result["report"])
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        detailed: bool = False,
    ):
        """
        Initialize the Crypto Research Agent.

        Args:
            api_key: Anthropic API key. If not provided, reads from
                     ANTHROPIC_API_KEY environment variable.
            model: The Claude model to use. Defaults to claude-sonnet-4-20250514
                   which offers a good balance of capability and cost.
            detailed: If True, requests more detailed analysis from Claude.

        Raises:
            ValueError: If no API key is provided or found in environment.

        Security Note:
            API keys should NEVER be hardcoded. This implementation follows
            best practices by reading from environment variables.
        """
        # Try to get API key from parameter, fall back to environment variable
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        # Fail fast if no API key - better than cryptic errors later
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Initialize the Anthropic client
        # This handles all HTTP communication with Claude's API
        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.detailed = detailed

    def research(self, ticker: str) -> dict[str, Any]:
        """
        Research a cryptocurrency and generate a comprehensive brief.

        This is the CORE METHOD that implements the agentic loop pattern.
        It orchestrates the entire research process:

        STEP 1: Send initial request to Claude with the research task
        STEP 2: Enter the agentic loop:
                - Check if Claude wants to use a tool
                - If yes: execute tool, send results back, repeat
                - If no: Claude is done, exit loop
        STEP 3: Extract and return the final research report

        The Agentic Loop Visualized:
        ┌──────────────────────────────────────────────────────────┐
        │                                                          │
        │  ┌─────────┐    ┌─────────────┐    ┌─────────────────┐   │
        │  │ Request │───►│   Claude    │───►│ Tool Requested? │   │
        │  └─────────┘    │  (thinks)   │    └────────┬────────┘   │
        │                 └─────────────┘             │            │
        │                       ▲                     │            │
        │                       │              ┌──────┴──────┐     │
        │                       │              │             │     │
        │                       │           Yes│          No │     │
        │                       │              ▼             ▼     │
        │                 ┌─────┴─────┐  ┌──────────┐  ┌─────────┐ │
        │                 │Send Result│◄─│Execute   │  │  Done!  │ │
        │                 │ to Claude │  │  Tool    │  │ Extract │ │
        │                 └───────────┘  └──────────┘  │ Report  │ │
        │                                              └─────────┘ │
        └──────────────────────────────────────────────────────────┘

        Args:
            ticker: The cryptocurrency ticker symbol (e.g., 'BTC', 'ETH')

        Returns:
            A dictionary containing:
            - success (bool): Whether the research completed successfully
            - ticker (str): The researched ticker symbol
            - report (str): The generated research brief (markdown format)
            - tool_calls (list): List of tools that were called (for transparency)
            - model (str): The model used
            - error (str): Error message if unsuccessful
        """
        # Normalize ticker to uppercase for consistency
        ticker = ticker.upper()

        # Track which tools were called (useful for debugging and transparency)
        tool_calls_made: list[dict[str, Any]] = []

        # =====================================================================
        # STEP 1: Prepare the user message
        # =====================================================================
        # We can modify the prompt based on the 'detailed' flag to get
        # different levels of analysis from Claude.

        detail_instruction = ""
        if self.detailed:
            detail_instruction = (
                "\n\nProvide an EXTREMELY detailed analysis including:\n"
                "- Technical analysis of price movements\n"
                "- Comparison to market trends\n"
                "- Detailed news analysis with potential market impact\n"
                "- Risk factors and considerations\n"
                "- Supply and tokenomics analysis"
            )

        user_message = f"Research the cryptocurrency {ticker} and provide a comprehensive research brief.{detail_instruction}"

        # Initialize the conversation history
        # This list will grow as we add assistant responses and tool results
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": user_message}
        ]

        try:
            # =================================================================
            # STEP 2: Make the initial API request to Claude
            # =================================================================
            # We send:
            # - The model to use
            # - Maximum tokens for the response
            # - The system prompt (defines Claude's behavior)
            # - Available tools (so Claude knows what it can use)
            # - The conversation messages

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=get_all_tools(),
                messages=messages,
            )

            # =================================================================
            # STEP 3: THE AGENTIC LOOP
            # =================================================================
            # This is the key innovation! We keep looping as long as Claude
            # wants to use tools. The stop_reason tells us what Claude wants:
            # - "tool_use": Claude wants to call a tool
            # - "end_turn": Claude is done and has a final response

            while response.stop_reason == "tool_use":
                # Claude wants to use one or more tools
                # We need to execute them and send results back

                tool_results = []

                # Process each content block in Claude's response
                # Claude can request multiple tools in one response
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        # Extract tool call details
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id  # Unique ID to match results

                        # Execute the tool (this calls our Python functions)
                        tool_result = execute_tool(tool_name, tool_input)

                        # Track this tool call for transparency/debugging
                        tool_calls_made.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "result_preview": tool_result[:200] + "..." if len(tool_result) > 200 else tool_result,
                        })

                        # Format the result for Claude
                        # The tool_use_id links this result to Claude's request
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": tool_result,
                        })

                # =============================================================
                # Update conversation history
                # =============================================================
                # We need to add:
                # 1. Claude's response (including its tool use requests)
                # 2. The tool results (as a "user" message - this is the API format)

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                # =============================================================
                # Continue the conversation
                # =============================================================
                # Send the updated conversation back to Claude
                # Claude will either request more tools or give a final answer

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=get_all_tools(),
                    messages=messages,
                )

            # =================================================================
            # STEP 4: Extract the final response
            # =================================================================
            # The loop has ended, meaning Claude has finished using tools
            # and is ready to give us the final research report.

            final_response = ""
            for content_block in response.content:
                if hasattr(content_block, "text"):
                    final_response += content_block.text

            # Return structured result with all relevant information
            return {
                "success": True,
                "ticker": ticker,
                "report": final_response,
                "tool_calls": tool_calls_made,
                "model": self.model,
            }

        except Exception as e:
            # Handle any errors gracefully
            # We still return the tool_calls_made for debugging
            return {
                "success": False,
                "ticker": ticker,
                "error": str(e),
                "tool_calls": tool_calls_made,
            }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================
# This provides a simple functional interface for quick usage.
# Useful for scripts or when you don't need the full agent object.
# =============================================================================

def quick_research(ticker: str, detailed: bool = False) -> str:
    """
    Convenience function for quick cryptocurrency research.

    This is a simplified interface for cases where you just want
    the report string without dealing with the agent object.

    Args:
        ticker: The cryptocurrency ticker symbol
        detailed: Whether to provide detailed analysis

    Returns:
        The research report as a string, or an error message

    Example:
        >>> report = quick_research("ETH")
        >>> print(report)
    """
    try:
        agent = CryptoResearchAgent(detailed=detailed)
        result = agent.research(ticker)

        if result["success"]:
            return result["report"]
        else:
            return f"Research failed: {result['error']}"

    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
