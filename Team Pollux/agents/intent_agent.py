import re
from typing import Dict, List
from utils.logger import logger


class IntentAgent:
    """Analyze user intent from query"""

    def __init__(self):

        self.intent_patterns = {

            "eligibility": [
                r"eligible",
                r"qualif",
                r"can i apply",
                r"who can",
                r"am i",
                r"criteria",
                r"requirements",
            ],

            "benefits": [
                r"benefit",
                r"get",
                r"receive",
                r"amount",
                r"money",
                r"financial",
                r"support",
                r"assistance",
            ],

            "documents": [
                r"document",
                r"paper",
                r"certificate",
                r"proof",
                r"need to submit",
                r"required",
            ],

            "application": [
                r"apply",
                r"how to",
                r"process",
                r"procedure",
                r"application",
                r"register",
            ],

            "deadline": [
                r"deadline",
                r"last date",
                r"closing",
                r"expir",
                r"when",
                r"timeline",
            ],

            "contact": [
                r"contact",
                r"helpline",
                r"phone",
                r"email",
                r"office",
                r"department",
                r"official",
            ],
        }

        self.category_patterns = {

            "agriculture": [
                r"farm",
                r"agricultur",
                r"crop",
                r"kisan",
                r"rural",
            ],

            "education": [
                r"student",
                r"scholar",
                r"school",
                r"college",
                r"education",
            ],

            "health": [
                r"health",
                r"medical",
                r"hospital",
                r"disease",
                r"treatment",
            ],

            "housing": [
                r"house",
                r"home",
                r"shelter",
                r"housing",
                r"property",
            ],

            "business": [
                r"business",
                r"entrepreneur",
                r"startup",
                r"industry",
                r"sme",
            ],

            "social_welfare": [
                r"welfare",
                r"social",
                r"woman",
                r"child",
                r"disabled",
            ],

            "employment": [
                r"job",
                r"employ",
                r"unemployment",
                r"work",
                r"career",
            ],
        }

        logger.info("Intent Agent initialized")

    # --------------------------------------------------

    def analyze_intent(self, query: str) -> Dict:
        """Analyze user query to determine intent"""

        query_lower = query.lower()

        # Detect primary intent
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():

            score = 0

            for pattern in patterns:

                if re.search(pattern, query_lower):
                    score += 1

            if score > 0:
                intent_scores[intent] = score

        sorted_intents = sorted(
            intent_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        primary_intent = (
            sorted_intents[0][0] if sorted_intents else "general"
        )

        secondary_intents = [
            intent for intent, _ in sorted_intents[1:3]
        ]

        # --------------------------------------------------

        # Detect category
        category_scores = {}

        for category, patterns in self.category_patterns.items():

            score = 0

            for pattern in patterns:

                if re.search(pattern, query_lower):
                    score += 1

            if score > 0:
                category_scores[category] = score

        primary_category = (
            max(category_scores, key=category_scores.get)
            if category_scores
            else "general"
        )

        # --------------------------------------------------

        # Extract keywords
        keywords = re.findall(r"\b\w{4,}\b", query_lower)

        keywords = [
            k for k in keywords
            if k not in [
                "this",
                "that",
                "with",
                "from",
                "have",
                "what",
                "which",
            ]
        ]

        # --------------------------------------------------

        entities = self._extract_entities(query)

        result = {

            "primary_intent": primary_intent,
            "secondary_intents": secondary_intents,
            "category": primary_category,
            "keywords": keywords[:10],
            "entities": entities,
            "original_query": query,
        }

        logger.debug(f"Intent analysis: {result}")

        return result

    # --------------------------------------------------

    def _extract_entities(self, query: str) -> Dict:
        """Extract named entities"""

        entities = {}

        # Extract age
        age_match = re.search(
            r"(\d+)\s*(?:year|yr)",
            query,
            re.IGNORECASE,
        )

        if age_match:
            entities["age"] = int(age_match.group(1))

        # Extract income
        income_match = re.search(
            r"(?:income|earning|salary)\s*(?:of|is)?\s*(?:rs\.?|inr)?\s*(\d+(?:,\d+)?(?:\.\d+)?)",
            query,
            re.IGNORECASE,
        )

        if income_match:
            entities["income"] = float(
                income_match.group(1).replace(",", "")
            )

        # Extract state
        states = [
            "delhi",
            "mumbai",
            "karnataka",
            "tamil nadu",
            "uttar pradesh",
            "maharashtra",
            "gujarat",
            "west bengal",
            "rajasthan",
        ]

        for state in states:

            if state in query.lower():
                entities["state"] = state
                break

        return entities

    # --------------------------------------------------

    def generate_search_query(self, intent_analysis: Dict) -> str:
        """Generate optimized search query"""

        query_parts = []

        if intent_analysis["category"] != "general":
            query_parts.append(intent_analysis["category"])

        intent_mapping = {

            "eligibility": "eligibility criteria",
            "benefits": "benefits amount",
            "documents": "documents required",
            "application": "application process",
            "deadline": "deadline date",
            "contact": "contact information",
        }

        if intent_analysis["primary_intent"] in intent_mapping:

            query_parts.append(
                intent_mapping[intent_analysis["primary_intent"]]
            )

        query_parts.extend(intent_analysis["keywords"][:3])

        if "state" in intent_analysis["entities"]:
            query_parts.append(
                intent_analysis["entities"]["state"]
            )

        return " ".join(query_parts)


# --------------------------------------------------
# GLOBAL OBJECT (THIS FIXES YOUR ERROR)

intent_agent = IntentAgent()
