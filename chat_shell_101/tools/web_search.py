"""
Web search tool for internet search capabilities.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

import httpx

from .base import BaseTool, ToolInput, ToolOutput

logger = logging.getLogger(__name__)


class WebSearchInput(ToolInput):
    """Input schema for web search tool."""
    query: str = Field(..., description="Search query to execute")
    num_results: int = Field(default=5, ge=1, le=20, description="Number of results to return (1-20)")
    include_snippets: bool = Field(default=True, description="Include result snippets in output")


class WebSearchResult(BaseModel):
    """Single web search result."""
    title: str
    url: str
    snippet: Optional[str] = None


class WebSearchOutput(ToolOutput):
    """Output schema for web search tool."""
    results: List[WebSearchResult] = Field(default_factory=list)
    total_results: int = 0
    search_url: Optional[str] = None


class WebSearchTool(BaseTool):
    """Web search tool using DuckDuckGo or configurable search provider.

    This tool performs web searches and returns structured results.
    By default, it uses DuckDuckGo's instant answer API.

    Example:
        tool = WebSearchTool()
        result = await tool.execute(WebSearchInput(query="Python programming"))
    """

    name = "web_search"
    description = (
        "Search the web for information. "
        "Returns titles, URLs, and snippets of search results. "
        "Use this when you need current information not in your training data."
    )
    input_schema = WebSearchInput

    # DuckDuckGo instant answer API
    DEFAULT_SEARCH_URL = "https://duckduckgo.com/html/"
    DDG_INSTANT_ANSWER_URL = "https://api.duckduckgo.com/"

    def __init__(
        self,
        search_provider: str = "duckduckgo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize web search tool.

        Args:
            search_provider: Search provider to use ('duckduckgo', 'custom')
            api_key: API key for search provider (if required)
            base_url: Custom base URL for search API
        """
        self.search_provider = search_provider
        self.api_key = api_key
        self.base_url = base_url or self.DEFAULT_SEARCH_URL
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "ChatShell101/1.0 (Web Search Tool)"
                }
            )
        return self._client

    async def _search_duckduckgo(self, query: str, num_results: int) -> List[WebSearchResult]:
        """Search using DuckDuckGo.

        Note: DuckDuckGo's API has rate limiting. For production use,
        consider using a paid search API like Bing or Google.
        """
        client = await self._get_client()
        results = []

        try:
            # Try instant answer API first
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }

            response = await client.get(self.DDG_INSTANT_ANSWER_URL, params=params)

            if response.status_code == 200:
                data = response.json()

                # Add abstract if available
                if data.get("Abstract"):
                    results.append(WebSearchResult(
                        title=data.get("Heading", query),
                        url=data.get("AbstractURL", ""),
                        snippet=data.get("Abstract")
                    ))

                # Add related topics
                for topic in data.get("RelatedTopics", [])[:num_results - len(results)]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append(WebSearchResult(
                            title=topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else query,
                            url=topic.get("FirstURL", ""),
                            snippet=topic.get("Text", "")
                        ))

            # If no results from instant answer, fallback to HTML scraping
            if not results:
                results = await self._search_duckduckgo_html(query, num_results)

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            raise

        return results[:num_results]

    async def _search_duckduckgo_html(self, query: str, num_results: int) -> List[WebSearchResult]:
        """Fallback HTML scraping for DuckDuckGo."""
        client = await self._get_client()
        results = []

        try:
            params = {"q": query}
            response = await client.get(self.DEFAULT_SEARCH_URL, params=params)

            if response.status_code == 200:
                # Simple HTML parsing - in production, use BeautifulSoup
                html = response.text
                # This is a simplified parser - real implementation would use proper HTML parsing
                import re

                # Find result blocks
                result_blocks = re.findall(
                    r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                    html,
                    re.DOTALL
                )

                for i, (url, title_html) in enumerate(result_blocks[:num_results]):
                    # Clean up title (remove HTML tags)
                    title = re.sub(r'<[^>]+>', '', title_html)
                    # Decode HTML entities
                    title = title.replace('&quot;', '"').replace('&amp;', '&')

                    results.append(WebSearchResult(
                        title=title.strip(),
                        url=url,
                        snippet=None
                    ))

        except Exception as e:
            logger.error(f"DuckDuckGo HTML search failed: {e}")

        return results

    async def execute(self, input_data: WebSearchInput) -> ToolOutput:
        """Execute web search."""
        try:
            if self.search_provider == "duckduckgo":
                results = await self._search_duckduckgo(
                    input_data.query,
                    input_data.num_results
                )
            else:
                return ToolOutput(
                    result="",
                    error=f"Unsupported search provider: {self.search_provider}"
                )

            # Format results
            if not results:
                return ToolOutput(
                    result="No results found for the query.",
                    results=[],
                    total_results=0
                )

            # Create readable output
            output_lines = []
            for i, result in enumerate(results, 1):
                output_lines.append(f"{i}. {result.title}")
                output_lines.append(f"   URL: {result.url}")
                if input_data.include_snippets and result.snippet:
                    output_lines.append(f"   {result.snippet}")
                output_lines.append("")

            return ToolOutput(
                result="\n".join(output_lines),
                results=results,
                total_results=len(results)
            )

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolOutput(
                result="",
                error=f"Search failed: {str(e)}"
            )

    async def close(self):
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
