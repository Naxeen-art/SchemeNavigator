import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any
import streamlit as st
from utils.logger import logger
from agents.intent_agent import IntentAgent

class MatcherAgent:
    """Match user queries with relevant schemes"""
    
    def __init__(self):
        self.model = self._load_model()
        self.intent_agent = IntentAgent()
        logger.info("Matcher Agent initialized")
    
    @st.cache_resource
    def _load_model(_self):
        """Load sentence transformer model (cached)"""
        logger.info("Loading sentence transformer model...")
        return SentenceTransformer('all-MiniLM-L6-v2')
    
    def _prepare_scheme_text(self, scheme: Dict) -> str:
        """Prepare scheme text for embedding"""
        text_parts = [
            scheme.get('scheme_name', ''),
            scheme.get('description', ''),
            scheme.get('ministry', ''),
            scheme.get('beneficiaries', ''),
            scheme.get('category', ''),
            scheme.get('eligibility', ''),
            scheme.get('benefits', '')
        ]
        return ' '.join([str(part) for part in text_parts if part])
    
    def find_relevant_schemes(self, query: str, schemes: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Find most relevant schemes using semantic search
        """
        if not schemes:
            logger.warning("No schemes to match")
            return []
        
        # Analyze intent
        intent_analysis = self.intent_agent.analyze_intent(query)
        optimized_query = self.intent_agent.generate_search_query(intent_analysis)
        
        logger.info(f"Optimized query: {optimized_query}")
        
        # Prepare scheme texts
        scheme_texts = [self._prepare_scheme_text(scheme) for scheme in schemes]
        
        # Encode query and schemes
        query_embedding = self.model.encode([optimized_query])
        scheme_embeddings = self.model.encode(scheme_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, scheme_embeddings)[0]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Prepare results with metadata
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.25:  # Relevance threshold
                scheme = schemes[idx].copy()
                scheme['relevance_score'] = float(similarities[idx])
                scheme['match_details'] = {
                    'intent': intent_analysis['primary_intent'],
                    'category': intent_analysis['category'],
                    'matched_keywords': intent_analysis['keywords'][:3]
                }
                results.append(scheme)
        
        logger.info(f"Found {len(results)} relevant schemes for query")
        return results
    
    def filter_by_intent(self, schemes: List[Dict], intent: str) -> List[Dict]:
        """Filter schemes based on intent"""
        if not intent or intent == 'general':
            return schemes
        
        intent_fields = {
            'eligibility': ['eligibility', 'criteria'],
            'benefits': ['benefits', 'amount'],
            'documents': ['documents', 'required'],
            'application': ['application', 'process'],
            'deadline': ['deadline', 'date'],
            'contact': ['contact', 'helpline']
        }
        
        filtered = []
        for scheme in schemes:
            scheme_text = self._prepare_scheme_text(scheme).lower()
            keywords = intent_fields.get(intent, [])
            
            if any(keyword in scheme_text for keyword in keywords):
                filtered.append(scheme)
            else:
                # Keep but with lower priority
                scheme['intent_match'] = False
                filtered.append(scheme)
        
        return filtered
    
    def rank_by_entities(self, schemes: List[Dict], entities: Dict) -> List[Dict]:
        """Rank schemes based on entity matching"""
        if not entities:
            return schemes
        
        for scheme in schemes:
            entity_score = 0
            
            # Match by state
            if 'state' in entities:
                scheme_state = scheme.get('state', '').lower()
                if entities['state'].lower() in scheme_state:
                    entity_score += 0.3
            
            # Match by age
            if 'age' in entities:
                min_age = scheme.get('min_age', 0)
                max_age = scheme.get('max_age', 100)
                if min_age <= entities['age'] <= max_age:
                    entity_score += 0.3
            
            # Match by income
            if 'income' in entities:
                max_income = scheme.get('max_income', float('inf'))
                if entities['income'] <= max_income:
                    entity_score += 0.3
            
            scheme['entity_score'] = entity_score
            scheme['relevance_score'] = scheme.get('relevance_score', 0) + entity_score
        
        # Re-sort by combined score
        return sorted(schemes, key=lambda x: x.get('relevance_score', 0), reverse=True)

# Global instance
matcher = MatcherAgent()