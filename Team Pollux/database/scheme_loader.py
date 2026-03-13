import pandas as pd
import json
from typing import List, Dict, Any, Tuple
from utils.logger import logger
from database.mongo_handler import db

class SchemeLoader:
    """Handle loading schemes from different formats"""
    
    @staticmethod
    def load_from_json(json_data: str) -> Tuple[List[Dict], str]:
        """Load schemes from JSON string"""
        try:
            if isinstance(json_data, str):
                data = json.loads(json_data)
            else:
                data = json_data
            
            if isinstance(data, list):
                logger.info(f"Loaded {len(data)} schemes from JSON")
                return data, None
            else:
                logger.info("Loaded single scheme from JSON")
                return [data], None
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return None, f"JSON parsing error: {str(e)}"
    
    @staticmethod
    def load_from_csv(csv_file) -> Tuple[List[Dict], str]:
        """Load schemes from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            
            # Clean column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Convert to dict
            schemes = df.to_dict('records')
            
            # Validate required fields
            required_fields = ['scheme_name', 'description']
            for scheme in schemes:
                for field in required_fields:
                    if field not in scheme:
                        return None, f"Missing required field: {field}"
            
            logger.info(f"Loaded {len(schemes)} schemes from CSV")
            return schemes, None
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            return None, f"CSV parsing error: {str(e)}"
    
    @staticmethod
    def validate_scheme(scheme: Dict) -> Tuple[bool, str]:
        """Validate scheme data"""
        required_fields = ['scheme_name', 'description']
        
        for field in required_fields:
            if field not in scheme or not scheme[field]:
                return False, f"Missing required field: {field}"
        
        # Add scheme_id if not present
        if 'scheme_id' not in scheme:
            scheme['scheme_id'] = scheme['scheme_name'].lower().replace(' ', '_')
        
        return True, "Valid"
    
    @staticmethod
    def save_to_database(schemes: List[Dict]) -> Tuple[bool, str]:
        """Save schemes to database"""
        try:
            # Validate all schemes
            valid_schemes = []
            for scheme in schemes:
                is_valid, msg = SchemeLoader.validate_scheme(scheme)
                if is_valid:
                    valid_schemes.append(scheme)
                else:
                    logger.warning(f"Invalid scheme: {msg}")
            
            if valid_schemes:
                result = db.add_schemes_bulk(valid_schemes)
                return True, f"Successfully saved {len(result.inserted_ids)} schemes"
            else:
                return False, "No valid schemes to save"
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            return False, str(e)