from typing import List, Dict
import logging
from pathlib import Path

# Import all components
from preprocessing.text_cleaner import TextCleaner
from preprocessing.sentence_splitter import SentenceSplitter
from stanford_nlp.corenlp_wrapper import CoreNLPWrapper
from features.lexical_features import LexicalFeatureExtractor
from features.syntactic_features import SyntacticFeatureExtractor
from domain_specific.violence_lexicon import ViolenceLexicon
from domain_specific.african_ner import AfricanNER

class ViolentEventNLPPipeline:
    """
    Complete NLP pipeline for violent event processing.
    """
    
    def __init__(self, config: Dict):
        """
        Initialize pipeline.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize components
        self.logger.info("Initializing NLP pipeline components...")
        
        self.text_cleaner = TextCleaner()
        self.sentence_splitter = SentenceSplitter()
        
        # Stanford CoreNLP
        corenlp_path = config.get('stanford_corenlp', {}).get('path', './stanford-corenlp')
        memory = config.get('stanford_corenlp', {}).get('memory', '4g')
        self.corenlp = CoreNLPWrapper(corenlp_path, memory)
        
        # Feature extractors
        self.violence_lexicon = ViolenceLexicon()
        self.lexical_features = LexicalFeatureExtractor(list(self.violence_lexicon.all_terms))
        self.syntactic_features = SyntacticFeatureExtractor()
        
        # Domain-specific NER
        self.african_ner = AfricanNER()
        
        self.logger.info("Pipeline initialization complete")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def process_article(self, article_text: str, article_id: str = None) -> Dict:
        """
        Process a complete article through the pipeline.
        
        Args:
            article_text: Raw article text
            article_id: Article identifier
            
        Returns:
            Processed article with all annotations
        """
        self.logger.info(f"Processing article: {article_id}")
        
        result = {
            'article_id': article_id,
            'original_text': article_text,
            'sentences': []
        }
        
        try:
            # Step 1: Clean text
            self.logger.debug("Cleaning text...")
            cleaned_text = self.text_cleaner.clean(article_text)
            result['cleaned_text'] = cleaned_text
            
            # Extract metadata
            metadata = self.text_cleaner.extract_metadata(cleaned_text)
            result['metadata'] = metadata
            
            # Step 2: Split into sentences
            self.logger.debug("Splitting sentences...")
            sentences = self.sentence_splitter.split(cleaned_text)
            result['num_sentences'] = len(sentences)
            
            # Step 3: Process each sentence
            for idx, sentence in enumerate(sentences):
                self.logger.debug(f"Processing sentence {idx+1}/{len(sentences)}")
                
                sentence_result = self.process_sentence(sentence, idx)
                result['sentences'].append(sentence_result)
            
            # Step 4: Article-level features
            result['article_features'] = self.extract_article_features(result)
            
            self.logger.info(f"Article processing complete: {len(sentences)} sentences")
            
        except Exception as e:
            self.logger.error(f"Error processing article: {e}")
            result['error'] = str(e)
        
        return result
    
    def process_sentence(self, sentence: str, sentence_idx: int) -> Dict:
        """
        Process a single sentence.
        
        Args:
            sentence: Sentence text
            sentence_idx: Sentence index in article
            
        Returns:
            Processed sentence with annotations
        """
        result = {
            'sentence_idx': sentence_idx,
            'text': sentence
        }
        
        try:
            # CoreNLP annotation
            annotation = self.corenlp.annotate(sentence)
            
            if annotation and 'sentences' in annotation:
                sent_ann = annotation['sentences'][0]
                
                # Extract tokens
                tokens = self.corenlp.get_tokens(sent_ann)
                result['tokens'] = tokens
                result['num_tokens'] = len(tokens)
                
                # Extract entities
                entities = self.corenlp.get_entities(sent_ann)
                
                # Enhance with African NER
                enhanced_entities = self.african_ner.enhance_ner(entities, sentence)
                result['entities'] = enhanced_entities
                
                # Extract dependencies
                dependencies = self.corenlp.get_dependencies(sent_ann)
                result['dependencies'] = dependencies
                
                # Extract features
                token_words = [t['word'] for t in tokens]
                
                # Lexical features
                lex_features = self.lexical_features.extract_features(token_words)
                result['lexical_features'] = lex_features
                
                # Syntactic features
                syn_features = self.syntactic_features.extract_features(tokens, dependencies)
                result['syntactic_features'] = syn_features
                
                # Violence indicators
                result['is_violence_sentence'] = lex_features.get('violence_term_count', 0) > 0
                
        except Exception as e:
            self.logger.error(f"Error processing sentence {sentence_idx}: {e}")
            result['error'] = str(e)
        
        return result
    
    def extract_article_features(self, article_result: Dict) -> Dict:
        """
        Extract article-level features.
        
        Args:
            article_result: Processed article
            
        Returns:
            Article-level features
        """
        features = {}
        
        sentences = article_result.get('sentences', [])
        
        # Count violence sentences
        violence_sentences = sum(1 for s in sentences if s.get('is_violence_sentence', False))
        features['num_violence_sentences'] = violence_sentences
        features['violence_sentence_ratio'] = violence_sentences / len(sentences) if sentences else 0
        
        # Aggregate entities
        all_entities = []
        for sent in sentences:
            all_entities.extend(sent.get('entities', []))
        
        # Count entity types
        from collections import Counter
        entity_types = Counter(e['type'] for e in all_entities)
        features['entity_counts'] = dict(entity_types)
        
        # Check for actors
        features['has_organization'] = entity_types.get('ORGANIZATION', 0) > 0
        features['has_person'] = entity_types.get('PERSON', 0) > 0
        features['has_location'] = entity_types.get('LOCATION', 0) > 0
        features['has_date'] = entity_types.get('DATE', 0) > 0
        
        return features
    
    def close(self):
        """Cleanup resources."""
        self.corenlp.close()
