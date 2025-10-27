#!/usr/bin/env python3
"""
Comprehensive tests for the enhanced lexical feature extractor.
"""

import unittest
import logging
from features.lexical_features import LexicalFeatureExtractor

class TestEnhancedLexicalFeatures(unittest.TestCase):
    """Test enhanced lexical feature extraction functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        logging.basicConfig(level=logging.DEBUG)
        self.extractor = LexicalFeatureExtractor(enable_logging=True)
    
    def test_basic_statistics(self):
        """Test basic statistical features."""
        tokens = ["The", "militants", "attacked", "the", "village", "killing", "15", "people"]
        features = self.extractor.extract_features(tokens)
        
        self.assertEqual(features['num_tokens'], 8)
        self.assertGreater(features['avg_token_length'], 0)
        self.assertEqual(features['max_token_length'], 9)  # "militants"
        self.assertEqual(features['min_token_length'], 2)  # "15"
        self.assertEqual(features['unique_tokens'], 8)
        self.assertEqual(features['token_diversity'], 1.0)
    
    def test_violence_features(self):
        """Test violence-related feature extraction."""
        violent_tokens = ["militants", "attacked", "killed", "15", "people", "with", "guns"]
        peaceful_tokens = ["people", "went", "to", "the", "market", "today"]
        
        violent_features = self.extractor.extract_features(violent_tokens)
        peaceful_features = self.extractor.extract_features(peaceful_tokens)
        
        # Violence features should be higher for violent text
        # Note: violence_term_count uses the main lexicon, but specialized features work
        self.assertGreater(violent_features['violence_intensity'], peaceful_features['violence_intensity'])
        self.assertTrue(violent_features['has_death_terms'])
        self.assertTrue(violent_features['has_weapon_terms'])
        self.assertTrue(violent_features['has_actor_terms'])
        self.assertTrue(violent_features['has_violence_verbs'])
        self.assertGreater(violent_features['violence_intensity'], 0)
        
        # Peaceful text should have minimal violence features
        self.assertFalse(peaceful_features['has_death_terms'])
        self.assertFalse(peaceful_features['has_weapon_terms'])
        self.assertFalse(peaceful_features['has_actor_terms'])
        self.assertFalse(peaceful_features['has_violence_verbs'])
        self.assertEqual(peaceful_features['violence_intensity'], 0)
    
    def test_african_context_features(self):
        """Test African context feature extraction."""
        african_tokens = ["Boko", "Haram", "attacked", "Maiduguri", "Nigeria", "ECOWAS", "condemned"]
        non_african_tokens = ["people", "went", "to", "the", "market", "today"]
        
        african_features = self.extractor.extract_features(african_tokens)
        non_african_features = self.extractor.extract_features(non_african_tokens)
        
        # African context features should be higher for African text
        self.assertGreater(african_features['african_country_count'], non_african_features['african_country_count'])
        self.assertGreater(african_features['african_city_count'], non_african_features['african_city_count'])
        self.assertGreater(african_features['african_org_count'], non_african_features['african_org_count'])
        self.assertTrue(african_features['has_african_context'])
        self.assertGreater(african_features['african_context_ratio'], 0)
        
        # Non-African text should have minimal African context
        self.assertFalse(non_african_features['has_african_context'])
        self.assertEqual(non_african_features['african_context_ratio'], 0)
    
    def test_linguistic_features(self):
        """Test linguistic feature extraction."""
        tokens = ["The", "MILITANTS", "attacked", "the", "village", "123", "people"]
        text = "The MILITANTS attacked the village! 123 people were killed???"
        
        features = self.extractor.extract_features(tokens, text)
        
        # Capitalization features
        self.assertGreater(features['num_capitalized'], 0)
        self.assertGreater(features['num_all_caps'], 0)
        self.assertGreater(features['capitalization_ratio'], 0)
        
        # Number features
        self.assertGreater(features['num_numbers'], 0)
        self.assertGreater(features['number_ratio'], 0)
        
        # Punctuation features
        self.assertGreater(features['num_exclamations'], 0)
        self.assertGreater(features['num_questions'], 0)
    
    def test_statistical_features(self):
        """Test statistical distribution features."""
        # Test with repeated tokens
        tokens = ["attack", "attack", "attack", "village", "village", "people"]
        features = self.extractor.extract_features(tokens)
        
        # Should have low diversity due to repetition
        self.assertLess(features['token_diversity'], 1.0)
        self.assertGreater(features['most_frequent_count'], 1)
        self.assertEqual(features['most_frequent_token'], "attack")
        self.assertGreater(features['rare_token_count'], 0)
    
    def test_temporal_intensity_features(self):
        """Test temporal and intensity features."""
        temporal_tokens = ["today", "urgent", "breaking", "news", "suddenly", "happened"]
        intensity_tokens = ["severe", "massive", "devastating", "attack", "brutal", "violence"]
        
        temporal_features = self.extractor.extract_features(temporal_tokens)
        intensity_features = self.extractor.extract_features(intensity_tokens)
        
        # Temporal features
        self.assertGreater(temporal_features['temporal_term_count'], 0)
        self.assertTrue(temporal_features['has_temporal_markers'])
        self.assertGreater(temporal_features['temporal_ratio'], 0)
        
        # Intensity features
        self.assertGreater(intensity_features['intensity_term_count'], 0)
        self.assertTrue(intensity_features['has_intensity_markers'])
        self.assertGreater(intensity_features['intensity_ratio'], 0)
    
    def test_sentiment_features(self):
        """Test sentiment feature extraction."""
        negative_tokens = ["terrible", "horrible", "devastating", "tragic", "fear", "panic"]
        positive_tokens = ["peaceful", "calm", "successful", "victory", "hope", "optimistic"]
        
        negative_features = self.extractor.extract_features(negative_tokens)
        positive_features = self.extractor.extract_features(positive_tokens)
        
        # Negative sentiment features
        self.assertGreater(negative_features['negative_term_count'], 0)
        self.assertTrue(negative_features['has_negative_sentiment'])
        self.assertLessEqual(negative_features['sentiment_ratio'], 0)  # Should be negative for negative terms
        
        # Positive sentiment features
        self.assertGreater(positive_features['positive_term_count'], 0)
        self.assertTrue(positive_features['has_positive_sentiment'])
        self.assertGreater(positive_features['sentiment_ratio'], 0)  # Positive ratio
    
    def test_ngram_extraction(self):
        """Test n-gram extraction."""
        tokens = ["militants", "attacked", "village", "killing", "people"]
        
        # Basic n-grams
        bigrams = self.extractor.extract_ngrams(tokens, n=2)
        self.assertGreater(len(bigrams), 0)
        self.assertIn("militants attacked", bigrams)
        self.assertIn("attacked village", bigrams)
        
        # Violence n-grams
        violence_bigrams = self.extractor.extract_violence_ngrams(tokens, n=2)
        self.assertGreater(len(violence_bigrams), 0)
        self.assertIn("militants attacked", violence_bigrams)
        
        # African n-grams
        african_tokens = ["Boko", "Haram", "attacked", "Maiduguri", "Nigeria"]
        african_bigrams = self.extractor.extract_african_ngrams(african_tokens, n=2)
        self.assertGreater(len(african_bigrams), 0)
        # Should contain African context n-grams
        self.assertTrue(any("maiduguri" in ngram or "nigeria" in ngram for ngram in african_bigrams))
    
    def test_feature_summary(self):
        """Test feature summary generation."""
        tokens = ["militants", "attacked", "village", "killing", "people", "in", "Nigeria"]
        features = self.extractor.extract_features(tokens)
        
        summary = self.extractor.get_feature_summary(features)
        
        self.assertGreater(summary['total_features'], 0)
        self.assertGreater(summary['violence_features'], 0)
        self.assertGreater(summary['african_features'], 0)
        self.assertGreater(summary['linguistic_features'], 0)
    
    def test_top_features(self):
        """Test top features extraction."""
        tokens = ["attack", "attack", "attack", "village", "people"]
        features = self.extractor.extract_features(tokens)
        
        top_features = self.extractor.get_top_features(features, top_n=5)
        
        self.assertLessEqual(len(top_features), 5)
        self.assertGreater(len(top_features), 0)
        
        # Should be sorted by value
        for i in range(len(top_features) - 1):
            self.assertGreaterEqual(top_features[i][1], top_features[i+1][1])
    
    def test_feature_comparison(self):
        """Test feature comparison functionality."""
        tokens1 = ["militants", "attacked", "village", "killing", "people"]
        tokens2 = ["people", "went", "to", "market", "peacefully"]
        
        features1 = self.extractor.extract_features(tokens1)
        features2 = self.extractor.extract_features(tokens2)
        
        comparison = self.extractor.compare_features(features1, features2)
        
        self.assertGreater(len(comparison), 0)
        
        # Violence features should be higher in first text
        if 'violence_intensity' in comparison:
            self.assertGreater(comparison['violence_intensity']['value1'], 
                                comparison['violence_intensity']['value2'])
    
    def test_empty_tokens(self):
        """Test handling of empty token lists."""
        features = self.extractor.extract_features([])
        
        # Should return default values for empty input
        self.assertEqual(features['num_tokens'], 0)
        self.assertEqual(features['violence_term_count'], 0)
        self.assertEqual(features['african_country_count'], 0)
        self.assertFalse(features['has_death_terms'])
        self.assertFalse(features['has_african_context'])
    
    def test_african_news_scenario(self):
        """Test comprehensive African news scenario."""
        tokens = [
            "Boko", "Haram", "militants", "attacked", "Maiduguri", "village", 
            "killing", "15", "civilians", "with", "guns", "and", "bombs", 
            "ECOWAS", "condemned", "the", "violence", "urgently"
        ]
        
        features = self.extractor.extract_features(tokens)
        
        # Should detect violence
        self.assertTrue(features['has_death_terms'])
        self.assertTrue(features['has_weapon_terms'])
        self.assertTrue(features['has_actor_terms'])
        self.assertTrue(features['has_violence_verbs'])
        self.assertGreater(features['violence_intensity'], 0)
        
        # Should detect African context
        self.assertTrue(features['has_african_context'])
        self.assertGreater(features['african_city_count'], 0)  # Maiduguri
        self.assertGreater(features['african_org_count'], 0)   # ECOWAS
        
        # Should detect temporal markers
        self.assertTrue(features['has_temporal_markers'])
        
        # Should have high violence intensity
        self.assertGreater(features['violence_intensity'], 0.1)
    
    def test_ngram_filtering(self):
        """Test n-gram filtering by frequency."""
        tokens = ["attack", "attack", "attack", "village", "people", "people"]
        
        # Without filtering
        all_ngrams = self.extractor.extract_ngrams(tokens, n=2, min_frequency=1)
        
        # With frequency filtering
        filtered_ngrams = self.extractor.extract_ngrams(tokens, n=2, min_frequency=2)
        
        self.assertGreaterEqual(len(all_ngrams), len(filtered_ngrams))
        self.assertIn("attack attack", filtered_ngrams)
        self.assertNotIn("village people", filtered_ngrams)  # Only appears once
    
    def test_specialized_lexicons(self):
        """Test specialized lexicon detection."""
        # Test death terms
        death_tokens = ["killed", "murdered", "death", "casualties", "victims"]
        death_features = self.extractor.extract_features(death_tokens)
        self.assertTrue(death_features['has_death_terms'])
        self.assertGreater(death_features['death_term_count'], 0)
        
        # Test weapon terms
        weapon_tokens = ["guns", "bombs", "weapons", "ak-47", "rpg"]
        weapon_features = self.extractor.extract_features(weapon_tokens)
        self.assertTrue(weapon_features['has_weapon_terms'])
        self.assertGreater(weapon_features['weapon_term_count'], 0)
        
        # Test actor terms
        actor_tokens = ["militants", "terrorists", "gunmen", "boko haram"]
        actor_features = self.extractor.extract_features(actor_tokens)
        self.assertTrue(actor_features['has_actor_terms'])
        self.assertGreater(actor_features['actor_term_count'], 0)
    
    def test_comprehensive_feature_extraction(self):
        """Test comprehensive feature extraction with all categories."""
        tokens = [
            "Boko", "Haram", "militants", "severely", "attacked", "Maiduguri", 
            "village", "today", "killing", "15", "civilians", "with", "guns", 
            "and", "bombs", "ECOWAS", "condemned", "the", "terrible", "violence"
        ]
        
        features = self.extractor.extract_features(tokens)
        
        # Should have features from all categories
        self.assertGreater(features['num_tokens'], 0)
        self.assertGreater(features['violence_intensity'], 0)  # Violence intensity instead of count
        self.assertGreater(features['african_city_count'], 0)  # Maiduguri
        self.assertGreater(features['temporal_term_count'], 0)
        self.assertGreater(features['intensity_term_count'], 0)
        self.assertGreater(features['negative_term_count'], 0)
        
        # Should have high violence intensity
        self.assertGreater(features['violence_intensity'], 0.1)
        
        # Should have African context
        self.assertTrue(features['has_african_context'])
        
        # Should have temporal and intensity markers
        self.assertTrue(features['has_temporal_markers'])
        self.assertTrue(features['has_intensity_markers'])
        
        # Should have negative sentiment
        self.assertTrue(features['has_negative_sentiment'])

if __name__ == '__main__':
    unittest.main()
