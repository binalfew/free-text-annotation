# test_feature_extraction_integration_final.py

import unittest
from features.lexical_features import LexicalFeatureExtractor
from features.syntactic_features import SyntacticFeatureExtractor
from domain_specific.violence_lexicon import ViolenceLexicon

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
            {'word': 'Armed', 'pos': 'JJ', 'index': 0, 'lemma': 'armed'},
            {'word': 'militants', 'pos': 'NNS', 'index': 1, 'lemma': 'militant'},
            {'word': 'kill', 'pos': 'VBD', 'index': 2, 'lemma': 'kill'},
            {'word': '15', 'pos': 'CD', 'index': 3, 'lemma': '15'},
            {'word': 'civilians', 'pos': 'NNS', 'index': 4, 'lemma': 'civilian'},
            {'word': 'in', 'pos': 'IN', 'index': 5, 'lemma': 'in'},
            {'word': 'Maiduguri', 'pos': 'NNP', 'index': 6, 'lemma': 'Maiduguri'}
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
        self.assertTrue(syntactic_features['has_violence_verb'])
        self.assertTrue(syntactic_features['has_nsubj'])
        self.assertTrue(syntactic_features['has_dobj'])
        self.assertTrue(syntactic_features['has_agent_patient'])
    
    def test_feature_consistency(self):
        """Test that features are consistent across different sentence structures."""
        # Active voice
        tokens1 = [
            {'word': 'Militants', 'pos': 'NNS', 'index': 0, 'lemma': 'militant'},
            {'word': 'attacked', 'pos': 'VBD', 'index': 1, 'lemma': 'attack'},
            {'word': 'the', 'pos': 'DT', 'index': 2, 'lemma': 'the'},
            {'word': 'village', 'pos': 'NN', 'index': 3, 'lemma': 'village'}
        ]
        deps1 = [
            {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
            {'dep': 'det', 'governor': 4, 'dependent': 3},
            {'dep': 'dobj', 'governor': 2, 'dependent': 4}
        ]
        
        # Passive voice
        tokens2 = [
            {'word': 'The', 'pos': 'DT', 'index': 0, 'lemma': 'the'},
            {'word': 'village', 'pos': 'NN', 'index': 1, 'lemma': 'village'},
            {'word': 'was', 'pos': 'VBD', 'index': 2, 'lemma': 'be'},
            {'word': 'attacked', 'pos': 'VBN', 'index': 3, 'lemma': 'attack'},
            {'word': 'by', 'pos': 'IN', 'index': 4, 'lemma': 'by'},
            {'word': 'militants', 'pos': 'NNS', 'index': 5, 'lemma': 'militant'}
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
        self.assertTrue(syn1['has_violence_verb'])
        self.assertTrue(syn2['has_violence_verb'])
        
        # Both should have similar violence term counts
        self.assertGreater(lex1['violence_term_count'], 0)
        self.assertGreater(lex2['violence_term_count'], 0)
    
    def test_weapon_detection_integration(self):
        """Test weapon detection across lexical and syntactic features."""
        tokens = [
            {'word': 'gunmen', 'pos': 'NNS', 'index': 0, 'lemma': 'gunman'},
            {'word': 'fired', 'pos': 'VBD', 'index': 1, 'lemma': 'fire'},
            {'word': 'gun', 'pos': 'NN', 'index': 2, 'lemma': 'gun'},
            {'word': 'at', 'pos': 'IN', 'index': 3, 'lemma': 'at'},
            {'word': 'civilians', 'pos': 'NNS', 'index': 4, 'lemma': 'civilian'}
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
        self.assertTrue(syntactic_features['has_violence_verb'])
    
    def test_casualty_extraction_integration(self):
        """Test casualty extraction across features."""
        tokens = [
            {'word': 'At', 'pos': 'IN', 'index': 0, 'lemma': 'at'},
            {'word': 'least', 'pos': 'JJS', 'index': 1, 'lemma': 'least'},
            {'word': '25', 'pos': 'CD', 'index': 2, 'lemma': '25'},
            {'word': 'people', 'pos': 'NNS', 'index': 3, 'lemma': 'people'},
            {'word': 'were', 'pos': 'VBD', 'index': 4, 'lemma': 'be'},
            {'word': 'dead', 'pos': 'JJ', 'index': 5, 'lemma': 'dead'},
            {'word': 'and', 'pos': 'CC', 'index': 6, 'lemma': 'and'},
            {'word': '12', 'pos': 'CD', 'index': 7, 'lemma': '12'},
            {'word': 'injured', 'pos': 'VBN', 'index': 8, 'lemma': 'injure'}
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
        self.assertTrue(lexical_features['has_death_term'])
        self.assertTrue(syntactic_features['has_violence_verb'])
        self.assertGreater(lexical_features['num_numbers'], 0)
    
    def test_actor_identification_integration(self):
        """Test actor identification across features."""
        tokens = [
            {'word': 'Boko', 'pos': 'NNP', 'index': 0, 'lemma': 'Boko'},
            {'word': 'Haram', 'pos': 'NNP', 'index': 1, 'lemma': 'Haram'},
            {'word': 'militants', 'pos': 'NNS', 'index': 2, 'lemma': 'militant'},
            {'word': 'attacked', 'pos': 'VBD', 'index': 3, 'lemma': 'attack'},
            {'word': 'the', 'pos': 'DT', 'index': 4, 'lemma': 'the'},
            {'word': 'village', 'pos': 'NN', 'index': 5, 'lemma': 'village'}
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
        self.assertTrue(syntactic_features['has_violence_verb'])
        self.assertTrue(syntactic_features['has_nsubj'])
    
    def test_feature_completeness(self):
        """Test that all expected features are present."""
        tokens = [
            {'word': 'Armed', 'pos': 'JJ', 'index': 0, 'lemma': 'armed'},
            {'word': 'militants', 'pos': 'NNS', 'index': 1, 'lemma': 'militant'},
            {'word': 'kill', 'pos': 'VBD', 'index': 2, 'lemma': 'kill'},
            {'word': '15', 'pos': 'CD', 'index': 3, 'lemma': '15'},
            {'word': 'civilians', 'pos': 'NNS', 'index': 4, 'lemma': 'civilian'}
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
            'num_verbs', 'num_nouns', 'num_adj', 'has_violence_verb',
            'has_nsubj', 'has_dobj', 'has_iobj', 'has_agent_patient'
        ]
        for feature in expected_syntactic:
            self.assertIn(feature, syntactic_features)
    
    def test_edge_cases_integration(self):
        """Test edge cases in feature extraction integration."""
        # Empty input
        lex_empty = self.lexical_extractor.extract_features([])
        syn_empty = self.syntactic_extractor.extract_features([], [])
        
        self.assertEqual(lex_empty['num_tokens'], 0)
        self.assertEqual(syn_empty['num_verbs'], 0)
        
        # Non-violence text
        tokens = [
            {'word': 'The', 'pos': 'DT', 'index': 0, 'lemma': 'the'},
            {'word': 'weather', 'pos': 'NN', 'index': 1, 'lemma': 'weather'},
            {'word': 'is', 'pos': 'VBZ', 'index': 2, 'lemma': 'be'},
            {'word': 'nice', 'pos': 'JJ', 'index': 3, 'lemma': 'nice'}
        ]
        dependencies = [
            {'dep': 'det', 'governor': 2, 'dependent': 1},
            {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
            {'dep': 'cop', 'governor': 3, 'dependent': 3}
        ]
        
        lex_features = self.lexical_extractor.extract_features([t['word'] for t in tokens])
        syn_features = self.syntactic_extractor.extract_features(tokens, dependencies)
        
        self.assertEqual(lex_features['violence_term_count'], 0)
        self.assertFalse(syn_features['has_violence_verb'])

if __name__ == '__main__':
    unittest.main()
