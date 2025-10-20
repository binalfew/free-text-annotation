import re
import html
from typing import List, Dict
import unicodedata

class TextCleaner:
    """
    Clean and normalize raw news article text.
    """
    
    def __init__(self):
        """Initialize text cleaner."""
        # Common HTML patterns to remove
        self.html_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<style[^>]*>.*?</style>',
            r'<[^>]+>',  # All HTML tags
        ]
        
        # Navigation/boilerplate patterns
        self.boilerplate_patterns = [
            r'Share on Facebook',
            r'Tweet this',
            r'Print this article',
            r'Advertisement',
            r'Related Articles?:',
            r'Read more:',
            r'Copyright \d{4}',
        ]
    
    def clean(self, text: str) -> str:
        """
        Clean raw article text.
        
        Args:
            text: Raw article text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        for pattern in self.html_patterns:
            text = re.sub(pattern, ' ', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove boilerplate
        for pattern in self.boilerplate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Fix encoding issues
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove multiple blank lines
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        return text
    
    def extract_metadata(self, text: str) -> Dict:
        """
        Extract article metadata if present.
        
        Args:
            text: Article text
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Try to extract dateline (location - date)
        dateline_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–]\s*'
        match = re.match(dateline_pattern, text)
        if match:
            metadata['dateline_location'] = match.group(1)
        
        # Try to extract source
        source_patterns = [
            r'\((Reuters|AFP|AP|BBC)\)',
            r'By\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        for pattern in source_patterns:
            match = re.search(pattern, text)
            if match:
                metadata['source'] = match.group(1)
                break
        
        return metadata
