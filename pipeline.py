from typing import List, Dict
import logging
from pathlib import Path

# Import all components
from preprocessing.text_cleaner import TextCleaner
from preprocessing.sentence_splitter import SentenceSplitter
from stanford_nlp.corenlp_wrapper import CoreNLPWrapper
from features.lexical_features import LexicalFeatureExtractor
from features.syntactic_features import SyntacticFeatureExtractor
from domain.violence_lexicon import ViolenceLexicon
from domain.african_ner import AfricanNER

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

        corenlp_config = self._validate_config()

        # Initialize components
        self.logger.info("Initializing NLP pipeline components...")

        self.text_cleaner = TextCleaner()
        self.sentence_splitter = SentenceSplitter()

        # Stanford CoreNLP (requires server running)
        corenlp_path = corenlp_config['path']
        memory = corenlp_config.get('memory', '4g')
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

    def _validate_config(self) -> Dict:
        """Validate that the minimal configuration is present."""
        if 'stanford_corenlp' not in self.config:
            raise KeyError("Missing 'stanford_corenlp' configuration section")

        corenlp_config = self.config['stanford_corenlp']
        if 'path' not in corenlp_config:
            raise KeyError("Missing 'stanford_corenlp.path' configuration value")

        return corenlp_config
    
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

            # Step 2: Annotate entire article with Stanford CoreNLP
            # This enables coreference resolution across sentences
            self.logger.debug("Annotating article with Stanford CoreNLP...")
            full_annotation = self.corenlp.annotate(cleaned_text)

            # Extract sentences from CoreNLP output
            sentences = full_annotation.get('sentences', [])
            result['num_sentences'] = len(sentences)

            # Extract coreference chains if available
            if 'coref_chains' in full_annotation:
                result['coref_chains'] = full_annotation['coref_chains']
                self.logger.debug(f"Extracted {len(full_annotation['coref_chains'])} coreference chains")

            # Process each sentence from CoreNLP
            for sent_ann in sentences:
                sent_idx = sent_ann.get('index', 0)
                sentence_result = self._process_corenlp_sentence(sent_ann, sent_idx)
                result['sentences'].append(sentence_result)

            # Step 3: Article-level features
            result['article_features'] = self.extract_article_features(result)

            self.logger.info(f"Article processing complete: {len(result['sentences'])} sentences")

        except Exception as e:
            self.logger.error(f"Error processing article: {e}")
            result['error'] = str(e)

        return result

    def _process_corenlp_sentence(self, sent_ann: Dict, sentence_idx: int) -> Dict:
        """
        Process a sentence annotation that came from Stanford CoreNLP server.

        Args:
            sent_ann: Sentence annotation from Stanford CoreNLP
            sentence_idx: Sentence index in article

        Returns:
            Processed sentence with all features
        """
        # Reconstruct sentence text from tokens
        tokens = sent_ann.get('tokens', [])
        sentence_text = ' '.join(t.get('word', '') for t in tokens)

        result = {
            'index': sentence_idx,
            'sentence_idx': sentence_idx,
            'text': sentence_text,
            'tokens': tokens,
            'num_tokens': len(tokens)
        }

        try:
            # Extract entities
            entities = self.corenlp.get_entities(sent_ann)

            # Enhance with African NER
            enhanced_entities = self.african_ner.enhance_ner(entities, sentence_text)
            result['entities'] = enhanced_entities

            # Extract dependencies
            dependencies = self.corenlp.get_dependencies(sent_ann)
            result['dependencies'] = dependencies

            # Store basic dependencies in both formats for compatibility
            result['basicDependencies'] = sent_ann.get('basicDependencies', [])

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
            self.logger.error(f"Error processing CoreNLP sentence {sentence_idx}: {e}")
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
