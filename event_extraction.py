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
    
    def extract(self, sentence_annotation: Dict, triggers: List[Dict], article_date: Optional[str] = None, article_text: Optional[str] = None) -> List[Dict]:
        """
        Extract 5W1H for each trigger in sentence.

        Args:
            sentence_annotation: CoreNLP annotation
            triggers: List of detected triggers
            article_date: Article publication date for date normalization
            article_text: Full article text for context (e.g., responsibility claims)

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
            extraction['who'] = self._extract_who(trigger, sentence_annotation, article_text)
            extraction['whom'] = self._extract_whom(trigger, sentence_annotation)
            extraction['where'] = self._extract_where(sentence_annotation)
            extraction['when'] = self._extract_when(sentence_annotation, article_date)
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
    
    def _extract_who(self, trigger: Dict, sent_ann: Dict, article_text: Optional[str] = None) -> Optional[Dict]:
        """
        Extract actor (Who did it).

        Strategy: Look for subject of violence verb using multiple approaches
        """
        dependencies = sent_ann.get('dependencies', sent_ann.get('basicDependencies', []))
        tokens = sent_ann.get('tokens', [])
        entities = sent_ann.get('entities', [])
        text = sent_ann.get('text', '')

        trigger_idx = trigger['sentence_index']  # Use sentence_index from trigger

        # APPROACH 0: Check for "claimed responsibility" patterns in article context
        # This is critical for cases like "Al-Shabaab claimed responsibility for the attack"
        if article_text:
            responsibility_actor = self._extract_actor_from_responsibility_claim(article_text, entities)
            if responsibility_actor:
                return responsibility_actor

        # APPROACH 0.5: Try to extract from title/first sentence patterns
        # Patterns like "Police officers killed...", "Armed gang robbed..."
        title_actor = self._extract_actor_from_title_pattern(text, entities)
        if title_actor:
            return title_actor

        # Approach 1: Find subject dependency (nsubj, nsubjpass, agent)
        actor_idx = None
        for dep in dependencies:
            gov = dep.get('governor')
            dep_type = dep.get('dep', '')

            # Match against trigger position (both 0-indexed and 1-indexed)
            if gov == trigger_idx + 1 or gov == trigger_idx:
                if dep_type in ['nsubj', 'nsubjpass', 'agent', 'csubj']:
                    actor_idx = dep.get('dependent')
                    # Normalize to 0-indexed
                    if actor_idx > 0:
                        actor_idx = actor_idx - 1
                    break

        # Approach 2: Look for ORGANIZATION or PERSON entities before trigger
        if actor_idx is None:
            for entity in entities:
                if entity.get('type') in ['ORGANIZATION', 'PERSON']:
                    # Check if entity appears before trigger in sentence
                    entity_text = entity.get('text', '')
                    if entity_text and entity_text in text:
                        entity_pos = text.find(entity_text)
                        trigger_pos = text.find(trigger['word'])
                        if entity_pos < trigger_pos and trigger_pos - entity_pos < 100:
                            # Validate this is likely an actor (not a location like "Bakara")
                            if self._is_likely_actor(entity_text):
                                return {
                                    'text': entity_text,
                                    'type': entity.get('subtype', entity.get('type')),
                                    'metadata': entity.get('metadata', {})
                                }

        # Approach 3: Extract from dependencies
        if actor_idx is not None and 0 <= actor_idx < len(tokens):
            # Extract actor span with modifiers
            actor_span = self._extract_noun_phrase(actor_idx, dependencies, tokens)

            # Build actor text
            actor_text = ' '.join([tokens[i]['word'] for i in actor_span])

            # CRITICAL: Validate this is likely an actor
            if not self._is_likely_actor(actor_text):
                # Reject this and continue to next approach
                actor_idx = None
            else:
                # Identify actor type
                actor_type = self._identify_actor(actor_text, entities)

                return {
                    'text': actor_text,
                    'type': actor_type.get('type', 'unknown'),
                    'metadata': actor_type
                }

        # Approach 4: Pattern-based extraction for common actor patterns
        # Look for patterns like "X killed/attacked" where X is a noun phrase
        if trigger_idx > 0:
            # Check tokens before trigger
            for i in range(max(0, trigger_idx - 5), trigger_idx):
                token = tokens[i]
                pos = token.get('pos', '')
                # Look for noun phrases (NNP, NNPS, NN, NNS)
                if pos.startswith('NN'):
                    actor_span = self._extract_noun_phrase(i, dependencies, tokens)
                    actor_text = ' '.join([tokens[idx]['word'] for idx in actor_span])

                    # Verify this looks like an actor (not just any noun)
                    if self._is_likely_actor(actor_text):
                        actor_type = self._identify_actor(actor_text, entities)
                        return {
                            'text': actor_text,
                            'type': actor_type.get('type', 'unknown'),
                            'metadata': actor_type
                        }

        return None

    def _extract_actor_from_responsibility_claim(self, article_text: str, entities: List[Dict]) -> Optional[Dict]:
        """
        Extract actor from responsibility claims like 'X claimed responsibility for the attack'.

        Args:
            article_text: Full article text
            entities: List of entities from the article

        Returns:
            Actor dict or None
        """
        import re

        # Patterns for responsibility claims
        patterns = [
            r'([A-Z][A-Za-z\-\s]+?)\s+claimed responsibility',
            r'([A-Z][A-Za-z\-\s]+?)\s+took responsibility',
            r'([A-Z][A-Za-z\-\s]+?)\s+said (they|it) (was|were) responsible',
            r'responsibility was claimed by ([A-Z][A-Za-z\-\s]+)',
            r'([A-Z][A-Za-z\-\s]+?)\s+stated that (they|the group)',
        ]

        for pattern in patterns:
            match = re.search(pattern, article_text)
            if match:
                potential_actor = match.group(1).strip()

                # Validate this is likely an actor
                if self._is_likely_actor(potential_actor):
                    # Try to match with an entity for more metadata
                    for entity in entities:
                        if entity.get('type') == 'ORGANIZATION':
                            entity_text = entity.get('text', '')
                            if entity_text and entity_text.lower() in potential_actor.lower():
                                return {
                                    'text': entity_text,
                                    'type': entity.get('subtype', 'ORGANIZATION'),
                                    'metadata': entity.get('metadata', {}),
                                    'from_responsibility_claim': True
                                }

                    # If no entity match, return the extracted actor
                    return {
                        'text': potential_actor,
                        'type': 'ORGANIZATION',
                        'metadata': {},
                        'from_responsibility_claim': True
                    }

        return None

    def _extract_actor_from_title_pattern(self, sentence_text: str, entities: List[Dict]) -> Optional[Dict]:
        """
        Extract actor from title/sentence patterns.

        Handles patterns like:
        - "Police officers fired..."
        - "Armed gang robbed..."
        - "Three officers killed..."
        - "A suicide bomber detonated..."

        Args:
            sentence_text: Sentence text
            entities: Entities from sentence

        Returns:
            Actor dict or None
        """
        import re

        # Pattern 1: [Number] + [Actor noun] + [verb]
        # Examples: "Three police officers", "A suicide bomber", "Six gunmen"
        patterns = [
            r'^((?:Three|Four|Five|Six|Seven|Eight|Nine|Ten|A|An)\s+[^,\.]+?(?:officers?|police|gunmen|gang|group|militants?|soldiers?|fighters?|bombers?|attackers?))',
            r'^([A-Z][a-z]+\s+(?:officers?|police|gunmen|gang|group|militants?|soldiers?|fighters?|bombers?|attackers?))',
            r'((?:police|military|security)\s+(?:officers?|forces?|personnel))',
            r'(armed\s+gang)',
            r'(suicide\s+bomber)',
            r'([A-Z][a-z]+\s+community)',  # For ethnic communities
        ]

        for pattern in patterns:
            match = re.search(pattern, sentence_text, re.IGNORECASE)
            if match:
                potential_actor = match.group(1).strip()

                # Validate this is likely an actor
                if self._is_likely_actor(potential_actor):
                    actor_type = self._identify_actor(potential_actor, entities)
                    return {
                        'text': potential_actor,
                        'type': actor_type.get('type', 'unknown'),
                        'metadata': actor_type,
                        'from_title_pattern': True
                    }

        return None

    def _extract_whom(self, trigger: Dict, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract victim (Whom it affected).

        Strategy: Look for object of violence verb and casualty mentions
        """
        dependencies = sent_ann.get('dependencies', sent_ann.get('basicDependencies', []))
        tokens = sent_ann.get('tokens', [])
        text = sent_ann.get('text', '')
        entities = sent_ann.get('entities', [])

        trigger_idx = trigger['sentence_index']

        # Approach 1: Find object dependency (dobj, nmod, obl, iobj)
        victim_idx = None
        for dep in dependencies:
            gov = dep.get('governor')
            dep_type = dep.get('dep', '')

            # Match against trigger position
            if gov == trigger_idx + 1 or gov == trigger_idx:
                if dep_type in ['dobj', 'nmod', 'obl', 'iobj', 'nmod:poss', 'obl:tmod']:
                    victim_idx = dep.get('dependent')
                    # Normalize to 0-indexed
                    if victim_idx > 0:
                        victim_idx = victim_idx - 1

                    # Make sure it's not a location or temporal expression
                    if 0 <= victim_idx < len(tokens):
                        token = tokens[victim_idx]
                        if not token.get('ner', '') in ['LOCATION', 'DATE', 'TIME']:
                            break
                    victim_idx = None

        # Approach 2: Extract from dependencies
        if victim_idx is not None and 0 <= victim_idx < len(tokens):
            victim_span = self._extract_noun_phrase(victim_idx, dependencies, tokens)
            victim_text = ' '.join([tokens[i]['word'] for i in victim_span])

            # Extract casualty numbers from full sentence context
            casualties = self._extract_casualties_from_sentence(text)

            return {
                'text': victim_text,
                'deaths': casualties.get('deaths'),
                'injuries': casualties.get('injuries'),
                'type': self._classify_victim_type(victim_text)
            }

        # Approach 3: Look for casualty patterns in full sentence
        # Even if we can't find direct object, extract casualties
        casualties = self._extract_casualties_from_sentence(text)

        if casualties.get('deaths') or casualties.get('injuries'):
            # Try to find victim noun in sentence
            victim_text = self._extract_victim_from_casualty_pattern(text)

            return {
                'text': victim_text if victim_text else 'casualties',
                'deaths': casualties.get('deaths'),
                'injuries': casualties.get('injuries'),
                'type': self._classify_victim_type(victim_text) if victim_text else 'unknown'
            }

        # Approach 4: Look for PERSON entities after trigger (named victims)
        for entity in entities:
            if entity.get('type') == 'PERSON':
                entity_text = entity.get('text', '')
                if entity_text and entity_text in text:
                    entity_pos = text.find(entity_text)
                    trigger_pos = text.find(trigger['word'])
                    if entity_pos > trigger_pos:
                        casualties = self._extract_casualties_from_sentence(text)
                        return {
                            'text': entity_text,
                            'deaths': casualties.get('deaths'),
                            'injuries': casualties.get('injuries'),
                            'type': 'civilian',
                            'named_victim': True
                        }

        # Approach 5: Search for victim indicators in sentence even without direct object
        victim_indicators = ['civilian', 'civilians', 'people', 'persons', 'resident', 'residents',
                            'villager', 'villagers', 'student', 'students', 'child', 'children',
                            'woman', 'women', 'man', 'men', 'guard', 'officer', 'officers']

        for indicator in victim_indicators:
            if indicator in text.lower():
                casualties = self._extract_casualties_from_sentence(text)
                if casualties.get('deaths') or casualties.get('injuries'):
                    # Found casualties with victim type
                    victim_type = 'combatant' if indicator in ['officer', 'officers', 'soldier', 'soldiers', 'guard'] else 'civilian'
                    return {
                        'text': indicator,
                        'deaths': casualties.get('deaths'),
                        'injuries': casualties.get('injuries'),
                        'type': victim_type,
                        'inferred': True
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
    
    def _extract_when(self, sent_ann: Dict, article_date: Optional[str] = None) -> Optional[Dict]:
        """
        Extract time (When it happened).

        Strategy: Find DATE/TIME entities and temporal expressions
        """
        entities = sent_ann.get('entities', [])
        tokens = sent_ann.get('tokens', [])

        # Import date normalizer
        try:
            from utils.date_normalizer import DateNormalizer
            normalizer = DateNormalizer()
        except ImportError:
            normalizer = None

        # Find date entities
        dates = [e for e in entities if e.get('type') == 'DATE']

        if dates:
            date_text = dates[0]['text']
            normalized = None
            if normalizer:
                normalized = normalizer.normalize_date(date_text, article_date)

            return {
                'text': date_text,
                'type': 'EXPLICIT',
                'normalized': normalized
            }

        # Look for temporal words
        temporal_words = {'yesterday', 'today', 'tonight', 'monday', 'tuesday',
                         'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                         'morning', 'afternoon', 'evening', 'night'}

        for token in tokens:
            if token.get('lemma', '').lower() in temporal_words:
                date_text = token['word']
                normalized = None
                if normalizer and article_date:
                    normalized = normalizer.normalize_date(date_text, article_date)

                return {
                    'text': date_text,
                    'type': 'RELATIVE',
                    'normalized': normalized
                }

        return None
    
    def _extract_how(self, trigger: Dict, sent_ann: Dict) -> Optional[Dict]:
        """
        Extract method/weapon (How it was done).

        Strategy: Look for weapon mentions and tactical descriptions
        """
        tokens = sent_ann.get('tokens', [])
        text = sent_ann.get('text', '')

        # Expanded weapon keywords
        weapons = {
            # Firearms
            'gun', 'rifle', 'rifles', 'pistol', 'pistols', 'firearm', 'firearms',
            'ak-47', 'ak47', 'kalashnikov', 'm16', 'weapon', 'weapons',
            # Explosives
            'bomb', 'bombs', 'explosive', 'explosives', 'ied', 'grenade', 'grenades',
            'rocket', 'rpg', 'mortar', 'mine', 'mines',
            # Edged weapons
            'knife', 'knives', 'machete', 'machetes', 'blade', 'sword', 'spear', 'spears',
            # Other
            'ammunition', 'bullet', 'bullets', 'shell', 'device'
        }

        # Expanded tactical keywords
        tactics = {
            'ambush', 'raid', 'assault', 'attack', 'attacks',
            'suicide', 'car-bomb', 'roadside', 'ied',
            'stormed', 'storm'
        }

        found_weapons = []
        found_tactics = []

        # Search in tokens
        for token in tokens:
            word_lower = token.get('word', '').lower()
            lemma = token.get('lemma', '').lower()

            if lemma in weapons or word_lower in weapons:
                found_weapons.append(token['word'].lower())
            if lemma in tactics or word_lower in tactics:
                found_tactics.append(token['word'].lower())

        # Also search text for multi-word weapons
        text_lower = text.lower()
        multi_word_weapons = {
            'live ammunition': 'live ammunition',
            'tear gas': 'tear gas',
            'rubber bullets': 'rubber bullets',
            'molotov cocktail': 'Molotov cocktail',
            'improvised explosive': 'improvised explosive',
            'explosive device': 'explosive device',
            'suicide bomb': 'suicide bomb',
            'car bomb': 'car bomb'
        }

        for pattern, weapon_name in multi_word_weapons.items():
            if pattern in text_lower:
                found_weapons.append(weapon_name)

        # Deduplicate and clean
        found_weapons = list(set(found_weapons))
        found_tactics = list(set(found_tactics))

        if found_weapons or found_tactics:
            return {
                'weapons': found_weapons,
                'tactics': found_tactics,
                'text': ', '.join(found_weapons + found_tactics)
            }

        # Fallback: infer from trigger
        trigger_lemma = trigger['lemma']
        if 'bomb' in trigger_lemma or 'explode' in trigger_lemma or 'detonate' in trigger_lemma:
            return {'weapons': ['explosive'], 'tactics': [], 'text': 'explosive'}
        elif 'shoot' in trigger_lemma or 'fire' in trigger_lemma or 'gun' in trigger_lemma:
            return {'weapons': ['firearms'], 'tactics': [], 'text': 'firearms'}
        elif 'suicide' in text_lower:
            return {'weapons': ['explosive'], 'tactics': ['suicide'], 'text': 'explosive, suicide'}

        return None
    
    def _is_likely_actor(self, text: str) -> bool:
        """Check if text looks like an actor/perpetrator."""
        text_lower = text.lower()

        # Known actor indicators (including known organizations)
        actor_keywords = {
            'group', 'force', 'forces', 'army', 'military', 'police', 'officer', 'officers',
            'soldier', 'soldiers', 'troop', 'troops', 'militant', 'militants', 'fighter', 'fighters',
            'rebel', 'rebels', 'insurgent', 'insurgents', 'terrorist', 'terrorists',
            'gang', 'gunman', 'gunmen', 'attacker', 'attackers', 'bomber',
            'shabaab', 'boko', 'haram', 'aqim', 'isis', 'al-qaeda', 'al-shabaab',
            'supporters', 'protesters', 'demonstrators', 'community', 'communities', 'militia', 'militias',
            # Common African ethnic/communal groups
            'hema', 'lendu', 'hutu', 'tutsi', 'fulani', 'hausa', 'yoruba', 'igbo',
            'nuer', 'dinka', 'shona', 'ndebele', 'zulu', 'xhosa',
            # Other actor types
            'herders', 'farmers', 'pastoralists', 'nomads', 'tribesmen'
        }

        # CRITICAL: Check actor keywords FIRST (before non-actor check)
        # This prevents false rejections like "a" in "al-shabaab"
        if any(keyword in text_lower for keyword in actor_keywords):
            return True

        # CRITICAL: Exclude obvious non-actors (using word boundaries)
        non_actor_indicators = {
            # Places
            'market', 'markets', 'building', 'buildings', 'town', 'city', 'village',
            'street', 'road', 'area', 'region', 'country', 'province', 'state',
            'restaurant', 'hotel', 'mosque', 'church', 'school', 'hospital',
            # Times/descriptive words
            'morning', 'afternoon', 'evening', 'night', 'day', 'week', 'month',
            'violent', 'recent', 'deadly', 'latest', 'ongoing'
        }

        # Articles/determiners and single letters (as complete words only)
        single_word_non_actors = {
            'the', 'a', 'an', 'this', 'that', 'these', 'those',
            'during', 'after', 'before', 'in', 'at', 'on', 'by'
        }

        # Check if text is EXACTLY one of the single-word non-actors
        if text_lower in single_word_non_actors:
            return False

        # Check for non-actor indicators (substring match)
        if any(non_actor in text_lower for non_actor in non_actor_indicators):
            return False

        # Reject if contains numbers (but not as part of a larger name)
        if any(char.isdigit() for char in text) and len(text) < 5:
            return False

        # If it's less than 2 characters, reject
        if len(text.strip()) < 2:
            return False

        # If it's a proper noun (starts with capital) and has multiple words, might be an organization
        words = text.split()
        if len(words) >= 2 and all(w[0].isupper() for w in words if w):
            # Multi-word proper nouns are likely organizations/groups
            return True

        return False

    def _extract_victim_from_casualty_pattern(self, text: str) -> Optional[str]:
        """Extract victim type from casualty patterns in text."""
        text_lower = text.lower()

        # Patterns like "killing 15 civilians", "15 people killed"
        patterns = [
            r'(?:killing|killed|kill)\s+(?:at least\s+)?(?:\d+\s+)?(\w+)',
            r'(\d+\s+\w+)\s+(?:killed|dead|died)',
            r'(?:death|deaths)\s+of\s+(?:\d+\s+)?(\w+)',
            r'(\w+)\s+(?:and\s+\w+\s+)?(?:killed|dead|died)'
        ]

        victim_words = {'civilian', 'civilians', 'people', 'person', 'persons', 'resident',
                       'residents', 'villager', 'villagers', 'student', 'students',
                       'child', 'children', 'woman', 'women', 'man', 'men'}

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                potential_victim = match.group(1).strip()
                # Check if it's actually a victim word
                for victim_word in victim_words:
                    if victim_word in potential_victim:
                        return potential_victim

        return None

    def _extract_casualties_from_sentence(self, text: str) -> Dict:
        """
        Extract casualty numbers from full sentence text.

        This is more robust than the old method as it searches the full sentence.
        """
        casualties = {'deaths': None, 'injuries': None}
        text_lower = text.lower()

        # CRITICAL FIX: Exclude ages (e.g., "22-year-old") from casualty extraction
        # Remove age patterns before extracting casualties
        age_pattern = r'\d+-year-old'
        text_lower_no_ages = re.sub(age_pattern, 'PERSON', text_lower)

        # Enhanced death patterns - now work on text without ages
        death_patterns = [
            r'killing\s+(?:at least\s+)?(\d+)',
            r'killed\s+(?:at least\s+)?(\d+)',
            r'(\d+)\s+(?:people|persons|civilians|soldiers|residents|villagers|students)\s*(?:were\s+)?(?:killed|dead|died)',
            r'death\s+of\s+(?:the\s+)?(\d+)',
            r'(\d+)\s+(?:killed|dead|died)',
            r'(\d+)\s+(?:have\s+)?died',
            r'left\s+(\d+)\s+(?:people\s+)?dead',
            r'(\d+)\s+people\s+dead',
            r'toll\s+of\s+(\d+)',
            r'(\d+)\s+deaths?'
        ]

        # Try each pattern on text without ages
        for pattern in death_patterns:
            match = re.search(pattern, text_lower_no_ages)
            if match:
                try:
                    num = int(match.group(1))
                    # Sanity check: casualty numbers should be reasonable (< 10000)
                    if num > 0 and num < 10000:
                        casualties['deaths'] = num
                        break
                except (ValueError, IndexError):
                    pass

        # Enhanced injury patterns
        injury_patterns = [
            r'injuring\s+(?:at least\s+)?(\d+)',
            r'injured\s+(?:at least\s+)?(\d+)',
            r'(\d+)\s+(?:people|persons|civilians|soldiers|others)\s*(?:were\s+)?(?:injured|wounded|hurt)',
            r'(\d+)\s+(?:injured|wounded|hurt)',
            r'(\d+)\s+(?:have\s+been\s+)?(?:injured|wounded)',
            r'(\d+)\s+others?\s+(?:injured|wounded)',
            r'including\s+(\d+)\s+(?:police\s+)?officers'
        ]

        for pattern in injury_patterns:
            match = re.search(pattern, text_lower_no_ages)
            if match:
                try:
                    num = int(match.group(1))
                    if num > 0 and num < 10000:
                        casualties['injuries'] = num
                        break
                except (ValueError, IndexError):
                    pass

        # Special case: "X dead and Y injured" pattern
        combined_pattern = r'(\d+)\s+(?:people\s+)?dead\s+and\s+(\d+)\s+injured'
        match = re.search(combined_pattern, text_lower_no_ages)
        if match:
            try:
                d = int(match.group(1))
                i = int(match.group(2))
                if d > 0 and d < 10000:
                    casualties['deaths'] = d
                if i > 0 and i < 10000:
                    casualties['injuries'] = i
            except (ValueError, IndexError):
                pass

        # Special case: "X people dead, Y injured" or similar variations
        alt_combined = r'(\d+)\s+(?:people|persons)\s+(?:dead|killed).*?(\d+)\s+injured'
        match = re.search(alt_combined, text_lower_no_ages)
        if match and not casualties['deaths']:  # Only if not already found
            try:
                d = int(match.group(1))
                i = int(match.group(2))
                if d > 0 and d < 10000:
                    casualties['deaths'] = d
                if i > 0 and i < 10000:
                    casualties['injuries'] = i
            except (ValueError, IndexError):
                pass

        return casualties

    def _extract_noun_phrase(self, head_idx: int, dependencies: List[Dict],
                           tokens: List[Dict]) -> List[int]:
        """
        Extract complete noun phrase starting from head.

        Returns:
            List of token indices in the phrase
        """
        phrase_indices = {head_idx}

        # Add modifiers - look for dependencies where head is governor
        for dep in dependencies:
            gov = dep.get('governor')
            # Try both 1-indexed and 0-indexed
            if gov == head_idx + 1 or gov == head_idx:
                dep_type = dep.get('dep', '')
                if dep_type in ['det', 'amod', 'compound', 'nummod', 'nmod', 'case', 'advmod']:
                    dependent = dep.get('dependent')
                    # Normalize to 0-indexed
                    if dependent > 0:
                        phrase_indices.add(dependent - 1)
                    else:
                        phrase_indices.add(dependent)

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

        # Initialize taxonomy classifier
        try:
            from taxonomy_classifier import TaxonomyClassifier
            self.taxonomy_classifier = TaxonomyClassifier()
        except ImportError:
            self.logger.warning("TaxonomyClassifier not available")
            self.taxonomy_classifier = None
    
    def extract_events(self, article_annotation: Dict, article_date: Optional[str] = None) -> List[Dict]:
        """
        Extract all events from annotated article.

        Args:
            article_annotation: Output from NLP pipeline
            article_date: Article publication date for date normalization

        Returns:
            List of extracted events with 5W1H
        """
        events = []

        sentences = article_annotation.get('sentences', [])
        article_text = article_annotation.get('cleaned_text', article_annotation.get('original_text', ''))
        article_id = article_annotation.get('article_id', 'unknown')

        # Extract article-level context
        article_context = self._extract_article_context(article_annotation)

        # Extract article date if not provided
        if not article_date:
            metadata = article_annotation.get('metadata', {})
            article_date = metadata.get('date')

        for sent_idx, sentence in enumerate(sentences):
            # Detect triggers
            triggers = self.trigger_detector.detect_triggers(sentence)

            if not triggers:
                continue

            # Extract 5W1H for each trigger (pass article_date and article_text)
            extractions = self.fivew1h_extractor.extract(sentence, triggers, article_date, article_text)

            for extraction in extractions:
                # Propagate article-level context to incomplete extractions
                extraction = self._propagate_context(extraction, article_context, sentence)

                # Ensure trigger has correct sentence_index
                trigger = extraction['trigger']
                trigger['sentence_index'] = sent_idx

                event = {
                    'article_id': article_id,
                    'sentence_index': sent_idx,
                    'sentence_text': sentence.get('text', ''),
                    'trigger': trigger,
                    'who': extraction['who'],
                    'what': extraction['what'],
                    'whom': extraction['whom'],
                    'where': extraction['where'],
                    'when': extraction['when'],
                    'how': extraction['how'],
                    'confidence': self._calculate_confidence(extraction),
                    'completeness': self._calculate_completeness(extraction)
                }

                # Add taxonomy classification
                if self.taxonomy_classifier:
                    taxonomy_l1, taxonomy_l2, taxonomy_l3 = self.taxonomy_classifier.classify(event)
                    event['taxonomy_l1'] = taxonomy_l1
                    event['taxonomy_l2'] = taxonomy_l2
                    event['taxonomy_l3'] = taxonomy_l3
                else:
                    event['taxonomy_l1'] = ''
                    event['taxonomy_l2'] = ''
                    event['taxonomy_l3'] = ''

                events.append(event)

        # First pass: Detect and split reciprocal violence events
        events = self._detect_reciprocal_violence(events, sentences)
        self.logger.debug(f"After reciprocal violence detection: {len(events)} events")

        # Second pass: Merge events within same/adjacent sentences
        events = self._merge_similar_events(events)
        self.logger.debug(f"After merge similar events: {len(events)} events")

        # Third pass: CLUSTER events across entire article (coreference resolution)
        events = self._cluster_coreferent_events(events, article_annotation)
        self.logger.debug(f"After cluster coreferent events: {len(events)} events")

        # Fourth pass: Filter by salience (keep only main newsworthy events, not background context)
        events = self._filter_by_salience(events, article_annotation)
        self.logger.debug(f"After salience filtering: {len(events)} events")

        # Filter out very low confidence events
        # Increase threshold to reduce noise
        events = [e for e in events if e['confidence'] >= 0.30]
        self.logger.debug(f"After confidence filtering (>= 0.30): {len(events)} events")

        return events
    
    def _calculate_confidence(self, extraction: Dict) -> float:
        """
        Calculate confidence score for extraction.

        Args:
            extraction: 5W1H extraction

        Returns:
            Confidence score 0-1
        """
        score = 0.0

        # Critical components (higher weight)
        if extraction.get('who'):
            score += 0.25
        if extraction.get('whom'):
            score += 0.25
            # Bonus if casualties are extracted
            if extraction['whom'].get('deaths') or extraction['whom'].get('injuries'):
                score += 0.10

        # Important components (medium weight)
        if extraction.get('where'):
            score += 0.15
        if extraction.get('when'):
            score += 0.10

        # Supporting components (lower weight)
        if extraction.get('how'):
            score += 0.10

        # Bonus for specific entity types
        if extraction.get('who'):
            actor_type = extraction['who'].get('type', 'unknown')
            if actor_type != 'unknown':
                score += 0.05

        # Ensure score is between 0 and 1
        return round(min(score, 1.0), 2)

    def _detect_reciprocal_violence(self, events: List[Dict], sentences: List[Dict]) -> List[Dict]:
        """
        Detect and split reciprocal violence events.

        Patterns like "clashes between X and Y" should become 2 events:
        - Event 1: X (actor) -> Y (victim)
        - Event 2: Y (actor) -> X (victim)

        Args:
            events: List of extracted events
            sentences: Article sentences

        Returns:
            Expanded event list with reciprocal violence split
        """
        import re

        expanded_events = []
        processed_sentences = set()  # Track sentences that have been split into reciprocal pairs

        for event in events:
            sentence_text = event.get('sentence_text', '')
            sentence_idx = event.get('sentence_index')
            trigger_lemma = event.get('trigger', {}).get('lemma', '')

            # If this sentence already created a reciprocal pair, don't create another
            if sentence_idx in processed_sentences:
                expanded_events.append(event)
                continue

            # Check if this is a reciprocal violence pattern
            # Note: Use (.+?) to match "any text" not [^and] which means "any char except a, n, d"
            reciprocal_patterns = [
                r'between\s+(.+?)\s+and\s+(.+?)(?:\s+in|\s+communities|\s+have|,)',
                r'clash(?:es)?\s+between\s+(.+?)\s+and\s+(.+?)(?:\s+in|\s+communities|,)',
                r'violence\s+between\s+(.+?)\s+and\s+(.+?)(?:\s+in|\s+communities|,)',
                r'fight(?:ing)?\s+between\s+(.+?)\s+and\s+(.+?)(?:\s+in|\s+communities|,)',
                r'conflict\s+between\s+(.+?)\s+and\s+(.+?)(?:\s+in|\s+communities|,)',
                r'([A-Z]\w+(?:\s+\w+)?)\s+(?:and|vs|versus)\s+([A-Z]\w+(?:\s+\w+)?)\s+clash(?:ed)?',
                r'([A-Z]\w+(?:\s+\w+)?)\s+(?:and|vs|versus)\s+([A-Z]\w+(?:\s+\w+)?)\s+fought',
            ]

            matched = False
            for pattern in reciprocal_patterns:
                match = re.search(pattern, sentence_text, re.IGNORECASE)
                if match:
                    actor1_text = match.group(1).strip()
                    actor2_text = match.group(2).strip()

                    # Validate both are likely actors
                    if self.fivew1h_extractor._is_likely_actor(actor1_text) and self.fivew1h_extractor._is_likely_actor(actor2_text):
                        # Create two events - one from each perspective

                        # Event 1: Actor1 -> Actor2
                        event1 = event.copy()
                        event1['who'] = {
                            'text': actor1_text,
                            'type': 'communal',  # Default for inter-community violence
                            'metadata': {}
                        }
                        event1['whom'] = {
                            'text': actor2_text,
                            'type': 'civilian',
                            'deaths': event.get('whom', {}).get('deaths'),
                            'injuries': event.get('whom', {}).get('injuries')
                        }
                        event1['reciprocal_violence'] = True
                        event1['reciprocal_pair'] = 1

                        # Event 2: Actor2 -> Actor1
                        event2 = event.copy()
                        event2['who'] = {
                            'text': actor2_text,
                            'type': 'communal',
                            'metadata': {}
                        }
                        event2['whom'] = {
                            'text': actor1_text,
                            'type': 'civilian',
                            'deaths': None,  # Casualties split between events
                            'injuries': None
                        }
                        event2['reciprocal_violence'] = True
                        event2['reciprocal_pair'] = 2

                        # Recalculate confidence and completeness for both
                        event1['confidence'] = self._calculate_confidence(event1)
                        event1['completeness'] = self._calculate_completeness(event1)
                        event2['confidence'] = self._calculate_confidence(event2)
                        event2['completeness'] = self._calculate_completeness(event2)

                        expanded_events.append(event1)
                        expanded_events.append(event2)
                        processed_sentences.add(sentence_idx)  # Mark sentence as processed
                        matched = True
                        break

            # If no reciprocal pattern matched, keep original event
            if not matched:
                expanded_events.append(event)

        return expanded_events

    def _calculate_completeness(self, extraction: Dict) -> float:
        """
        Calculate completeness score based on presence of 5W1H components.

        Args:
            extraction: 5W1H extraction

        Returns:
            Completeness score 0-1 (1 = all components present)
        """
        score = 0.0
        total_components = 6  # who, what, whom, where, when, how

        # What (trigger/event type) - always present
        if extraction.get('what'):
            score += 1

        # Who (actor)
        if extraction.get('who'):
            score += 1

        # Whom (victim/casualties)
        if extraction.get('whom'):
            score += 1

        # Where (location)
        if extraction.get('where'):
            score += 1

        # When (time/date)
        if extraction.get('when'):
            score += 1

        # How (weapon/method)
        if extraction.get('how'):
            score += 1

        completeness = score / total_components
        return round(completeness, 2)

    def _extract_article_context(self, article_annotation: Dict) -> Dict:
        """
        Extract article-level context (location, time, actors mentioned).

        Args:
            article_annotation: Full article annotation

        Returns:
            Dict with article-level context
        """
        context = {
            'locations': [],
            'dates': [],
            'organizations': [],
            'persons': []
        }

        sentences = article_annotation.get('sentences', [])

        # Collect all entities from article
        for sentence in sentences:
            entities = sentence.get('entities', [])

            for entity in entities:
                entity_type = entity.get('type')
                entity_text = entity.get('text', '')

                if entity_type == 'LOCATION' and entity_text not in context['locations']:
                    context['locations'].append({
                        'text': entity_text,
                        'type': entity.get('subtype', entity_type),
                        'metadata': entity.get('metadata', {})
                    })
                elif entity_type == 'DATE' and entity_text not in [d['text'] for d in context['dates']]:
                    context['dates'].append({
                        'text': entity_text,
                        'type': 'EXPLICIT'
                    })
                elif entity_type == 'ORGANIZATION' and entity_text not in [o['text'] for o in context['organizations']]:
                    context['organizations'].append({
                        'text': entity_text,
                        'type': entity.get('subtype', entity_type),
                        'metadata': entity.get('metadata', {})
                    })
                elif entity_type == 'PERSON' and entity_text not in [p['text'] for p in context['persons']]:
                    context['persons'].append({
                        'text': entity_text
                    })

        return context

    def _propagate_context(self, extraction: Dict, article_context: Dict, sentence: Dict) -> Dict:
        """
        Propagate article-level context to extraction if components are missing.

        Args:
            extraction: Event extraction
            article_context: Article-level context
            sentence: Current sentence

        Returns:
            Enhanced extraction
        """
        # Propagate location if missing
        if not extraction.get('where') and article_context['locations']:
            # Use the first (usually most prominent) location
            extraction['where'] = article_context['locations'][0].copy()
            extraction['where']['type'] = 'INFERRED'

        # Propagate time if missing
        if not extraction.get('when') and article_context['dates']:
            extraction['when'] = article_context['dates'][0].copy()
            extraction['when']['type'] = 'INFERRED'

        # CRITICAL: Propagate actor if missing and article has organizations
        if not extraction.get('who') and article_context['organizations']:
            # Try to find an organization that looks like a perpetrator
            for org in article_context['organizations']:
                org_text_lower = org['text'].lower()
                # Check if organization is likely a perpetrator
                perpetrator_indicators = ['shabaab', 'boko', 'haram', 'aqim', 'isis',
                                         'militant', 'terrorist', 'rebel', 'insurgent',
                                         'gang', 'group']

                if any(ind in org_text_lower for ind in perpetrator_indicators):
                    extraction['who'] = {
                        'text': org['text'],
                        'type': org.get('type', 'ORGANIZATION'),
                        'metadata': org.get('metadata', {}),
                        'inferred': True  # Mark as inferred from article
                    }
                    break

        # If still no actor, try to infer from sentence entities
        if not extraction.get('who'):
            entities = sentence.get('entities', [])
            for entity in entities:
                if entity.get('type') == 'ORGANIZATION':
                    # Check if it's mentioned before the trigger
                    text = sentence.get('text', '')
                    trigger = extraction.get('trigger', {})
                    trigger_word = trigger.get('word', '')

                    entity_text = entity.get('text', '')
                    if entity_text and trigger_word:
                        entity_pos = text.find(entity_text)
                        trigger_pos = text.find(trigger_word)

                        if 0 <= entity_pos < trigger_pos:
                            extraction['who'] = {
                                'text': entity_text,
                                'type': entity.get('subtype', entity.get('type')),
                                'metadata': entity.get('metadata', {}),
                                'inferred': True
                            }
                            break

        return extraction

    def _filter_by_salience(self, events: List[Dict], article_annotation: Dict) -> List[Dict]:
        """
        Filter events by salience to keep only main newsworthy events.

        Removes background context and references to other incidents.
        Uses multiple signals to determine if event is main news vs. background.

        Args:
            events: List of extracted events
            article_annotation: Full article annotation

        Returns:
            Filtered list containing only salient events
        """
        if not events:
            return events

        # SPECIAL CASE: Keep all reciprocal violence events together
        # Reciprocal violence (e.g., "Hema vs Lendu") should always keep both perspectives
        reciprocal_events = [e for e in events if e.get('reciprocal_violence')]
        non_reciprocal_events = [e for e in events if not e.get('reciprocal_violence')]

        # Calculate salience score for each non-reciprocal event
        scored_events = []
        for event in non_reciprocal_events:
            score = self._calculate_salience_score(event, article_annotation)
            scored_events.append((event, score))
            # Debug logging
            trigger = event.get('trigger', {})
            self.logger.debug(f"Salience score for trigger '{trigger.get('word')}' (sent {trigger.get('sentence_index')}): {score}")

        # Sort by salience score (descending)
        scored_events.sort(key=lambda x: x[1], reverse=True)

        # Keep events above salience threshold
        # High-salience events are main news (score >= 7)
        # Low-salience events are background context (score < 7)
        # INCREASED from 5 to 7 for more aggressive filtering
        salient_events = reciprocal_events.copy()  # Always keep reciprocal events
        for event, score in scored_events:
            if score >= 7:
                salient_events.append(event)

        # If nothing passed threshold, keep only the top event
        # Most articles report 1 main event
        if not salient_events and events:
            salient_events = [e for e, s in scored_events[:1]]
            self.logger.debug(f"No events passed salience threshold, keeping top 1 event only")

        return salient_events

    def _calculate_salience_score(self, event: Dict, article_annotation: Dict) -> int:
        """
        Calculate salience score for an event.

        Higher score = more likely to be main news event
        Lower score = more likely to be background context

        Signals:
        - Early in article (+3): First 2 sentences are usually main news
        - Has casualties (+4): Main events usually report deaths/injuries
        - Has victim (+2): Specific victims indicate concrete event
        - High completeness (+2): Main events have more details
        - High confidence (+2): Main events are clearer
        - Location matches article context (+2): Main event location in headline/metadata
        - Past tense trigger (-2): May indicate background/historical context
        - Conditional/modal context (-3): "would", "could", "might" suggest non-actual event

        Args:
            event: Event to score
            article_annotation: Article context

        Returns:
            Salience score (0-15, higher = more salient)
        """
        score = 0

        # Signal 1: Position in article (+3 for first 2 sentences)
        trigger = event.get('trigger', {})
        sentence_idx = trigger.get('sentence_index', 999)
        if sentence_idx <= 2:
            score += 3

        # Signal 2: Has casualties (+4) - main events report deaths/injuries
        whom = event.get('whom')
        if whom:
            deaths = whom.get('deaths')
            injuries = whom.get('injuries')
            if deaths is not None or injuries is not None:
                score += 4

        # Signal 3: Has specific victim (+2)
        if whom and whom.get('text'):
            score += 2

        # Signal 4: High completeness (+2 if >= 80%)
        completeness = event.get('completeness', 0)
        if completeness >= 0.8:
            score += 2

        # Signal 5: High confidence (+2 if >= 0.8)
        confidence = event.get('confidence', 0)
        if confidence >= 0.8:
            score += 2

        # Signal 6: Location matches article location (+2)
        where = event.get('where')
        if where:
            location_text = where.get('text', '').lower()
            # Check against article title/first sentence
            sentences = article_annotation.get('sentences', [])
            if sentences:
                first_text = sentences[0].get('text', '').lower()
                if location_text in first_text:
                    score += 2

        # NEGATIVE SIGNALS

        # Signal 7: Past tense in background context (-2)
        # Check if trigger is past tense and far from beginning
        trigger_pos = trigger.get('pos', '')
        if trigger_pos == 'VBD' and sentence_idx > 3:
            score -= 1

        # Signal 8: Modal/conditional context (-3)
        # Check sentence for modal verbs suggesting hypothetical
        if sentence_idx < len(article_annotation.get('sentences', [])):
            sentence = article_annotation['sentences'][sentence_idx]
            text_lower = sentence.get('text', '').lower()
            modal_indicators = ['would', 'could', 'might', 'may', 'should', 'if', 'in case']
            if any(modal in text_lower for modal in modal_indicators):
                score -= 3

        return max(0, score)  # Don't go negative

    def _merge_similar_events(self, events: List[Dict]) -> List[Dict]:
        """
        Merge or deduplicate similar events from the same sentence.

        Args:
            events: List of extracted events

        Returns:
            Merged/deduplicated event list
        """
        if len(events) <= 1:
            return events

        merged = []
        used = set()

        for i, event1 in enumerate(events):
            if i in used:
                continue

            # Check if this event should be merged with another
            merged_event = event1.copy()
            merged_with = []

            for j, event2 in enumerate(events):
                if j <= i or j in used:
                    continue

                # Merge criteria: same sentence and related triggers
                if event1['sentence_index'] == event2['sentence_index']:
                    if self._should_merge_events(event1, event2):
                        # Merge event2 into event1
                        merged_event = self._merge_two_events(merged_event, event2)
                        used.add(j)
                        merged_with.append(j)

            merged.append(merged_event)
            used.add(i)

        return merged

    def _should_merge_events(self, event1: Dict, event2: Dict) -> bool:
        """
        Determine if two events should be merged.

        Args:
            event1, event2: Events to compare

        Returns:
            True if events should be merged
        """
        # AGGRESSIVE MERGING: Merge events from same OR adjacent sentences
        sentence_diff = abs(event1['sentence_index'] - event2['sentence_index'])
        if sentence_diff > 2:  # Only merge if within 2 sentences of each other
            return False

        # Check trigger relationship
        trigger1 = event1['trigger']['lemma']
        trigger2 = event2['trigger']['lemma']

        # Related trigger groups - EXPANDED
        related_groups = [
            {'kill', 'murder', 'assassinate', 'massacre', 'slay', 'execute', 'death'},
            {'bomb', 'explode', 'detonate', 'blast', 'explosion', 'bombing'},
            {'shoot', 'fire', 'gun', 'shot', 'firing', 'shooting'},
            {'attack', 'assault', 'raid', 'storm', 'ambush', 'strike'},
            {'injure', 'wound', 'hurt', 'harm', 'injured', 'wounded'},
            {'kidnap', 'abduct', 'seize', 'capture'},
            {'destroy', 'burn', 'raze', 'demolish', 'destroyed'}
        ]

        for group in related_groups:
            if trigger1 in group and trigger2 in group:
                return True

        # Check if one is describing the other (e.g., "bombing" and "explosion")
        describing_pairs = [
            ('bomb', 'explosion'),
            ('bombing', 'explosion'),
            ('detonate', 'explosion'),
            ('attack', 'killing'),
            ('attack', 'kill'),
            ('shoot', 'death'),
            ('shoot', 'kill'),
            ('fire', 'kill'),
            ('detonate', 'blast'),
            ('injure', 'kill'),  # Often same incident
            ('destroy', 'attack')
        ]

        for t1, t2 in describing_pairs:
            if (trigger1 == t1 and trigger2 == t2) or (trigger1 == t2 and trigger2 == t1):
                return True

        # AGGRESSIVE: If they share the same location AND casualties, likely same event
        loc1 = event1.get('where', {})
        loc2 = event2.get('where', {})
        if loc1 and loc2 and loc1.get('text') == loc2.get('text'):
            casualties1 = event1.get('whom', {})
            casualties2 = event2.get('whom', {})

            # If both have casualties and they match, it's the same event
            if casualties1 and casualties2:
                deaths1 = casualties1.get('deaths')
                deaths2 = casualties2.get('deaths')
                if deaths1 and deaths2 and deaths1 == deaths2:
                    return True

        return False

    def _merge_two_events(self, event1: Dict, event2: Dict) -> Dict:
        """
        Merge two events, combining their information.

        Args:
            event1: Primary event
            event2: Secondary event to merge in

        Returns:
            Merged event
        """
        merged = event1.copy()

        # For each 5W1H component, use the more complete one
        for component in ['who', 'whom', 'where', 'when', 'how']:
            val1 = merged.get(component)
            val2 = event2.get(component)

            # If event1 is missing this component but event2 has it
            if not val1 and val2:
                merged[component] = val2
            # If both have it, prefer the one with more information
            elif val1 and val2:
                if isinstance(val1, dict) and isinstance(val2, dict):
                    # Merge dictionaries, preferring non-null values from event2
                    for key, value in val2.items():
                        if value and not val1.get(key):
                            val1[key] = value

        # Recalculate confidence for merged event
        merged['confidence'] = self._calculate_confidence(merged)

        return merged

    def _cluster_coreferent_events(self, events: List[Dict], article_annotation: Dict) -> List[Dict]:
        """
        Cluster events that refer to the same real-world incident.

        This handles coreference across multiple sentences describing the same event.

        Args:
            events: List of extracted events
            article_annotation: Full article annotation

        Returns:
            Clustered events (one per real incident)
        """
        if len(events) <= 1:
            return events

        # Build similarity matrix
        n = len(events)
        clusters = []  # List of event clusters
        used = set()

        for i in range(n):
            if i in used:
                continue

            # Start new cluster with this event
            cluster = [events[i]]
            used.add(i)

            # Find all events that should be in same cluster
            for j in range(i + 1, n):
                if j in used:
                    continue

                if self._events_refer_to_same_incident(events[i], events[j], article_annotation):
                    cluster.append(events[j])
                    used.add(j)

            # If cluster has multiple events, merge them into one
            if len(cluster) > 1:
                merged_event = self._merge_event_cluster(cluster)
                clusters.append(merged_event)
            else:
                clusters.append(cluster[0])

        return clusters

    def _events_refer_to_same_incident(self, event1: Dict, event2: Dict, article_annotation: Dict) -> bool:
        """
        Determine if two events refer to the same real-world incident.

        Uses multiple signals:
        - Same actor
        - Same location
        - Same casualties (deaths/injuries)
        - Close temporal proximity (within 3 sentences)
        - Related event types

        Args:
            event1, event2: Events to compare
            article_annotation: Article context

        Returns:
            True if events likely describe same incident
        """
        # CRITICAL: Never merge reciprocal violence events with anything
        # Reciprocal violence (e.g., "Hema vs Lendu") are intentionally separate events
        # and should not be merged with other events at all
        if event1.get('reciprocal_violence') or event2.get('reciprocal_violence'):
            return False

        score = 0

        # Signal 1: Same actor (strong signal)
        who1 = event1.get('who')
        who2 = event2.get('who')
        if who1 and who2:
            actor1_text = who1.get('text', '').lower()
            actor2_text = who2.get('text', '').lower()
            if actor1_text and actor2_text and actor1_text == actor2_text:
                score += 3  # Strong signal
            elif actor1_text and actor2_text:
                # Check if one contains the other (e.g., "Al-Shabaab" vs "group")
                if actor1_text in actor2_text or actor2_text in actor1_text:
                    score += 2

        # Signal 2: Same location (strong signal)
        where1 = event1.get('where')
        where2 = event2.get('where')
        if where1 and where2:
            loc1_text = where1.get('text', '').lower()
            loc2_text = where2.get('text', '').lower()
            if loc1_text and loc2_text and loc1_text == loc2_text:
                score += 3  # Strong signal

        # Signal 3: Same casualties (very strong signal)
        whom1 = event1.get('whom')
        whom2 = event2.get('whom')
        if whom1 and whom2:
            deaths1 = whom1.get('deaths')
            deaths2 = whom2.get('deaths')
            injuries1 = whom1.get('injuries')
            injuries2 = whom2.get('injuries')

            # If both have same death count (and it's not None), very likely same event
            if deaths1 and deaths2 and deaths1 == deaths2:
                score += 5  # Very strong signal

            # Same injury count
            if injuries1 and injuries2 and injuries1 == injuries2:
                score += 3

        # Signal 4: Temporal proximity (within 3 sentences)
        sent_diff = abs(event1.get('sentence_index', 0) - event2.get('sentence_index', 0))
        if sent_diff <= 3:
            score += 1
        elif sent_diff <= 5:
            score += 0.5

        # Signal 5: Related event types (medium signal)
        trigger1 = event1.get('trigger', {}).get('lemma', '')
        trigger2 = event2.get('trigger', {}).get('lemma', '')

        # Strongly related triggers (describing different aspects of same event)
        related_pairs = [
            ('detonate', 'explosion'), ('detonate', 'bomb'), ('bomb', 'explosion'),
            ('kill', 'death'), ('shoot', 'kill'), ('fire', 'kill'),
            ('attack', 'kill'), ('storm', 'attack'), ('injure', 'kill')
        ]

        for t1, t2 in related_pairs:
            if (trigger1 == t1 and trigger2 == t2) or (trigger1 == t2 and trigger2 == t1):
                score += 2
                break

        # Same trigger type
        if trigger1 == trigger2:
            score += 1

        # Decision threshold
        # AGGRESSIVE: Lower threshold to merge more events
        # If score >= 4, likely same incident (was 5)
        # If score >= 7, very likely same incident
        return score >= 4

    def _merge_event_cluster(self, cluster: List[Dict]) -> Dict:
        """
        Merge a cluster of events into a single comprehensive event.

        Takes the best information from each event in cluster.

        Args:
            cluster: List of events describing same incident

        Returns:
            Single merged event
        """
        if len(cluster) == 1:
            return cluster[0]

        # Start with the event that has highest completeness
        events_by_completeness = sorted(cluster, key=lambda e: e.get('confidence', 0), reverse=True)
        merged = events_by_completeness[0].copy()

        # Merge information from other events
        for event in cluster[1:]:
            # For each component, take the better/more complete one
            for component in ['who', 'whom', 'where', 'when', 'how']:
                current = merged.get(component)
                new = event.get(component)

                # If we don't have this component, take it from new event
                if not current and new:
                    merged[component] = new

                # If both have it, merge dictionaries
                elif current and new and isinstance(current, dict) and isinstance(new, dict):
                    # Prefer non-null, more specific values
                    for key, value in new.items():
                        if value and not current.get(key):
                            current[key] = value
                        # Special case: prefer named victims over generic ones
                        elif key == 'text' and value and new.get('named_victim'):
                            current[key] = value
                            current['named_victim'] = True
                        # Special case: casualties - take if higher/more complete
                        elif key in ['deaths', 'injuries'] and value:
                            if not current.get(key) or value > current.get(key):
                                current[key] = value

            # Combine weapons
            how_merged = merged.get('how')
            how_new = event.get('how')
            if how_merged and how_new and isinstance(how_merged, dict) and isinstance(how_new, dict):
                # Combine weapon lists
                weapons_merged = set(how_merged.get('weapons', []))
                weapons_new = set(how_new.get('weapons', []))
                combined_weapons = list(weapons_merged.union(weapons_new))
                if combined_weapons:
                    how_merged['weapons'] = combined_weapons
                    how_merged['text'] = ', '.join(combined_weapons)

        # Use the most specific/informative trigger
        # Prefer action verbs over nouns
        best_trigger = merged.get('trigger')
        for event in cluster:
            trigger = event.get('trigger', {})
            if trigger.get('type') == 'verb' and best_trigger.get('type') == 'noun':
                merged['trigger'] = trigger
                merged['what'] = event.get('what')

        # Recalculate confidence for merged event
        merged['confidence'] = self._calculate_confidence(merged)

        # Add metadata about cluster size
        merged['cluster_size'] = len(cluster)
        merged['sentence_indices'] = sorted(set(e.get('sentence_index', 0) for e in cluster))

        return merged


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
    from domain.violence_lexicon import ViolenceLexicon
    from domain.african_ner import AfricanNER
    
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
