# utils/translator.py

import requests
import hashlib
from typing import Optional
from utils.logger import logger

class Translator:
    """Translation service for English-Tamil language support"""
    
    def __init__(self):
        self.cache = {}
        self.api_url = "https://translate.googleapis.com/translate_a/single"
        
    def translate(self, text: str, src: str = 'auto', dest: str = 'en') -> str:
        """
        Translate text between languages
        Args:
            text: Text to translate
            src: Source language code ('auto', 'en', 'ta')
            dest: Destination language code ('en', 'ta')
        Returns:
            Translated text
        """
        if not text:
            return text
        
        # Create cache key
        cache_key = hashlib.md5(f"{text}_{src}_{dest}".encode()).hexdigest()
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # If source is auto and text contains Tamil, set src to 'ta'
            if src == 'auto' and self._contains_tamil(text):
                src = 'ta'
            
            # Use Google Translate API
            params = {
                'client': 'gtx',
                'sl': src,
                'tl': dest,
                'dt': 't',
                'q': text
            }
            
            response = requests.get(self.api_url, params=params, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                translated_text = ''.join([part[0] for part in result[0] if part[0]])
                
                # Cache the result
                self.cache[cache_key] = translated_text
                return translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
        
        # Return original text if translation fails
        return text
    
    def _contains_tamil(self, text: str) -> bool:
        """Check if text contains Tamil characters"""
        tamil_range = range(0x0B80, 0x0BFF + 1)
        return any(ord(char) in tamil_range for char in text)
    
    def get_language_name(self, lang_code: str) -> str:
        """Get language name from code"""
        languages = {
            'en': 'English',
            'ta': 'தமிழ்'
        }
        return languages.get(lang_code, lang_code)
    
    def detect_language(self, text: str) -> str:
        """Detect if text is Tamil or English"""
        if self._contains_tamil(text):
            return 'ta'
        return 'en'