"""
BATCH PROCESSING AND OUTPUT FORMATTING
=======================================

Process multiple articles and format output to match annotation schema.

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

import pandas as pd
import json
from pathlib import Path
from typing import List, Dict
import logging
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

# ============================================================================
# Output Formatter
# ============================================================================

class AnnotationFormatter:
    """
    Format extracted events to match annotation template schema.
    """
    
    def __init__(self):
        """Initialize formatter."""
        self.logger = logging.getLogger(__name__)
    
    def format_events(self, article_id: str, article_data: Dict, 
                     extracted_events: List[Dict]) -> pd.DataFrame:
        """
        Format extracted events for annotation template.
        
        Args:
            article_id: Article identifier
            article_data: Article metadata (URL, source, date, text)
            extracted_events: List of extracted events
            
        Returns:
            DataFrame matching Event Records sheet format
        """
        records = []
        
        for event_idx, event in enumerate(extracted_events, 1):
            record = self._create_event_record(
                article_id, event_idx, article_data, event
            )
            records.append(record)
        
        if not records:
            self.logger.warning(f"No events extracted for {article_id}")
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        return df
    
    def _create_event_record(self, article_id: str, event_idx: int,
                           article_data: Dict, event: Dict) -> Dict:
        """Create single event record."""
        
        # Generate Event ID
        event_id = f"{article_id}_EVT_{event_idx:02d}"
        
        # Extract 5W1H components
        who = event.get('who', {}) or {}
        what = event.get('what', {}) or {}
        whom = event.get('whom', {}) or {}
        where = event.get('where', {}) or {}
        when = event.get('when', {}) or {}
        how = event.get('how', {}) or {}
        
        record = {
            # Identification
            'Event_ID': event_id,
            'Article_ID': article_id,
            'Event_Trigger_Text': event['trigger']['word'],
            'Sentence_Numbers': str(event['sentence_index'] + 1),
            'Event_Description': event.get('sentence_text', '')[:200],
            
            # Actor (Who)
            'Actor_Text': who.get('text', 'Unknown'),
            'Actor_Normalized': self._normalize_actor(who),
            'Actor_Type': self._classify_actor_type(who),
            'Actor_Confidence': 0.7,  # Placeholder - would calculate properly
            
            # Victim (Whom)
            'Victim_Text': whom.get('text', 'Not specified'),
            'Victim_Normalized': whom.get('text', 'Not specified'),
            'Victim_Type': whom.get('type', 'Unknown'),
            'Deaths': whom.get('deaths'),
            'Injuries': whom.get('injuries'),
            'Victim_Confidence': 0.7,
            
            # Location (Where)
            'Location_Text': where.get('text', 'Not specified'),
            'Location_Normalized': where.get('text', 'Not specified'),
            'Location_Specific': where.get('text', ''),
            'Location_City': '',
            'Location_State': '',
            'Location_Country': where.get('country', ''),
            'Location_Coordinates': '',
            'Location_Confidence': 0.7 if where.get('text') else 0.3,
            
            # Date (When)
            'Date_Text': when.get('text', 'Not specified'),
            'Date_Normalized': article_data.get('publication_date', ''),
            'Time_of_Day': self._extract_time_of_day(when),
            'Date_Confidence': 0.7 if when.get('text') else 0.3,
            
            # Weapon/Method (How)
            'Weapon_Text': how.get('text', 'Not specified'),
            'Weapon_Normalized': ', '.join(how.get('weapons', [])) if how else '',
            'Weapon_Category': self._classify_weapon(how),
            'Tactic': ', '.join(how.get('tactics', [])) if how else '',
            
            # Taxonomy (What) - Preliminary classification
            'Taxonomy_L1': self._classify_L1(what, who),
            'Taxonomy_L2': '',  # Would need ML classifier
            'Taxonomy_L3': '',  # Would need ML classifier
            'Taxonomy_L4': '',
            'Classification_Confidence': 0.5,  # Low until ML classifier trained
            'Alternative_Classification': '',
            
            # Quality Control
            'Multi_Label': False,
            'Flagged_for_Review': event.get('confidence', 0) < 0.5,
            'Notes': self._generate_notes(event)
        }
        
        return record
    
    def _normalize_actor(self, who: Dict) -> str:
        """Normalize actor name."""
        if not who or not who.get('text'):
            return 'Unknown'
        
        text = who['text']
        
        # If it's a known group, use that
        metadata = who.get('metadata', {})
        if metadata.get('known_group'):
            # Extract group name
            return text
        
        # Otherwise, use descriptive term
        return text
    
    def _classify_actor_type(self, who: Dict) -> str:
        """Classify actor type for controlled vocabulary."""
        if not who or not who.get('metadata'):
            return 'Unknown'
        
        actor_type = who['metadata'].get('type', 'unknown')
        
        # Map to controlled vocabulary
        type_mapping = {
            'state': 'State forces',
            'terrorist': 'Non-state armed group',
            'rebel': 'Non-state armed group',
            'criminal': 'Criminal organization',
            'unknown': 'Unknown'
        }
        
        return type_mapping.get(actor_type, 'Unknown')
    
    def _extract_time_of_day(self, when: Dict) -> str:
        """Extract time of day."""
        if not when or not when.get('text'):
            return 'Unknown'
        
        text_lower = when['text'].lower()
        
        if 'morning' in text_lower or 'dawn' in text_lower:
            return 'Morning'
        elif 'afternoon' in text_lower:
            return 'Afternoon'
        elif 'evening' in text_lower:
            return 'Evening'
        elif 'night' in text_lower:
            return 'Night'
        else:
            return 'Unknown'
    
    def _classify_weapon(self, how: Dict) -> str:
        """Classify weapon category."""
        if not how:
            return 'Unknown'
        
        weapons = how.get('weapons', [])
        if not weapons:
            return 'Unknown'
        
        weapons_str = ' '.join(weapons).lower()
        
        if any(w in weapons_str for w in ['gun', 'rifle', 'firearm']):
            return 'Firearms'
        elif any(w in weapons_str for w in ['bomb', 'explosive', 'ied', 'grenade']):
            return 'Explosives'
        elif any(w in weapons_str for w in ['knife', 'machete']):
            return 'Edged weapons'
        else:
            return 'Multiple'
    
    def _classify_L1(self, what: Dict, who: Dict) -> str:
        """Preliminary Level 1 taxonomy classification."""
        # This is a simple heuristic - real classification needs ML
        
        # Check actor type
        if who and who.get('metadata'):
            actor_type = who['metadata'].get('type', '')
            
            if actor_type in ['terrorist', 'rebel']:
                return 'Political Violence'
            elif actor_type == 'criminal':
                return 'Criminal Violence'
            elif actor_type == 'state':
                # Could be Political Repression or legitimate conflict
                return 'Political Violence'  # Simplified
        
        # Fallback
        return 'Political Violence'
    
    def _generate_notes(self, event: Dict) -> str:
        """Generate notes about extraction quality."""
        notes = []
        
        if event.get('confidence', 1.0) < 0.5:
            notes.append('Low confidence extraction')
        
        missing = []
        if not event.get('who'):
            missing.append('actor')
        if not event.get('whom'):
            missing.append('victim')
        if not event.get('where'):
            missing.append('location')
        
        if missing:
            notes.append(f"Missing: {', '.join(missing)}")
        
        return '; '.join(notes) if notes else ''


# ============================================================================
# Batch Processor
# ============================================================================

class BatchProcessor:
    """
    Process multiple articles in batch.
    """
    
    def __init__(self, pipeline, event_extractor, formatter,
                 output_dir: str = './output'):
        """
        Initialize batch processor.
        
        Args:
            pipeline: ViolentEventNLPPipeline instance
            event_extractor: EventExtractor instance
            formatter: AnnotationFormatter instance
            output_dir: Directory for output files
        """
        self.pipeline = pipeline
        self.extractor = event_extractor
        self.formatter = formatter
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def process_articles(self, articles: List[Dict], 
                        batch_name: str = None,
                        parallel: bool = False) -> Dict:
        """
        Process multiple articles.
        
        Args:
            articles: List of article dicts with 'id', 'text', 'url', etc.
            batch_name: Name for this batch
            parallel: Whether to use parallel processing
            
        Returns:
            Processing results summary
        """
        if batch_name is None:
            batch_name = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Processing {len(articles)} articles in batch: {batch_name}")
        
        results = {
            'batch_name': batch_name,
            'total_articles': len(articles),
            'processed': 0,
            'failed': 0,
            'total_events': 0,
            'articles': []
        }
        
        if parallel:
            results = self._process_parallel(articles, batch_name, results)
        else:
            results = self._process_sequential(articles, batch_name, results)
        
        # Save batch summary
        self._save_batch_summary(results)
        
        return results
    
    def _process_sequential(self, articles: List[Dict], 
                          batch_name: str, results: Dict) -> Dict:
        """Process articles sequentially."""
        
        all_event_records = []
        
        for article in articles:
            try:
                article_result = self._process_single_article(article)
                
                results['articles'].append(article_result)
                results['processed'] += 1
                results['total_events'] += article_result['num_events']
                
                # Collect event records
                if article_result.get('event_records') is not None:
                    all_event_records.append(article_result['event_records'])
                
                article_id = article.get('id', 'unknown')
                self.logger.info(
                    f"Processed {article_id}: {article_result['num_events']} events"
                )
                
            except Exception as e:
                article_id = article.get('id', 'unknown')
                self.logger.error(f"Failed to process {article_id}: {e}")
                results['failed'] += 1
                results['articles'].append({
                    'article_id': article_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Combine all event records into single DataFrame
        if all_event_records:
            combined_df = pd.concat(all_event_records, ignore_index=True)
            output_file = self.output_dir / f"{batch_name}_events.xlsx"
            combined_df.to_excel(output_file, index=False, sheet_name='Event Records')
            results['output_file'] = str(output_file)
            self.logger.info(f"Saved {len(combined_df)} events to {output_file}")
        
        return results
    
    def _process_parallel(self, articles: List[Dict],
                         batch_name: str, results: Dict) -> Dict:
        """Process articles in parallel."""
        # Parallel processing would close/reopen CoreNLP for each process
        # For now, use sequential; parallel is more complex with CoreNLP
        self.logger.warning("Parallel processing not fully implemented; using sequential")
        return self._process_sequential(articles, batch_name, results)
    
    def _process_single_article(self, article: Dict) -> Dict:
        """
        Process single article through complete pipeline.
        
        Args:
            article: Article dict with 'id', 'text', metadata
            
        Returns:
            Processing result
        """
        article_id = article['id']
        article_text = article['text']
        
        # Step 1: NLP Pipeline
        nlp_result = self.pipeline.process_article(article_text, article_id)
        
        # Step 2: Event Extraction
        events = self.extractor.extract_events(nlp_result)
        
        # Step 3: Format for annotation template
        event_df = self.formatter.format_events(article_id, article, events)
        
        result = {
            'article_id': article_id,
            'status': 'success',
            'num_events': len(events),
            'event_records': event_df,
            'processing_time': None  # Could add timing
        }
        
        return result
    
    def _save_batch_summary(self, results: Dict):
        """Save batch processing summary."""
        summary_file = self.output_dir / f"{results['batch_name']}_summary.json"
        
        # Remove DataFrames for JSON serialization
        summary = results.copy()
        for article in summary['articles']:
            if 'event_records' in article:
                del article['event_records']
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Batch summary saved to {summary_file}")


# ============================================================================
# Article Loader
# ============================================================================

class ArticleLoader:
    """
    Load articles from various sources.
    """
    
    @staticmethod
    def load_from_json(file_path: str) -> List[Dict]:
        """
        Load articles from JSON file.
        
        Expected format:
        [
            {
                "id": "ART_001",
                "url": "https://...",
                "title": "...",
                "text": "...",
                "source": "Reuters",
                "publication_date": "2024-03-20"
            },
            ...
        ]
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            articles = json.load(f)
        return articles
    
    @staticmethod
    def load_from_csv(file_path: str) -> List[Dict]:
        """
        Load articles from CSV.
        
        Expected columns: id, url, title, text, source, publication_date
        """
        df = pd.read_csv(file_path)
        articles = df.to_dict('records')
        return articles
    
    @staticmethod
    def load_from_directory(dir_path: str, pattern: str = '*.txt') -> List[Dict]:
        """
        Load articles from text files in directory.
        
        Each file = one article, filename = article ID
        """
        articles = []
        dir_path = Path(dir_path)
        
        for file_path in dir_path.glob(pattern):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            article = {
                'id': file_path.stem,  # Filename without extension
                'text': text,
                'source': 'file',
                'publication_date': None
            }
            articles.append(article)
        
        return articles


