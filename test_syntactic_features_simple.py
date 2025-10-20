# test_syntactic_features_simple.py

import unittest
from features.syntactic_features import SyntacticFeatureExtractor

class TestSyntacticFeatureExtractor(unittest.TestCase):
    """Test syntactic feature extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = SyntacticFeatureExtractor()
    
    def test_basic_feature_extraction(self):
        """Test basic feature extraction."""
        tokens = [
            {'word': 'Militants', 'pos': 'NNS', 'index': 0},
            {'word': 'killed', 'pos': 'VBD', 'index': 1},
            {'word': 'civilians', 'pos': 'NNS', 'index': 2}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'dobj', 'governor': 2, 'dependent': 3}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        # Test basic features
        self.assertIn('num_verbs', features)
        self.assertIn('num_nouns', features)
        self.assertIn('num_adj', features)
        self.assertIn('has_violence_verb', features)
        self.assertIn('has_nsubj', features)
        self.assertIn('has_dobj', features)
        self.assertIn('has_agent_patient', features)
        
        # Test values
        self.assertEqual(features['num_verbs'], 1)
        self.assertEqual(features['num_nouns'], 2)
        self.assertTrue(features['has_violence_verb'])
        self.assertTrue(features['has_nsubj'])
        self.assertTrue(features['has_dobj'])
        self.assertTrue(features['has_agent_patient'])
    
    def test_violence_verb_detection(self):
        """Test violence verb detection."""
        # Test with violence verb
        tokens = [
            {'word': 'Militants', 'pos': 'NNS', 'index': 0},
            {'word': 'killed', 'pos': 'VBD', 'index': 1},
            {'word': 'civilians', 'pos': 'NNS', 'index': 2}
        ]
        dependencies = []
        
        features = self.extractor.extract_features(tokens, dependencies)
        self.assertTrue(features['has_violence_verb'])
        
        # Test without violence verb
        tokens = [
            {'word': 'People', 'pos': 'NNS', 'index': 0},
            {'word': 'walked', 'pos': 'VBD', 'index': 1},
            {'word': 'home', 'pos': 'NN', 'index': 2}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        self.assertFalse(features['has_violence_verb'])
    
    def test_dependency_patterns(self):
        """Test dependency pattern detection."""
        tokens = [
            {'word': 'Gunmen', 'pos': 'NNS', 'index': 0},
            {'word': 'fired', 'pos': 'VBD', 'index': 1},
            {'word': 'at', 'pos': 'IN', 'index': 2},
            {'word': 'civilians', 'pos': 'NNS', 'index': 3}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'nmod', 'governor': 2, 'dependent': 4}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertTrue(features['has_nsubj'])
        self.assertFalse(features['has_dobj'])
        self.assertFalse(features['has_agent_patient'])
    
    def test_agent_patient_pattern(self):
        """Test agent-patient pattern detection."""
        tokens = [
            {'word': 'Boko', 'pos': 'NNP', 'index': 0},
            {'word': 'Haram', 'pos': 'NNP', 'index': 1},
            {'word': 'attacked', 'pos': 'VBD', 'index': 2},
            {'word': 'village', 'pos': 'NN', 'index': 3}
        ]
        dependencies = [
            {'dep': 'compound', 'governor': 2, 'dependent': 1},
            {'dep': 'compound', 'governor': 3, 'dependent': 2},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'dobj', 'governor': 3, 'dependent': 4}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertTrue(features['has_nsubj'])
        self.assertTrue(features['has_dobj'])
        self.assertTrue(features['has_agent_patient'])
    
    def test_pos_tag_distribution(self):
        """Test POS tag distribution counting."""
        tokens = [
            {'word': 'The', 'pos': 'DT', 'index': 0},
            {'word': 'armed', 'pos': 'JJ', 'index': 1},
            {'word': 'militants', 'pos': 'NNS', 'index': 2},
            {'word': 'attacked', 'pos': 'VBD', 'index': 3},
            {'word': 'the', 'pos': 'DT', 'index': 4},
            {'word': 'village', 'pos': 'NN', 'index': 5}
        ]
        dependencies = []
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        self.assertEqual(features['num_verbs'], 1)  # 'attacked'
        self.assertEqual(features['num_nouns'], 2)  # 'militants', 'village'
        self.assertEqual(features['num_adj'], 1)   # 'armed'
    
    def test_empty_input(self):
        """Test handling of empty input."""
        features = self.extractor.extract_features([], [])
        
        self.assertEqual(features['num_verbs'], 0)
        self.assertEqual(features['num_nouns'], 0)
        self.assertEqual(features['num_adj'], 0)
        self.assertFalse(features['has_violence_verb'])
        self.assertFalse(features['has_nsubj'])
        self.assertFalse(features['has_dobj'])
        self.assertFalse(features['has_agent_patient'])
    
    def test_dependency_path_extraction(self):
        """Test dependency path extraction."""
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'dobj', 'governor': 2, 'dependent': 3},
            {'dep': 'nmod', 'governor': 2, 'dependent': 4}
        ]
        
        # Test path extraction
        path = self.extractor.extract_dependency_path(dependencies, 1, 3)
        # The actual path depends on the graph structure
        self.assertIsInstance(path, list)
    
    def test_complex_sentence(self):
        """Test complex sentence with multiple clauses."""
        tokens = [
            {'word': 'When', 'pos': 'WRB', 'index': 0},
            {'word': 'militants', 'pos': 'NNS', 'index': 1},
            {'word': 'attacked', 'pos': 'VBD', 'index': 2},
            {'word': 'the', 'pos': 'DT', 'index': 3},
            {'word': 'village', 'pos': 'NN', 'index': 4},
            {'word': 'they', 'pos': 'PRP', 'index': 5},
            {'word': 'killed', 'pos': 'VBD', 'index': 6},
            {'word': '15', 'pos': 'CD', 'index': 7},
            {'word': 'civilians', 'pos': 'NNS', 'index': 8}
        ]
        dependencies = [
            {'dep': 'advmod', 'governor': 3, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'det', 'governor': 5, 'dependent': 4},
            {'dep': 'dobj', 'governor': 3, 'dependent': 5},
            {'dep': 'nsubj', 'governor': 7, 'dependent': 6},
            {'dep': 'dobj', 'governor': 7, 'dependent': 9},
            {'dep': 'nummod', 'governor': 9, 'dependent': 8}
        ]
        
        features = self.extractor.extract_features(tokens, dependencies)
        
        # Should detect violence verbs
        self.assertTrue(features['has_violence_verb'])
        
        # Should detect dependency patterns
        self.assertTrue(features['has_nsubj'])
        self.assertTrue(features['has_dobj'])
        self.assertTrue(features['has_agent_patient'])
        
        # Should count POS tags correctly
        self.assertEqual(features['num_verbs'], 2)  # 'attacked', 'killed'
        self.assertEqual(features['num_nouns'], 3)  # 'militants', 'village', 'civilians'

if __name__ == '__main__':
    unittest.main()
