# agents/matcher_agent.py - Add error handling for imports

import numpy as np
import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote
import hashlib
import streamlit as st

from utils.logger import logger
from filters.domain_filters import DomainFilter

# Handle sentence-transformers import with fallback
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    TRANSFORMERS_AVAILABLE = True
    logger.info("Sentence transformers available")
except ImportError as e:
    logger.warning(f"Sentence transformers not available: {e}")
    TRANSFORMERS_AVAILABLE = False
    
    # Fallback to sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

# Handle intent agent import
try:
    from agents.intent_agent import IntentAgent
except ImportError:
    # Create a simple intent agent if not available
    class IntentAgent:
        def analyze_intent(self, query):
            return {
                "primary_intent": "general",
                "secondary_intents": [],
                "category": "general",
                "keywords": [],
                "entities": {},
                "original_query": query
            }
        def generate_search_query(self, intent):
            return intent.get("original_query", "")

# Handle web search and translator imports
try:
    from services.web_search_service import WebSearchService
except ImportError:
    class WebSearchService:
        def __init__(self):
            self.enabled = False
        def search(self, query, domain, max_results):
            return []

try:
    from utils.translator import Translator
except ImportError:
    class Translator:
        def translate(self, text, src='auto', dest='en'):
            return text
        def detect_language(self, text):
            return 'en'
        def _contains_tamil(self, text):
            return False


