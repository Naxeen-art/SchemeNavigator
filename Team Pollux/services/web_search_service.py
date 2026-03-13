# services/web_search_service.py

import os
import requests
from typing import List, Dict
from duckduckgo_search import DDGS
from utils.logger import logger


class WebSearchService:
    """Service for searching schemes on the internet"""

    def __init__(self):
        self.enabled = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
        self.timeout = int(os.getenv("WEB_SEARCH_TIMEOUT", "10"))

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Main search method"""

        if not self.enabled:
            logger.info("Web search disabled")
            return []

        results = []

        # Search government scheme portals
        results.extend(self._search_web(query, max_results))

        return results[:max_results]

    # -----------------------------------------------------
    # Generic Government Web Search
    # -----------------------------------------------------

    def _search_web(self, query: str, limit: int) -> List[Dict]:
        """Search government websites"""

        results = []

        try:
            search_query = f"{query} government scheme site:gov.in OR site:tngov.in"

            logger.info(f"Web search query: {search_query}")

            with DDGS() as ddgs:
                search_results = ddgs.text(search_query, max_results=limit)

                for r in search_results:

                    results.append({
                        "scheme_name": r.get("title"),
                        "description": r.get("body"),
                        "source_url": r.get("href"),
                        "source": "web",
                        "category": "Government Scheme"
                    })

        except Exception as e:
            logger.error(f"Web search failed: {e}")

        return results

    # -----------------------------------------------------
    # Optional: myScheme Portal
    # -----------------------------------------------------

    def _search_myscheme(self, query: str, limit: int) -> List[Dict]:

        try:
            logger.info(f"Searching myScheme portal: {query}")

            url = "https://www.myscheme.gov.in/search"

            params = {
                "q": query
            }

            response = requests.get(url, params=params, timeout=self.timeout)

            if response.status_code != 200:
                return []

            # In real implementation you would parse HTML here
            # For now returning empty list
            return []

        except Exception as e:
            logger.error(f"myScheme search failed: {e}")
            return []

    # -----------------------------------------------------
    # Optional: Data.gov.in
    # -----------------------------------------------------

    def _search_datagov(self, query: str, limit: int) -> List[Dict]:

        try:
            logger.info(f"Searching Data.gov.in: {query}")

            # Placeholder for API integration
            return []

        except Exception as e:
            logger.error(f"Data.gov search failed: {e}")
            return []
