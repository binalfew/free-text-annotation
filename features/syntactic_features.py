from typing import List, Dict
from collections import Counter

class SyntacticFeatureExtractor:
    """
    Extract syntactic features from parsed sentences.
    """
    
    def __init__(self):
        """Initialize extractor."""
        self.violence_verbs = ['kill', 'attack', 'bomb', 'shoot', 'murder']
    
    def extract_features(self, tokens: List[Dict], dependencies: List[Dict]) -> Dict:
        """
        Extract syntactic features.
        
        Args:
            tokens: Token annotations with POS tags
            dependencies: Dependency relations
            
        Returns:
            Feature dictionary
        """
        features = {}
        
        # POS tag distribution
        pos_tags = [t.get('pos', '') for t in tokens]
        pos_counter = Counter(pos_tags)
        
        features['num_verbs'] = pos_counter.get('VB', 0) + pos_counter.get('VBD', 0) + pos_counter.get('VBZ', 0)
        features['num_nouns'] = pos_counter.get('NN', 0) + pos_counter.get('NNS', 0) + pos_counter.get('NNP', 0)
        features['num_adj'] = pos_counter.get('JJ', 0) + pos_counter.get('JJR', 0)
        
        # Verb patterns
        lemmas = [t.get('lemma', '').lower() for t in tokens]
        features['has_violence_verb'] = any(v in lemmas for v in self.violence_verbs)
        
        # Dependency patterns
        if dependencies:
            dep_types = [d.get('dep', '') for d in dependencies]
            dep_counter = Counter(dep_types)
            
            # Subject-verb-object patterns
            features['has_nsubj'] = 'nsubj' in dep_types  # Subject
            features['has_dobj'] = 'dobj' in dep_types    # Direct object
            features['has_iobj'] = 'iobj' in dep_types    # Indirect object
            
            # Check for agent-patient patterns (who did what to whom)
            features['has_agent_patient'] = self._has_agent_patient_pattern(dependencies)
        
        return features
    
    def _has_agent_patient_pattern(self, dependencies: List[Dict]) -> bool:
        """
        Check if sentence has agent-patient pattern.
        (e.g., "Militants [agent] killed [action] civilians [patient]")
        """
        # Look for nsubj (agent) and dobj (patient) connected to same verb
        verb_subjects = {}
        verb_objects = {}
        
        for dep in dependencies:
            dep_type = dep.get('dep', '')
            governor = dep.get('governor', 0)
            
            if dep_type == 'nsubj':
                verb_subjects[governor] = dep.get('dependent', 0)
            elif dep_type == 'dobj':
                verb_objects[governor] = dep.get('dependent', 0)
        
        # Check if any verb has both subject and object
        for verb_idx in verb_subjects:
            if verb_idx in verb_objects:
                return True
        
        return False
    
    def extract_dependency_path(self, dependencies: List[Dict], 
                                source_idx: int, target_idx: int) -> List[str]:
        """
        Extract dependency path between two tokens.
        
        Args:
            dependencies: Dependency relations
            source_idx: Source token index
            target_idx: Target token index
            
        Returns:
            List of dependency types in path
        """
        # Build adjacency graph
        graph = {}
        for dep in dependencies:
            gov = dep.get('governor', 0)
            dep_idx = dep.get('dependent', 0)
            dep_type = dep.get('dep', '')
            
            if gov not in graph:
                graph[gov] = []
            graph[gov].append((dep_idx, dep_type))
            
            # Add reverse edge
            if dep_idx not in graph:
                graph[dep_idx] = []
            graph[dep_idx].append((gov, f"{dep_type}_inv"))
        
        # BFS to find path
        from collections import deque
        
        queue = deque([(source_idx, [])])
        visited = {source_idx}
        
        while queue:
            current, path = queue.popleft()
            
            if current == target_idx:
                return path
            
            if current in graph:
                for neighbor, edge_type in graph[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [edge_type]))
        
        return []  # No path found