class HybridMatcherAgent:
    """Enhanced matcher with web search, domain filtering, and dual language support"""
    
    def __init__(self):
        self.intent_agent = IntentAgent()
        self.domain_filter = DomainFilter()
        self.web_search = WebSearchService()
        self.translator = Translator()
        self.TRANSFORMERS_AVAILABLE = TRANSFORMERS_AVAILABLE
        
        if self.TRANSFORMERS_AVAILABLE:
            self.model = self._load_model()
        else:
            self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            logger.info("Using TF-IDF vectorizer instead of sentence transformers")

        self.web_search_enabled = True
        self.last_request_time = 0
        self.min_request_interval = 2
        self.search_cache = {}
        self.cache_ttl = 3600

        logger.info("Hybrid Matcher Agent initialized")

    @st.cache_resource
    def _load_model(_self):
        """Load sentence transformer model if available"""
        if TRANSFORMERS_AVAILABLE:
            logger.info("Loading sentence transformer model...")
            return SentenceTransformer("all-MiniLM-L6-v2")
        return None

    def _prepare_scheme_text(self, scheme: Dict) -> str:
        """Prepare scheme text for embedding"""
        parts = [
            scheme.get("scheme_name", ""),
            scheme.get("description", ""),
            scheme.get("ministry", ""),
            scheme.get("beneficiaries", ""),
            scheme.get("category", ""),
            scheme.get("eligibility", ""),
            scheme.get("benefits", ""),
        ]
        return " ".join([str(p) for p in parts if p])

    def detect_query_domain(self, query: str) -> str:
        """Detect which domain the query belongs to"""
        query_lower = query.lower()
        
        domain_keywords = {
            'msme': ['msme', 'business', 'industry', 'enterprise', 'company', 
                     'firm', 'manufacturing', 'startup', 'entrepreneur'],
            'agriculture': ['farmer', 'agriculture', 'farming', 'crop', 'kisan',
                           'farm', 'cultivation', 'irrigation', 'rural',
                           'விவசாயி', 'விவசாயம்'],
            'education': ['student', 'education', 'school', 'college', 'scholarship',
                         'university', 'learning', 'training',
                         'மாணவர்', 'கல்வி', 'பள்ளி'],
            'women': ['woman', 'women', 'female', 'girl', 'lady', 'mother',
                     'wife', 'widow', 'mahila', 'magalir',
                     'பெண்கள்', 'மகளிர்'],
            'health': ['health', 'medical', 'hospital', 'disease', 'treatment',
                      'insurance', 'ayushman', 'arogya',
                      'சுகாதாரம்', 'மருத்துவம்'],
            'housing': ['house', 'home', 'housing', 'shelter', 'awas',
                       'வீடு', 'குடியிருப்பு'],
            'pension': ['pension', 'old age', 'senior citizen', 'retirement',
                       'ஓய்வூதியம்', 'முதியோர்'],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                logger.info(f"Detected domain: {domain}")
                return domain
        
        return 'general'

    def is_tamil_query(self, query: str) -> bool:
        """Check if query contains Tamil text"""
        return self.translator._contains_tamil(query)

    def find_relevant_schemes(self, query: str, local_schemes: List[Dict], top_k: int = 5) -> List[Dict]:
        """Search local DB first, then internet with domain filtering and duplicate removal"""
        
        # Check if query is in Tamil
        is_tamil = self.is_tamil_query(query)
        if is_tamil:
            logger.info("Tamil query detected")
            english_query = self.translator.translate(query, src='ta', dest='en')
            logger.info(f"Translated to English: {english_query}")
        else:
            english_query = query
        
        # Detect domain and analyze intent
        domain = self.detect_query_domain(english_query)
        intent = self.intent_agent.analyze_intent(english_query)
        logger.info(f"Intent analysis - Domain: {domain}, Category: {intent['category']}")
        
        # Search local database
        local_results = self._search_local_db(english_query, local_schemes, top_k * 3)
        
        # Apply filtering and boosting
        filtered_results = self.apply_domain_filtering(english_query, local_results, domain)
        boosted_results = self.apply_intent_boosting(filtered_results, intent)
        
        # Remove duplicates
        unique_results = self._remove_duplicates(boosted_results)
        
        # Take top_k
        final_results = unique_results[:top_k]
        
        # Search internet if needed
        if len(final_results) < top_k and self.web_search_enabled:
            needed = top_k - len(final_results)
            logger.info(f"Searching internet for {needed} additional schemes...")
            
            internet_results = self.web_search.search(english_query, domain, needed * 3)
            
            filtered_internet = self.apply_domain_filtering(english_query, internet_results, domain)
            boosted_internet = self.apply_intent_boosting(filtered_internet, intent)
            
            # Get existing IDs to avoid duplicates
            existing_ids = [s.get('scheme_id') for s in final_results if s.get('scheme_id')]
            unique_internet = self._remove_duplicates(boosted_internet, existing_ids)
            
            final_results.extend(unique_internet[:needed])
        
        # Final reranking
        if self.TRANSFORMERS_AVAILABLE:
            final_results = self._rerank_results(final_results, english_query)
        
        # Remove any remaining duplicates
        final_results = self._remove_duplicates(final_results)
        
        # Translate back to Tamil if needed
        if is_tamil:
            final_results = self._translate_results(final_results, 'ta')
        
        logger.info(f"Returning {len(final_results)} relevant schemes for domain '{domain}'")
        return final_results[:top_k]

    def _remove_duplicates(self, schemes: List[Dict], existing_ids: List[str] = None) -> List[Dict]:
        """Remove duplicate schemes based on scheme_id"""
        seen_ids = set(existing_ids or [])
        unique_schemes = []
        
        for scheme in schemes:
            scheme_id = scheme.get('scheme_id')
            
            if not scheme_id and scheme.get('scheme_name'):
                scheme_id = scheme['scheme_name'].lower().replace(' ', '_')
                scheme['scheme_id'] = scheme_id
            
            if scheme_id and scheme_id not in seen_ids:
                seen_ids.add(scheme_id)
                unique_schemes.append(scheme)
            elif not scheme_id:
                # If no ID, use name+source as key
                unique_key = f"{scheme.get('scheme_name', '')}_{scheme.get('source', '')}"
                if unique_key not in seen_ids:
                    seen_ids.add(unique_key)
                    unique_schemes.append(scheme)
        
        if len(schemes) > len(unique_schemes):
            logger.info(f"Removed {len(schemes) - len(unique_schemes)} duplicates")
        
        return unique_schemes

    def _translate_results(self, schemes: List[Dict], dest_lang: str = 'ta') -> List[Dict]:
        """Translate scheme results to target language"""
        for scheme in schemes:
            scheme['scheme_name'] = self.translator.translate(scheme.get('scheme_name', ''), dest=dest_lang)
            scheme['description'] = self.translator.translate(scheme.get('description', ''), dest=dest_lang)
            
            if scheme.get('eligibility'):
                scheme['eligibility'] = self.translator.translate(scheme['eligibility'], dest=dest_lang)
            if scheme.get('benefits'):
                scheme['benefits'] = self.translator.translate(scheme['benefits'], dest=dest_lang)
            if scheme.get('application_process'):
                scheme['application_process'] = self.translator.translate(scheme['application_process'], dest=dest_lang)
        
        return schemes

    def apply_domain_filtering(self, query: str, schemes: List[Dict], domain: str) -> List[Dict]:
        """Apply domain-specific filtering"""
        if not schemes:
            return []
        
        # Simple filtering based on domain
        if domain != 'general':
            filtered = []
            domain_lower = domain.lower()
            
            for scheme in schemes:
                scheme_text = f"{scheme.get('category', '')} {scheme.get('description', '')}".lower()
                if domain_lower in scheme_text:
                    filtered.append(scheme)
                else:
                    # Keep with lower score
                    scheme['relevance_score'] = scheme.get('relevance_score', 0.5) * 0.8
                    filtered.append(scheme)
            
            logger.info(f"Domain filter ({domain}): kept {len(filtered)} schemes")
            return filtered
        
        return schemes

    def apply_intent_boosting(self, schemes: List[Dict], intent: Dict) -> List[Dict]:
        """Boost scores based on intent analysis"""
        if not schemes:
            return schemes
        
        for scheme in schemes:
            # Simple boosting based on category match
            if intent.get('category') != 'general':
                scheme_category = scheme.get('category', '').lower()
                if intent['category'] in scheme_category:
                    scheme['relevance_score'] = scheme.get('relevance_score', 0.5) * 1.2
        
        return sorted(schemes, key=lambda x: x.get('relevance_score', 0), reverse=True)

    def _search_local_db(self, query, local_schemes, top_k):
        """Search schemes in local database"""
        if not local_schemes:
            return []

        if self.TRANSFORMERS_AVAILABLE:
            # Use sentence transformers
            intent = self.intent_agent.analyze_intent(query)
            optimized_query = self.intent_agent.generate_search_query(intent)

            scheme_texts = [self._prepare_scheme_text(scheme) for scheme in local_schemes]

            query_embedding = self.model.encode([optimized_query])
            scheme_embeddings = self.model.encode(scheme_texts)

            similarities = cosine_similarity(query_embedding, scheme_embeddings)[0]

            results = []
            for idx, score in enumerate(similarities):
                if score > 0.25:
                    scheme = local_schemes[idx].copy()
                    scheme["relevance_score"] = float(score)
                    scheme["source"] = "local_database"
                    scheme["source_type"] = "local"
                    results.append(scheme)
        else:
            # Use TF-IDF
            scheme_texts = [self._prepare_scheme_text(scheme) for scheme in local_schemes]
            
            try:
                all_texts = [query] + scheme_texts
                vectors = self.vectorizer.fit_transform(all_texts)
                
                query_vector = vectors[0:1]
                scheme_vectors = vectors[1:]
                
                similarities = cosine_similarity(query_vector, scheme_vectors)[0]
                
                results = []
                for idx, score in enumerate(similarities):
                    if score > 0.1:
                        scheme = local_schemes[idx].copy()
                        scheme["relevance_score"] = float(score)
                        scheme["source"] = "local_database"
                        scheme["source_type"] = "local"
                        results.append(scheme)
            except Exception as e:
                logger.error(f"TF-IDF error: {e}")
                results = []

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

    def _rerank_results(self, results, query):
        """Re-rank combined results using transformers if available"""
        if not results or not self.TRANSFORMERS_AVAILABLE:
            return results

        texts = [f"{r.get('scheme_name','')} {r.get('description','')}" for r in results]
        
        query_embedding = self.model.encode([query])
        result_embeddings = self.model.encode(texts)
        
        similarities = cosine_similarity(query_embedding, result_embeddings)[0]
        
        for i, r in enumerate(results):
            original_score = r.get('relevance_score', 0.5)
            new_score = float(similarities[i])
            r["relevance_score"] = (original_score * 0.4) + (new_score * 0.6)
        
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    def clear_cache(self):
        """Clear the search cache"""
        self.search_cache.clear()
        logger.info("Search cache cleared")

# Global instance
matcher = HybridMatcherAgent()