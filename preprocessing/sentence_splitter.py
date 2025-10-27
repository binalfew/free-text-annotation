from typing import List, Set, Optional
import re
import logging

class SentenceSplitter:
    """
    Enhanced sentence splitter with special handling for abbreviations,
    quotes, African context, and violence-related terminology.
    """
    
    def __init__(self, min_sentence_length: int = 3, enable_logging: bool = False):
        """
        Initialize sentence splitter.
        
        Args:
            min_sentence_length: Minimum word count for valid sentences
            enable_logging: Enable debug logging
        """
        self.min_sentence_length = min_sentence_length
        self.logger = logging.getLogger(__name__) if enable_logging else None
        
        # Comprehensive abbreviations that don't end sentences
        self.abbreviations = self._build_abbreviation_set()
        
        # African-specific terms and organizations
        self.african_terms = {
            'Al-Shabaab', 'Boko Haram', 'ISWAP', 'Al-Qaeda', 'ISIS', 'ISIL',
            'Maiduguri', 'Kano', 'Lagos', 'Abuja', 'Mogadishu', 'Nairobi',
            'ECOWAS', 'AU', 'IGAD', 'SADC', 'EAC'
        }
        
        # Violence-related abbreviations
        self.violence_abbreviations = {
            'IED', 'RPG', 'AK-47', 'M-16', 'IEDs', 'RPGs',
            'UN', 'UNHCR', 'UNICEF', 'WHO', 'ICRC', 'MSF'
        }
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _build_abbreviation_set(self) -> Set[str]:
        """Build comprehensive set of abbreviations."""
        abbreviations = {
            # Common titles and names
            'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.', 'Rev.', 'Capt.',
            'Col.', 'Gen.', 'Lt.', 'Sgt.', 'Maj.', 'Cpl.', 'Pvt.',
            
            # Academic and professional
            'Ph.D.', 'M.D.', 'B.A.', 'M.A.', 'B.S.', 'M.S.', 'J.D.', 'LL.M.',
            'CPA', 'MBA', 'CEO', 'CFO', 'CTO', 'VP', 'SVP', 'EVP',
            
            # Geographic and political
            'U.S.', 'U.K.', 'U.N.', 'E.U.', 'NATO', 'UNESCO', 'WHO', 'IMF',
            'USA', 'UK', 'EU', 'UN', 'US', 'UK', 'EU', 'UN',
            
            # Time and dates
            'a.m.', 'p.m.', 'A.M.', 'P.M.', 'AM', 'PM',
            'Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'Jun.', 'Jul.',
            'Aug.', 'Sep.', 'Sept.', 'Oct.', 'Nov.', 'Dec.',
            
            # Common abbreviations
            'vs.', 'etc.', 'e.g.', 'i.e.', 'cf.', 'viz.', 'approx.',
            'inc.', 'corp.', 'ltd.', 'co.', 'st.', 'ave.', 'blvd.',
            'no.', 'vol.', 'pp.', 'ed.', 'eds.', 'trans.', 'comp.',
            
            # African and violence context
            'ECOWAS', 'AU', 'IGAD', 'SADC', 'EAC', 'UNHCR', 'UNICEF',
            'ICRC', 'MSF', 'WHO', 'UN', 'NATO', 'EU', 'US', 'UK',
            'IED', 'RPG', 'AK-47', 'M-16', 'IEDs', 'RPGs'
        }
        return abbreviations
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        # Pattern for sentence boundaries - more sophisticated
        self.sentence_pattern = re.compile(
            r'(?<=[.!?])\s+(?=[A-Z])|'  # Standard sentence boundary
            r'(?<=[.!?])\s+(?=")|'      # Before quotes
            r'(?<=[.!?])\s+(?=\d)|'     # Before numbers (for lists)
            r'(?<=[.!?])\s+(?=\*)|'     # Before bullet points
            r'(?<=[.!?])\s+(?=-)|'      # Before dashes
            r'(?<=[.!?])\s+(?=\u2022)'   # Before bullet symbols
        )
        
        # Pattern for quotes and dialogue
        self.quote_pattern = re.compile(r'"[^"]*"')
        
        # Pattern for numbers and dates
        self.number_date_pattern = re.compile(
            r'\b\d{1,2}:\d{2}\s*(?:a\.?m\.?|p\.?m\.?)\b|'  # Time
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+\d{4}\b|'  # Date
            r'\b\d{1,2}\.\d{1,2}\.\d{4}\b|'  # Date format
            r'\b\d+\.\d+\b'  # Decimal numbers
        )
        
        # Pattern for African names and organizations
        self.african_name_pattern = re.compile(
            r'\b(?:Al-Shabaab|Boko Haram|ISWAP|ECOWAS|AU|IGAD|SADC|EAC)\b',
            re.IGNORECASE
        )
    
    def split(self, text: str) -> List[str]:
        """
        Split text into sentences with enhanced handling for various edge cases.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text or not text.strip():
            return []
        
        if self.logger:
            self.logger.debug(f"Splitting text of length {len(text)}")
        
        # Step 1: Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Step 2: Protect special patterns
        protected_text, replacements = self._protect_patterns(processed_text)
        
        # Step 3: Split on sentence boundaries
        sentences = self._split_sentences(protected_text)
        
        # Step 4: Restore protected patterns
        sentences = self._restore_patterns(sentences, replacements)
        
        # Step 5: Clean and validate sentences
        sentences = self._clean_and_validate(sentences)
        
        if self.logger:
            self.logger.debug(f"Split into {len(sentences)} sentences")
        
        return sentences
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better sentence splitting."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle common encoding issues
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('—', '-').replace('–', '-')
        
        return text
    
    def _protect_patterns(self, text: str) -> tuple:
        """Protect special patterns from being split."""
        protected_text = text
        replacements = {}
        replacement_id = 0
        
        # Protect abbreviations (be more careful about word boundaries)
        for abbr in self.abbreviations:
            # Use word boundaries to avoid partial matches
            pattern = re.compile(r'\b' + re.escape(abbr) + r'\b')
            if pattern.search(protected_text):
                placeholder = f"<ABBR_{replacement_id}>"
                protected_text = pattern.sub(placeholder, protected_text)
                replacements[placeholder] = abbr
                replacement_id += 1
        
        # Protect quotes and dialogue
        quote_matches = self.quote_pattern.findall(protected_text)
        for quote in quote_matches:
            placeholder = f"<QUOTE_{replacement_id}>"
            protected_text = protected_text.replace(quote, placeholder)
            replacements[placeholder] = quote
            replacement_id += 1
        
        # Protect numbers and dates
        number_matches = self.number_date_pattern.findall(protected_text)
        for number in number_matches:
            placeholder = f"<NUM_{replacement_id}>"
            protected_text = protected_text.replace(number, placeholder)
            replacements[placeholder] = number
            replacement_id += 1
        
        # Protect African names and organizations
        african_matches = self.african_name_pattern.findall(protected_text)
        for name in african_matches:
            placeholder = f"<AFR_{replacement_id}>"
            protected_text = protected_text.replace(name, placeholder)
            replacements[placeholder] = name
            replacement_id += 1
        
        return protected_text, replacements
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using enhanced patterns."""
        # Use a more flexible approach that handles protected text
        # Split on sentence boundaries: . ! ? followed by space
        sentence_boundary = re.compile(r'([.!?]+)\s+')
        
        # Split the text
        parts = sentence_boundary.split(text)
        
        sentences = []
        current_sentence = ""
        
        for i, part in enumerate(parts):
            current_sentence += part
            
            # If this part is just punctuation and there's more text, we have a sentence boundary
            if (re.match(r'^[.!?]+$', part) and 
                i + 1 < len(parts) and 
                len(current_sentence.strip()) > 0):
                
                sentences.append(current_sentence.strip())
                current_sentence = ""
        
        # Add any remaining text
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def _restore_patterns(self, sentences: List[str], replacements: dict) -> List[str]:
        """Restore protected patterns in sentences."""
        restored_sentences = []
        
        for sentence in sentences:
            restored_sentence = sentence
            for placeholder, original in replacements.items():
                restored_sentence = restored_sentence.replace(placeholder, original)
            restored_sentences.append(restored_sentence)
        
        return restored_sentences
    
    def _clean_and_validate(self, sentences: List[str]) -> List[str]:
        """Clean and validate sentences."""
        valid_sentences = []
        
        for sentence in sentences:
            # Clean whitespace
            sentence = sentence.strip()
            
            # Skip empty sentences
            if not sentence:
                continue
            
            # Skip very short sentences (likely fragments)
            word_count = len(sentence.split())
            if word_count < self.min_sentence_length:
                if self.logger:
                    self.logger.debug(f"Skipping short sentence: '{sentence}' ({word_count} words)")
                continue
            
            # Skip sentences that are just punctuation
            if re.match(r'^[.!?,\-_\s]+$', sentence):
                if self.logger:
                    self.logger.debug(f"Skipping punctuation-only sentence: '{sentence}'")
                continue
            
            # Skip sentences that start with lowercase (likely fragments)
            if sentence and sentence[0].islower() and not sentence[0].isalpha():
                # Allow sentences starting with quotes or numbers
                if not (sentence.startswith('"') or sentence[0].isdigit()):
                    if self.logger:
                        self.logger.debug(f"Skipping lowercase-start sentence: '{sentence}'")
                    continue
            
            valid_sentences.append(sentence)
        
        return valid_sentences
    
    def add_abbreviation(self, abbreviation: str):
        """Add a new abbreviation to the set."""
        self.abbreviations.add(abbreviation)
        if self.logger:
            self.logger.debug(f"Added abbreviation: {abbreviation}")
    
    def add_african_term(self, term: str):
        """Add a new African term to the set."""
        self.african_terms.add(term)
        if self.logger:
            self.logger.debug(f"Added African term: {term}")
    
    def get_statistics(self, text: str) -> dict:
        """Get statistics about the text and splitting process."""
        sentences = self.split(text)
        
        return {
            'total_sentences': len(sentences),
            'avg_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            'shortest_sentence': min(len(s.split()) for s in sentences) if sentences else 0,
            'longest_sentence': max(len(s.split()) for s in sentences) if sentences else 0,
            'abbreviations_found': len([abbr for abbr in self.abbreviations if abbr in text]),
            'african_terms_found': len([term for term in self.african_terms if term in text])
        }
