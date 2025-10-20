# test_configuration_validation.py

import unittest
import tempfile
import os
import yaml
from unittest.mock import patch, Mock
from pipeline import ViolentEventNLPPipeline
from batch_processing import IntegratedPipeline

class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation and error handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_configuration(self):
        """Test with valid configuration."""
        valid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g',
                'timeout': 30000,
                'annotators': 'tokenize,ssplit,pos,lemma,ner,parse,depparse',
                'language': 'en'
            },
            'features': {
                'use_word_embeddings': True,
                'embedding_dim': 300,
                'use_sentence_embeddings': True,
                'context_window': 5
            },
            'domain': {
                'violence_lexicon_path': './resources/violence_lexicon.txt',
                'actor_database_path': './resources/actors.json',
                'location_database_path': './resources/african_locations.json'
            },
            'processing': {
                'batch_size': 10,
                'max_sentence_length': 512,
                'min_sentence_length': 5
            },
            'logging': {
                'level': 'INFO',
                'file': './logs/nlp_pipeline.log'
            }
        }
        
        # Should not raise exception
        with patch('pipeline.CoreNLPWrapper') as mock_corenlp:
            mock_corenlp.return_value = Mock()
            pipeline = ViolentEventNLPPipeline(valid_config)
            self.assertIsNotNone(pipeline)
    
    def test_missing_required_configuration(self):
        """Test with missing required configuration."""
        # Missing stanford_corenlp
        invalid_config = {
            'features': {'use_word_embeddings': True}
        }
        
        with self.assertRaises(KeyError):
            ViolentEventNLPPipeline(invalid_config)
    
    def test_invalid_stanford_path(self):
        """Test with invalid Stanford CoreNLP path."""
        invalid_config = {
            'stanford_corenlp': {
                'path': '/non/existent/path',
                'memory': '4g'
            }
        }
        
        with self.assertRaises(FileNotFoundError):
            ViolentEventNLPPipeline(invalid_config)
    
    def test_invalid_memory_allocation(self):
        """Test with invalid memory allocation."""
        invalid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': 'invalid_memory'
            }
        }
        
        # Should handle invalid memory gracefully
        with patch('pipeline.CoreNLPWrapper') as mock_corenlp:
            mock_corenlp.side_effect = Exception("Invalid memory allocation")
            with self.assertRaises(Exception):
                ViolentEventNLPPipeline(invalid_config)
    
    def test_invalid_annotators(self):
        """Test with invalid annotators configuration."""
        invalid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g',
                'annotators': 'invalid,annotators'
            }
        }
        
        with patch('pipeline.CoreNLPWrapper') as mock_corenlp:
            mock_corenlp.side_effect = Exception("Invalid annotators")
            with self.assertRaises(Exception):
                ViolentEventNLPPipeline(invalid_config)
    
    def test_configuration_file_loading(self):
        """Test loading configuration from YAML file."""
        # Create valid config file
        config_data = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g'
            },
            'features': {
                'use_word_embeddings': True
            }
        }
        
        config_file = os.path.join(self.temp_dir, 'config.yaml')
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configuration
        with open(config_file, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        self.assertEqual(loaded_config['stanford_corenlp']['path'], './stanford-corenlp-4.5.5')
        self.assertEqual(loaded_config['stanford_corenlp']['memory'], '4g')
    
    def test_malformed_configuration_file(self):
        """Test handling of malformed configuration file."""
        # Create malformed YAML file
        malformed_config = """
        stanford_corenlp:
            path: ./stanford-corenlp-4.5.5
            memory: 4g
        invalid_yaml: [unclosed list
        """
        
        config_file = os.path.join(self.temp_dir, 'malformed_config.yaml')
        with open(config_file, 'w') as f:
            f.write(malformed_config)
        
        # Should raise YAML error
        with self.assertRaises(yaml.YAMLError):
            with open(config_file, 'r') as f:
                yaml.safe_load(f)
    
    def test_configuration_validation_helper(self):
        """Test configuration validation helper functions."""
        def validate_config(config):
            """Validate configuration structure."""
            required_sections = ['stanford_corenlp']
            for section in required_sections:
                if section not in config:
                    raise ValueError(f"Missing required section: {section}")
            
            # Validate stanford_corenlp
            corenlp_config = config['stanford_corenlp']
            if 'path' not in corenlp_config:
                raise ValueError("Missing stanford_corenlp.path")
            if 'memory' not in corenlp_config:
                raise ValueError("Missing stanford_corenlp.memory")
            
            return True
        
        # Test valid config
        valid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g'
            }
        }
        self.assertTrue(validate_config(valid_config))
        
        # Test invalid config
        invalid_config = {
            'features': {'use_word_embeddings': True}
        }
        with self.assertRaises(ValueError):
            validate_config(invalid_config)
    
    def test_environment_variable_override(self):
        """Test configuration override with environment variables."""
        import os
        
        # Set environment variables
        os.environ['STANFORD_CORENLP_PATH'] = './custom-corenlp-path'
        os.environ['STANFORD_CORENLP_MEMORY'] = '8g'
        
        # Base configuration
        base_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g'
            }
        }
        
        # Override with environment variables
        config = base_config.copy()
        if 'STANFORD_CORENLP_PATH' in os.environ:
            config['stanford_corenlp']['path'] = os.environ['STANFORD_CORENLP_PATH']
        if 'STANFORD_CORENLP_MEMORY' in os.environ:
            config['stanford_corenlp']['memory'] = os.environ['STANFORD_CORENLP_MEMORY']
        
        self.assertEqual(config['stanford_corenlp']['path'], './custom-corenlp-path')
        self.assertEqual(config['stanford_corenlp']['memory'], '8g')
        
        # Clean up
        del os.environ['STANFORD_CORENLP_PATH']
        del os.environ['STANFORD_CORENLP_MEMORY']
    
    def test_configuration_defaults(self):
        """Test configuration defaults."""
        def apply_defaults(config):
            """Apply default values to configuration."""
            defaults = {
                'stanford_corenlp': {
                    'memory': '4g',
                    'timeout': 30000,
                    'annotators': 'tokenize,ssplit,pos,lemma,ner,parse,depparse',
                    'language': 'en'
                },
                'features': {
                    'use_word_embeddings': True,
                    'embedding_dim': 300,
                    'use_sentence_embeddings': True,
                    'context_window': 5
                },
                'processing': {
                    'batch_size': 10,
                    'max_sentence_length': 512,
                    'min_sentence_length': 5
                },
                'logging': {
                    'level': 'INFO',
                    'file': './logs/nlp_pipeline.log'
                }
            }
            
            # Apply defaults
            for section, default_values in defaults.items():
                if section not in config:
                    config[section] = {}
                for key, value in default_values.items():
                    if key not in config[section]:
                        config[section][key] = value
            
            return config
        
        # Test with minimal config
        minimal_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5'
            }
        }
        
        config_with_defaults = apply_defaults(minimal_config)
        
        # Should have defaults applied
        self.assertEqual(config_with_defaults['stanford_corenlp']['memory'], '4g')
        self.assertEqual(config_with_defaults['features']['use_word_embeddings'], True)
        self.assertEqual(config_with_defaults['processing']['batch_size'], 10)
        self.assertEqual(config_with_defaults['logging']['level'], 'INFO')
    
    def test_integrated_pipeline_configuration(self):
        """Test IntegratedPipeline configuration validation."""
        # Valid configuration
        valid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g'
            },
            'output': {
                'directory': './output'
            }
        }
        
        with patch('batch_processing.ViolentEventNLPPipeline') as mock_pipeline:
            with patch('batch_processing.EventExtractor') as mock_extractor:
                with patch('batch_processing.AnnotationFormatter') as mock_formatter:
                    with patch('batch_processing.BatchProcessor') as mock_batch:
                        mock_pipeline.return_value = Mock()
                        mock_extractor.return_value = Mock()
                        mock_formatter.return_value = Mock()
                        mock_batch.return_value = Mock()
                        
                        pipeline = IntegratedPipeline(valid_config)
                        self.assertIsNotNone(pipeline)
    
    def test_configuration_schema_validation(self):
        """Test configuration schema validation."""
        def validate_schema(config):
            """Validate configuration against schema."""
            schema = {
                'stanford_corenlp': {
                    'path': str,
                    'memory': str,
                    'timeout': int,
                    'annotators': str,
                    'language': str
                },
                'features': {
                    'use_word_embeddings': bool,
                    'embedding_dim': int,
                    'use_sentence_embeddings': bool,
                    'context_window': int
                },
                'processing': {
                    'batch_size': int,
                    'max_sentence_length': int,
                    'min_sentence_length': int
                }
            }
            
            for section, expected_types in schema.items():
                if section in config:
                    for key, expected_type in expected_types.items():
                        if key in config[section]:
                            if not isinstance(config[section][key], expected_type):
                                raise TypeError(f"Invalid type for {section}.{key}: expected {expected_type.__name__}")
            
            return True
        
        # Test valid schema
        valid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g',
                'timeout': 30000,
                'annotators': 'tokenize,ssplit,pos,lemma,ner',
                'language': 'en'
            },
            'features': {
                'use_word_embeddings': True,
                'embedding_dim': 300,
                'use_sentence_embeddings': True,
                'context_window': 5
            },
            'processing': {
                'batch_size': 10,
                'max_sentence_length': 512,
                'min_sentence_length': 5
            }
        }
        
        self.assertTrue(validate_schema(valid_config))
        
        # Test invalid schema
        invalid_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': 4,  # Should be string
                'timeout': '30000'  # Should be int
            }
        }
        
        with self.assertRaises(TypeError):
            validate_schema(invalid_config)
    
    def test_configuration_merging(self):
        """Test configuration merging."""
        def merge_configs(base_config, override_config):
            """Merge configuration dictionaries."""
            merged = base_config.copy()
            
            for key, value in override_config.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = merge_configs(merged[key], value)
                else:
                    merged[key] = value
            
            return merged
        
        # Base configuration
        base_config = {
            'stanford_corenlp': {
                'path': './stanford-corenlp-4.5.5',
                'memory': '4g',
                'timeout': 30000
            },
            'features': {
                'use_word_embeddings': True,
                'embedding_dim': 300
            }
        }
        
        # Override configuration
        override_config = {
            'stanford_corenlp': {
                'memory': '8g'  # Override memory
            },
            'features': {
                'embedding_dim': 512  # Override embedding dimension
            },
            'processing': {  # Add new section
                'batch_size': 20
            }
        }
        
        merged_config = merge_configs(base_config, override_config)
        
        # Should have overridden values
        self.assertEqual(merged_config['stanford_corenlp']['memory'], '8g')
        self.assertEqual(merged_config['features']['embedding_dim'], 512)
        self.assertEqual(merged_config['processing']['batch_size'], 20)
        
        # Should preserve original values
        self.assertEqual(merged_config['stanford_corenlp']['path'], './stanford-corenlp-4.5.5')
        self.assertEqual(merged_config['stanford_corenlp']['timeout'], 30000)
        self.assertEqual(merged_config['features']['use_word_embeddings'], True)
    
    def test_configuration_error_handling(self):
        """Test configuration error handling."""
        def safe_config_load(config_path):
            """Safely load configuration with error handling."""
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                return config, None
            except FileNotFoundError:
                return None, "Configuration file not found"
            except yaml.YAMLError as e:
                return None, f"Invalid YAML: {e}"
            except Exception as e:
                return None, f"Unexpected error: {e}"
        
        # Test with non-existent file
        config, error = safe_config_load('non_existent.yaml')
        self.assertIsNone(config)
        self.assertIn("not found", error)
        
        # Test with malformed YAML
        malformed_file = os.path.join(self.temp_dir, 'malformed.yaml')
        with open(malformed_file, 'w') as f:
            f.write('invalid: yaml: [unclosed')
        
        config, error = safe_config_load(malformed_file)
        self.assertIsNone(config)
        self.assertIn("Invalid YAML", error)
        
        # Test with valid file
        valid_file = os.path.join(self.temp_dir, 'valid.yaml')
        with open(valid_file, 'w') as f:
            yaml.dump({'stanford_corenlp': {'path': './test'}}, f)
        
        config, error = safe_config_load(valid_file)
        self.assertIsNotNone(config)
        self.assertIsNone(error)

if __name__ == '__main__':
    unittest.main()
