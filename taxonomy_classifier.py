"""
Hierarchical Taxonomy Classification
====================================

Classifies violent events into a 3-level taxonomy hierarchy.

Level 1: High-level category
Level 2: Mid-level category
Level 3: Specific event type

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

from typing import Dict, Optional, Tuple
import re


class TaxonomyClassifier:
    """
    Classify violent events into hierarchical taxonomy.
    """

    def __init__(self):
        """Initialize taxonomy classifier."""
        # Define taxonomy hierarchy
        self.taxonomy = {
            'Political Violence': {
                'Terrorism': [
                    'Suicide Bombing',
                    'Car Bombing',
                    'Armed Assault',
                    'Kidnapping',
                    'Assassination'
                ],
                'Election Violence': [
                    'Protest Violence',
                    'Poll Violence',
                    'Campaign Violence'
                ],
                'Insurgency': [
                    'Armed Clash',
                    'Ambush',
                    'Raid'
                ]
            },
            'State Violence Against Civilians': {
                'Extrajudicial Killings': [
                    'Police Shooting',
                    'Military Execution',
                    'Targeted Killing'
                ],
                'State Repression of Protests': [
                    'Police Violence',
                    'Crackdown',
                    'Dispersal Violence'
                ],
                'Forced Displacement': [
                    'Forced Eviction',
                    'Population Transfer'
                ]
            },
            'Communal Violence': {
                'Ethnic/Tribal Conflict': [
                    'Armed Clash',
                    'Massacre',
                    'Raid'
                ],
                'Religious Violence': [
                    'Sectarian Attack',
                    'Religious Riot'
                ],
                'Resource Conflict': [
                    'Land Dispute Violence',
                    'Water Conflict Violence'
                ]
            },
            'Criminal Violence': {
                'Armed Robbery/Banditry': [
                    'Bank Robbery',
                    'Highway Robbery',
                    'Home Invasion'
                ],
                'Kidnapping for Ransom': [
                    'Abduction',
                    'Hostage Taking'
                ],
                'Gang Violence': [
                    'Gang Shooting',
                    'Turf War'
                ]
            }
        }

    def classify(self, event: Dict) -> Tuple[str, str, str]:
        """
        Classify event into 3-level taxonomy.

        Args:
            event: Event dictionary with who, what, whom, etc.

        Returns:
            Tuple of (Level1, Level2, Level3)
        """
        # Extract relevant features
        trigger_lemma = event.get('trigger', {}).get('lemma', '')
        actor = event.get('who', {}) if event.get('who') else {}
        actor_type = actor.get('type', 'unknown') if actor else 'unknown'
        actor_text = actor.get('text', '').lower() if actor else ''
        victim = event.get('whom', {}) if event.get('whom') else {}
        victim_type = victim.get('type', 'unknown') if victim else 'unknown'
        victim_text = victim.get('text', '').lower() if victim else ''
        how = event.get('how', {}) if event.get('how') else {}
        weapons = how.get('weapons', []) if how else []
        tactics = how.get('tactics', []) if how else []
        sentence_text = event.get('sentence_text', '').lower()

        # Level 1: Determine high-level category
        level1 = self._classify_level1(actor_type, actor_text, victim_type, trigger_lemma)

        # Level 2: Determine mid-level category
        level2 = self._classify_level2(level1, actor_type, actor_text, weapons, tactics, trigger_lemma, sentence_text, victim_text)

        # Level 3: Determine specific type
        level3 = self._classify_level3(level1, level2, weapons, tactics, trigger_lemma, actor_text, sentence_text)

        return level1, level2, level3

    def _classify_level1(self, actor_type: str, actor_text: str, victim_type: str, trigger: str) -> str:
        """Classify Level 1 (high-level category)."""

        # State Violence Against Civilians
        state_indicators = ['state', 'police', 'military', 'soldier', 'officer', 'security force']
        if any(ind in actor_text for ind in state_indicators):
            if victim_type == 'civilian':
                return 'State Violence Against Civilians'

        # Criminal Violence
        criminal_indicators = ['gang', 'robber', 'bandit', 'criminal']
        if actor_type == 'criminal' or any(ind in actor_text for ind in criminal_indicators):
            return 'Criminal Violence'

        # Political Violence (includes terrorism)
        political_indicators = ['terrorist', 'rebel', 'insurgent', 'militant']
        terrorism_indicators = ['shabaab', 'boko', 'haram', 'al-qaeda', 'isis', 'aqim']
        if actor_type in ['terrorist', 'rebel'] or any(ind in actor_text for ind in terrorism_indicators):
            return 'Political Violence'

        # Communal Violence
        communal_indicators = ['community', 'ethnic', 'tribal', 'clan']
        if actor_type == 'communal' or any(ind in actor_text for ind in communal_indicators):
            return 'Communal Violence'

        # Election violence indicators
        election_indicators = ['protest', 'election', 'opposition', 'demonstrator']
        if any(ind in actor_text for ind in election_indicators):
            return 'Political Violence'

        # Default to Political Violence for unknown armed actors
        return 'Political Violence'

    def _classify_level2(self, level1: str, actor_type: str, actor_text: str,
                        weapons: list, tactics: list, trigger: str,
                        sentence_text: str = '', victim_text: str = '') -> str:
        """Classify Level 2 (mid-level category)."""

        if level1 == 'Political Violence':
            # Check for terrorism indicators
            terrorism_indicators = ['shabaab', 'boko', 'haram', 'al-qaeda', 'isis', 'suicide']
            if actor_type == 'terrorist' or any(ind in actor_text for ind in terrorism_indicators):
                return 'Terrorism'
            if 'suicide' in tactics:
                return 'Terrorism'

            # Check for election violence (also check sentence context)
            election_indicators = ['election', 'protest', 'opposition', 'demonstrator', 'voting', 'poll']
            if any(ind in actor_text or ind in sentence_text for ind in election_indicators):
                return 'Election Violence'

            # Default to Insurgency
            return 'Insurgency'

        elif level1 == 'State Violence Against Civilians':
            # Check for repression of protests (check victim text and sentence)
            protest_indicators = ['protest', 'demonstrator', 'rally', 'opposition supporter']
            if any(ind in victim_text or ind in sentence_text for ind in protest_indicators):
                return 'State Repression of Protests'

            # Default to Extrajudicial Killings
            return 'Extrajudicial Killings'

        elif level1 == 'Communal Violence':
            # Check for election-related communal violence first
            election_indicators = ['election', 'voting', 'opposition', 'poll']
            if any(ind in sentence_text for ind in election_indicators):
                # If it's election-related communal violence, reclassify as Political Violence > Election Violence
                # This is handled at Level 1 classification, so we keep it as communal here
                pass

            # Check for ethnic conflict
            ethnic_indicators = ['community', 'ethnic', 'tribal', 'hema', 'lendu', 'hutu', 'tutsi']
            if any(ind in actor_text for ind in ethnic_indicators):
                return 'Ethnic/Tribal Conflict'

            # Check for religious violence
            religious_indicators = ['muslim', 'christian', 'sectarian', 'religious']
            if any(ind in actor_text for ind in religious_indicators):
                return 'Religious Violence'

            # Check for resource conflict
            resource_indicators = ['land', 'water', 'grazing', 'cattle']
            if any(ind in actor_text for ind in resource_indicators):
                return 'Resource Conflict'

            return 'Ethnic/Tribal Conflict'

        elif level1 == 'Criminal Violence':
            # Check for armed robbery (check sentence context too)
            robbery_indicators = ['rob', 'robbery', 'bank', 'stole', 'loot', 'robbed']
            if any(ind in trigger or ind in actor_text or ind in sentence_text for ind in robbery_indicators):
                return 'Armed Robbery/Banditry'

            # Check for kidnapping
            kidnap_indicators = ['kidnap', 'abduct', 'hostage']
            if any(ind in trigger or ind in sentence_text for ind in kidnap_indicators):
                return 'Kidnapping for Ransom'

            # Default to gang violence
            return 'Gang Violence'

        return 'Unknown'

    def _classify_level3(self, level1: str, level2: str, weapons: list, tactics: list,
                         trigger: str, actor_text: str, sentence_text: str = '') -> str:
        """Classify Level 3 (specific type)."""

        # For Terrorism
        if level2 == 'Terrorism':
            if 'suicide' in tactics:
                if 'car' in weapons or 'vehicle' in weapons:
                    return 'Car Bombing'
                return 'Suicide Bombing'
            if 'bomb' in trigger or 'explosive' in str(weapons):
                return 'Armed Assault'
            if 'kidnap' in trigger or 'abduct' in trigger:
                return 'Kidnapping'
            if 'assassin' in trigger:
                return 'Assassination'
            return 'Armed Assault'

        # For Election Violence
        elif level2 == 'Election Violence':
            if 'protest' in actor_text or 'demonstr' in actor_text or 'protest' in sentence_text:
                return 'Protest Violence'
            if 'poll' in actor_text or 'voting' in actor_text or 'poll' in sentence_text:
                return 'Poll Violence'
            return 'Campaign Violence'

        # For Extrajudicial Killings
        elif level2 == 'Extrajudicial Killings':
            if 'police' in actor_text:
                return 'Police Shooting'
            if 'military' in actor_text or 'soldier' in actor_text:
                return 'Military Execution'
            return 'Targeted Killing'

        # For State Repression
        elif level2 == 'State Repression of Protests':
            if 'dispersal' in actor_text or 'disperse' in trigger:
                return 'Dispersal Violence'
            if 'crackdown' in actor_text:
                return 'Crackdown'
            return 'Police Violence'

        # For Ethnic/Tribal Conflict
        elif level2 == 'Ethnic/Tribal Conflict':
            if 'massacre' in trigger:
                return 'Massacre'
            if 'raid' in trigger or 'attack' in trigger:
                return 'Raid'
            return 'Armed Clash'

        # For Armed Robbery
        elif level2 == 'Armed Robbery/Banditry':
            if 'bank' in actor_text or 'bank' in trigger or 'bank' in sentence_text:
                return 'Bank Robbery'
            if 'highway' in actor_text or 'road' in actor_text or 'highway' in sentence_text:
                return 'Highway Robbery'
            return 'Armed Robbery/Banditry'

        # For Kidnapping
        elif level2 == 'Kidnapping for Ransom':
            if 'hostage' in trigger or 'hostage' in actor_text:
                return 'Hostage Taking'
            return 'Abduction'

        # Default: use level2 as level3
        return level2


# Example usage
if __name__ == '__main__':
    classifier = TaxonomyClassifier()

    # Test case 1: Al-Shabaab suicide bombing
    event1 = {
        'trigger': {'lemma': 'attack'},
        'who': {'text': 'Al-Shabaab', 'type': 'TERRORIST'},
        'whom': {'text': 'civilians', 'type': 'civilian'},
        'how': {'weapons': ['explosive', 'suicide bomb'], 'tactics': ['suicide']}
    }
    l1, l2, l3 = classifier.classify(event1)
    print(f"Event 1: {l1} > {l2} > {l3}")

    # Test case 2: Police shooting civilians
    event2 = {
        'trigger': {'lemma': 'shooting'},
        'who': {'text': 'police officers', 'type': 'state'},
        'whom': {'text': 'protesters', 'type': 'civilian'},
        'how': {'weapons': ['firearms'], 'tactics': []}
    }
    l1, l2, l3 = classifier.classify(event2)
    print(f"Event 2: {l1} > {l2} > {l3}")

    # Test case 3: Ethnic clash
    event3 = {
        'trigger': {'lemma': 'clashes'},
        'who': {'text': 'Hema community', 'type': 'communal'},
        'whom': {'text': 'Lendu community', 'type': 'civilian'},
        'how': {'weapons': ['machetes'], 'tactics': []}
    }
    l1, l2, l3 = classifier.classify(event3)
    print(f"Event 3: {l1} > {l2} > {l3}")
