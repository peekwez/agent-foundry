# type: ignore
import json
import os
from collections.abc import Sequence
from typing import Any, Literal

import requests
import urllib3
from agents import FunctionTool, RunContextWrapper
from pydantic import BaseModel, Field
from tavily import TavilyClient

# typing: ignore
from tavily.errors import (
    BadRequestError,
    ForbiddenError,
    InvalidAPIKeyError,
    UsageLimitExceededError,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WebSearchArguments(BaseModel):
    query: str = Field(..., description="The search query.")
    num_results: int = Field(10, description="The number of search results to return.")


class SearchResult(BaseModel):
    title: str = Field(..., description="The title of the search result.")
    content: str = Field(
        ..., description="AI content of relevant content from the search result."
    )
    url: str = Field(..., description="The URL of the search result.")
    raw_content: str | None = Field(
        default=None, description="The raw content of the search result."
    )


class SearchResults(BaseModel):
    results: list[SearchResult] = Field(
        default=[], description="List of search results."
    )


class CustomTavilyClient(TavilyClient):  # type: ignore
    def _search(
        self,
        query: str,
        search_depth: Literal["basic", "advanced"] = "basic",
        topic: Literal["general", "news", "finance"] = "general",
        time_range: Literal["day", "week", "month", "year"] | None = None,
        days: int = 7,
        max_results: int = 5,
        include_domains: Sequence[str] | None = None,
        exclude_domains: Sequence[str] | None = None,
        include_answer: bool | Literal["basic", "advanced"] = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        timeout: int = 60,
        **kwargs: Any,
    ) -> Any:
        """
        Internal search method to send the request to the API.
        """

        data: dict[str, Any] = {
            "query": query,
            "search_depth": search_depth,
            "topic": topic,
            "time_range": time_range,
            "days": days,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "max_results": max_results,
            "include_domains": include_domains,
            "exclude_domains": exclude_domains,
            "include_images": include_images,
        }

        if kwargs:
            data.update(kwargs)

        timeout = min(timeout, 120)

        response = requests.post(
            self.base_url + "/search",
            data=json.dumps(data),
            headers=self.headers,
            timeout=timeout,
            proxies=self.proxies,
            verify=False,
        )

        if response.status_code == 200:
            return response.json()
        else:
            detail = ""
            try:
                detail = response.json().get("detail", {}).get("error", None)
            except Exception:
                pass

            if response.status_code == 429:
                raise UsageLimitExceededError(detail)
            elif response.status_code in [403, 432, 433]:
                raise ForbiddenError(detail)
            elif response.status_code == 401:
                raise InvalidAPIKeyError(detail)
            elif response.status_code == 400:
                raise BadRequestError(detail)
            else:
                raise response.raise_for_status()  # type: ignore


def search_web(query: str, num_results: int) -> str:
    """
    Perform a web search using the provided query and number of results.

    Args:
        query (str): The search query.
        num_results (int): The number of search results to return.

    Returns:
        str: A JSON string containing the search results.
    """
    client = CustomTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    ret: dict[str, Any] = client.search(  # type: ignore
        query,
        topic="general",
        include_raw_content=True,
        max_results=num_results,
        timeout=3000,
    )

    results: list[SearchResult] = []
    for result in ret.get("results", []):
        result = SearchResult(
            title=result.get("title"),
            content=result.get("content"),
            url=result.get("url"),
            raw_content=result.get("raw_content"),
        )
        results.append(result)

    search_results = SearchResults(results=results)
    return search_results.model_dump_json(indent=2)


async def run_web_search(ctx: RunContextWrapper[Any], args: str) -> str:
    """
    Run the web search tool with the provided context and arguments.

    Args:
        ctx (RunContextWrapper): The context wrapper for the run.
        args (str): The arguments for the web search.

    Returns:
        str: The result of the web search.
    """
    if isinstance(args, str):
        parsed = WebSearchArguments.model_validate_json(args)
    elif isinstance(args, dict):
        parsed = WebSearchArguments.model_validate(args)
    else:
        raise ValueError("Invalid argument type for web search")
    return search_web(parsed.query, parsed.num_results)


tool = FunctionTool(
    name="web_search",
    description="Perform a web search using the provided query.",
    params_json_schema=WebSearchArguments.model_json_schema(),
    on_invoke_tool=run_web_search,
)
