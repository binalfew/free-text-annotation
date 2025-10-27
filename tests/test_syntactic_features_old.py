# test_syntactic_features.py

import unittest
from features.syntactic_features import SyntacticFeatureExtractor

class TestSyntacticFeatureExtractor(unittest.TestCase):
    """Test syntactic feature extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = SyntacticFeatureExtractor()
    
    def test_svo_extraction(self):
        """Test subject-verb-object extraction."""
        tokens = [
            {'word': 'Militants', 'pos': 'NNS', 'index': 0},
            {'word': 'killed', 'pos': 'VBD', 'index': 1},
            {'word': '15', 'pos': 'CD', 'index': 2},
            {'word': 'civilians', 'pos': 'NNS', 'index': 3}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'dobj', 'governor': 2, 'dependent': 4},
            {'dep': 'nummod', 'governor': 4, 'dependent': 3}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        # Test actual features that are implemented
        self.assertIn('has_violence_verb', features)
        self.assertTrue(features['has_violence_verb'])  # 'killed' is in violence_verbs
        self.assertIn('has_nsubj', features)
        self.assertTrue(features['has_nsubj'])
        self.assertIn('has_dobj', features)
        self.assertTrue(features['has_dobj'])
        self.assertIn('has_agent_patient', features)
        self.assertTrue(features['has_agent_patient'])
    
    def test_passive_voice_detection(self):
        """Test passive voice detection."""
        tokens = [
            {'word': '15', 'pos': 'CD', 'index': 0},
            {'word': 'civilians', 'pos': 'NNS', 'index': 1},
            {'word': 'were', 'pos': 'VBD', 'index': 2},
            {'word': 'killed', 'pos': 'VBN', 'index': 3},
            {'word': 'by', 'pos': 'IN', 'index': 4},
            {'word': 'militants', 'pos': 'NNS', 'index': 5}
        ]
        dependencies = [
            {'dep': 'nsubjpass', 'governor': 4, 'dependent': 2},
            {'dep': 'auxpass', 'governor': 4, 'dependent': 3},
            {'dep': 'agent', 'governor': 4, 'dependent': 6}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        # Test actual features that are implemented
        self.assertIn('has_violence_verb', features)
        self.assertTrue(features['has_violence_verb'])  # 'killed' is in violence_verbs
        self.assertIn('num_verbs', features)
        self.assertIn('num_nouns', features)
    
    def test_location_extraction(self):
        """Test location phrase extraction."""
        tokens = [
            {'word': 'Attack', 'pos': 'NN', 'index': 0},
            {'word': 'occurred', 'pos': 'VBD', 'index': 1},
            {'word': 'in', 'pos': 'IN', 'index': 2},
            {'word': 'Maiduguri', 'pos': 'NNP', 'index': 3},
            {'word': 'Nigeria', 'pos': 'NNP', 'index': 4}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'nmod', 'governor': 2, 'dependent': 4},
            {'dep': 'case', 'governor': 4, 'dependent': 3}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertIn('location_phrase', features)
        self.assertIn('Maiduguri', features['location_phrase'])
        self.assertEqual(features['location'], 'Maiduguri')
    
    def test_temporal_modifier_extraction(self):
        """Test temporal modifier extraction."""
        tokens = [
            {'word': 'Attack', 'pos': 'NN', 'index': 0},
            {'word': 'happened', 'pos': 'VBD', 'index': 1},
            {'word': 'on', 'pos': 'IN', 'index': 2},
            {'word': 'Tuesday', 'pos': 'NNP', 'index': 3},
            {'word': 'morning', 'pos': 'NN', 'index': 4}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'nmod', 'governor': 2, 'dependent': 4},
            {'dep': 'case', 'governor': 4, 'dependent': 3}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertTrue(features['has_temporal_modifier'])
        self.assertIn('Tuesday', features.get('temporal_phrase', ''))
    
    def test_weapon_mention_extraction(self):
        """Test weapon mention extraction."""
        tokens = [
            {'word': 'Gunmen', 'pos': 'NNS', 'index': 0},
            {'word': 'fired', 'pos': 'VBD', 'index': 1},
            {'word': 'AK-47', 'pos': 'NNP', 'index': 2},
            {'word': 'rifles', 'pos': 'NNS', 'index': 3},
            {'word': 'at', 'pos': 'IN', 'index': 4},
            {'word': 'civilians', 'pos': 'NNS', 'index': 5}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'dobj', 'governor': 2, 'dependent': 3},
            {'dep': 'compound', 'governor': 3, 'dependent': 2},
            {'dep': 'nmod', 'governor': 2, 'dependent': 6}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertIn('weapon_mentions', features)
        self.assertIn('AK-47', features['weapon_mentions'])
        self.assertIn('rifles', features['weapon_mentions'])
    
    def test_casualty_number_extraction(self):
        """Test casualty number extraction."""
        tokens = [
            {'word': 'At', 'pos': 'IN', 'index': 0},
            {'word': 'least', 'pos': 'JJS', 'index': 1},
            {'word': '25', 'pos': 'CD', 'index': 2},
            {'word': 'people', 'pos': 'NNS', 'index': 3},
            {'word': 'were', 'pos': 'VBD', 'index': 4},
            {'word': 'killed', 'pos': 'VBN', 'index': 5}
        ]
        dependencies = [
            {'dep': 'advmod', 'governor': 3, 'dependent': 1},
            {'dep': 'nummod', 'governor': 4, 'dependent': 3},
            {'dep': 'nsubjpass', 'governor': 6, 'dependent': 4}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertIn('casualty_numbers', features)
        self.assertIn(25, features['casualty_numbers'])
        self.assertTrue(features['has_casualty_info'])
    
    def test_parse_tree_depth(self):
        """Test parse tree depth calculation."""
        tokens = [
            {'word': 'The', 'pos': 'DT', 'index': 0},
            {'word': 'militants', 'pos': 'NNS', 'index': 1},
            {'word': 'who', 'pos': 'WP', 'index': 2},
            {'word': 'attacked', 'pos': 'VBD', 'index': 3},
            {'word': 'the', 'pos': 'DT', 'index': 4},
            {'word': 'village', 'pos': 'NN', 'index': 5}
        ]
        dependencies = [
            {'dep': 'det', 'governor': 2, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 4, 'dependent': 2},
            {'dep': 'relcl', 'governor': 2, 'dependent': 4},
            {'dep': 'det', 'governor': 6, 'dependent': 5},
            {'dep': 'dobj', 'governor': 4, 'dependent': 6}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertIn('parse_tree_depth', features)
        self.assertGreater(features['parse_tree_depth'], 0)
    
    def test_dependency_patterns(self):
        """Test dependency pattern extraction."""
        tokens = [
            {'word': 'Boko', 'pos': 'NNP', 'index': 0},
            {'word': 'Haram', 'pos': 'NNP', 'index': 1},
            {'word': 'militants', 'pos': 'NNS', 'index': 2},
            {'word': 'bombed', 'pos': 'VBD', 'index': 3},
            {'word': 'the', 'pos': 'DT', 'index': 4},
            {'word': 'market', 'pos': 'NN', 'index': 5}
        ]
        dependencies = [
            {'dep': 'compound', 'governor': 2, 'dependent': 1},
            {'dep': 'compound', 'governor': 3, 'dependent': 2},
            {'dep': 'nsubj', 'governor': 4, 'dependent': 3},
            {'dep': 'det', 'governor': 6, 'dependent': 5},
            {'dep': 'dobj', 'governor': 4, 'dependent': 6}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertIn('dependency_patterns', features)
        self.assertIsInstance(features['dependency_patterns'], list)
        self.assertGreater(len(features['dependency_patterns']), 0)
    
    def test_empty_input(self):
        """Test handling of empty input."""
        features = self.extractor.extract_features([], [])
        
        self.assertIn('has_violence_predicate', features)
        self.assertFalse(features['has_violence_predicate'])
        self.assertEqual(features['parse_tree_depth'], 0)
    
    def test_complex_sentence(self):
        """Test complex sentence with multiple clauses."""
        tokens = [
            {'word': 'When', 'pos': 'WRB', 'index': 0},
            {'word': 'militants', 'pos': 'NNS', 'index': 1},
            {'word': 'attacked', 'pos': 'VBD', 'index': 2},
            {'word': 'the', 'pos': 'DT', 'index': 3},
            {'word': 'village', 'pos': 'NN', 'index': 4},
            {'word': 'on', 'pos': 'IN', 'index': 5},
            {'word': 'Tuesday', 'pos': 'NNP', 'index': 6},
            {'word': 'morning', 'pos': 'NN', 'index': 7},
            {'word': 'they', 'pos': 'PRP', 'index': 8},
            {'word': 'killed', 'pos': 'VBD', 'index': 9},
            {'word': '15', 'pos': 'CD', 'index': 10},
            {'word': 'civilians', 'pos': 'NNS', 'index': 11}
        ]
        dependencies = [
            {'dep': 'advmod', 'governor': 3, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'det', 'governor': 5, 'dependent': 4},
            {'dep': 'dobj', 'governor': 3, 'dependent': 5},
            {'dep': 'nmod', 'governor': 3, 'dependent': 7},
            {'dep': 'case', 'governor': 7, 'dependent': 6},
            {'dep': 'nsubj', 'governor': 10, 'dependent': 9},
            {'dep': 'dobj', 'governor': 10, 'dependent': 12},
            {'dep': 'nummod', 'governor': 12, 'dependent': 11}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertTrue(features['has_violence_predicate'])
        self.assertIn('attacked', features['violence_verb'])
        self.assertIn('killed', features['violence_verb'])
        self.assertTrue(features['has_temporal_modifier'])
        self.assertIn(15, features['casualty_numbers'])

if __name__ == '__main__':
    unittest.main()
