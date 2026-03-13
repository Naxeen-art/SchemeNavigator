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
        """Load sentence transformer model"""
        logger.info("Loading sentence transformer model...")
        return SentenceTransformer("all-MiniLM-L6-v2")

    # -------------------------
    # Prepare scheme text
    # -------------------------

    def _prepare_scheme_text(self, scheme: Dict) -> str:

        text_parts = [
            scheme.get("scheme_name", ""),
            scheme.get("description", ""),
            scheme.get("ministry", ""),
            scheme.get("beneficiaries", ""),
            scheme.get("category", ""),
            scheme.get("eligibility", ""),
            scheme.get("benefits", ""),
        ]

        return " ".join([str(x) for x in text_parts if x])

    # -------------------------
    # Detect user type
    # -------------------------

    def detect_user_type(self, query: str):

        q = query.lower()

        if "farmer" in q or "agriculture" in q:
            return "farmer"

        if "student" in q:
            return "student"

        if "woman" in q or "women" in q:
            return "women"

        if "startup" in q or "business" in q:
            return "entrepreneur"

        return "general"

    # -------------------------
    # Filter schemes
    # -------------------------

    def filter_schemes(self, schemes: List[Dict], user_type: str, query: str):

        query = query.lower()

        filtered = schemes

        # Filter for farmer
        if user_type == "farmer":

            filtered = [
                s
                for s in schemes
                if "agriculture" in str(s.get("category", "")).lower()
                or "farmer" in str(s.get("beneficiaries", "")).lower()
            ]

        # Filter for students
        elif user_type == "student":

            filtered = [
                s
                for s in schemes
                if "education" in str(s.get("category", "")).lower()
                or "student" in str(s.get("beneficiaries", "")).lower()
            ]

        # Filter for women
        elif user_type == "women":

            filtered = [
                s
                for s in schemes
                if "women" in str(s.get("beneficiaries", "")).lower()
                or "women" in str(s.get("category", "")).lower()
            ]

        # State filter
        if "tamil nadu" in query:

            filtered = [
                s
                for s in filtered
                if "tamil nadu" in str(s.get("state", "")).lower()
                or "tamil nadu" in str(s.get("ministry", "")).lower()
            ]

        return filtered if filtered else schemes

    # -------------------------
    # Main matching
    # -------------------------

    def find_relevant_schemes(
        self, query: str, schemes: List[Dict], top_k: int = 5
    ) -> List[Dict]:

        if not schemes:
            logger.warning("No schemes to match")
            return []

        # Detect user type
        user_type = self.detect_user_type(query)

        # Filter schemes
        schemes = self.filter_schemes(schemes, user_type, query)

        logger.info(f"Schemes after filtering: {len(schemes)}")

        # Intent analysis
        intent_analysis = self.intent_agent.analyze_intent(query)
        optimized_query = self.intent_agent.generate_search_query(
            intent_analysis
        )

        logger.info(f"Optimized query: {optimized_query}")

        # Prepare texts
        scheme_texts = [self._prepare_scheme_text(s) for s in schemes]

        # Embeddings
        query_embedding = self.model.encode([optimized_query])
        scheme_embeddings = self.model.encode(scheme_texts)

        # Similarity
        similarities = cosine_similarity(query_embedding, scheme_embeddings)[0]

        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []

        for idx in top_indices:

            if similarities[idx] > 0.35:

                scheme = schemes[idx].copy()

                scheme["relevance_score"] = float(similarities[idx])

                scheme["match_details"] = {
                    "intent": intent_analysis["primary_intent"],
                    "category": intent_analysis["category"],
                    "matched_keywords": intent_analysis["keywords"][:3],
                    "user_type": user_type,
                }

                results.append(scheme)

        logger.info(f"Found {len(results)} relevant schemes")

        return results

    # -------------------------
    # Entity ranking
    # -------------------------

    def rank_by_entities(self, schemes: List[Dict], entities: Dict):

        if not entities:
            return schemes

        for scheme in schemes:

            entity_score = 0

            if "state" in entities:
                if entities["state"].lower() in str(
                    scheme.get("state", "")
                ).lower():
                    entity_score += 0.3

            if "age" in entities:
                min_age = scheme.get("min_age", 0)
                max_age = scheme.get("max_age", 100)

                if min_age <= entities["age"] <= max_age:
                    entity_score += 0.3

            if "income" in entities:
                max_income = scheme.get("max_income", float("inf"))

                if entities["income"] <= max_income:
                    entity_score += 0.3

            scheme["entity_score"] = entity_score
            scheme["relevance_score"] = scheme.get(
                "relevance_score", 0
            ) + entity_score

        return sorted(
            schemes, key=lambda x: x.get("relevance_score", 0), reverse=True
        )


# Global instance
matcher = MatcherAgent()
