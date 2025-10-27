from typing import List, Dict, Set, Optional, Tuple
from collections import Counter, defaultdict
import numpy as np
import re
import logging

class LexicalFeatureExtractor:
    """
    Enhanced lexical feature extractor for African news and violent event analysis.
    Extracts comprehensive linguistic features for ML models.
    """
    
    def __init__(self, violence_lexicon: List[str] = None, enable_logging: bool = False):
        """
        Initialize enhanced feature extractor.
        
        Args:
            violence_lexicon: List of violence-related terms
            enable_logging: Enable debug logging
        """
        self.logger = logging.getLogger(__name__) if enable_logging else None
        self.violence_lexicon = violence_lexicon or self._default_violence_lexicon()
        
        # Initialize specialized lexicons
        self._initialize_lexicons()
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _initialize_lexicons(self):
        """Initialize specialized lexicons for African news analysis."""
        # Violence categories
        self.death_terms = {
            'kill', 'killed', 'killing', 'murder', 'murdered', 'murdering',
            'death', 'dead', 'died', 'dying', 'fatal', 'fatality',
            'casualty', 'casualties', 'victim', 'victims', 'slain'
        }
        
        self.weapon_terms = {
            'gun', 'guns', 'rifle', 'rifles', 'pistol', 'pistols',
            'bomb', 'bombs', 'explosive', 'explosives', 'grenade', 'grenades',
            'weapon', 'weapons', 'ammunition', 'ammo', 'bullet', 'bullets',
            'ak-47', 'ak47', 'rpg', 'ied', 'ieds', 'landmine', 'landmines'
        }
        
        self.actor_terms = {
            'militant', 'militants', 'rebel', 'rebels', 'terrorist', 'terrorists',
            'gunman', 'gunmen', 'insurgent', 'insurgents', 'fighter', 'fighters',
            'combatant', 'combatants', 'soldier', 'soldiers', 'troop', 'troops',
            'boko haram', 'al-shabaab', 'iswap', 'al-qaeda', 'isis', 'isil'
        }
        
        self.violence_verbs = {
            'attack', 'attacked', 'attacking', 'attacks', 'assault', 'assaulted',
            'bomb', 'bombed', 'bombing', 'bombs', 'shoot', 'shot', 'shooting',
            'shoots', 'explode', 'exploded', 'exploding', 'explodes', 'detonate',
            'detonated', 'detonating', 'detonates', 'raid', 'raided', 'raiding',
            'raids', 'ambush', 'ambushed', 'ambushing', 'ambushes', 'clash',
            'clashed', 'clashing', 'clashes', 'fight', 'fought', 'fighting',
            'fights', 'battle', 'battled', 'battling', 'battles', 'wound',
            'wounded', 'wounding', 'wounds', 'injure', 'injured', 'injuring',
            'injures', 'kidnap', 'kidnapped', 'kidnapping', 'kidnaps', 'abduct',
            'abducted', 'abducting', 'abducts', 'massacre', 'massacred',
            'massacring', 'massacres'
        }
        
        # African context terms
        self.african_countries = {
            'nigeria', 'kenya', 'south africa', 'ghana', 'ethiopia', 'tanzania',
            'uganda', 'morocco', 'algeria', 'sudan', 'angola', 'mozambique',
            'madagascar', 'cameroon', 'niger', 'burkina faso', 'mali', 'malawi',
            'zambia', 'somalia', 'senegal', 'chad', 'zimbabwe', 'guinea',
            'rwanda', 'benin', 'tunisia', 'burundi', 'south sudan', 'togo'
        }
        
        self.african_cities = {
            'lagos', 'cairo', 'kinshasa', 'johannesburg', 'nairobi', 'abuja',
            'kano', 'ibadan', 'cape town', 'casablanca', 'addis ababa',
            'dar es salaam', 'kampala', 'dakar', 'bamako', 'ouagadougou',
            'lusaka', 'harare', 'maputo', 'antananarivo', 'yaoundé',
            'niamey', 'bujumbura', 'kigali', 'banjul', 'freetown',
            'monrovia', 'conakry', 'bissau', 'praia', 'são tomé', 'malabo',
            'libreville', 'brazzaville', 'bangui', 'n\'djamena', 'khartoum',
            'juba', 'asmara', 'djibouti', 'mogadishu', 'hargeisa',
            'maiduguri', 'kaduna', 'port harcourt', 'benin city', 'zaria',
            'jos', 'ilorin', 'oyo', 'enugu', 'abeokuta', 'sokoto'
        }
        
        self.african_organizations = {
            'ecowas', 'au', 'igad', 'sadc', 'eac', 'un', 'unhcr', 'unicef',
            'who', 'icrc', 'msf', 'nato', 'eu', 'us', 'uk'
        }
        
        # Temporal markers
        self.temporal_terms = {
            'today', 'yesterday', 'tomorrow', 'morning', 'afternoon', 'evening',
            'night', 'dawn', 'dusk', 'recently', 'recent', 'latest', 'newest',
            'breaking', 'urgent', 'urgently', 'immediate', 'sudden', 'suddenly', 'quickly',
            'rapidly', 'fast', 'slow', 'slowly', 'gradually', 'eventually'
        }
        
        # Intensity markers
        self.intensity_terms = {
            'severe', 'extreme', 'massive', 'devastating', 'brutal', 'violent',
            'intense', 'fierce', 'heavy', 'light', 'minor', 'major',
            'significant', 'substantial', 'terrible', 'horrible', 'awful'
        }
        
        # Sentiment indicators
        self.negative_terms = {
            'terrible', 'horrible', 'awful', 'devastating', 'tragic', 'sad',
            'fear', 'fearful', 'scared', 'terrified', 'panic', 'panic',
            'chaos', 'chaotic', 'crisis', 'emergency', 'urgent', 'critical'
        }
        
        self.positive_terms = {
            'peaceful', 'calm', 'stable', 'secure', 'safe', 'protected',
            'successful', 'victory', 'triumph', 'hope', 'hopeful', 'optimistic'
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        # Number patterns
        self.number_pattern = re.compile(r'\b\d+\b')
        self.percentage_pattern = re.compile(r'\b\d+%\b')
        self.time_pattern = re.compile(r'\b\d{1,2}:\d{2}\b')
        self.date_pattern = re.compile(r'\b\d{1,2}/\d{1,2}/\d{4}\b')
        
        # Capitalization patterns
        self.capitalized_pattern = re.compile(r'\b[A-Z][a-z]+\b')
        self.all_caps_pattern = re.compile(r'\b[A-Z]{2,}\b')
        
        # Punctuation patterns
        self.exclamation_pattern = re.compile(r'!+')
        self.question_pattern = re.compile(r'\?+')
        self.ellipsis_pattern = re.compile(r'\.{3,}')
    
    def extract_features(self, tokens: List[str], text: str = None) -> Dict:
        """
        Extract comprehensive lexical features from tokens.
        
        Args:
            tokens: List of word tokens
            text: Original text (optional, for pattern matching)
            
        Returns:
            Feature dictionary with comprehensive linguistic features
        """
        if self.logger:
            self.logger.debug(f"Extracting features from {len(tokens)} tokens")
        
        features = {}
        
        # Basic statistics
        features.update(self._extract_basic_statistics(tokens))
        
        # Violence-related features
        features.update(self._extract_violence_features(tokens))
        
        # African context features
        features.update(self._extract_african_context_features(tokens))
        
        # Linguistic features
        features.update(self._extract_linguistic_features(tokens, text))
        
        # Statistical features
        features.update(self._extract_statistical_features(tokens))
        
        # Temporal and intensity features
        features.update(self._extract_temporal_intensity_features(tokens))
        
        # Sentiment features
        features.update(self._extract_sentiment_features(tokens))
        
        return features
    
    def _extract_basic_statistics(self, tokens: List[str]) -> Dict:
        """Extract basic statistical features."""
        features = {}
        
        if not tokens:
            return {
                'num_tokens': 0,
                'avg_token_length': 0.0,
                'max_token_length': 0,
                'min_token_length': 0,
                'unique_tokens': 0,
                'token_diversity': 0.0
            }
        
        token_lengths = [len(t) for t in tokens]
        
        features['num_tokens'] = len(tokens)
        features['avg_token_length'] = np.mean(token_lengths)
        features['max_token_length'] = max(token_lengths)
        features['min_token_length'] = min(token_lengths)
        features['unique_tokens'] = len(set(tokens))
        features['token_diversity'] = len(set(tokens)) / len(tokens) if tokens else 0
        
        return features
    
    def _extract_violence_features(self, tokens: List[str]) -> Dict:
        """Extract violence-related features."""
        features = {}
        
        if not tokens:
            return {
                'violence_term_count': 0,
                'violence_term_ratio': 0.0,
                'death_term_count': 0,
                'weapon_term_count': 0,
                'actor_term_count': 0,
                'violence_verb_count': 0,
                'has_death_terms': False,
                'has_weapon_terms': False,
                'has_actor_terms': False,
                'has_violence_verbs': False,
                'violence_intensity': 0.0
            }
        
        # Convert to lowercase for matching
        lower_tokens = [t.lower() for t in tokens]
        
        # Violence term counts
        violence_count = sum(1 for t in lower_tokens if t in self.violence_lexicon)
        death_count = sum(1 for t in lower_tokens if t in self.death_terms)
        weapon_count = sum(1 for t in lower_tokens if t in self.weapon_terms)
        actor_count = sum(1 for t in lower_tokens if t in self.actor_terms)
        violence_verb_count = sum(1 for t in lower_tokens if t in self.violence_verbs)
        
        # Also check for multi-word terms
        text_lower = ' '.join(lower_tokens)
        for term in self.actor_terms:
            if ' ' in term and term in text_lower:
                actor_count += 1
        
        features['violence_term_count'] = violence_count
        features['violence_term_ratio'] = violence_count / len(tokens)
        features['death_term_count'] = death_count
        features['weapon_term_count'] = weapon_count
        features['actor_term_count'] = actor_count
        features['violence_verb_count'] = violence_verb_count
        
        # Boolean features
        features['has_death_terms'] = death_count > 0
        features['has_weapon_terms'] = weapon_count > 0
        features['has_actor_terms'] = actor_count > 0
        features['has_violence_verbs'] = violence_verb_count > 0
        
        # Violence intensity (weighted combination)
        features['violence_intensity'] = (
            death_count * 3 +  # Death terms are most serious
            weapon_count * 2 +  # Weapons indicate capability
            actor_count * 1.5 +  # Actors indicate agency
            violence_verb_count * 1  # Verbs indicate action
        ) / len(tokens)
        
        return features
    
    def _extract_african_context_features(self, tokens: List[str]) -> Dict:
        """Extract African context features."""
        features = {}
        
        if not tokens:
            return {
                'african_country_count': 0,
                'african_city_count': 0,
                'african_org_count': 0,
                'has_african_context': False,
                'african_context_ratio': 0.0
            }
        
        lower_tokens = [t.lower() for t in tokens]
        
        # Count African entities (including multi-word terms)
        text_lower = ' '.join(lower_tokens)
        country_count = sum(1 for t in lower_tokens if t in self.african_countries)
        city_count = sum(1 for t in lower_tokens if t in self.african_cities)
        org_count = sum(1 for t in lower_tokens if t in self.african_organizations)
        
        # Also check for multi-word African terms
        for term in self.african_countries:
            if ' ' in term and term in text_lower:
                country_count += 1
        for term in self.african_cities:
            if ' ' in term and term in text_lower:
                city_count += 1
        for term in self.african_organizations:
            if ' ' in term and term in text_lower:
                org_count += 1
        
        # Check for "Boko Haram" specifically (case sensitive in original tokens)
        if 'boko haram' in text_lower:
            # This is an actor term, but we're in African context features
            # We could add it to a separate actor count if needed
            pass
        
        features['african_country_count'] = country_count
        features['african_city_count'] = city_count
        features['african_org_count'] = org_count
        features['has_african_context'] = (country_count + city_count + org_count) > 0
        features['african_context_ratio'] = (country_count + city_count + org_count) / len(tokens)
        
        return features
    
    def _extract_linguistic_features(self, tokens: List[str], text: str = None) -> Dict:
        """Extract linguistic features."""
        features = {}
        
        if not tokens:
            return {
                'num_capitalized': 0,
                'num_all_caps': 0,
                'num_numbers': 0,
                'num_punctuation': 0,
                'capitalization_ratio': 0.0,
                'number_ratio': 0.0
            }
        
        # Capitalization features
        capitalized_count = sum(1 for t in tokens if t[0].isupper() and len(t) > 1)
        all_caps_count = sum(1 for t in tokens if t.isupper() and len(t) > 1)
        
        features['num_capitalized'] = capitalized_count
        features['num_all_caps'] = all_caps_count
        features['capitalization_ratio'] = capitalized_count / len(tokens)
        
        # Number features
        number_count = sum(1 for t in tokens if t.isdigit())
        features['num_numbers'] = number_count
        features['number_ratio'] = number_count / len(tokens)
        
        # Punctuation features (if text is provided)
        if text:
            features['num_exclamations'] = len(self.exclamation_pattern.findall(text))
            features['num_questions'] = len(self.question_pattern.findall(text))
            features['num_ellipsis'] = len(self.ellipsis_pattern.findall(text))
        else:
            features['num_exclamations'] = 0
            features['num_questions'] = 0
            features['num_ellipsis'] = 0
        
        return features
    
    def _extract_statistical_features(self, tokens: List[str]) -> Dict:
        """Extract statistical distribution features."""
        features = {}
        
        if not tokens:
            return {
                'token_frequency_std': 0.0,
                'most_frequent_token': '',
                'most_frequent_count': 0,
                'rare_token_count': 0,
                'rare_token_ratio': 0.0
            }
        
        # Token frequency analysis
        token_counts = Counter(tokens)
        frequencies = list(token_counts.values())
        
        features['token_frequency_std'] = np.std(frequencies) if len(frequencies) > 1 else 0.0
        
        # Most frequent token
        if token_counts:
            most_frequent = token_counts.most_common(1)[0]
            features['most_frequent_token'] = most_frequent[0]
            features['most_frequent_count'] = most_frequent[1]
        else:
            features['most_frequent_token'] = ''
            features['most_frequent_count'] = 0
        
        # Rare tokens (appearing only once)
        rare_count = sum(1 for count in frequencies if count == 1)
        features['rare_token_count'] = rare_count
        features['rare_token_ratio'] = rare_count / len(tokens)
        
        return features
    
    def _extract_temporal_intensity_features(self, tokens: List[str]) -> Dict:
        """Extract temporal and intensity features."""
        features = {}
        
        if not tokens:
            return {
                'temporal_term_count': 0,
                'intensity_term_count': 0,
                'has_temporal_markers': False,
                'has_intensity_markers': False,
                'temporal_ratio': 0.0,
                'intensity_ratio': 0.0
            }
        
        lower_tokens = [t.lower() for t in tokens]
        
        # Temporal markers
        temporal_count = sum(1 for t in lower_tokens if t in self.temporal_terms)
        features['temporal_term_count'] = temporal_count
        features['has_temporal_markers'] = temporal_count > 0
        features['temporal_ratio'] = temporal_count / len(tokens)
        
        # Intensity markers
        intensity_count = sum(1 for t in lower_tokens if t in self.intensity_terms)
        features['intensity_term_count'] = intensity_count
        features['has_intensity_markers'] = intensity_count > 0
        features['intensity_ratio'] = intensity_count / len(tokens)
        
        return features
    
    def _extract_sentiment_features(self, tokens: List[str]) -> Dict:
        """Extract sentiment-related features."""
        features = {}
        
        if not tokens:
            return {
                'negative_term_count': 0,
                'positive_term_count': 0,
                'sentiment_ratio': 0.0,
                'has_negative_sentiment': False,
                'has_positive_sentiment': False
            }
        
        lower_tokens = [t.lower() for t in tokens]
        
        # Sentiment term counts
        negative_count = sum(1 for t in lower_tokens if t in self.negative_terms)
        positive_count = sum(1 for t in lower_tokens if t in self.positive_terms)
        
        features['negative_term_count'] = negative_count
        features['positive_term_count'] = positive_count
        features['has_negative_sentiment'] = negative_count > 0
        features['has_positive_sentiment'] = positive_count > 0
        
        # Sentiment ratio (positive - negative, so positive values indicate positive sentiment)
        total_sentiment_terms = negative_count + positive_count
        if total_sentiment_terms > 0:
            features['sentiment_ratio'] = (positive_count - negative_count) / total_sentiment_terms
        else:
            features['sentiment_ratio'] = 0.0
        
        return features
    
    def extract_ngrams(self, tokens: List[str], n: int = 2, min_frequency: int = 1) -> Counter:
        """
        Extract n-grams with filtering and weighting.
        
        Args:
            tokens: List of tokens
            n: N-gram size
            min_frequency: Minimum frequency threshold
            
        Returns:
            Counter of n-grams
        """
        if len(tokens) < n:
            return Counter()
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram.lower())
        
        ngram_counter = Counter(ngrams)
        
        # Filter by minimum frequency
        if min_frequency > 1:
            ngram_counter = Counter({k: v for k, v in ngram_counter.items() if v >= min_frequency})
        
        return ngram_counter
    
    def extract_violence_ngrams(self, tokens: List[str], n: int = 2) -> Counter:
        """Extract n-grams containing violence terms."""
        if len(tokens) < n:
            return Counter()
        
        violence_ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram_tokens = tokens[i:i+n]
            ngram_text = ' '.join(ngram_tokens).lower()
            
            # Check if n-gram contains any violence terms
            if any(term in ngram_text for term in self.violence_lexicon):
                violence_ngrams.append(ngram_text)
        
        return Counter(violence_ngrams)
    
    def extract_african_ngrams(self, tokens: List[str], n: int = 2) -> Counter:
        """Extract n-grams containing African context terms."""
        if len(tokens) < n:
            return Counter()
        
        african_ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram_tokens = tokens[i:i+n]
            ngram_text = ' '.join(ngram_tokens).lower()
            
            # Check if n-gram contains any African terms
            african_terms = (self.african_countries | 
                           self.african_cities | 
                           self.african_organizations)
            
            if any(term in ngram_text for term in african_terms):
                african_ngrams.append(ngram_text)
        
        return Counter(african_ngrams)
    
    def get_feature_summary(self, features: Dict) -> Dict:
        """Get a summary of extracted features."""
        summary = {
            'total_features': len(features),
            'violence_features': sum(1 for k in features.keys() if 'violence' in k or 'death' in k or 'weapon' in k or 'actor' in k),
            'african_features': sum(1 for k in features.keys() if 'african' in k),
            'linguistic_features': sum(1 for k in features.keys() if any(term in k for term in ['capital', 'number', 'token', 'diversity'])),
            'sentiment_features': sum(1 for k in features.keys() if 'sentiment' in k or 'negative' in k or 'positive' in k),
            'temporal_features': sum(1 for k in features.keys() if 'temporal' in k or 'intensity' in k)
        }
        
        return summary
    
    def get_top_features(self, features: Dict, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get top N features by value."""
        # Filter numeric features
        numeric_features = {k: v for k, v in features.items() 
                          if isinstance(v, (int, float)) and not isinstance(v, bool)}
        
        # Sort by value
        sorted_features = sorted(numeric_features.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_features[:top_n]
    
    def compare_features(self, features1: Dict, features2: Dict) -> Dict:
        """Compare two feature sets."""
        comparison = {}
        
        # Get common keys
        common_keys = set(features1.keys()) & set(features2.keys())
        
        for key in common_keys:
            if isinstance(features1[key], (int, float)) and isinstance(features2[key], (int, float)):
                comparison[key] = {
                    'value1': features1[key],
                    'value2': features2[key],
                    'difference': features1[key] - features2[key],
                    'ratio': features1[key] / features2[key] if features2[key] != 0 else float('inf')
                }
        
        return comparison
    
    def _default_violence_lexicon(self) -> List[str]:
        """Default violence vocabulary."""
        return [
            'kill', 'attack', 'bomb', 'shoot', 'murder', 'assault',
            'kidnap', 'abduct', 'massacre', 'raid', 'ambush',
            'explode', 'detonate', 'clash', 'fight', 'battle',
            'wound', 'injure', 'death', 'casualty', 'victim',
            'militant', 'rebel', 'terrorist', 'gunman', 'insurgent'
        ]
