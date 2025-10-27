from typing import Set, Dict, List

class ViolenceLexicon:
    """
    Comprehensive lexicon of violence-related terms.
    """
    
    def __init__(self):
        """Initialize violence lexicon."""
        self.verbs = self._load_violence_verbs()
        self.nouns = self._load_violence_nouns()
        self.actors = self._load_actor_terms()
        self.weapons = self._load_weapon_terms()
        self.all_terms = self.verbs | self.nouns | self.actors | self.weapons
    
    def _load_violence_verbs(self) -> Set[str]:
        """Violence action verbs."""
        return {
            # Killing
            'kill', 'kills', 'killed', 'killing', 'slay', 'slain',
            'murder', 'murdered', 'murdering', 'execute', 'executed',
            'assassinate', 'assassinated', 'massacre', 'massacred',
            
            # Attacking
            'attack', 'attacks', 'attacked', 'attacking',
            'assault', 'assaulted', 'assaulting',
            'raid', 'raided', 'raiding',
            'ambush', 'ambushed', 'ambushing',
            'storm', 'stormed', 'storming',
            
            # Shooting
            'shoot', 'shot', 'shooting', 'shoots',
            'fire', 'fired', 'firing', 'gunned',
            
            # Bombing
            'bomb', 'bombed', 'bombing', 'bombs',
            'explode', 'exploded', 'exploding',
            'detonate', 'detonated', 'detonating',
            'blast', 'blasted', 'blasting',
            
            # Abducting
            'kidnap', 'kidnapped', 'kidnapping',
            'abduct', 'abducted', 'abducting',
            'seize', 'seized', 'seizing',
            'capture', 'captured', 'capturing',
            
            # Fighting
            'fight', 'fought', 'fighting',
            'clash', 'clashed', 'clashing',
            'battle', 'battled', 'battling',
            
            # Injuring
            'wound', 'wounded', 'wounding',
            'injure', 'injured', 'injuring',
            'hurt', 'harm', 'harmed',
            
            # Destroying
            'destroy', 'destroyed', 'destroying',
            'burn', 'burned', 'burnt', 'burning',
            'raze', 'razed', 'razing',
        }
    
    def _load_violence_nouns(self) -> Set[str]:
        """Violence event nouns."""
        return {
            # Events
            'attack', 'attacks', 'assault', 'assaults',
            'raid', 'raids', 'ambush', 'ambushes',
            'bombing', 'bombings', 'explosion', 'explosions',
            'shooting', 'shootings', 'massacre', 'massacres',
            'killing', 'killings', 'murder', 'murders',
            'assassination', 'kidnapping', 'abduction',
            'clash', 'clashes', 'battle', 'battles',
            'violence', 'bloodshed', 'carnage',
            
            # Outcomes
            'death', 'deaths', 'casualty', 'casualties',
            'victim', 'victims', 'fatality', 'fatalities',
            'injury', 'injuries', 'wounded',
            
            # Weapons (as nouns)
            'gun', 'guns', 'rifle', 'rifles',
            'bomb', 'bombs', 'explosive', 'explosives',
            'grenade', 'grenades', 'rocket', 'rockets',
            'weapon', 'weapons', 'ammunition',
        }
    
    def _load_actor_terms(self) -> Set[str]:
        """Terms for violence actors."""
        return {
            'militant', 'militants', 'militia', 'militias',
            'rebel', 'rebels', 'insurgent', 'insurgents',
            'terrorist', 'terrorists', 'extremist', 'extremists',
            'gunman', 'gunmen', 'fighter', 'fighters',
            'attacker', 'attackers', 'assailant', 'assailants',
            'perpetrator', 'perpetrators',
            'soldier', 'soldiers', 'troop', 'troops',
            'force', 'forces', 'military', 'army',
            'police', 'officer', 'officers',
        }
    
    def _load_weapon_terms(self) -> Set[str]:
        """Weapon-related terms."""
        return {
            # Firearms
            'gun', 'guns', 'rifle', 'rifles', 'pistol', 'pistols',
            'firearm', 'firearms', 'ak-47', 'kalashnikov',
            'automatic', 'semi-automatic',
            
            # Explosives
            'bomb', 'bombs', 'ied', 'explosive', 'explosives',
            'grenade', 'grenades', 'dynamite', 'tnt',
            'suicide-bomber', 'car-bomb', 'vbied',
            
            # Heavy weapons
            'rocket', 'rockets', 'missile', 'missiles',
            'mortar', 'mortars', 'artillery',
            'rpg', 'launcher',
            
            # Other
            'weapon', 'weapons', 'ammunition', 'bullet', 'bullets',
            'machete', 'knife', 'knives', 'blade',
        }
    
    def is_violence_term(self, word: str) -> bool:
        """Check if word is violence-related."""
        return word.lower() in self.all_terms
    
    def get_term_category(self, word: str) -> str:
        """Get category of violence term."""
        word_lower = word.lower()
        
        if word_lower in self.verbs:
            return 'violence_verb'
        elif word_lower in self.nouns:
            return 'violence_noun'
        elif word_lower in self.actors:
            return 'actor'
        elif word_lower in self.weapons:
            return 'weapon'
        else:
            return 'other'
    
    def save_to_file(self, filepath: str):
        """Save lexicon to text file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Violence Verbs\n")
            for term in sorted(self.verbs):
                f.write(f"{term}\n")
            
            f.write("\n# Violence Nouns\n")
            for term in sorted(self.nouns):
                f.write(f"{term}\n")
            
            f.write("\n# Actor Terms\n")
            for term in sorted(self.actors):
                f.write(f"{term}\n")
            
            f.write("\n# Weapon Terms\n")
            for term in sorted(self.weapons):
                f.write(f"{term}\n")
