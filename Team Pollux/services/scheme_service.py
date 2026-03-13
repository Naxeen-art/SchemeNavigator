from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

from models.scheme_model import SchemeModel, SchemeResponse, QueryAnalysis, UserQuery
from database.mongo_handler import db
from agents.intent_agent import IntentAgent
from agents.matcher_agent import MatcherAgent
from utils.logger import logger
from utils.helpers import validate_scheme_data, format_scheme_for_display

class SchemeService:
    """Business logic service for scheme operations"""
    
    def __init__(self):
        self.intent_agent = IntentAgent()
        self.matcher_agent = MatcherAgent()
        logger.info("Scheme Service initialized")
    
    def search_schemes(self, query: str, user_email: Optional[str] = None, top_k: int = 5) -> Tuple[List[SchemeResponse], QueryAnalysis]:
        """
        Search for relevant schemes based on user query
        
        Args:
            query: User's search query
            user_email: Optional user email for tracking
            top_k: Number of results to return
            
        Returns:
            Tuple of (list of scheme responses, query analysis)
        """
        try:
            # Analyze query intent
            analysis_dict = self.intent_agent.analyze_intent(query)
            analysis = QueryAnalysis(**analysis_dict)
            
            # Get all schemes from database
            schemes_data = db.get_all_schemes()
            
            if not schemes_data:
                logger.warning("No schemes found in database")
                return [], analysis
            
            # Convert to SchemeModel objects
            schemes = []
            for scheme_dict in schemes_data:
                try:
                    scheme = SchemeModel(**scheme_dict)
                    schemes.append(scheme)
                except Exception as e:
                    logger.error(f"Error validating scheme: {e}")
                    continue
            
            # Find relevant schemes
            relevant_schemes = self.matcher_agent.find_relevant_schemes(
                query, 
                [s.dict() for s in schemes], 
                top_k=top_k
            )
            
            # Create response objects
            responses = []
            for scheme_dict in relevant_schemes:
                try:
                    scheme = SchemeModel(**scheme_dict)
                    response = SchemeResponse(
                        scheme=scheme,
                        relevance_score=scheme_dict.get('relevance_score', 0),
                        match_details=scheme_dict.get('match_details', {})
                    )
                    responses.append(response)
                except Exception as e:
                    logger.error(f"Error creating scheme response: {e}")
            
            # Save query if user email provided
            if user_email:
                self.save_user_query(
                    user_email=user_email,
                    query=query,
                    response=f"Found {len(responses)} schemes",
                    analysis=analysis
                )
            
            logger.info(f"Search completed: found {len(responses)} schemes for query")
            return responses, analysis
            
        except Exception as e:
            logger.error(f"Error in search_schemes: {e}")
            return [], QueryAnalysis(primary_intent="error", original_query=query)
    
    def get_scheme_by_id(self, scheme_id: str) -> Optional[SchemeModel]:
        """Get scheme by ID"""
        try:
            scheme_dict = db.get_scheme_by_id(scheme_id)
            if scheme_dict:
                return SchemeModel(**scheme_dict)
            return None
        except Exception as e:
            logger.error(f"Error getting scheme {scheme_id}: {e}")
            return None
    
    def add_scheme(self, scheme_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Add a new scheme"""
        try:
            # Validate and create scheme model
            is_valid, error = validate_scheme_data(scheme_data)
            if not is_valid:
                return False, error
            
            scheme = SchemeModel(**scheme_data)
            
            # Check if scheme already exists
            existing = db.get_scheme_by_id(scheme.scheme_id)
            if existing:
                return False, f"Scheme with ID {scheme.scheme_id} already exists"
            
            # Save to database
            db.add_scheme(scheme.dict())
            logger.info(f"Added new scheme: {scheme.scheme_name}")
            return True, "Scheme added successfully"
            
        except Exception as e:
            logger.error(f"Error adding scheme: {e}")
            return False, str(e)
    
    def add_schemes_bulk(self, schemes_data: List[Dict[str, Any]]) -> Tuple[int, List[str]]:
        """Add multiple schemes"""
        valid_schemes = []
        errors = []
        
        for idx, scheme_data in enumerate(schemes_data):
            try:
                is_valid, error = validate_scheme_data(scheme_data)
                if is_valid:
                    scheme = SchemeModel(**scheme_data)
                    valid_schemes.append(scheme.dict())
                else:
                    errors.append(f"Row {idx + 1}: {error}")
            except Exception as e:
                errors.append(f"Row {idx + 1}: {str(e)}")
        
        if valid_schemes:
            result = db.add_schemes_bulk(valid_schemes)
            logger.info(f"Bulk added {len(valid_schemes)} schemes")
            return len(valid_schemes), errors
        
        return 0, errors
    
    def update_scheme(self, scheme_id: str, update_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Update an existing scheme"""
        try:
            # Validate update data
            existing = self.get_scheme_by_id(scheme_id)
            if not existing:
                return False, f"Scheme {scheme_id} not found"
            
            # Merge with existing data
            updated_data = existing.dict()
            updated_data.update(update_data)
            
            # Validate updated data
            scheme = SchemeModel(**updated_data)
            
            # Update in database
            db.update_scheme(scheme_id, scheme.dict())
            logger.info(f"Updated scheme: {scheme_id}")
            return True, "Scheme updated successfully"
            
        except Exception as e:
            logger.error(f"Error updating scheme {scheme_id}: {e}")
            return False, str(e)
    
    def delete_scheme(self, scheme_id: str) -> Tuple[bool, str]:
        """Delete a scheme"""
        try:
            result = db.delete_scheme(scheme_id)
            if result.deleted_count > 0:
                logger.info(f"Deleted scheme: {scheme_id}")
                return True, "Scheme deleted successfully"
            return False, f"Scheme {scheme_id} not found"
        except Exception as e:
            logger.error(f"Error deleting scheme {scheme_id}: {e}")
            return False, str(e)
    
    def save_user_query(self, user_email: str, query: str, response: str, 
                       analysis: Optional[QueryAnalysis] = None, 
                       schemes_clicked: List[str] = None) -> None:
        """Save user query to database"""
        try:
            user_query = UserQuery(
                user_email=user_email,
                query=query,
                response=response,
                schemes_clicked=schemes_clicked or [],
                analysis=analysis.dict() if analysis else None
            )
            db.save_user_query(
                user_email=user_email,
                query=query,
                response=response,
                schemes_clicked=schemes_clicked
            )
        except Exception as e:
            logger.error(f"Error saving user query: {e}")
    
    def get_user_query_history(self, user_email: str, limit: int = 50) -> List[Dict]:
        """Get user's query history"""
        try:
            return db.get_user_queries(user_email, limit)
        except Exception as e:
            logger.error(f"Error getting user history: {e}")
            return []
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get enhanced dashboard statistics"""
        try:
            basic_stats = db.get_dashboard_stats()
            
            # Get schemes by category
            schemes = db.get_all_schemes()
            schemes_by_category = {}
            for scheme in schemes:
                category = scheme.get('category', 'Uncategorized')
                schemes_by_category[category] = schemes_by_category.get(category, 0) + 1
            
            # Get queries by intent
            queries = db.get_all_queries(limit=500)
            queries_by_intent = {}
            for query in queries:
                if query.get('analysis') and 'primary_intent' in query['analysis']:
                    intent = query['analysis']['primary_intent']
                    queries_by_intent[intent] = queries_by_intent.get(intent, 0) + 1
            
            # Get top schemes (most viewed)
            scheme_views = {}
            for query in queries:
                for scheme in query.get('schemes_clicked', []):
                    scheme_views[scheme] = scheme_views.get(scheme, 0) + 1
            
            top_schemes = [
                {'name': name, 'views': views}
                for name, views in sorted(scheme_views.items(), key=lambda x: x[1], reverse=True)[:5]
            ]
            
            enhanced_stats = {
                **basic_stats,
                'schemes_by_category': schemes_by_category,
                'queries_by_intent': queries_by_intent,
                'top_schemes': top_schemes
            }
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return basic_stats if 'basic_stats' in locals() else {}
    
    def export_schemes(self, format: str = 'json') -> Tuple[bool, Any]:
        """Export all schemes to specified format"""
        try:
            schemes = db.get_all_schemes()
            
            if format == 'json':
                import json
                return True, json.dumps(schemes, indent=2, default=str)
            
            elif format == 'csv':
                df = pd.DataFrame(schemes)
                return True, df.to_csv(index=False)
            
            elif format == 'excel':
                df = pd.DataFrame(schemes)
                return True, df.to_excel(index=False)
            
            else:
                return False, f"Unsupported format: {format}"
                
        except Exception as e:
            logger.error(f"Error exporting schemes: {e}")
            return False, str(e)
    
    def search_by_criteria(self, **criteria) -> List[SchemeModel]:
        """Search schemes by specific criteria"""
        try:
            schemes = db.get_all_schemes()
            results = []
            
            for scheme_dict in schemes:
                match = True
                
                # Apply filters
                if 'category' in criteria and scheme_dict.get('category') != criteria['category']:
                    match = False
                
                if 'state' in criteria and scheme_dict.get('state') != criteria['state']:
                    match = False
                
                if 'min_age' in criteria:
                    if scheme_dict.get('max_age', 100) < criteria['min_age']:
                        match = False
                
                if 'max_age' in criteria:
                    if scheme_dict.get('min_age', 0) > criteria['max_age']:
                        match = False
                
                if 'income' in criteria:
                    max_income = scheme_dict.get('max_income')
                    if max_income and criteria['income'] > max_income:
                        match = False
                
                if match:
                    try:
                        results.append(SchemeModel(**scheme_dict))
                    except:
                        continue
            
            logger.info(f"Found {len(results)} schemes matching criteria")
            return results
            
        except Exception as e:
            logger.error(f"Error in search_by_criteria: {e}")
            return []

# Global service instance
scheme_service = SchemeService()