from typing import List, Dict
from collections import Counter
import numpy as np

class LexicalFeatureExtractor:
    """
    Extract lexical features for ML.
    """
    
    def __init__(self, violence_lexicon: List[str] = None):
        """
        Initialize feature extractor.
        
        Args:
            violence_lexicon: List of violence-related terms
        """
        self.violence_lexicon = violence_lexicon or self._default_violence_lexicon()
    
    def _default_violence_lexicon(self) -> List[str]:
        """Default violence vocabulary."""
        return [
            'kill', 'attack', 'bomb', 'shoot', 'murder', 'assault',
            'kidnap', 'abduct', 'massacre', 'raid', 'ambush',
            'explode', 'detonate', 'clash', 'fight', 'battle',
            'wound', 'injure', 'death', 'casualty', 'victim',
            'militant', 'rebel', 'terrorist', 'gunman', 'insurgent'
        ]
    
    def extract_features(self, tokens: List[str]) -> Dict:
        """
        Extract lexical features from tokens.
        
        Args:
            tokens: List of word tokens
            
        Returns:
            Feature dictionary
        """
        features = {}
        
        # Basic statistics
        features['num_tokens'] = len(tokens)
        features['avg_token_length'] = np.mean([len(t) for t in tokens])
        
        # Violence indicators
        violence_count = sum(1 for t in tokens if t.lower() in self.violence_lexicon)
        features['violence_term_count'] = violence_count
        features['violence_term_ratio'] = violence_count / len(tokens) if tokens else 0
        
        # Check for specific violence types
        features['has_death_term'] = any(t.lower() in ['kill', 'death', 'dead', 'died'] for t in tokens)
        features['has_weapon_term'] = any(t.lower() in ['gun', 'bomb', 'weapon', 'explosive'] for t in tokens)
        features['has_actor_term'] = any(t.lower() in ['militant', 'rebel', 'terrorist', 'gunman'] for t in tokens)
        
        # Capitalization (for NER hints)
        features['num_capitalized'] = sum(1 for t in tokens if t[0].isupper())
        
        # Numbers (casualties, dates)
        features['num_numbers'] = sum(1 for t in tokens if t.isdigit())
        
        return features
    
    def extract_ngrams(self, tokens: List[str], n: int = 2) -> Counter:
        """
        Extract n-grams.
        
        Args:
            tokens: List of tokens
            n: N-gram size
            
        Returns:
            Counter of n-grams
        """
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram.lower())
        
        return Counter(ngrams)
