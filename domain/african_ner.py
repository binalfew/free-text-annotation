import json
from typing import Dict, List, Tuple

class AfricanNER:
    """
    Named Entity Recognition enhanced for African contexts.
    """
    
    def __init__(self, location_db_path: str = None, actor_db_path: str = None):
        """
        Initialize African NER.
        
        Args:
            location_db_path: Path to African locations JSON
            actor_db_path: Path to armed groups/actors JSON
        """
        self.locations = self._load_locations(location_db_path)
        self.actors = self._load_actors(actor_db_path)
    
    def _load_locations(self, path: str = None) -> Dict:
        """Load African location database."""
        # Default locations if no file provided
        default_locations = {
            # Countries
            'Nigeria': {'type': 'COUNTRY', 'region': 'West Africa'},
            'Somalia': {'type': 'COUNTRY', 'region': 'East Africa'},
            'Mali': {'type': 'COUNTRY', 'region': 'West Africa'},
            'Kenya': {'type': 'COUNTRY', 'region': 'East Africa'},
            'Ethiopia': {'type': 'COUNTRY', 'region': 'East Africa'},
            'Sudan': {'type': 'COUNTRY', 'region': 'North Africa'},
            'South Sudan': {'type': 'COUNTRY', 'region': 'East Africa'},
            'DRC': {'type': 'COUNTRY', 'region': 'Central Africa', 'full_name': 'Democratic Republic of Congo'},
            'Democratic Republic of Congo': {'type': 'COUNTRY', 'region': 'Central Africa'},
            'CAR': {'type': 'COUNTRY', 'region': 'Central Africa', 'full_name': 'Central African Republic'},
            'Senegal': {'type': 'COUNTRY', 'region': 'West Africa'},
            
            # Major cities
            'Mogadishu': {'type': 'CITY', 'country': 'Somalia'},
            'Nairobi': {'type': 'CITY', 'country': 'Kenya'},
            'Lagos': {'type': 'CITY', 'country': 'Nigeria'},
            'Maiduguri': {'type': 'CITY', 'country': 'Nigeria'},
            'Addis Ababa': {'type': 'CITY', 'country': 'Ethiopia'},
            'Gao': {'type': 'CITY', 'country': 'Mali'},
            'Kidal': {'type': 'CITY', 'country': 'Mali'},
            'Bamako': {'type': 'CITY', 'country': 'Mali'},
            'Beni': {'type': 'CITY', 'country': 'Democratic Republic of Congo'},
            'Dakar': {'type': 'CITY', 'country': 'Senegal'},
            'Kainama': {'type': 'CITY', 'country': 'Democratic Republic of Congo'},
            'Westlands': {'type': 'CITY', 'country': 'Kenya'},
            
            # States/Provinces
            'Borno State': {'type': 'STATE', 'country': 'Nigeria'},
            'Adamawa State': {'type': 'STATE', 'country': 'Nigeria'},
            'Oromia': {'type': 'REGION', 'country': 'Ethiopia'},
            'Tigray': {'type': 'REGION', 'country': 'Ethiopia'},
            'North Kivu': {'type': 'REGION', 'country': 'Democratic Republic of Congo'},
            'Lower Shabelle': {'type': 'REGION', 'country': 'Somalia'},
        }
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_locations
        
        return default_locations
    
    def _load_actors(self, path: str = None) -> Dict:
        """Load armed groups/actors database."""
        default_actors = {
            # Terrorist groups
            'Boko Haram': {'type': 'TERRORIST', 'region': 'West Africa', 'country': 'Nigeria'},
            'Al-Shabaab': {'type': 'TERRORIST', 'region': 'East Africa', 'country': 'Somalia'},
            'AQIM': {'type': 'TERRORIST', 'region': 'North Africa', 'full_name': 'Al-Qaeda in the Islamic Maghreb'},
            'JNIM': {'type': 'TERRORIST', 'region': 'West Africa', 'full_name': 'Jama\'at Nasr al-Islam wal Muslimin'},
            'ISIS-WA': {'type': 'TERRORIST', 'region': 'West Africa', 'full_name': 'Islamic State West Africa Province'},
            
            # Rebel groups
            'M23': {'type': 'REBEL', 'region': 'Central Africa', 'country': 'DRC'},
            'ADF': {'type': 'REBEL', 'region': 'Central Africa', 'full_name': 'Allied Democratic Forces'},
            'LRA': {'type': 'REBEL', 'region': 'Central Africa', 'full_name': 'Lord\'s Resistance Army'},
            'FDLR': {'type': 'REBEL', 'region': 'Central Africa'},
            'OLA': {'type': 'REBEL', 'region': 'East Africa', 'full_name': 'Oromo Liberation Army'},
        }
        
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default_actors
        
        return default_actors
    
    def recognize_location(self, text: str) -> List[Tuple[str, Dict]]:
        """
        Recognize African locations in text.
        
        Returns:
            List of (location_name, metadata) tuples
        """
        found = []
        
        for location, metadata in self.locations.items():
            if location.lower() in text.lower():
                found.append((location, metadata))
        
        return found
    
    def recognize_actor(self, text: str) -> List[Tuple[str, Dict]]:
        """
        Recognize armed groups/actors in text.
        
        Returns:
            List of (actor_name, metadata) tuples
        """
        found = []
        
        for actor, metadata in self.actors.items():
            # Check full name and acronym
            if actor.lower() in text.lower():
                found.append((actor, metadata))
            
            # Check full name if exists
            if 'full_name' in metadata:
                if metadata['full_name'].lower() in text.lower():
                    found.append((actor, metadata))
        
        return found
    
    def enhance_ner(self, entities: List[Dict], text: str) -> List[Dict]:
        """
        Enhance standard NER with African-specific entities.
        
        Args:
            entities: Entities from standard NER
            text: Original text
            
        Returns:
            Enhanced entity list
        """
        enhanced = entities.copy()
        
        # Add African locations
        locations = self.recognize_location(text)
        for loc_name, metadata in locations:
            # Check if not already in entities
            if not any(e['text'].lower() == loc_name.lower() for e in enhanced):
                enhanced.append({
                    'text': loc_name,
                    'type': 'LOCATION',
                    'subtype': metadata.get('type', 'UNKNOWN'),
                    'metadata': metadata
                })
        
        # Add armed groups
        actors = self.recognize_actor(text)
        for actor_name, metadata in actors:
            if not any(e['text'].lower() == actor_name.lower() for e in enhanced):
                enhanced.append({
                    'text': actor_name,
                    'type': 'ORGANIZATION',
                    'subtype': metadata.get('type', 'UNKNOWN'),
                    'metadata': metadata
                })
        
        return enhanced
