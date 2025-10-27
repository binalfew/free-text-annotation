#!/usr/bin/env python3
"""
Comprehensive tests for the enhanced text cleaner.
"""

import unittest
import logging
from preprocessing.text_cleaner import TextCleaner

class TestEnhancedTextCleaner(unittest.TestCase):
    """Test enhanced text cleaning functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        logging.basicConfig(level=logging.DEBUG)
        self.cleaner = TextCleaner(enable_logging=True)
    
    def test_basic_html_cleaning(self):
        """Test basic HTML tag removal."""
        html_text = """
        <html>
        <head><title>Breaking News</title></head>
        <body>
        <h1>Violence in Nigeria</h1>
        <p>Armed militants attacked a village.</p>
        <div>Advertisement</div>
        </body>
        </html>
        """
        
        cleaned = self.cleaner.clean(html_text)
        
        self.assertNotIn('<html>', cleaned)
        self.assertNotIn('<head>', cleaned)
        self.assertNotIn('<body>', cleaned)
        self.assertNotIn('<h1>', cleaned)
        self.assertNotIn('<p>', cleaned)
        self.assertNotIn('<div>', cleaned)
        self.assertIn('Violence in Nigeria', cleaned)
        self.assertIn('Armed militants attacked', cleaned)
    
    def test_african_news_article(self):
        """Test cleaning of typical African news article."""
        raw_text = """
        <html>
        <head><title>Boko Haram Attack in Maiduguri</title></head>
        <body>
        <h1>MAIDUGURI, Nigeria - At least 15 people were killed when suspected Boko Haram militants 
        attacked a village in northeastern Nigeria on Tuesday.</h1>
        <p>The attackers arrived at dawn and opened fire on residents. Witnesses said the gunmen 
        burned several houses before fleeing.</p>
        <p>Advertisement</p>
        <p>The U.N. condemned the violence and called for immediate action.</p>
        <div>Share on Facebook</div>
        <div>Related Articles:</div>
        </body>
        </html>
        """
        
        cleaned = self.cleaner.clean(raw_text)
        
        # Should preserve content
        self.assertIn('Boko Haram', cleaned)
        self.assertIn('Maiduguri', cleaned)
        self.assertIn('15 people were killed', cleaned)
        self.assertIn('U.N.', cleaned)
        
        # Should remove boilerplate
        self.assertNotIn('Advertisement', cleaned)
        self.assertNotIn('Share on Facebook', cleaned)
        self.assertNotIn('Related Articles:', cleaned)
    
    def test_encoding_issues(self):
        """Test handling of encoding issues."""
        text_with_encoding_issues = """
        He said "This is violence." She replied "No, it's not." 
        The situation was unclear. The attack occurred at 3:30 p.m.
        """
        
        cleaned = self.cleaner.clean(text_with_encoding_issues)
        
        # Should handle smart quotes
        self.assertIn('"This is violence."', cleaned)
        self.assertIn('"No, it\'s not."', cleaned)
        self.assertIn('3:30 p.m.', cleaned)
    
    def test_metadata_extraction(self):
        """Test metadata extraction."""
        text = """
        MAIDUGURI, Nigeria - At least 15 people were killed when suspected Boko Haram militants 
        attacked a village in northeastern Nigeria on Tuesday. By John Smith. (Reuters)
        """
        
        metadata = self.cleaner.extract_metadata(text)
        
        self.assertEqual(metadata['dateline_location'], 'MAIDUGURI, Nigeria')
        self.assertEqual(metadata['source'], 'Reuters')
        self.assertEqual(metadata['author'], 'John Smith')
        self.assertTrue(metadata['has_violence_content'])
        self.assertIn('Nigeria', metadata['african_entities'])
        self.assertGreater(metadata['quality_score'], 0)
    
    def test_african_entities_extraction(self):
        """Test African entities extraction."""
        text = """
        The attack occurred in Lagos, Nigeria. The militants also struck in Kano. 
        ECOWAS representatives visited the area. The U.N. condemned the violence.
        """
        
        metadata = self.cleaner.extract_metadata(text)
        
        self.assertIn('Nigeria', metadata['african_entities'])
        self.assertIn('Lagos', metadata['african_entities'])
        self.assertIn('Kano', metadata['african_entities'])
    
    def test_violence_content_detection(self):
        """Test violence content detection."""
        violent_text = "Armed militants attacked the village. They killed 15 civilians."
        peaceful_text = "The weather was nice today. People went to the market."
        
        violent_metadata = self.cleaner.extract_metadata(violent_text)
        peaceful_metadata = self.cleaner.extract_metadata(peaceful_text)
        
        self.assertTrue(violent_metadata['has_violence_content'])
        self.assertFalse(peaceful_metadata['has_violence_content'])
        self.assertGreater(violent_metadata['violence_indicators'], 0)
        self.assertEqual(peaceful_metadata['violence_indicators'], 0)
    
    def test_quality_score_calculation(self):
        """Test quality score calculation."""
        high_quality_text = """
        MAIDUGURI, Nigeria - At least 15 people were killed when suspected Boko Haram militants 
        attacked a village in northeastern Nigeria on Tuesday. The attackers arrived at dawn and 
        opened fire on residents. Witnesses said the gunmen burned several houses before fleeing.
        The U.N. condemned the violence and called for immediate action. ECOWAS representatives 
        are expected to visit the area.
        """
        
        low_quality_text = "Short text."
        
        high_quality_metadata = self.cleaner.extract_metadata(high_quality_text)
        low_quality_metadata = self.cleaner.extract_metadata(low_quality_text)
        
        self.assertGreater(high_quality_metadata['quality_score'], low_quality_metadata['quality_score'])
        self.assertGreaterEqual(high_quality_metadata['quality_score'], 0.5)
    
    def test_cleaning_statistics(self):
        """Test cleaning statistics."""
        original_text = """
        <html><body>
        <h1>Breaking News</h1>
        <p>Armed militants attacked a village.</p>
        <div>Advertisement</div>
        <div>Share on Facebook</div>
        </body></html>
        """
        
        cleaned_text = self.cleaner.clean(original_text)
        stats = self.cleaner.get_cleaning_statistics(original_text, cleaned_text)
        
        self.assertGreater(stats['original_length'], stats['cleaned_length'])
        self.assertGreater(stats['reduction_percentage'], 0)
        self.assertGreater(stats['html_tags_removed'], 0)
    
    def test_text_quality_validation(self):
        """Test text quality validation."""
        good_text = "This is a well-formed article with proper sentences. It has good content."
        bad_text = "SHORT"
        encoding_issues_text = "THIS TEXT HAS ENCODING ISSUES WITH ALL CAPS AND IS VERY LONG TO TRIGGER THE DETECTION"
        
        good_validation = self.cleaner.validate_text_quality(good_text)
        bad_validation = self.cleaner.validate_text_quality(bad_text)
        encoding_validation = self.cleaner.validate_text_quality(encoding_issues_text)
        
        self.assertTrue(good_validation['is_valid'])
        self.assertFalse(bad_validation['is_valid'])
        self.assertFalse(encoding_validation['is_valid'])
        
        self.assertIn('Text too short', bad_validation['issues'])
        self.assertIn('Possible encoding issues', encoding_validation['issues'])
    
    def test_duplicate_content_removal(self):
        """Test duplicate content removal."""
        text_with_duplicates = """
        First paragraph with unique content.
        Second paragraph with unique content.
        First paragraph with unique content.
        Third paragraph with unique content.
        """
        
        cleaned = self.cleaner.clean(text_with_duplicates)
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        
        # Should remove duplicates
        self.assertEqual(len(lines), 3)  # Only unique lines
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        text_with_whitespace = """
        This    has    multiple    spaces.
        
        And    multiple    newlines.
        
        
        """
        
        cleaned = self.cleaner.clean(text_with_whitespace)
        
        # Should normalize whitespace
        self.assertNotIn('    ', cleaned)  # No multiple spaces
        self.assertNotIn('\n\n\n', cleaned)  # No multiple newlines
    
    def test_boilerplate_removal(self):
        """Test boilerplate content removal."""
        text_with_boilerplate = """
        Breaking news article content here.
        Advertisement
        Share on Facebook
        Tweet this
        Related Articles:
        Read more:
        Copyright 2024
        All rights reserved
        """
        
        cleaned = self.cleaner.clean(text_with_boilerplate)
        
        # Should remove boilerplate
        self.assertNotIn('Advertisement', cleaned)
        self.assertNotIn('Share on Facebook', cleaned)
        self.assertNotIn('Tweet this', cleaned)
        self.assertNotIn('Related Articles:', cleaned)
        self.assertNotIn('Read more:', cleaned)
        self.assertNotIn('Copyright 2024', cleaned)
        self.assertNotIn('All rights reserved', cleaned)
        
        # Should preserve content
        self.assertIn('article content here', cleaned)
    
    def test_african_news_sources(self):
        """Test African news source detection."""
        text_with_sources = """
        By John Smith (Reuters)
        Source: BBC Africa
        Reporting by Jane Doe
        """
        
        metadata = self.cleaner.extract_metadata(text_with_sources)
        
        # Should detect sources
        self.assertIsNotNone(metadata['source'])
        self.assertIsNotNone(metadata['author'])
    
    def test_date_extraction(self):
        """Test date extraction."""
        text_with_dates = """
        Published on March 15, 2024
        Updated: 15/03/2024
        Date: 2024-03-15
        """
        
        metadata = self.cleaner.extract_metadata(text_with_dates)
        
        # Should extract at least one date
        self.assertIsNotNone(metadata['publication_date'])
    
    def test_empty_and_edge_cases(self):
        """Test edge cases and empty inputs."""
        # Empty text
        self.assertEqual(self.cleaner.clean(""), "")
        self.assertEqual(self.cleaner.clean("   "), "")
        
        # Only HTML
        html_only = "<html><body></body></html>"
        cleaned = self.cleaner.clean(html_only)
        self.assertEqual(cleaned.strip(), "")
        
        # Only boilerplate
        boilerplate_only = "Advertisement Share on Facebook"
        cleaned = self.cleaner.clean(boilerplate_only)
        self.assertEqual(cleaned.strip(), "")
    
    def test_preserve_quotes_option(self):
        """Test preserve quotes option."""
        cleaner_with_quotes = TextCleaner(preserve_quotes=True)
        cleaner_without_quotes = TextCleaner(preserve_quotes=False)
        
        text_with_quotes = 'He said "This is important." She replied "I agree."'
        
        cleaned_with_quotes = cleaner_with_quotes.clean(text_with_quotes)
        cleaned_without_quotes = cleaner_without_quotes.clean(text_with_quotes)
        
        # Both should preserve quotes for now (no difference in current implementation)
        self.assertIn('"This is important."', cleaned_with_quotes)
        self.assertIn('"I agree."', cleaned_with_quotes)

if __name__ == '__main__':
    unittest.main()
