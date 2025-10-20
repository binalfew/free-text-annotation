from typing import List
import re

class SentenceSplitter:
    """
    Split text into sentences with special handling for abbreviations.
    """
    
    def __init__(self):
        """Initialize sentence splitter."""
        # Common abbreviations that don't end sentences
        self.abbreviations = {
            'Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.',
            'vs.', 'etc.', 'e.g.', 'i.e.', 'p.m.', 'a.m.',
            'U.S.', 'U.K.', 'U.N.', 'E.U.',
            'Jan.', 'Feb.', 'Mar.', 'Apr.', 'Jun.', 'Jul.',
            'Aug.', 'Sep.', 'Sept.', 'Oct.', 'Nov.', 'Dec.'
        }
    
    def split(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        # Protect abbreviations
        protected_text = text
        for abbr in self.abbreviations:
            protected_text = protected_text.replace(abbr, abbr.replace('.', '<PERIOD>'))
        
        # Split on sentence boundaries
        # Look for: . ! ? followed by space and capital letter
        sentence_pattern = r'([.!?]+)\s+(?=[A-Z])'
        parts = re.split(sentence_pattern, protected_text)
        
        # Reconstruct sentences
        sentences = []
        current = ""
        
        for i, part in enumerate(parts):
            current += part
            # If this is punctuation and next part starts with capital
            if re.match(r'[.!?]+$', part) and i + 1 < len(parts):
                # Restore periods in abbreviations
                current = current.replace('<PERIOD>', '.')
                sentences.append(current.strip())
                current = ""
        
        # Add any remaining text
        if current:
            current = current.replace('<PERIOD>', '.')
            sentences.append(current.strip())
        
        # Filter out very short "sentences" (likely errors)
        sentences = [s for s in sentences if len(s.split()) >= 3]
        
        return sentences
