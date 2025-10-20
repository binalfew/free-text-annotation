# stanford_nlp/corenlp_wrapper.py
import subprocess
import json
import os
import tempfile
from typing import Dict, List

class CoreNLPWrapper:
    def __init__(self, corenlp_path: str, memory: str = '4g'):
        """
        Initialize CoreNLP using direct Java command.
        
        Args:
            corenlp_path: Path to CoreNLP directory
            memory: Memory allocation (e.g., '4g')
        """
        self.corenlp_path = os.path.abspath(corenlp_path)
        self.memory = memory
        
        # Verify CoreNLP exists
        if not os.path.exists(self.corenlp_path):
            raise FileNotFoundError(f"CoreNLP not found at: {self.corenlp_path}")
        
        # Find the main JAR file
        jar_files = [f for f in os.listdir(self.corenlp_path) if f.endswith('.jar')]
        if not jar_files:
            raise FileNotFoundError(f"No JAR files found in {self.corenlp_path}")
        
        print(f"CoreNLP initialized at: {self.corenlp_path}")
        print(f"Memory: {memory}")
        
    def annotate(self, text: str) -> Dict:
        """
        Annotate text using CoreNLP.
        
        Args:
            text: Input text
            
        Returns:
            Annotation dictionary with sentences and tokens
        """
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as input_file:
            input_file.write(text)
            input_path = input_file.name
        
        # CoreNLP writes output to its working directory, so we need to construct the path there
        input_filename = os.path.basename(input_path)
        output_path = os.path.join(self.corenlp_path, input_filename + '.json')
        
        try:
            # Build classpath (all JARs in directory)
            classpath = os.path.join(self.corenlp_path, '*')
            
            # Build Java command
            cmd = [
                'java',
                f'-Xmx{self.memory}',
                '-cp', classpath,
                'edu.stanford.nlp.pipeline.StanfordCoreNLP',
                '-annotators', 'tokenize,ssplit,pos,lemma,ner,parse,depparse',
                '-outputFormat', 'json',
                '-file', input_path
            ]
            
            # Run CoreNLP process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.corenlp_path
            )
            
            # Wait for completion
            stdout, stderr = process.communicate(timeout=60)
            
            if process.returncode != 0:
                print(f"CoreNLP stderr: {stderr}")
                raise RuntimeError(f"CoreNLP failed with return code {process.returncode}")
            
            # Read JSON output from file
            if not os.path.exists(output_path):
                print(f"CoreNLP stdout: {stdout}")
                print(f"CoreNLP stderr: {stderr}")
                raise RuntimeError(f"CoreNLP did not create output file: {output_path}")
            
            with open(output_path, 'r') as f:
                result = json.load(f)
            
            return result
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("CoreNLP processing timeout (>60 seconds)")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON from CoreNLP: {e}")
        except Exception as e:
            raise RuntimeError(f"CoreNLP error: {e}")
        finally:
            # Cleanup temporary files
            try:
                if os.path.exists(input_path):
                    os.unlink(input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            except:
                pass
    
    def get_tokens(self, sentence: Dict) -> List[Dict]:
        """
        Extract tokens from sentence.
        
        Args:
            sentence: Sentence dictionary from CoreNLP
            
        Returns:
            List of token dictionaries
        """
        return sentence.get('tokens', [])
    
    def get_entities(self, sentence: Dict) -> List[Dict]:
        """
        Extract named entities from sentence.
        
        Args:
            sentence: Sentence dictionary from CoreNLP
            
        Returns:
            List of entity dictionaries with 'text' and 'type' keys
        """
        entities = []
        tokens = sentence.get('tokens', [])
        
        current_entity = None
        current_text = []
        
        for token in tokens:
            ner_tag = token.get('ner', 'O')
            
            if ner_tag != 'O':
                if current_entity == ner_tag:
                    # Continue current entity
                    current_text.append(token['word'])
                else:
                    # Save previous entity and start new one
                    if current_entity:
                        entities.append({
                            'text': ' '.join(current_text),
                            'type': current_entity
                        })
                    current_entity = ner_tag
                    current_text = [token['word']]
            else:
                # End of entity
                if current_entity:
                    entities.append({
                        'text': ' '.join(current_text),
                        'type': current_entity
                    })
                    current_entity = None
                    current_text = []
        
        # Save last entity if exists
        if current_entity:
            entities.append({
                'text': ' '.join(current_text),
                'type': current_entity
            })
        
        return entities
    
    def get_dependencies(self, sentence: Dict) -> List[Dict]:
        """
        Extract dependency relations from sentence.
        
        Args:
            sentence: Sentence dictionary from CoreNLP
            
        Returns:
            List of dependency dictionaries
        """
        deps = sentence.get('basicDependencies', [])
        return [
            {
                'relation': dep['dep'],
                'governor': dep['governorGloss'],
                'dependent': dep['dependentGloss']
            }
            for dep in deps
        ]
    
    def close(self):
        """
        Cleanup (no-op for subprocess approach).
        """
        pass