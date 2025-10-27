# test_event_extraction_edge_cases.py

import unittest
from event_extraction import EventExtractor, EventTriggerDetector, FiveW1HExtractor
from domain.violence_lexicon import ViolenceLexicon
from domain.african_ner import AfricanNER

class TestEventExtractionEdgeCases(unittest.TestCase):
    """Test edge cases in event extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.lexicon = ViolenceLexicon()
        self.ner = AfricanNER()
        self.extractor = EventExtractor(self.lexicon, self.ner)
        self.trigger_detector = EventTriggerDetector(self.lexicon)
        self.fivew1h_extractor = FiveW1HExtractor(self.ner)
    
    def test_ambiguous_triggers(self):
        """Test handling of ambiguous event triggers."""
        # "attack" as noun vs verb
        sentence_annotation = {
            'tokens': [
                {'word': 'The', 'pos': 'DT', 'index': 0, 'lemma': 'the'},
                {'word': 'attack', 'pos': 'NN', 'index': 1, 'lemma': 'attack'},
                {'word': 'was', 'pos': 'VBD', 'index': 2, 'lemma': 'be'},
                {'word': 'brutal', 'pos': 'JJ', 'index': 3, 'lemma': 'brutal'}
            ],
            'basicDependencies': [
                {'dep': 'det', 'governor': 2, 'dependent': 1},
                {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
                {'dep': 'cop', 'governor': 3, 'dependent': 3}
            ]
        }
        
        triggers = self.trigger_detector.detect_triggers(sentence_annotation)
        
        # Should detect "attack" as noun trigger
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]['word'], 'attack')
        self.assertEqual(triggers[0]['type'], 'noun')
    
    def test_implicit_violence(self):
        """Test detection of implicit violence."""
        # Violence without explicit trigger words
        sentence_annotation = {
            'tokens': [
                {'word': '15', 'pos': 'CD', 'index': 0, 'lemma': '15'},
                {'word': 'people', 'pos': 'NNS', 'index': 1, 'lemma': 'people'},
                {'word': 'killed', 'pos': 'VBD', 'index': 2, 'lemma': 'kill'},
                {'word': 'in', 'pos': 'IN', 'index': 3, 'lemma': 'in'},
                {'word': 'Maiduguri', 'pos': 'NNP', 'index': 4, 'lemma': 'Maiduguri'}
            ],
            'basicDependencies': [
                {'dep': 'nummod', 'governor': 2, 'dependent': 1},
                {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
                {'dep': 'nmod', 'governor': 3, 'dependent': 5}
            ]
        }
        
        triggers = self.trigger_detector.detect_triggers(sentence_annotation)
        
        # Should detect "killed" as trigger
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]['word'], 'killed')
    
    def test_complex_sentence_structure(self):
        """Test complex sentence with multiple clauses."""
        sentence_annotation = {
            'tokens': [
                {'word': 'When', 'pos': 'WRB', 'index': 0, 'lemma': 'when'},
                {'word': 'militants', 'pos': 'NNS', 'index': 1, 'lemma': 'militant'},
                {'word': 'attacked', 'pos': 'VBD', 'index': 2, 'lemma': 'attack'},
                {'word': 'the', 'pos': 'DT', 'index': 3, 'lemma': 'the'},
                {'word': 'village', 'pos': 'NN', 'index': 4, 'lemma': 'village'},
                {'word': 'they', 'pos': 'PRP', 'index': 5, 'lemma': 'they'},
                {'word': 'killed', 'pos': 'VBD', 'index': 6, 'lemma': 'kill'},
                {'word': '15', 'pos': 'CD', 'index': 7, 'lemma': '15'},
                {'word': 'civilians', 'pos': 'NNS', 'index': 8, 'lemma': 'civilian'}
            ],
            'basicDependencies': [
                {'dep': 'advmod', 'governor': 3, 'dependent': 1},
                {'dep': 'nsubj', 'governor': 3, 'dependent': 2},
                {'dep': 'det', 'governor': 5, 'dependent': 4},
                {'dep': 'dobj', 'governor': 3, 'dependent': 5},
                {'dep': 'nsubj', 'governor': 7, 'dependent': 6},
                {'dep': 'dobj', 'governor': 7, 'dependent': 9},
                {'dep': 'nummod', 'governor': 9, 'dependent': 8}
            ]
        }
        
        triggers = self.trigger_detector.detect_triggers(sentence_annotation)
        
        # Should detect both triggers
        self.assertEqual(len(triggers), 2)
        trigger_words = [t['word'] for t in triggers]
        self.assertIn('attacked', trigger_words)
        self.assertIn('killed', trigger_words)
    
    
    def test_missing_components(self):
        """Test extraction when some 5W1H components are missing."""
        sentence_annotation = {
            'tokens': [
                {'word': 'Attack', 'pos': 'NN', 'index': 0, 'lemma': 'attack'},
                {'word': 'occurred', 'pos': 'VBD', 'index': 1, 'lemma': 'occurred'},
                {'word': 'yesterday', 'pos': 'NN', 'index': 2, 'lemma': 'yesterday'}
            ],
            'basicDependencies': [
                {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
                {'dep': 'nmod', 'governor': 2, 'dependent': 3}
            ],
            'entities': []
        }
        
        triggers = self.trigger_detector.detect_triggers(sentence_annotation)
        extractions = self.fivew1h_extractor.extract(sentence_annotation, triggers)
        
        # Should handle missing components gracefully
        self.assertEqual(len(extractions), 1)
        extraction = extractions[0]
        
        # Some components should be None
        self.assertIsNone(extraction['who'])
        self.assertIsNone(extraction['whom'])
        self.assertIsNotNone(extraction['when'])
        self.assertIn('yesterday', extraction['when']['text'])
    
    
    
    def test_quoted_speech(self):
        """Test extraction from quoted speech."""
        sentence_annotation = {
            'tokens': [
                {'word': 'He', 'pos': 'PRP', 'index': 0, 'lemma': 'he'},
                {'word': 'said', 'pos': 'VBD', 'index': 1, 'lemma': 'said'},
                {'word': '"', 'pos': '``', 'index': 2, 'lemma': '"'},
                {'word': 'Militants', 'pos': 'NNS', 'index': 3, 'lemma': 'militants'},
                {'word': 'killed', 'pos': 'VBD', 'index': 4, 'lemma': 'killed'},
                {'word': '15', 'pos': 'CD', 'index': 5, 'lemma': '15'},
                {'word': 'people', 'pos': 'NNS', 'index': 6, 'lemma': 'people'},
                {'word': '"', 'pos': "''", 'index': 7}
            ],
            'basicDependencies': [
                {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
                {'dep': 'nsubj', 'governor': 5, 'dependent': 4},
                {'dep': 'dobj', 'governor': 5, 'dependent': 7},
                {'dep': 'nummod', 'governor': 7, 'dependent': 6}
            ],
            'entities': []
        }
        
        triggers = self.trigger_detector.detect_triggers(sentence_annotation)
        extractions = self.fivew1h_extractor.extract(sentence_annotation, triggers)
        
        # Should extract from quoted speech
        self.assertEqual(len(triggers), 1)
        self.assertEqual(len(extractions), 1)
        
        extraction = extractions[0]
        self.assertIsNotNone(extraction['who'])
        self.assertIn('Militants', extraction['who']['text'])
        self.assertIsNotNone(extraction['whom'])
        self.assertIn('people', extraction['whom']['text'])
    
    def test_temporal_expressions(self):
        """Test extraction of temporal expressions."""
        sentence_annotation = {
            'tokens': [
                {'word': 'Attack', 'pos': 'NN', 'index': 0, 'lemma': 'attack'},
                {'word': 'happened', 'pos': 'VBD', 'index': 1, 'lemma': 'happened'},
                {'word': 'on', 'pos': 'IN', 'index': 2, 'lemma': 'on'},
                {'word': 'Tuesday', 'pos': 'NNP', 'index': 3, 'lemma': 'tuesday'},
                {'word': 'morning', 'pos': 'NN', 'index': 4, 'lemma': 'morning'},
                {'word': 'at', 'pos': 'IN', 'index': 5, 'lemma': 'at'},
                {'word': '3', 'pos': 'CD', 'index': 6, 'lemma': '3'},
                {'word': 'a.m.', 'pos': 'NN', 'index': 7, 'lemma': 'a.m.'}
            ],
            'basicDependencies': [
                {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
                {'dep': 'nmod', 'governor': 2, 'dependent': 4},
                {'dep': 'case', 'governor': 4, 'dependent': 3},
                {'dep': 'nmod', 'governor': 2, 'dependent': 7},
                {'dep': 'case', 'governor': 7, 'dependent': 6}
            ],
            'entities': [
                {'text': 'Tuesday', 'type': 'DATE'}
            ]
        }
        
        triggers = self.trigger_detector.detect_triggers(sentence_annotation)
        extractions = self.fivew1h_extractor.extract(sentence_annotation, triggers)
        
        # Should extract temporal information
        self.assertEqual(len(extractions), 1)
        extraction = extractions[0]
        
        self.assertIsNotNone(extraction['when'])
        self.assertIn('Tuesday', extraction['when']['text'])
    
    def test_confidence_scoring(self):
        """Test confidence scoring for extractions."""
        # High confidence case
        high_conf_annotation = {
            'tokens': [
                {'word': 'Boko', 'pos': 'NNP', 'index': 0, 'lemma': 'boko'},
                {'word': 'Haram', 'pos': 'NNP', 'index': 1, 'lemma': 'haram'},
                {'word': 'militants', 'pos': 'NNS', 'index': 2, 'lemma': 'militants'},
                {'word': 'killed', 'pos': 'VBD', 'index': 3, 'lemma': 'killed'},
                {'word': '15', 'pos': 'CD', 'index': 4, 'lemma': '15'},
                {'word': 'civilians', 'pos': 'NNS', 'index': 5, 'lemma': 'civilians'},
                {'word': 'in', 'pos': 'IN', 'index': 6, 'lemma': 'in'},
                {'word': 'Maiduguri', 'pos': 'NNP', 'index': 7, 'lemma': 'maiduguri'},
                {'word': 'on', 'pos': 'IN', 'index': 8, 'lemma': 'on'},
                {'word': 'Tuesday', 'pos': 'NNP', 'index': 9, 'lemma': 'tuesday'}
            ],
            'basicDependencies': [
                {'dep': 'compound', 'governor': 2, 'dependent': 1},
                {'dep': 'compound', 'governor': 3, 'dependent': 2},
                {'dep': 'nsubj', 'governor': 4, 'dependent': 3},
                {'dep': 'dobj', 'governor': 4, 'dependent': 6},
                {'dep': 'nummod', 'governor': 6, 'dependent': 5},
                {'dep': 'nmod', 'governor': 4, 'dependent': 8},
                {'dep': 'case', 'governor': 8, 'dependent': 7},
                {'dep': 'nmod', 'governor': 4, 'dependent': 10},
                {'dep': 'case', 'governor': 10, 'dependent': 9}
            ],
            'entities': [
                {'text': 'Boko Haram', 'type': 'ORGANIZATION'},
                {'text': 'Maiduguri', 'type': 'LOCATION'},
                {'text': 'Tuesday', 'type': 'DATE'}
            ]
        }
        
        triggers = self.trigger_detector.detect_triggers(high_conf_annotation)
        extractions = self.fivew1h_extractor.extract(high_conf_annotation, triggers)
        
        # Should have high confidence
        self.assertEqual(len(extractions), 1)
        extraction = extractions[0]
        
        # Calculate confidence
        confidence = self.extractor._calculate_confidence(extraction)
        self.assertGreater(confidence, 0.7)
    
    def test_empty_sentence(self):
        """Test handling of empty sentence."""
        empty_annotation = {
            'tokens': [],
            'basicDependencies': [],
            'entities': []
        }
        
        triggers = self.trigger_detector.detect_triggers(empty_annotation)
        extractions = self.fivew1h_extractor.extract(empty_annotation, triggers)
        
        self.assertEqual(len(triggers), 0)
        self.assertEqual(len(extractions), 0)
    
    def test_malformed_dependencies(self):
        """Test handling of malformed dependency structures."""
        malformed_annotation = {
            'tokens': [
                {'word': 'Attack', 'pos': 'NN', 'index': 0, 'lemma': 'attack'},
                {'word': 'occurred', 'pos': 'VBD', 'index': 1, 'lemma': 'occurred'}
            ],
            'basicDependencies': [
                {'dep': 'nsubj', 'governor': 2, 'dependent': 1}
            ],
            'entities': []
        }
        
        # Should not raise exception
        triggers = self.trigger_detector.detect_triggers(malformed_annotation)
        extractions = self.fivew1h_extractor.extract(malformed_annotation, triggers)
        
        # Should handle gracefully
        self.assertIsInstance(triggers, list)
        self.assertIsInstance(extractions, list)

if __name__ == '__main__':
    unittest.main()