# ============================================================================
# Complete Pipeline Integration
# ============================================================================

class IntegratedPipeline:
    """
    Complete integrated system: NLP → Extraction → Formatting
    """
    
    def __init__(self, config: Dict):
        """
        Initialize complete pipeline.
        
        Args:
            config: Configuration dict
        """
        self.logger = self._setup_logging()
        
        # Import components (would normally be at top)
        from pipeline import ViolentEventNLPPipeline
        from event_extraction import EventExtractor
        from domain.violence_lexicon import ViolenceLexicon
        from domain.african_ner import AfricanNER
        
        # Initialize NLP pipeline
        self.logger.info("Initializing NLP pipeline...")
        self.nlp_pipeline = ViolentEventNLPPipeline(config)
        
        # Initialize event extractor
        self.logger.info("Initializing event extractor...")
        lexicon = ViolenceLexicon()
        ner = AfricanNER()
        self.event_extractor = EventExtractor(lexicon, ner)
        
        # Initialize formatter
        self.formatter = AnnotationFormatter()
        
        # Initialize batch processor
        output_dir = config.get('output', {}).get('directory', './output')
        self.batch_processor = BatchProcessor(
            self.nlp_pipeline,
            self.event_extractor,
            self.formatter,
            output_dir
        )
        
        self.logger.info("Pipeline initialization complete!")
    
    def _setup_logging(self):
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def process_from_file(self, input_file: str, file_type: str = 'json') -> Dict:
        """
        Process articles from file.
        
        Args:
            input_file: Path to input file
            file_type: 'json', 'csv', or 'directory'
            
        Returns:
            Processing results
        """
        self.logger.info(f"Loading articles from {input_file}")
        
        # Load articles
        if file_type == 'json':
            articles = ArticleLoader.load_from_json(input_file)
        elif file_type == 'csv':
            articles = ArticleLoader.load_from_csv(input_file)
        elif file_type == 'directory':
            articles = ArticleLoader.load_from_directory(input_file)
        else:
            raise ValueError(f"Unknown file_type: {file_type}")
        
        self.logger.info(f"Loaded {len(articles)} articles")
        
        # Process batch
        results = self.batch_processor.process_articles(articles)
        
        return results
    
    def process_single(self, article_id: str, article_text: str) -> pd.DataFrame:
        """
        Process single article and return DataFrame.
        
        Args:
            article_id: Article identifier
            article_text: Article text
            
        Returns:
            DataFrame with extracted events
        """
        article = {
            'id': article_id,
            'text': article_text,
            'source': 'manual',
            'publication_date': None
        }
        
        result = self.batch_processor._process_single_article(article)
        return result['event_records']
    
    def close(self):
        """Cleanup resources."""
        self.nlp_pipeline.close()


# ============================================================================
# Main Script
# ============================================================================

def main():
    """
    Main execution script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Process articles through event extraction pipeline')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--type', default='json', choices=['json', 'csv', 'directory'],
                       help='Input file type')
    parser.add_argument('--config', default='config.yaml', help='Configuration file')
    parser.add_argument('--output', default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Load config
    config = {
        'stanford_corenlp': {
            'path': './stanford-corenlp-4.5.5',
            'memory': '4g'
        },
        'output': {
            'directory': args.output
        }
    }
    
    # Initialize pipeline
    print("Initializing integrated pipeline...")
    pipeline = IntegratedPipeline(config)
    
    # Process articles
    print(f"Processing articles from {args.input}...")
    results = pipeline.process_from_file(args.input, args.type)
    
    # Print summary
    print("\n" + "="*70)
    print("PROCESSING SUMMARY")
    print("="*70)
    print(f"Total articles: {results['total_articles']}")
    print(f"Successfully processed: {results['processed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total events extracted: {results['total_events']}")
    print(f"Output file: {results.get('output_file', 'N/A')}")
    print("="*70)
    
    # Cleanup
    pipeline.close()
    print("\nProcessing complete!")


if __name__ == '__main__':
    main()
