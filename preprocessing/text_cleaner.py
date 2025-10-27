import re
import html
import logging
from typing import List, Dict, Optional, Set
import unicodedata
from datetime import datetime

class TextCleaner:
    """
    Enhanced text cleaner for African news articles and violent event content.
    Handles HTML, encoding issues, boilerplate, and extracts metadata.
    """
    
    def __init__(self, enable_logging: bool = False, preserve_quotes: bool = True):
        """
        Initialize enhanced text cleaner.
        
        Args:
            enable_logging: Enable debug logging
            preserve_quotes: Preserve quote marks in text
        """
        self.logger = logging.getLogger(__name__) if enable_logging else None
        self.preserve_quotes = preserve_quotes
        
        # Comprehensive HTML patterns to remove
        self.html_patterns = [
            r'<script[^>]*>.*?</script>',  # Scripts
            r'<style[^>]*>.*?</style>',    # Styles
            r'<noscript[^>]*>.*?</noscript>',  # NoScript
            r'<iframe[^>]*>.*?</iframe>',  # Iframes
            r'<object[^>]*>.*?</object>',  # Objects
            r'<embed[^>]*>.*?</embed>',   # Embeds
            r'<form[^>]*>.*?</form>',     # Forms
            r'<input[^>]*>',              # Input fields
            r'<button[^>]*>.*?</button>',  # Buttons
            r'<nav[^>]*>.*?</nav>',       # Navigation
            r'<header[^>]*>.*?</header>', # Headers
            r'<footer[^>]*>.*?</footer>', # Footers
            r'<aside[^>]*>.*?</aside>',   # Sidebars
            r'<[^>]+>',                   # All other HTML tags
        ]
        
        # Enhanced boilerplate patterns for news sites
        self.boilerplate_patterns = [
            # Social media
            r'Share on Facebook',
            r'Share on Twitter',
            r'Tweet this',
            r'Follow us on',
            r'Like us on Facebook',
            r'Subscribe to our newsletter',
            
            # Navigation
            r'Print this article',
            r'Email this article',
            r'Related Articles?:',
            r'Read more:',
            r'Continue reading',
            r'Full story',
            r'More details',
            r'Breaking news',
            r'Latest updates',
            
            # Advertisements
            r'Advertisement',
            r'Sponsored content',
            r'Promoted',
            r'Partner content',
            r'Advertorial',
            
            # Copyright and legal
            r'Copyright \d{4}',
            r'All rights reserved',
            r'Terms of use',
            r'Privacy policy',
            r'Cookie policy',
            
            # African news specific
            r'Subscribe to our newsletter',
            r'Get the latest news',
            r'Follow us for updates',
            r'Join our community',
            r'Download our app',
            
            # Common news site elements
            r'Loading\.\.\.',
            r'Please wait\.\.\.',
            r'Error loading content',
            r'Content not available',
            r'This page is loading',
        ]
        
        # African news source patterns
        self.african_sources = {
            'BBC Africa', 'CNN Africa', 'Al Jazeera', 'Reuters Africa',
            'AFP', 'AP', 'VOA Africa', 'DW Africa', 'France 24',
            'Nigerian Tribune', 'Premium Times', 'The Guardian Nigeria',
            'Daily Trust', 'Vanguard', 'This Day', 'The Punch',
            'Kenya Daily Nation', 'The Standard', 'Daily Monitor Uganda',
            'Mail & Guardian South Africa', 'City Press', 'Sowetan'
        }
        
        # Violence-related terms that should be preserved
        self.violence_terms = {
            'attack', 'attacked', 'attacking', 'attacks',
            'killed', 'killing', 'murdered', 'murder',
            'bombed', 'bombing', 'explosion', 'exploded',
            'shot', 'shooting', 'gunfire', 'gunmen',
            'militants', 'terrorists', 'insurgents',
            'violence', 'violent', 'conflict', 'war',
            'casualties', 'injured', 'wounded', 'dead'
        }
        
        # Compile patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.html_regex = [re.compile(pattern, re.DOTALL | re.IGNORECASE) 
                          for pattern in self.html_patterns]
        self.boilerplate_regex = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in self.boilerplate_patterns]
    
    def clean(self, text: str) -> str:
        """
        Clean raw article text with enhanced processing.
        
        Args:
            text: Raw article text
            
        Returns:
            Cleaned text
        """
        if not text or not text.strip():
            return ""
        
        if self.logger:
            self.logger.debug(f"Cleaning text of length {len(text)}")
        
        original_text = text
        
        # Step 1: Decode HTML entities
        text = html.unescape(text)
        
        # Step 2: Remove HTML tags
        for pattern in self.html_regex:
            text = pattern.sub(' ', text)
        
        # Step 3: Remove boilerplate content
        for pattern in self.boilerplate_regex:
            text = pattern.sub('', text)
        
        # Step 4: Handle encoding issues
        text = self._fix_encoding_issues(text)
        
        # Step 5: Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        
        # Step 6: Clean whitespace and formatting
        text = self._normalize_whitespace(text)
        
        # Step 7: Remove duplicate content
        text = self._remove_duplicate_content(text)
        
        # Step 8: Final cleanup
        text = self._final_cleanup(text)
        
        if self.logger:
            self.logger.debug(f"Cleaned text length: {len(text)} (reduction: {len(original_text) - len(text)} chars)")
        
        return text
    
    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding issues in text."""
        # Handle smart quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '-').replace('–', '-')
        text = text.replace('…', '...')
        
        # Handle other common encoding issues
        text = text.replace('Â', '')  # Common encoding artifact
        text = text.replace('â€™', "'")  # Smart apostrophe
        text = text.replace('â€œ', '"')  # Smart quote
        text = text.replace('â€', '"')  # Smart quote
        
        return text
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        return text.strip()
    
    def _remove_duplicate_content(self, text: str) -> str:
        """Remove duplicate sentences and paragraphs."""
        lines = text.split('\n')
        seen_lines = set()
        unique_lines = []
        
        for line in lines:
            line_clean = line.strip().lower()
            if line_clean and line_clean not in seen_lines:
                seen_lines.add(line_clean)
                unique_lines.append(line)
        
        return '\n'.join(unique_lines)
    
    def _final_cleanup(self, text: str) -> str:
        """Final cleanup steps."""
        # Remove very short lines (likely artifacts)
        lines = text.split('\n')
        lines = [line for line in lines if len(line.strip()) > 3 or not line.strip()]
        
        # Remove lines that are just punctuation
        lines = [line for line in lines if not re.match(r'^[.!?,\-_\s]+$', line.strip())]
        
        return '\n'.join(lines)
    
    def extract_metadata(self, text: str) -> Dict:
        """
        Extract comprehensive article metadata.
        
        Args:
            text: Article text
            
        Returns:
            Dictionary with metadata
        """
        metadata = {
            'dateline_location': None,
            'source': None,
            'author': None,
            'publication_date': None,
            'word_count': len(text.split()),
            'has_violence_content': False,
            'african_entities': [],
            'quality_score': 0.0
        }
        
        # Extract dateline (location - date)
        dateline_patterns = [
            r'^([A-Z][A-Z\s,]+?)\s*[-–]\s*',  # All caps location (including commas) - non-greedy
            r'^([A-Z][A-Z\s,]+?[a-z]+[A-Z\s,]*?)\s*[-–]\s*',  # Mixed case location
            r'^([A-Z][a-z]+,\s+[A-Z][a-z]+)\s*[-–]\s*',  # City, Country format
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[-–]\s*',  # Standard dateline
        ]
        
        for pattern in dateline_patterns:
            match = re.match(pattern, text)
            if match:
                metadata['dateline_location'] = match.group(1).strip()
                break
        
        # Extract source
        source_patterns = [
            r'\((Reuters|AFP|AP|BBC|CNN|Al Jazeera|VOA|DW)\)',
            r'By\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Source:\s*([A-Za-z\s]+)',
            r'Reporting by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in source_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['source'] = match.group(1).strip()
                break
        
        # Extract author
        author_patterns = [
            r'By\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Author:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
            r'Written by\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                metadata['author'] = match.group(1).strip()
                break
        
        # Extract publication date
        date_patterns = [
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                metadata['publication_date'] = match.group(1)
                break
        
        # Check for violence content
        violence_indicators = sum(1 for term in self.violence_terms if term in text.lower())
        metadata['has_violence_content'] = violence_indicators > 0
        metadata['violence_indicators'] = violence_indicators
        
        # Extract African entities
        african_entities = self._extract_african_entities(text)
        metadata['african_entities'] = african_entities
        
        # Calculate quality score
        metadata['quality_score'] = self._calculate_quality_score(text, metadata)
        
        return metadata
    
    def _extract_african_entities(self, text: str) -> List[str]:
        """Extract African entities from text."""
        entities = []
        
        # African countries
        african_countries = [
            'Nigeria', 'Kenya', 'South Africa', 'Ghana', 'Ethiopia', 'Tanzania',
            'Uganda', 'Morocco', 'Algeria', 'Sudan', 'Angola', 'Mozambique',
            'Madagascar', 'Cameroon', 'Niger', 'Burkina Faso', 'Mali', 'Malawi',
            'Zambia', 'Somalia', 'Senegal', 'Chad', 'Zimbabwe', 'Guinea',
            'Rwanda', 'Benin', 'Tunisia', 'Burundi', 'South Sudan', 'Togo'
        ]
        
        # African cities
        african_cities = [
            'Lagos', 'Cairo', 'Kinshasa', 'Johannesburg', 'Nairobi', 'Abuja',
            'Kano', 'Ibadan', 'Cape Town', 'Casablanca', 'Addis Ababa',
            'Dar es Salaam', 'Kampala', 'Dakar', 'Bamako', 'Ouagadougou',
            'Lusaka', 'Harare', 'Maputo', 'Antananarivo', 'Yaoundé',
            'Niamey', 'Bujumbura', 'Kigali', 'Dakar', 'Banjul', 'Freetown',
            'Monrovia', 'Conakry', 'Bissau', 'Praia', 'São Tomé', 'Malabo',
            'Libreville', 'Brazzaville', 'Kinshasa', 'Bangui', 'N\'Djamena',
            'Khartoum', 'Juba', 'Asmara', 'Djibouti', 'Mogadishu', 'Hargeisa'
        ]
        
        # Check for countries
        for country in african_countries:
            if country in text:
                entities.append(country)
        
        # Check for cities
        for city in african_cities:
            if city in text:
                entities.append(city)
        
        return list(set(entities))  # Remove duplicates
    
    def _calculate_quality_score(self, text: str, metadata: Dict) -> float:
        """Calculate text quality score."""
        score = 0.0
        
        # Length factor (longer articles are generally better)
        word_count = len(text.split())
        if word_count > 50:
            score += 0.2
        if word_count > 100:
            score += 0.2
        if word_count > 300:
            score += 0.1
        
        # Metadata completeness
        if metadata['dateline_location']:
            score += 0.15
        if metadata['source']:
            score += 0.15
        if metadata['author']:
            score += 0.1
        if metadata['publication_date']:
            score += 0.1
        
        # Content quality indicators
        if metadata['has_violence_content']:
            score += 0.1  # Violence content is relevant for this pipeline
        
        if metadata['african_entities']:
            score += 0.1  # African context is relevant
        
        # Text structure indicators
        sentences = text.split('.')
        if len(sentences) > 3:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_cleaning_statistics(self, original_text: str, cleaned_text: str) -> Dict:
        """Get statistics about the cleaning process."""
        return {
            'original_length': len(original_text),
            'cleaned_length': len(cleaned_text),
            'reduction_percentage': ((len(original_text) - len(cleaned_text)) / len(original_text)) * 100 if original_text else 0,
            'original_words': len(original_text.split()),
            'cleaned_words': len(cleaned_text.split()),
            'html_tags_removed': len(re.findall(r'<[^>]+>', original_text)),
            'lines_removed': len(original_text.split('\n')) - len(cleaned_text.split('\n')),
        }
    
    def validate_text_quality(self, text: str) -> Dict:
        """Validate text quality and return issues."""
        issues = []
        
        if len(text.strip()) < 50:
            issues.append("Text too short")
        
        if len(text.split()) < 10:
            issues.append("Too few words")
        
        if not re.search(r'[.!?]', text):
            issues.append("No sentence endings found")
        
        if re.search(r'[A-Z]{15,}', text):
            issues.append("Possible encoding issues (all caps)")
        
        if text.count(' ') / len(text) > 0.3:
            issues.append("Too much whitespace")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'quality_score': self._calculate_quality_score(text, self.extract_metadata(text))
        }
