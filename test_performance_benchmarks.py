# test_performance_benchmarks.py

import unittest
import time
import tempfile
import os
from unittest.mock import Mock, patch
from pipeline import ViolentEventNLPPipeline
from batch_processing import BatchProcessor, AnnotationFormatter
from domain_specific.violence_lexicon import ViolenceLexicon
from domain_specific.african_ner import AfricanNER

class TestPerformanceBenchmarks(unittest.TestCase):
    """Test performance benchmarks for the NLP pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock configuration
        self.config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g'
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_single_article_processing_time(self):
        """Test processing time for single article."""
        # Mock pipeline to avoid CoreNLP dependency
        with patch('pipeline.ViolentEventNLPPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline_class.return_value = mock_pipeline
            
            # Mock processing result
            mock_pipeline.process_article.return_value = {
                'article_id': 'TEST_001',
                'sentences': [
                    {
                        'text': 'Militants killed 15 civilians in Maiduguri.',
                        'tokens': [
                            {'word': 'Militants', 'pos': 'NNS'},
                            {'word': 'killed', 'pos': 'VBD'},
                            {'word': '15', 'pos': 'CD'},
                            {'word': 'civilians', 'pos': 'NNS'},
                            {'word': 'in', 'pos': 'IN'},
                            {'word': 'Maiduguri', 'pos': 'NNP'}
                        ],
                        'entities': [
                            {'text': 'Maiduguri', 'type': 'LOCATION'}
                        ],
                        'dependencies': []
                    }
                ]
            }
            
            # Measure processing time
            start_time = time.time()
            pipeline = ViolentEventNLPPipeline(self.config)
            result = pipeline.process_article("Test article", "TEST_001")
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete within reasonable time (mocked)
            self.assertLess(processing_time, 5.0)  # 5 seconds max for mocked processing
            self.assertIn('article_id', result)
    
    def test_batch_processing_performance(self):
        """Test batch processing performance."""
        # Create test articles
        articles = []
        for i in range(10):
            articles.append({
                'id': f'ART_{i:03d}',
                'text': f'Article {i}: Militants attacked village {i} and killed {i+1} people.',
                'source': 'test',
                'publication_date': '2024-01-01'
            })
        
        # Mock components
        mock_pipeline = Mock()
        mock_extractor = Mock()
        formatter = AnnotationFormatter()
        
        # Mock processing results
        mock_pipeline.process_article.return_value = {'sentences': []}
        mock_extractor.extract_events.return_value = []
        
        batch_processor = BatchProcessor(
            mock_pipeline, mock_extractor, formatter, self.temp_dir
        )
        
        # Measure batch processing time
        start_time = time.time()
        results = batch_processor.process_articles(articles)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process all articles
        self.assertEqual(results['total_articles'], 10)
        self.assertEqual(results['processed'], 10)
        
        # Should complete within reasonable time
        self.assertLess(processing_time, 10.0)  # 10 seconds max for mocked batch
        
        # Calculate throughput
        throughput = results['total_articles'] / processing_time
        self.assertGreater(throughput, 0.1)  # At least 0.1 articles per second
    
    def test_memory_usage_simulation(self):
        """Test memory usage with large articles."""
        # Create large article
        large_text = "Militants attacked the village. " * 1000  # ~30k characters
        large_article = {
            'id': 'LARGE_001',
            'text': large_text,
            'source': 'test'
        }
        
        # Mock pipeline
        with patch('pipeline.ViolentEventNLPPipeline') as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline_class.return_value = mock_pipeline
            
            # Mock processing with memory simulation
            def mock_process_article(text, article_id):
                # Simulate memory usage based on text length
                memory_usage = len(text) / 1000  # Rough estimate
                if memory_usage > 50:  # Simulate memory limit
                    raise MemoryError("Simulated memory limit exceeded")
                return {'sentences': []}
            
            mock_pipeline.process_article.side_effect = mock_process_article
            
            # Test memory handling
            pipeline = ViolentEventNLPPipeline(self.config)
            
            # Should handle large text gracefully
            try:
                result = pipeline.process_article(large_text, "LARGE_001")
                self.assertIn('article_id', result)
            except MemoryError:
                # Expected for very large text
                pass
    
    def test_concurrent_processing_simulation(self):
        """Test concurrent processing performance."""
        articles = [
            {'id': f'ART_{i:03d}', 'text': f'Article {i} content'} 
            for i in range(20)
        ]
        
        # Mock components
        mock_pipeline = Mock()
        mock_extractor = Mock()
        formatter = AnnotationFormatter()
        
        # Mock processing with simulated delays
        def mock_process_article(text, article_id):
            time.sleep(0.01)  # 10ms delay per article
            return {'sentences': []}
        
        mock_pipeline.process_article.side_effect = mock_process_article
        mock_extractor.extract_events.return_value = []
        
        batch_processor = BatchProcessor(
            mock_pipeline, mock_extractor, formatter, self.temp_dir
        )
        
        # Test sequential processing
        start_time = time.time()
        results_seq = batch_processor.process_articles(articles, parallel=False)
        seq_time = time.time() - start_time
        
        # Test parallel processing (simulated)
        start_time = time.time()
        results_par = batch_processor.process_articles(articles, parallel=True)
        par_time = time.time() - start_time
        
        # Both should process all articles
        self.assertEqual(results_seq['total_articles'], 20)
        self.assertEqual(results_par['total_articles'], 20)
        
        # Note: Current implementation doesn't have true parallel processing
        # This test verifies the interface works
    
    def test_feature_extraction_performance(self):
        """Test feature extraction performance."""
        from features.lexical_features import LexicalFeatureExtractor
        from features.syntactic_features import SyntacticFeatureExtractor
        
        lexicon = ViolenceLexicon()
        lexical_extractor = LexicalFeatureExtractor(list(lexicon.all_terms))
        syntactic_extractor = SyntacticFeatureExtractor()
        
        # Test with various sentence lengths
        test_cases = [
            ("Short sentence.", 1),
            ("Militants killed civilians in village.", 7),
            ("Armed militants from Boko Haram attacked the village in Maiduguri on Tuesday morning and killed 15 civilians.", 20)
        ]
        
        for sentence, expected_tokens in test_cases:
            tokens = sentence.split()
            
            # Measure lexical feature extraction
            start_time = time.time()
            lexical_features = lexical_extractor.extract_features(tokens)
            lex_time = time.time() - start_time
            
            # Measure syntactic feature extraction (mocked)
            mock_tokens = [{'word': w, 'pos': 'NN', 'index': i} for i, w in enumerate(tokens)]
            mock_deps = [{'dep': 'nsubj', 'governor': 1, 'dependent': 2}]
            
            start_time = time.time()
            syntactic_features = syntactic_extractor.extract_features(mock_tokens, mock_deps)
            syn_time = time.time() - start_time
            
            # Should complete quickly
            self.assertLess(lex_time, 0.1)  # 100ms max
            self.assertLess(syn_time, 0.1)  # 100ms max
            
            # Should extract features
            self.assertIn('num_tokens', lexical_features)
            self.assertIn('has_violence_predicate', syntactic_features)
    
    def test_lexicon_performance(self):
        """Test lexicon lookup performance."""
        lexicon = ViolenceLexicon()
        
        # Test with various word counts
        test_words = [
            'killed', 'attack', 'militant', 'civilian', 'village',
            'peaceful', 'happy', 'beautiful', 'wonderful', 'amazing'
        ] * 100  # 1000 words total
        
        # Measure lexicon lookup time
        start_time = time.time()
        violence_count = 0
        for word in test_words:
            if lexicon.is_violence_term(word):
                violence_count += 1
        lookup_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(lookup_time, 1.0)  # 1 second max for 1000 lookups
        
        # Should find violence terms
        self.assertGreater(violence_count, 0)
        
        # Calculate lookup rate
        lookup_rate = len(test_words) / lookup_time
        self.assertGreater(lookup_rate, 100)  # At least 100 lookups per second
    
    def test_ner_performance(self):
        """Test NER performance."""
        ner = AfricanNER()
        
        # Test with various text lengths
        test_texts = [
            "Militants attacked Maiduguri.",
            "Boko Haram militants attacked the village in Maiduguri, Nigeria on Tuesday morning.",
            "Armed militants from Boko Haram attacked the village in Maiduguri, Nigeria on Tuesday morning and killed 15 civilians in the attack that occurred near the central market."
        ]
        
        for text in test_texts:
            # Measure location recognition
            start_time = time.time()
            locations = ner.recognize_location(text)
            loc_time = time.time() - start_time
            
            # Measure actor recognition
            start_time = time.time()
            actors = ner.recognize_actor(text)
            act_time = time.time() - start_time
            
            # Should complete quickly
            self.assertLess(loc_time, 0.1)  # 100ms max
            self.assertLess(act_time, 0.1)  # 100ms max
            
            # Should find entities in longer texts
            if len(text) > 50:
                self.assertGreater(len(locations) + len(actors), 0)
    
    def test_output_generation_performance(self):
        """Test output generation performance."""
        formatter = AnnotationFormatter()
        
        # Create test events
        events = []
        for i in range(100):
            events.append({
                'trigger': {'word': 'killed'},
                'who': {'text': f'Actor {i}'},
                'whom': {'text': f'Victim {i}'},
                'where': {'text': f'Location {i}'},
                'when': {'text': 'Tuesday'},
                'how': {'text': 'firearms'}
            })
        
        article_data = {
            'id': 'TEST_001',
            'text': 'Test article',
            'source': 'test'
        }
        
        # Measure formatting time
        start_time = time.time()
        df = formatter.format_events('TEST_001', article_data, events)
        format_time = time.time() - start_time
        
        # Should complete quickly
        self.assertLess(format_time, 1.0)  # 1 second max for 100 events
        
        # Should generate correct output
        self.assertEqual(len(df), 100)
        self.assertIn('Event_ID', df.columns)
        self.assertIn('Actor_Text', df.columns)
    
    def test_scalability_benchmarks(self):
        """Test scalability with increasing data sizes."""
        # Test with different batch sizes
        batch_sizes = [1, 5, 10, 20, 50]
        
        for batch_size in batch_sizes:
            articles = [
                {'id': f'ART_{i:03d}', 'text': f'Article {i} content'} 
                for i in range(batch_size)
            ]
            
            # Mock components
            mock_pipeline = Mock()
            mock_extractor = Mock()
            formatter = AnnotationFormatter()
            
            mock_pipeline.process_article.return_value = {'sentences': []}
            mock_extractor.extract_events.return_value = []
            
            batch_processor = BatchProcessor(
                mock_pipeline, mock_extractor, formatter, self.temp_dir
            )
            
            # Measure processing time
            start_time = time.time()
            results = batch_processor.process_articles(articles)
            processing_time = time.time() - start_time
            
            # Should process all articles
            self.assertEqual(results['total_articles'], batch_size)
            self.assertEqual(results['processed'], batch_size)
            
            # Should scale reasonably (linear or sub-linear)
            if batch_size > 1:
                time_per_article = processing_time / batch_size
                self.assertLess(time_per_article, 1.0)  # Max 1 second per article
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        # Create large dataset
        large_articles = []
        for i in range(100):
            large_articles.append({
                'id': f'LARGE_{i:03d}',
                'text': 'Militants attacked village. ' * 100,  # ~3k characters each
                'source': 'test'
            })
        
        # Mock components
        mock_pipeline = Mock()
        mock_extractor = Mock()
        formatter = AnnotationFormatter()
        
        mock_pipeline.process_article.return_value = {'sentences': []}
        mock_extractor.extract_events.return_value = []
        
        batch_processor = BatchProcessor(
            mock_pipeline, mock_extractor, formatter, self.temp_dir
        )
        
        # Process large dataset
        start_time = time.time()
        results = batch_processor.process_articles(large_articles)
        processing_time = time.time() - start_time
        
        # Should handle large dataset
        self.assertEqual(results['total_articles'], 100)
        self.assertEqual(results['processed'], 100)
        
        # Should complete within reasonable time
        self.assertLess(processing_time, 30.0)  # 30 seconds max for 100 large articles
        
        # Calculate throughput
        throughput = results['total_articles'] / processing_time
        self.assertGreater(throughput, 1.0)  # At least 1 article per second

if __name__ == '__main__':
    unittest.main()
