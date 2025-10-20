"""
EVENT DETECTION AND 5W1H EXTRACTION
====================================

Core event extraction components for violent event system.

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

from typing import List, Dict, Tuple, Optional
import re
from collections import defaultdict
import logging

# ============================================================================
# Event Trigger Detection
# ============================================================================

class EventTriggerDetector:
    """
    Detect violent event triggers in sentences.
    """
    
    def __init__(self, violence_lexicon):
        """
        Initialize trigger detector.
        
        Args:
            violence_lexicon: ViolenceLexicon instance
        """
        self.lexicon = violence_lexicon
        self.logger = logging.getLogger(__name__)
        
        # Trigger patterns (verb-based)
        self.trigger_verbs = violence_lexicon.verbs
        
        # Trigger nouns
        self.trigger_nouns = {
            'attack', 'attacks', 'assault', 'assaults',
            'raid', 'raids', 'ambush', 'ambushes',
            'bombing', 'bombings', 'explosion', 'explosions',
            'shooting', 'shootings', 'massacre', 'massacres',
            'killing', 'killings', 'clash', 'clashes'
        }
    
    def detect_triggers(self, sentence_annotation: Dict) -> List[Dict]:
        """
        Detect event triggers in annotated sentence.
        
        Args:
            sentence_annotation: CoreNLP sentence annotation
            
        Returns:
            List of trigger dictionaries with position and type
        """
        triggers = []
        tokens = sentence_annotation.get('tokens', [])
        
        for i, token in enumerate(tokens):
            word = token.get('word', '')
            lemma = token.get('lemma', '').lower()
            pos = token.get('pos', '')
            
            # Check if this is a trigger
            is_trigger = False
            trigger_type = None
            
            # Verb triggers
            if pos.startswith('VB') and lemma in self.trigger_verbs:
                is_trigger = True
                trigger_type = 'verb'
            
            # Noun triggers
            elif pos.startswith('NN') and lemma in self.trigger_nouns:
                is_trigger = True
                trigger_type = 'noun'
            
            if is_trigger:
                trigger = {
                    'word': word,
                    'lemma': lemma,
                    'pos': pos,
                    'index': i,
                    'type': trigger_type,
                    'sentence_index': token.get('index', i)
                }
                triggers.append(trigger)
        
        return triggers
    
    def score_sentence(self, sentence_annotation: Dict) -> float:
        """
        Score how likely sentence describes violent event.
        
        Args:
            sentence_annotation: CoreNLP annotation
            
        Returns:
            Score between 0 and 1
        """
        triggers = self.detect_triggers(sentence_annotation)
        
        if not triggers:
            return 0.0
        
        tokens = sentence_annotation.get('tokens', [])
        token_count = len(tokens)
        
        # Base score from trigger count
        trigger_count = len(triggers)
        base_score = min(trigger_count / 5, 0.5)  # Max 0.5 from triggers
        
        # Bonus for violence-related context
        violence_words = sum(1 for t in tokens 
                           if t.get('lemma', '').lower() in self.lexicon.all_terms)
        context_score = min(violence_words / token_count, 0.3)
        
        # Bonus for entities (actors, locations)
        entities = sentence_annotation.get('entities', [])
        entity_score = min(len(entities) / 10, 0.2)
        
        total_score = base_score + context_score + entity_score
        return min(total_score, 1.0)


# ============================================================================
# 5W1H Extractor
# ============================================================================

class FiveW1HExtractor:
    """
    Extract Who, What, Whom, Where, When, How from violent events.
    """
    
    def __init__(self, african_ner):
        """
        Initialize extractor.
        
        Args:
            african_ner: AfricanNER instance
        """
        self.ner = african_ner
        self.logger = logging.getLogger(__name__)
    
    def extract(self, sentence_annotation: Dict, triggers: List[Dict]) -> List[Dict]:
        """
        Extract 5W1H for each trigger in sentence.
        
        Args:
            sentence_annotation: CoreNLP annotation
            triggers: List of detected triggers
            
        Returns:
            List of event extractions (one per trigger)
        """
        extractions = []
        
        for trigger in triggers:
            extraction = {
                'trigger': trigger,
                'who': None,      # Actor
                'what': None,     # Event type
                'whom': None,     # Victim
                'where': None,    # Location
                'when': None,     # Time
                'how': None       # Method/weapon
            }
            
            # Extract for this trigger
            extraction['what'] = self._extract_what(trigger, sentence_annotation)
            extraction['who'] = self._extract_who(trigger, sentence_annotation)
            extraction['whom'] = self._extract_whom(trigger, sentence_annotation)
            extraction['where'] = self._extract_where(sentence_annotation)
            extraction['when'] = self._extract_when(sentence_annotation)
            extraction['how'] = self._extract_how(trigger, sentence_annotation)
            
            extractions.append(extraction)
        
        return extractions
    
    def _extract_what(self, trigger: Dict, sent_ann: Dict) -> Dict:
        """
        Extract event type (What happened).
        
        Returns:
            Event type information
        """
        return {
            'type': 'violence',
            'trigger_word': trigger['word'],
            'trigger_lemma': trigger['lemma'],
            'preliminary_type': self._classify_event_type(trigger['lemma'])
        }
    
    def _classify_event_type(self, trigger_lemma: str) -> str:
        """Preliminary event classification from trigger."""
        # Map trigger to event type
        killing_verbs = {'kill', 'murder', 'assassinate', 'execute', 'massacre', 'slay'}
        bombing_verbs = {'bomb', 'explode', 'detonate', 'blast'}
        shooting_verbs = {'shoot', 'fire', 'gun'}
        kidnap_verbs = {'kidnap', 'abduct', 'seize', 'capture'}
        attack_verbs = {'attack', 'assault', 'raid', 'storm', 'ambush'}
        
        if trigger_lemma in killing_verbs:
            return 'killing'
        elif trigger_lemma in bombing_verbs:
            return 'bombing'
        elif trigger_lemma in shooting_verbs:
            return 'shooting'
        elif trigger_lemma in kidnap_verbs:
            return 'kidnapping'
        elif trigger_lemma in attack_verbs:
            return 'armed_attack'
        else:
            return 'violence'
    
    def _extract_who(self, trigger: Dict, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract actor (Who did it).
        
        Strategy: Look for subject of violence verb
        """
        dependencies = sent_ann.get('basicDependencies', [])
        tokens = sent_ann.get('tokens', [])
        entities = sent_ann.get('entities', [])
        
        trigger_idx = trigger['index']
        
        # Find subject dependency
        actor_idx = None
        for dep in dependencies:
            if dep.get('governor') == trigger_idx + 1:  # CoreNLP uses 1-indexed
                if dep.get('dep') in ['nsubj', 'nsubjpass', 'agent']:
                    actor_idx = dep.get('dependent') - 1  # Convert to 0-indexed
                    break
        
        if actor_idx is not None:
            # Extract actor span
            actor_span = self._extract_noun_phrase(actor_idx, dependencies, tokens)
            
            # Check if it's a known organization
            actor_text = ' '.join([tokens[i]['word'] for i in actor_span])
            actor_metadata = self._identify_actor(actor_text, entities)
            
            return {
                'text': actor_text,
                'tokens': actor_span,
                'metadata': actor_metadata
            }
        
        return None
    
    def _extract_whom(self, trigger: Dict, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract victim (Whom it affected).
        
        Strategy: Look for object of violence verb
        """
        dependencies = sent_ann.get('basicDependencies', [])
        tokens = sent_ann.get('tokens', [])
        
        trigger_idx = trigger['index']
        
        # Find object dependency
        victim_idx = None
        for dep in dependencies:
            if dep.get('governor') == trigger_idx + 1:
                if dep.get('dep') in ['dobj', 'nmod', 'obl']:
                    victim_idx = dep.get('dependent') - 1
                    break
        
        if victim_idx is not None:
            victim_span = self._extract_noun_phrase(victim_idx, dependencies, tokens)
            victim_text = ' '.join([tokens[i]['word'] for i in victim_span])
            
            # Extract casualty numbers if present
            casualties = self._extract_casualties(victim_text, tokens, victim_span)
            
            return {
                'text': victim_text,
                'tokens': victim_span,
                'deaths': casualties.get('deaths'),
                'injuries': casualties.get('injuries'),
                'type': self._classify_victim_type(victim_text)
            }
        
        return None
    
    def _extract_where(self, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract location (Where it happened).
        
        Strategy: Find LOCATION entities and location prepositions
        """
        entities = sent_ann.get('entities', [])
        tokens = sent_ann.get('tokens', [])
        
        # Find location entities
        locations = [e for e in entities if e.get('type') == 'LOCATION']
        
        if locations:
            # Prefer more specific locations
            location = locations[0]
            
            # Check if we have metadata from AfricanNER
            metadata = location.get('metadata', {})
            
            return {
                'text': location['text'],
                'type': metadata.get('type', 'UNKNOWN'),
                'country': metadata.get('country'),
                'coordinates': None  # Would need geocoding
            }
        
        # Fallback: look for "in [place]" patterns
        for i, token in enumerate(tokens):
            if token.get('lemma', '').lower() == 'in':
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if next_token.get('pos', '').startswith('NNP'):
                        # Likely a location
                        return {
                            'text': next_token['word'],
                            'type': 'INFERRED',
                            'country': None,
                            'coordinates': None
                        }
        
        return None
    
    def _extract_when(self, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract time (When it happened).
        
        Strategy: Find DATE/TIME entities and temporal expressions
        """
        entities = sent_ann.get('entities', [])
        tokens = sent_ann.get('tokens', [])
        
        # Find date entities
        dates = [e for e in entities if e.get('type') == 'DATE']
        
        if dates:
            return {
                'text': dates[0]['text'],
                'type': 'EXPLICIT',
                'normalized': None  # Would need temporal normalization
            }
        
        # Look for temporal words
        temporal_words = {'yesterday', 'today', 'tonight', 'monday', 'tuesday', 
                         'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                         'morning', 'afternoon', 'evening', 'night'}
        
        for token in tokens:
            if token.get('lemma', '').lower() in temporal_words:
                return {
                    'text': token['word'],
                    'type': 'RELATIVE',
                    'normalized': None
                }
        
        return None
    
    def _extract_how(self, trigger: Dict, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract method/weapon (How it was done).
        
        Strategy: Look for weapon mentions and tactical descriptions
        """
        tokens = sent_ann.get('tokens', [])
        
        # Weapon keywords
        weapons = {
            'gun', 'rifle', 'pistol', 'firearm', 'ak-47',
            'bomb', 'explosive', 'ied', 'grenade',
            'knife', 'machete', 'blade'
        }
        
        # Tactical keywords
        tactics = {
            'ambush', 'raid', 'assault', 'attack',
            'suicide', 'car-bomb', 'roadside'
        }
        
        found_weapons = []
        found_tactics = []
        
        for token in tokens:
            lemma = token.get('lemma', '').lower()
            if lemma in weapons:
                found_weapons.append(token['word'])
            if lemma in tactics:
                found_tactics.append(token['word'])
        
        if found_weapons or found_tactics:
            return {
                'weapons': found_weapons,
                'tactics': found_tactics,
                'text': ', '.join(found_weapons + found_tactics)
            }
        
        # Fallback: infer from trigger
        trigger_lemma = trigger['lemma']
        if 'bomb' in trigger_lemma or 'explode' in trigger_lemma:
            return {'weapons': ['explosives'], 'tactics': [], 'text': 'explosives (inferred)'}
        elif 'shoot' in trigger_lemma:
            return {'weapons': ['firearms'], 'tactics': [], 'text': 'firearms (inferred)'}
        
        return None
    
    def _extract_noun_phrase(self, head_idx: int, dependencies: List[Dict], 
                           tokens: List[Dict]) -> List[int]:
        """
        Extract complete noun phrase starting from head.
        
        Returns:
            List of token indices in the phrase
        """
        phrase_indices = {head_idx}
        
        # Add modifiers
        for dep in dependencies:
            if dep.get('governor') == head_idx + 1:
                dep_type = dep.get('dep', '')
                if dep_type in ['det', 'amod', 'compound', 'nummod', 'nmod']:
                    phrase_indices.add(dep.get('dependent') - 1)
        
        # Sort indices
        return sorted(list(phrase_indices))
    
    def _extract_casualties(self, text: str, tokens: List[Dict], 
                          span: List[int]) -> Dict:
        """
        Extract casualty numbers from victim phrase.
        
        Returns:
            Dict with 'deaths' and 'injuries' keys
        """
        casualties = {'deaths': None, 'injuries': None}
        
        # Look for number + killed/dead/injured pattern
        text_lower = text.lower()
        
        # Deaths
        death_patterns = [
            r'(\d+)\s*(?:people|persons|civilians|soldiers)?\s*(?:killed|dead|died|deaths)',
            r'(?:killed|dead|died)\s*(\d+)',
            r'(\d+)\s*(?:killed|dead|died)'
        ]
        
        for pattern in death_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    casualties['deaths'] = int(match.group(1))
                    break
                except:
                    pass
        
        # Injuries
        injury_patterns = [
            r'(\d+)\s*(?:people|persons|civilians|soldiers)?\s*(?:injured|wounded|hurt)',
            r'(?:injured|wounded|hurt)\s*(\d+)',
            r'(\d+)\s*(?:injured|wounded|hurt)'
        ]
        
        for pattern in injury_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    casualties['injuries'] = int(match.group(1))
                    break
                except:
                    pass
        
        return casualties
    
    def _classify_victim_type(self, victim_text: str) -> str:
        """Classify victim type."""
        text_lower = victim_text.lower()
        
        civilian_indicators = {'civilian', 'people', 'resident', 'villager', 'child', 'woman'}
        combatant_indicators = {'soldier', 'troop', 'military', 'police', 'fighter'}
        
        if any(ind in text_lower for ind in civilian_indicators):
            return 'civilian'
        elif any(ind in text_lower for ind in combatant_indicators):
            return 'combatant'
        else:
            return 'unknown'
    
    def _identify_actor(self, actor_text: str, entities: List[Dict]) -> Dict:
        """
        Identify actor from text and entities.
        
        Returns:
            Actor metadata
        """
        text_lower = actor_text.lower()
        
        # Check if it's a known armed group
        for entity in entities:
            if entity.get('type') == 'ORGANIZATION':
                if entity.get('subtype') in ['TERRORIST', 'REBEL']:
                    return {
                        'type': entity.get('subtype').lower(),
                        'known_group': True,
                        'metadata': entity.get('metadata', {})
                    }
        
        # Infer from keywords
        terrorist_indicators = {'militant', 'extremist', 'jihadist', 'terrorist'}
        rebel_indicators = {'rebel', 'insurgent', 'fighter'}
        state_indicators = {'military', 'army', 'police', 'soldier', 'troop', 'force'}
        criminal_indicators = {'gunman', 'gang', 'robber', 'bandit'}
        
        if any(ind in text_lower for ind in state_indicators):
            return {'type': 'state', 'known_group': False}
        elif any(ind in text_lower for ind in terrorist_indicators):
            return {'type': 'terrorist', 'known_group': False}
        elif any(ind in text_lower for ind in rebel_indicators):
            return {'type': 'rebel', 'known_group': False}
        elif any(ind in text_lower for ind in criminal_indicators):
            return {'type': 'criminal', 'known_group': False}
        
        return {'type': 'unknown', 'known_group': False}


# ============================================================================
# Event Extractor (Main Orchestrator)
# ============================================================================

class EventExtractor:
    """
    Complete event extraction system.
    """
    
    def __init__(self, violence_lexicon, african_ner):
        """
        Initialize event extractor.
        
        Args:
            violence_lexicon: ViolenceLexicon instance
            african_ner: AfricanNER instance
        """
        self.trigger_detector = EventTriggerDetector(violence_lexicon)
        self.fivew1h_extractor = FiveW1HExtractor(african_ner)
        self.logger = logging.getLogger(__name__)
    
    def extract_events(self, article_annotation: Dict) -> List[Dict]:
        """
        Extract all events from annotated article.
        
        Args:
            article_annotation: Output from NLP pipeline
            
        Returns:
            List of extracted events with 5W1H
        """
        events = []
        
        sentences = article_annotation.get('sentences', [])
        
        for sent_idx, sentence in enumerate(sentences):
            # Detect triggers
            triggers = self.trigger_detector.detect_triggers(sentence)
            
            if not triggers:
                continue
            
            # Extract 5W1H for each trigger
            extractions = self.fivew1h_extractor.extract(sentence, triggers)
            
            for extraction in extractions:
                event = {
                    'sentence_index': sent_idx,
                    'sentence_text': sentence.get('text', ''),
                    'trigger': extraction['trigger'],
                    'who': extraction['who'],
                    'what': extraction['what'],
                    'whom': extraction['whom'],
                    'where': extraction['where'],
                    'when': extraction['when'],
                    'how': extraction['how'],
                    'confidence': self._calculate_confidence(extraction)
                }
                
                events.append(event)
        
        return events
    
    def _calculate_confidence(self, extraction: Dict) -> float:
        """
        Calculate confidence score for extraction.
        
        Args:
            extraction: 5W1H extraction
            
        Returns:
            Confidence score 0-1
        """
        # Score based on completeness
        components = ['who', 'whom', 'where', 'when', 'how']
        filled = sum(1 for comp in components if extraction.get(comp) is not None)
        
        completeness_score = filled / len(components)
        
        # Bonus for confirmed entities
        entity_bonus = 0.0
        if extraction.get('who'):
            if extraction['who'].get('metadata', {}).get('known_group'):
                entity_bonus += 0.1
        
        if extraction.get('where'):
            if extraction['where'].get('type') != 'INFERRED':
                entity_bonus += 0.1
        
        total_score = min(completeness_score + entity_bonus, 1.0)
        return round(total_score, 2)


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == '__main__':
    """
    Example of using event extraction.
    """
    
    # This would come from your NLP pipeline
    sample_sentence_annotation = {
        'tokens': [
            {'word': 'Militants', 'lemma': 'militant', 'pos': 'NNS', 'index': 0},
            {'word': 'killed', 'lemma': 'kill', 'pos': 'VBD', 'index': 1},
            {'word': '15', 'lemma': '15', 'pos': 'CD', 'index': 2},
            {'word': 'civilians', 'lemma': 'civilian', 'pos': 'NNS', 'index': 3},
            {'word': 'in', 'lemma': 'in', 'pos': 'IN', 'index': 4},
            {'word': 'Maiduguri', 'lemma': 'Maiduguri', 'pos': 'NNP', 'index': 5},
        ],
        'basicDependencies': [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'dobj', 'governor': 2, 'dependent': 4},
            {'dep': 'nummod', 'governor': 4, 'dependent': 3},
            {'dep': 'nmod', 'governor': 2, 'dependent': 6},
        ],
        'entities': [
            {'text': 'Maiduguri', 'type': 'LOCATION'}
        ]
    }
    
    # Initialize components
    from domain_specific.violence_lexicon import ViolenceLexicon
    from domain_specific.african_ner import AfricanNER
    
    lexicon = ViolenceLexicon()
    ner = AfricanNER()
    
    extractor = EventExtractor(lexicon, ner)
    
    # Extract events
    article_ann = {'sentences': [sample_sentence_annotation]}
    events = extractor.extract_events(article_ann)
    
    print(f"Extracted {len(events)} events")
    for event in events:
        print(f"\nEvent: {event['what']['trigger_lemma']}")
        print(f"  Who: {event['who']}")
        print(f"  Whom: {event['whom']}")
        print(f"  Where: {event['where']}")
        print(f"  Confidence: {event['confidence']}")
