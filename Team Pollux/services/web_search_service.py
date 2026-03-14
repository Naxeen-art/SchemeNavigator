# services/web_search_service.py

import os
import requests
import hashlib
import time
from typing import List, Dict
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from utils.logger import logger
import random

class WebSearchService:
    """Service for searching schemes on the internet"""

    def __init__(self):
        self.enabled = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
        self.timeout = int(os.getenv("WEB_SEARCH_TIMEOUT", "15"))
        self.scheme_portals = [
            "myscheme.gov.in",
            "india.gov.in",
            "tnschemes.tn.gov.in",
            "tn.gov.in/scheme",
            "data.gov.in",
            "pmkisan.gov.in",
            "scholarships.gov.in",
            "pmjay.gov.in",
            "msme.gov.in"
        ]
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        self.request_delay = 1  # Delay between requests to avoid rate limiting

    def search(self, query: str, domain: str = 'general', max_results: int = 5) -> List[Dict]:
        """Main search method with domain filtering and retry logic"""
        
        if not self.enabled:
            logger.info("Web search disabled")
            return []

        results = []
        
        # Add domain-specific keywords
        domain_keywords = {
            'msme': 'MSME business loan subsidy scheme',
            'agriculture': 'farmer agriculture crop kisan scheme',
            'education': 'student scholarship education loan scheme',
            'women': 'women mahila empowerment scheme',
            'health': 'health medical insurance ayushman scheme',
            'housing': 'housing home loan awas scheme',
            'pension': 'pension old age senior citizen scheme'
        }
        
        search_query = query
        if domain in domain_keywords and domain != 'general':
            search_query = f"{query} {domain_keywords[domain]}"
        
        # Try multiple search methods
        try:
            # Method 1: Government portal search
            portal_results = self._search_government_portals(search_query, max_results)
            results.extend(portal_results)
            
            # Method 2: DuckDuckGo search
            if len(results) < max_results:
                time.sleep(self.request_delay)
                ddg_results = self._search_duckduckgo(search_query, max_results - len(results))
                results.extend(ddg_results)
            
            # Method 3: Direct API calls to known scheme portals
            if len(results) < max_results:
                time.sleep(self.request_delay)
                api_results = self._search_scheme_apis(search_query, max_results - len(results))
                results.extend(api_results)
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
        
        # Remove duplicates and return
        return self._remove_duplicates(results)[:max_results]

    def _search_government_portals(self, query: str, limit: int) -> List[Dict]:
        """Search specific government scheme portals"""
        results = []
        
        for portal in self.scheme_portals[:3]:  # Limit to first 3 portals
            try:
                search_query = f"{query} site:{portal}"
                
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(search_query, max_results=limit))
                    
                    for r in search_results:
                        result = {
                            "scheme_id": f"web_{hashlib.md5(r.get('href', '').encode()).hexdigest()[:8]}",
                            "scheme_name": r.get("title", "Government Scheme"),
                            "description": r.get("body", "")[:300],
                            "official_url": r.get("href"),
                            "source": portal,
                            "source_type": "internet",
                            "category": "Government Scheme",
                            "relevance_score": 0.7
                        }
                        results.append(result)
                        
            except Exception as e:
                logger.debug(f"Portal search failed for {portal}: {e}")
                continue
        
        return results

    def _search_duckduckgo(self, query: str, limit: int) -> List[Dict]:
        """General DuckDuckGo web search"""
        results = []

        try:
            # Try different search variations
            search_variations = [
                f"{query} government scheme",
                f"{query} yojana",
                f"{query} scholarship",
                f"{query} loan subsidy"
            ]
            
            for search_query in search_variations[:2]:  # Try first 2 variations
                with DDGS() as ddgs:
                    search_results = ddgs.text(search_query, max_results=limit * 2)
                    
                    for r in search_results:
                        title = r.get("title", "").lower()
                        body = r.get("body", "").lower()
                        
                        # Filter for relevant content
                        if any(keyword in title or keyword in body for keyword in 
                               ['scheme', 'yojana', 'scholarship', 'loan', 'subsidy', 'grant']):
                            result = {
                                "scheme_id": f"web_{hashlib.md5(r.get('href', '').encode()).hexdigest()[:8]}",
                                "scheme_name": r.get("title", "Government Scheme"),
                                "description": r.get("body", "")[:300],
                                "official_url": r.get("href"),
                                "source": "web_search",
                                "source_type": "internet",
                                "relevance_score": 0.6
                            }
                            results.append(result)
                            
                            if len(results) >= limit:
                                break
                    
                    if len(results) >= limit:
                        break

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")

        return results

    def _search_scheme_apis(self, query: str, limit: int) -> List[Dict]:
        """Search known scheme APIs (mock implementation)"""
        results = []
        
        # This is a mock - in production, you'd integrate with real APIs
        mock_schemes = {
            'agriculture': [
                {
                    "scheme_id": "pmkisan_api_001",
                    "scheme_name": "PM Kisan Samman Nidhi",
                    "description": "Income support of ₹6000/year for farmers",
                    "ministry": "Ministry of Agriculture",
                    "official_url": "https://pmkisan.gov.in",
                    "category": "Agriculture"
                },
                {
                    "scheme_id": "pmfby_api_002",
                    "scheme_name": "PM Fasal Bima Yojana",
                    "description": "Crop insurance scheme for farmers",
                    "ministry": "Ministry of Agriculture",
                    "official_url": "https://pmfby.gov.in",
                    "category": "Agriculture"
                }
            ],
            'education': [
                {
                    "scheme_id": "nsp_api_001",
                    "scheme_name": "National Scholarship Portal",
                    "description": "Scholarships for students",
                    "ministry": "Ministry of Education",
                    "official_url": "https://scholarships.gov.in",
                    "category": "Education"
                }
            ],
            'women': [
                {
                    "scheme_id": "pmmy_api_001",
                    "scheme_name": "Pradhan Mantri Matru Vandana Yojana",
                    "description": "Maternity benefit program",
                    "ministry": "Ministry of Women and Child Development",
                    "official_url": "https://wcd.nic.in",
                    "category": "Women"
                }
            ]
        }
        
        # Match query with categories
        for category, schemes in mock_schemes.items():
            if category in query.lower():
                for scheme in schemes[:limit]:
                    scheme_copy = scheme.copy()
                    scheme_copy["relevance_score"] = 0.65
                    scheme_copy["source"] = "api"
                    scheme_copy["source_type"] = "internet"
                    results.append(scheme_copy)
        
        return results

    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL and name"""
        seen_urls = set()
        seen_names = set()
        unique_results = []
        
        for result in results:
            url = result.get('official_url')
            name = result.get('scheme_name', '').lower()
            
            # Check for duplicates
            url_dup = url and url in seen_urls
            name_dup = name and name in seen_names
            
            if not url_dup and not name_dup:
                if url:
                    seen_urls.add(url)
                if name:
                    seen_names.add(name)
                unique_results.append(result)
        
        return unique_results