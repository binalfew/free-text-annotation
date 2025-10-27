# test_feature_extraction_integration.py

import unittest
from features.lexical_features import LexicalFeatureExtractor
from features.syntactic_features import SyntacticFeatureExtractor
from domain.violence_lexicon import ViolenceLexicon

class TestFeatureExtractionIntegration(unittest.TestCase):
    """Test integration of feature extraction components."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lexicon = ViolenceLexicon()
        self.lexical_extractor = LexicalFeatureExtractor(list(self.lexicon.all_terms))
        self.syntactic_extractor = SyntacticFeatureExtractor()
    
    def test_combined_feature_extraction(self):
        """Test combined lexical and syntactic feature extraction."""
        # Sample sentence annotation
        tokens = [
            {'word': 'Armed', 'pos': 'JJ', 'index': 0},
            {'word': 'militants', 'pos': 'NNS', 'index': 1},
            {'word': 'killed', 'pos': 'VBD', 'index': 2},
            {'word': '15', 'pos': 'CD', 'index': 3},
            {'word': 'civilians', 'pos': 'NNS', 'index': 4},
            {'word': 'in', 'pos': 'IN', 'index': 5},
            {'word': 'Maiduguri', 'pos': 'NNP', 'index': 6}
        ]
        dependencies = [
            {'dep': 'amod', 'governor': 2, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'dobj', 'governor': 3, 'dependent': 5},
            {'dep': 'nummod', 'governor': 5, 'dependent': 4},
            {'dep': 'nmod', 'governor': 3, 'dependent': 7}
        ]
        
        # Extract lexical features
        token_words = [t['word'] for t in tokens]
        lexical_features = self.lexical_extractor.extract_features(token_words)
        
        # Extract syntactic features
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Verify lexical features
        self.assertIn('violence_term_count', lexical_features)
        self.assertGreater(lexical_features['violence_term_count'], 0)
        self.assertTrue(lexical_features['has_death_term'])
        self.assertTrue(lexical_features['has_actor_term'])
        
        # Verify syntactic features
        self.assertTrue(syntactic_features['has_violence_predicate'])
        self.assertEqual(syntactic_features['violence_verb'], 'killed')
        self.assertEqual(syntactic_features['subject'], 'militants')
        self.assertEqual(syntactic_features['object'], 'civilians')
        
        # Verify combined features make sense
        self.assertIn(15, syntactic_features.get('casualty_numbers', []))
        self.assertIn('Maiduguri', syntactic_features.get('location', ''))
    
    def test_feature_consistency(self):
        """Test that features are consistent across different sentence structures."""
        # Active voice
        tokens1 = [
            {'word': 'Militants', 'pos': 'NNS', 'index': 0},
            {'word': 'attacked', 'pos': 'VBD', 'index': 1},
            {'word': 'the', 'pos': 'DT', 'index': 2},
            {'word': 'village', 'pos': 'NN', 'index': 3}
        ]
        deps1 = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'det', 'governor': 4, 'dependent': 3},
            {'dep': 'dobj', 'governor': 2, 'dependent': 4}
        ]
        
        # Passive voice
        tokens2 = [
            {'word': 'The', 'pos': 'DT', 'index': 0},
            {'word': 'village', 'pos': 'NN', 'index': 1},
            {'word': 'was', 'pos': 'VBD', 'index': 2},
            {'word': 'attacked', 'pos': 'VBN', 'index': 3},
            {'word': 'by', 'pos': 'IN', 'index': 4},
            {'word': 'militants', 'pos': 'NNS', 'index': 5}
        ]
        deps2 = [
            {'dep': 'det', 'governor': 2, 'dependent': 1},
            {'dep': 'nsubjpass', 'governor': 4, 'dependent': 2},
            {'dep': 'auxpass', 'governor': 4, 'dependent': 3},
            {'dep': 'agent', 'governor': 4, 'dependent': 6}
        ]
        
        # Extract features for both
        lex1 = self.lexical_extractor.extract_features([t['word'] for t in tokens1])
        syn1 = self.syntactic_extractor.extract_features(tokens1, deps1)
        
        lex2 = self.lexical_extractor.extract_features([t['word'] for t in tokens2])
        syn2 = self.syntactic_extractor.extract_features(tokens2, deps2)
        
        # Both should detect violence
        self.assertTrue(syn1['has_violence_predicate'])
        self.assertTrue(syn2['has_violence_predicate'])
        
        # Both should have similar violence term counts
        self.assertGreater(lex1['violence_term_count'], 0)
        self.assertGreater(lex2['violence_term_count'], 0)
        
        # Voice should be different
        self.assertEqual(syn1['voice'], 'active')
        self.assertEqual(syn2['voice'], 'passive')
    
    def test_weapon_detection_integration(self):
        """Test weapon detection across lexical and syntactic features."""
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
            {'dep': 'dobj', 'governor': 2, 'dependent': 4},
            {'dep': 'compound', 'governor': 4, 'dependent': 3},
            {'dep': 'nmod', 'governor': 2, 'dependent': 6}
        ]
        
        lexical_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Both should detect weapons
        self.assertTrue(lexical_features['has_weapon_term'])
        self.assertIn('AK-47', syntactic_features.get('weapon_mentions', []))
        self.assertIn('rifles', syntactic_features.get('weapon_mentions', []))
    
    def test_casualty_extraction_integration(self):
        """Test casualty extraction across features."""
        tokens = [
            {'word': 'At', 'pos': 'IN', 'index': 0},
            {'word': 'least', 'pos': 'JJS', 'index': 1},
            {'word': '25', 'pos': 'CD', 'index': 2},
            {'word': 'people', 'pos': 'NNS', 'index': 3},
            {'word': 'were', 'pos': 'VBD', 'index': 4},
            {'word': 'killed', 'pos': 'VBN', 'index': 5},
            {'word': 'and', 'pos': 'CC', 'index': 6},
            {'word': '12', 'pos': 'CD', 'index': 7},
            {'word': 'injured', 'pos': 'VBN', 'index': 8}
        ]
        dependencies = [
            {'dep': 'advmod', 'governor': 3, 'dependent': 1},
            {'dep': 'nummod', 'governor': 4, 'dependent': 3},
            {'dep': 'nsubjpass', 'governor': 6, 'dependent': 4},
            {'dep': 'conj', 'governor': 6, 'dependent': 9},
            {'dep': 'nummod', 'governor': 9, 'dependent': 8}
        ]
        
        lexical_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Both should detect casualties
        self.assertTrue(lexical_features['has_casualty_info'])
        self.assertIn(25, syntactic_features.get('casualty_numbers', []))
        self.assertIn(12, syntactic_features.get('casualty_numbers', []))
    
    def test_actor_identification_integration(self):
        """Test actor identification across features."""
        tokens = [
            {'word': 'Boko', 'pos': 'NNP', 'index': 0},
            {'word': 'Haram', 'pos': 'NNP', 'index': 1},
            {'word': 'militants', 'pos': 'NNS', 'index': 2},
            {'word': 'attacked', 'pos': 'VBD', 'index': 3},
            {'word': 'the', 'pos': 'DT', 'index': 4},
            {'word': 'village', 'pos': 'NN', 'index': 5}
        ]
        dependencies = [
            {'dep': 'compound', 'governor': 2, 'dependent': 1},
            {'dep': 'compound', 'governor': 3, 'dependent': 2},
            {'dep': 'nsubj', 'governor': 4, 'dependent': 3},
            {'dep': 'det', 'governor': 6, 'dependent': 5},
            {'dep': 'dobj', 'governor': 4, 'dependent': 6}
        ]
        
        lexical_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Both should identify actors
        self.assertTrue(lexical_features['has_actor_term'])
        self.assertIn('militants', syntactic_features.get('subject', ''))
        self.assertIn('Boko Haram', ' '.join([t['word'] for t in tokens[:3]]))
    
    def test_location_extraction_integration(self):
        """Test location extraction across features."""
        tokens = [
            {'word': 'Attack', 'pos': 'NN', 'index': 0},
            {'word': 'occurred', 'pos': 'VBD', 'index': 1},
            {'word': 'in', 'pos': 'IN', 'index': 2},
            {'word': 'Mogadishu', 'pos': 'NNP', 'index': 3},
            {'word': 'Somalia', 'pos': 'NNP', 'index': 4}
        ]
        dependencies = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'nmod', 'governor': 2, 'dependent': 4},
            {'dep': 'case', 'governor': 4, 'dependent': 3}
        ]
        
        lexical_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Syntactic features should capture location
        self.assertIn('Mogadishu', syntactic_features.get('location', ''))
        self.assertIn('in Mogadishu', syntactic_features.get('location_phrase', ''))
    
    def test_temporal_information_integration(self):
        """Test temporal information extraction across features."""
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
        
        lexical_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Syntactic features should capture temporal information
        self.assertTrue(syntactic_features['has_temporal_modifier'])
        self.assertIn('Tuesday', syntactic_features.get('temporal_phrase', ''))
    
    def test_feature_completeness(self):
        """Test that all expected features are present."""
        tokens = [
            {'word': 'Armed', 'pos': 'JJ', 'index': 0},
            {'word': 'militants', 'pos': 'NNS', 'index': 1},
            {'word': 'killed', 'pos': 'VBD', 'index': 2},
            {'word': '15', 'pos': 'CD', 'index': 3},
            {'word': 'civilians', 'pos': 'NNS', 'index': 4}
        ]
        dependencies = [
            {'dep': 'amod', 'governor': 2, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'dobj', 'governor': 3, 'dependent': 5},
            {'dep': 'nummod', 'governor': 5, 'dependent': 4}
        ]
        
        lexical_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syntactic_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        # Check lexical features
        expected_lexical = [
            'num_tokens', 'avg_token_length', 'violence_term_count',
            'violence_term_ratio', 'has_death_term', 'has_weapon_term',
            'has_actor_term', 'num_capitalized', 'num_numbers'
        ]
        for feature in expected_lexical:
            self.assertIn(feature, lexical_features)
        
        # Check syntactic features
        expected_syntactic = [
            'has_violence_predicate', 'violence_verb', 'subject', 'object',
            'voice', 'parse_tree_depth'
        ]
        for feature in expected_syntactic:
            self.assertIn(feature, syntactic_features)
    
    def test_edge_cases_integration(self):
        """Test edge cases in feature extraction integration."""
        # Empty input
        lex_empty = self.lexical_extractor.extract_features([])
        syn_empty = self.syntactic_extractor.extract_features([], [])
        
        self.assertEqual(lex_empty['num_tokens'], 0)
        self.assertFalse(syn_empty['has_violence_predicate'])
        
        # Non-violence text
        tokens = [
            {'word': 'The', 'pos': 'DT', 'index': 0},
            {'word': 'weather', 'pos': 'NN', 'index': 1},
            {'word': 'is', 'pos': 'VBZ', 'index': 2},
            {'word': 'nice', 'pos': 'JJ', 'index': 3}
        ]
        dependencies = [
            {'dep': 'det', 'governor': 2, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'cop', 'governor': 3, 'dependent': 3}
        ]
        
        lex_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syn_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        self.assertEqual(lex_features['violence_term_count'], 0)
        self.assertFalse(syn_features['has_violence_predicate'])

if __name__ == '__main__':
    unittest.main()
