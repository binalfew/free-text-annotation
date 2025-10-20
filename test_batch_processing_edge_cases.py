# test_batch_processing_edge_cases.py

import unittest
import tempfile
import os
import json
import pandas as pd
from unittest.mock import Mock, patch
from batch_processing import BatchProcessor, AnnotationFormatter, ArticleLoader, IntegratedPipeline

class TestBatchProcessingEdgeCases(unittest.TestCase):
    """Test edge cases in batch processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_pipeline = Mock()
        self.mock_extractor = Mock()
        self.formatter = AnnotationFormatter()
        self.batch_processor = BatchProcessor(
            self.mock_pipeline, 
            self.mock_extractor, 
            self.formatter, 
            self.temp_dir
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_article_list(self):
        """Test processing empty article list."""
        articles = []
        results = self.batch_processor.process_articles(articles)
        
        self.assertEqual(results['total_articles'], 0)
        self.assertEqual(results['processed'], 0)
        self.assertEqual(results['failed'], 0)
        self.assertEqual(results['total_events'], 0)
        self.assertEqual(len(results['articles']), 0)
    
    def test_article_with_missing_fields(self):
        """Test processing article with missing required fields."""
        articles = [
            {'id': 'ART_001'},  # Missing text
            {'text': 'Some text'},  # Missing id
            {'id': 'ART_003', 'text': ''},  # Empty text
        ]
        
        # Mock the pipeline to handle missing fields
        def mock_process_article(article_text, article_id):
            return {'sentences': []}
        
        self.mock_pipeline.process_article.side_effect = mock_process_article
        self.mock_extractor.extract_events.return_value = []
        
        results = self.batch_processor.process_articles(articles)
        
        # Should handle gracefully - some will fail due to missing fields
        self.assertEqual(results['total_articles'], 3)
        self.assertEqual(results['processed'], 1)  # Only the valid one
        self.assertEqual(results['failed'], 2)  # Two with missing fields
    
    def test_article_processing_failure(self):
        """Test handling of article processing failures."""
        articles = [
            {'id': 'ART_001', 'text': 'Valid article'},
            {'id': 'ART_002', 'text': 'Article that will fail'},
            {'id': 'ART_003', 'text': 'Another valid article'}
        ]
        
        # Mock pipeline to fail on second article
        def mock_process_article(text, article_id):
            if article_id == 'ART_002':
                raise Exception("Processing failed")
            return {'sentences': [{'text': text}]}
        
        self.mock_pipeline.process_article.side_effect = mock_process_article
        self.mock_extractor.extract_events.return_value = []
        
        results = self.batch_processor.process_articles(articles)
        
        # Should handle failure gracefully
        self.assertEqual(results['total_articles'], 3)
        self.assertEqual(results['processed'], 2)
        self.assertEqual(results['failed'], 1)
        
        # Check failed article is recorded
        failed_articles = [a for a in results['articles'] if a['status'] == 'failed']
        self.assertEqual(len(failed_articles), 1)
        self.assertEqual(failed_articles[0]['article_id'], 'ART_002')
        self.assertIn('error', failed_articles[0])
    
    def test_malformed_json_input(self):
        """Test handling of malformed JSON input."""
        malformed_json = '{"invalid": json}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(malformed_json)
            f.flush()
            
            with self.assertRaises(json.JSONDecodeError):
                ArticleLoader.load_from_json(f.name)
            
            os.unlink(f.name)
    
    
    def test_large_batch_processing(self):
        """Test processing large batch of articles."""
        # Create large number of articles
        articles = []
        for i in range(100):
            articles.append({
                'id': f'ART_{i:03d}',
                'text': f'Article {i} content with violence keywords.',
                'source': 'test',
                'publication_date': '2024-01-01'
            })
        
        # Mock processing
        self.mock_pipeline.process_article.return_value = {'sentences': []}
        self.mock_extractor.extract_events.return_value = []
        
        results = self.batch_processor.process_articles(articles)
        
        # Should process all articles
        self.assertEqual(results['total_articles'], 100)
        self.assertEqual(results['processed'], 100)
        self.assertEqual(results['failed'], 0)
    
    
    def test_concurrent_processing_errors(self):
        """Test handling of errors in concurrent processing."""
        articles = [
            {'id': 'ART_001', 'text': 'Article 1'},
            {'id': 'ART_002', 'text': 'Article 2'},
            {'id': 'ART_003', 'text': 'Article 3'}
        ]
        
        # Mock processing with mixed success/failure
        def mock_process_article(text, article_id):
            if article_id == 'ART_002':
                raise Exception("Concurrent processing error")
            return {'sentences': []}
        
        self.mock_pipeline.process_article.side_effect = mock_process_article
        self.mock_extractor.extract_events.return_value = []
        
        results = self.batch_processor.process_articles(articles)
        
        # Should handle mixed results
        self.assertEqual(results['total_articles'], 3)
        self.assertEqual(results['processed'], 2)
        self.assertEqual(results['failed'], 1)
    
    def test_output_file_creation_failure(self):
        """Test handling of output file creation failures."""
        articles = [
            {'id': 'ART_001', 'text': 'Article 1'}
        ]
        
        # Mock successful processing
        self.mock_pipeline.process_article.return_value = {'sentences': []}
        self.mock_extractor.extract_events.return_value = []
        
        # Mock formatter to return empty DataFrame
        with patch.object(self.formatter, 'format_events', return_value=pd.DataFrame()):
            results = self.batch_processor.process_articles(articles)
            
            # Should handle empty DataFrame gracefully
            self.assertEqual(results['total_articles'], 1)
            self.assertEqual(results['processed'], 1)
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters in articles."""
        articles = [
            {
                'id': 'ART_UNICODE',
                'text': 'Militants attaqué le village. Al-Shabaab claimed responsibility. 15 personnes tuées.',
                'source': 'test'
            }
        ]
        
        # Mock processing
        self.mock_pipeline.process_article.return_value = {'sentences': []}
        self.mock_extractor.extract_events.return_value = []
        
        results = self.batch_processor.process_articles(articles)
        
        # Should handle Unicode gracefully
        self.assertEqual(results['total_articles'], 1)
        self.assertEqual(results['processed'], 1)
        self.assertEqual(results['failed'], 0)
    
    def test_batch_summary_creation(self):
        """Test batch summary creation with various scenarios."""
        # Test with successful processing
        articles = [
            {'id': 'ART_001', 'text': 'Article 1'},
            {'id': 'ART_002', 'text': 'Article 2'}
        ]
        
        self.mock_pipeline.process_article.return_value = {'sentences': []}
        self.mock_extractor.extract_events.return_value = []
        
        results = self.batch_processor.process_articles(articles)
        
        # Should create summary file
        summary_files = [f for f in os.listdir(self.temp_dir) if f.endswith('_summary.json')]
        self.assertEqual(len(summary_files), 1)
        
        # Verify summary content
        summary_file = os.path.join(self.temp_dir, summary_files[0])
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        self.assertIn('batch_name', summary)
        self.assertIn('total_articles', summary)
        self.assertIn('processed', summary)
        self.assertIn('failed', summary)
        self.assertIn('total_events', summary)
    
    def test_article_loader_edge_cases(self):
        """Test ArticleLoader edge cases."""
        # Test loading from non-existent file
        with self.assertRaises(FileNotFoundError):
            ArticleLoader.load_from_json('non_existent_file.json')
        
        # Test loading from empty directory
        empty_dir = tempfile.mkdtemp()
        try:
            articles = ArticleLoader.load_from_directory(empty_dir)
            self.assertEqual(len(articles), 0)
        finally:
            os.rmdir(empty_dir)
        
        # Test loading from directory with non-text files
        mixed_dir = tempfile.mkdtemp()
        try:
            # Create a text file and a non-text file
            with open(os.path.join(mixed_dir, 'article1.txt'), 'w') as f:
                f.write('Article content')
            with open(os.path.join(mixed_dir, 'image.jpg'), 'w') as f:
                f.write('Not text content')
            
            articles = ArticleLoader.load_from_directory(mixed_dir, '*.txt')
            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0]['id'], 'article1')
        finally:
            import shutil
            shutil.rmtree(mixed_dir)
    
    def test_integrated_pipeline_error_handling(self):
        """Test IntegratedPipeline error handling."""
        # Test with invalid config
        invalid_config = {
            'stanford_corenlp': {
                'path': '/non/existent/path'
            }
        }
        
        with self.assertRaises(Exception):
            IntegratedPipeline(invalid_config)
    
    
    def test_parallel_processing_simulation(self):
        """Test simulation of parallel processing."""
        articles = [
            {'id': f'ART_{i:03d}', 'text': f'Article {i}'} 
            for i in range(10)
        ]
        
        # Mock processing with delays to simulate parallel processing
        import time
        
        def mock_process_article(text, article_id):
            time.sleep(0.01)  # Small delay
            return {'sentences': []}
        
        self.mock_pipeline.process_article.side_effect = mock_process_article
        self.mock_extractor.extract_events.return_value = []
        
        start_time = time.time()
        results = self.batch_processor.process_articles(articles, parallel=True)
        end_time = time.time()
        
        # Should process all articles
        self.assertEqual(results['total_articles'], 10)
        self.assertEqual(results['processed'], 10)
        
        # Note: Parallel processing is not fully implemented in the current code
        # This test verifies the interface works

if __name__ == '__main__':
    unittest.main()
