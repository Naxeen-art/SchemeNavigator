# filters/domain_filters.py
from typing import List, Dict
import re

class DomainFilter:
    """Domain-specific filters for different query types"""
    
    @staticmethod
    def filter_msme_schemes(schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Filter schemes for MSME/business queries
        Returns only business-related schemes
        """
        
        # Business-related keywords to look for
        business_keywords = [
            'msme', 'business', 'enterprise', 'industry', 'manufacturing',
            'startup', 'entrepreneur', 'loan', 'subsidy', 'capital',
            'investment', 'small business', 'medium enterprise', 'udyam',
            'udyog', 'industrial', 'commercial', 'trade', 'venture',
            'micro', 'small scale', 'ssi', 'tiny', 'cottage'
        ]
        
        # Business-related categories (keep these)
        business_categories = [
            'business', 'msme', 'industrial subsidy', 'startup support',
            'enterprise development', 'industrial promotion', 'trade',
            'commerce', 'industry', 'manufacturing', 'entrepreneurship',
            'loan', 'financial assistance', 'credit', 'subsidy'
        ]
        
        # Irrelevant categories for MSME queries (exclude these)
        irrelevant_categories = [
            'education', 'transport', 'marriage assistance', 'women empowerment',
            'pension', 'health', 'housing', 'child protection', 'free laptop',
            'free bus', 'scholarship', 'student', 'farmer', 'agriculture',
            'crop', 'irrigation', 'old age', 'disability', 'widow'
        ]
        
        filtered_schemes = []
        
        for scheme in schemes:
            scheme_name = scheme.get('scheme_name', '').lower()
            scheme_desc = scheme.get('description', '').lower()
            scheme_category = scheme.get('category', '').lower()
            
            # Check if scheme is business-related
            is_business = False
            
            # Check category
            if any(cat in scheme_category for cat in business_categories):
                is_business = True
            
            # Check name and description for business keywords
            if any(keyword in scheme_name or keyword in scheme_desc 
                   for keyword in business_keywords):
                is_business = True
            
            # If it's in irrelevant categories, only keep if strongly business-indicated
            if any(irr in scheme_category for irr in irrelevant_categories):
                # Check if it has strong business indicators
                strong_business = any(keyword in scheme_name or keyword in scheme_desc 
                                      for keyword in ['msme', 'business', 'industry', 'enterprise'])
                if not strong_business:
                    continue
                is_business = True
            
            if is_business:
                filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    @staticmethod
    def filter_agriculture_schemes(schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Filter schemes for agriculture/farmer queries
        Returns only agriculture-related schemes
        """
        
        agriculture_keywords = [
            'farmer', 'agriculture', 'farming', 'crop', 'kisan',
            'farm', 'cultivation', 'irrigation', 'rural', 'land',
            'soil', 'seed', 'fertilizer', 'pesticide', 'harvest',
            'livestock', 'dairy', 'poultry', 'fisheries', 'animal husbandry',
            'organic', 'horticulture', 'plantation'
        ]
        
        agriculture_categories = [
            'agriculture', 'farming', 'crop', 'rural development',
            'farmer welfare', 'irrigation', 'horticulture'
        ]
        
        irrelevant_categories = [
            'education', 'transport', 'women empowerment', 'pension',
            'health', 'housing', 'child protection', 'msme', 'business',
            'startup', 'industry', 'manufacturing'
        ]
        
        filtered_schemes = []
        
        for scheme in schemes:
            scheme_name = scheme.get('scheme_name', '').lower()
            scheme_desc = scheme.get('description', '').lower()
            scheme_category = scheme.get('category', '').lower()
            
            is_agriculture = False
            
            if any(cat in scheme_category for cat in agriculture_categories):
                is_agriculture = True
            
            if any(keyword in scheme_name or keyword in scheme_desc 
                   for keyword in agriculture_keywords):
                is_agriculture = True
            
            if any(irr in scheme_category for irr in irrelevant_categories):
                if not any(keyword in scheme_name for keyword in ['farmer', 'kisan', 'agriculture']):
                    continue
                is_agriculture = True
            
            if is_agriculture:
                filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    @staticmethod
    def filter_education_schemes(schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Filter schemes for education/student queries
        """
        
        education_keywords = [
            'student', 'education', 'school', 'college', 'scholarship',
            'university', 'learning', 'training', 'academic', 'hostel',
            'book', 'laptop', 'fee', 'admission', 'study', 'exam'
        ]
        
        education_categories = [
            'education', 'scholarship', 'student welfare', 'academic'
        ]
        
        irrelevant_categories = [
            'agriculture', 'business', 'msme', 'women empowerment',
            'pension', 'health', 'housing', 'transport', 'marriage'
        ]
        
        filtered_schemes = []
        
        for scheme in schemes:
            scheme_name = scheme.get('scheme_name', '').lower()
            scheme_desc = scheme.get('description', '').lower()
            scheme_category = scheme.get('category', '').lower()
            
            is_education = False
            
            if any(cat in scheme_category for cat in education_categories):
                is_education = True
            
            if any(keyword in scheme_name or keyword in scheme_desc 
                   for keyword in education_keywords):
                is_education = True
            
            if any(irr in scheme_category for irr in irrelevant_categories):
                if not any(keyword in scheme_name for keyword in ['student', 'scholar', 'education']):
                    continue
                is_education = True
            
            if is_education:
                filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    @staticmethod
    def filter_women_schemes(schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Filter schemes for women-specific queries
        """
        
        women_keywords = [
            'woman', 'women', 'female', 'girl', 'lady', 'mother',
            'wife', 'widow', 'mahila', 'magalir', 'stree', 'kanya',
            'daughter', 'bride', 'maternal', 'pregnant'
        ]
        
        women_categories = [
            'women empowerment', 'women welfare', 'girl child',
            'maternity', 'marriage assistance', 'widow pension'
        ]
        
        filtered_schemes = []
        
        for scheme in schemes:
            scheme_name = scheme.get('scheme_name', '').lower()
            scheme_desc = scheme.get('description', '').lower()
            scheme_category = scheme.get('category', '').lower()
            
            is_women = False
            
            if any(cat in scheme_category for cat in women_categories):
                is_women = True
            
            if any(keyword in scheme_name or keyword in scheme_desc 
                   for keyword in women_keywords):
                is_women = True
            
            if is_women:
                filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    @staticmethod
    def filter_health_schemes(schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Filter schemes for health/medical queries
        """
        
        health_keywords = [
            'health', 'medical', 'hospital', 'disease', 'treatment',
            'insurance', 'ayushman', 'arogya', 'medicine', 'doctor',
            'surgery', 'clinic', 'wellness', 'nutrition', 'vaccination'
        ]
        
        health_categories = [
            'health', 'medical', 'insurance', 'healthcare'
        ]
        
        filtered_schemes = []
        
        for scheme in schemes:
            scheme_name = scheme.get('scheme_name', '').lower()
            scheme_desc = scheme.get('description', '').lower()
            scheme_category = scheme.get('category', '').lower()
            
            is_health = False
            
            if any(cat in scheme_category for cat in health_categories):
                is_health = True
            
            if any(keyword in scheme_name or keyword in scheme_desc 
                   for keyword in health_keywords):
                is_health = True
            
            if is_health:
                filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    @staticmethod
    def filter_pension_schemes(schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Filter schemes for pension/old age queries
        """
        
        pension_keywords = [
            'pension', 'old age', 'senior citizen', 'retirement',
            'elderly', 'aged', 'destitute', 'widow', 'disabled'
        ]
        
        pension_categories = [
            'pension', 'social security', 'old age welfare'
        ]
        
        filtered_schemes = []
        
        for scheme in schemes:
            scheme_name = scheme.get('scheme_name', '').lower()
            scheme_desc = scheme.get('description', '').lower()
            scheme_category = scheme.get('category', '').lower()
            
            is_pension = False
            
            if any(cat in scheme_category for cat in pension_categories):
                is_pension = True
            
            if any(keyword in scheme_name or keyword in scheme_desc 
                   for keyword in pension_keywords):
                is_pension = True
            
            if is_pension:
                filtered_schemes.append(scheme)
        
        return filtered_schemes
    
    @staticmethod
    def filter_by_domain(domain: str, schemes: List[Dict], query: str = "") -> List[Dict]:
        """
        Generic filter that calls the appropriate domain-specific filter
        """
        domain_filters = {
            'msme': DomainFilter.filter_msme_schemes,
            'agriculture': DomainFilter.filter_agriculture_schemes,
            'education': DomainFilter.filter_education_schemes,
            'women': DomainFilter.filter_women_schemes,
            'health': DomainFilter.filter_health_schemes,
            'pension': DomainFilter.filter_pension_schemes,
        }
        
        if domain in domain_filters:
            return domain_filters[domain](schemes, query)
        
        # Return all schemes for unknown domains
        return schemes


# Create a convenience function for easy importing
def get_domain_filter():
    """Return an instance of DomainFilter"""
    return DomainFilter()