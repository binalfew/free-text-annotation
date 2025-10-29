import json
import requests
from pathlib import Path
from typing import Dict, List
import logging


class CoreNLPWrapper:
    """Stanford CoreNLP server wrapper with full NLP capabilities."""

    def __init__(self, corenlp_path: str, memory: str = '4g'):
        """
        Initialize Stanford CoreNLP wrapper.

        Args:
            corenlp_path: Path to Stanford CoreNLP directory
            memory: Memory allocation for server (e.g., '4g', '6g')

        Raises:
            FileNotFoundError: If CoreNLP directory not found
            ConnectionError: If cannot connect to CoreNLP server
        """
        self.corenlp_path = Path(corenlp_path).expanduser()
        self.memory = memory
        self.logger = logging.getLogger(__name__)
        self.server_url = "http://localhost:9000"

        # Check if CoreNLP directory exists
        if not self.corenlp_path.exists():
            raise FileNotFoundError(
                f"Stanford CoreNLP not found at: {self.corenlp_path}\n"
                f"Please ensure Stanford CoreNLP is downloaded and extracted."
            )

        # Try to connect to Stanford CoreNLP server
        try:
            response = requests.get(self.server_url, timeout=2)
            self.logger.info("✓ Connected to Stanford CoreNLP server")
        except (requests.ConnectionError, requests.Timeout) as e:
            raise ConnectionError(
                f"Cannot connect to Stanford CoreNLP server at {self.server_url}\n"
                f"Please start the server using: ./start_corenlp_server.sh"
            ) from e

    def annotate(self, text: str) -> Dict:
        """
        Annotate text using Stanford CoreNLP server.

        Uses full annotator pipeline: tokenize, ssplit, pos, lemma, ner, depparse, coref

        Args:
            text: Text to annotate

        Returns:
            Dict containing:
                - sentences: List of annotated sentences with tokens, NER, dependencies
                - coref_chains: Coreference resolution chains

        Raises:
            Exception: If server returns error status
        """
        if not text or not text.strip():
            return {'sentences': [], 'coref_chains': []}

        properties = {
            'annotators': 'tokenize,ssplit,pos,lemma,ner,depparse,coref',
            'outputFormat': 'json',
            'coref.algorithm': 'statistical'
        }

        response = requests.post(
            self.server_url,
            params={'properties': json.dumps(properties)},
            data=text.encode('utf-8'),
            headers={'Content-Type': 'text/plain; charset=utf-8'},
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Server returned status {response.status_code}")

        result = response.json()

        # Process sentences to match our expected format
        processed_sentences = []
        for sent in result.get('sentences', []):
            tokens = []
            for token in sent.get('tokens', []):
                tokens.append({
                    'index': token.get('index'),
                    'word': token.get('word'),
                    'originalText': token.get('originalText'),
                    'lemma': token.get('lemma'),
                    'pos': token.get('pos'),
                    'ner': token.get('ner', 'O')
                })

            # Extract dependencies
            dependencies = []
            for dep in sent.get('basicDependencies', []):
                dependencies.append({
                    'dep': dep.get('dep'),
                    'governor': dep.get('governorGloss'),
                    'dependent': dep.get('dependentGloss'),
                    'governor_idx': dep.get('governor'),
                    'dependent_idx': dep.get('dependent')
                })

            processed_sentences.append({
                'index': sent.get('index'),
                'tokens': tokens,
                'basicDependencies': dependencies
            })

        # Extract coreference chains
        coref_chains = []
        if 'corefs' in result:
            for chain_id, mentions in result['corefs'].items():
                chain = {
                    'id': chain_id,
                    'mentions': []
                }
                for mention in mentions:
                    chain['mentions'].append({
                        'sentNum': mention.get('sentNum'),
                        'startIndex': mention.get('startIndex'),
                        'endIndex': mention.get('endIndex'),
                        'text': mention.get('text'),
                        'type': mention.get('type'),
                        'isRepresentative': mention.get('isRepresentativeMention', False)
                    })
                coref_chains.append(chain)

        return {
            'sentences': processed_sentences,
            'coref_chains': coref_chains
        }

    def get_tokens(self, sentence: Dict) -> List[Dict]:
        """Extract tokens from sentence annotation."""
        return sentence.get('tokens', [])

    def get_entities(self, sentence: Dict) -> List[Dict]:
        """Extract named entities from sentence annotation."""
        entities: List[Dict] = []
        tokens = sentence.get('tokens', [])

        current_entity = None
        current_text: List[str] = []

        for token in tokens:
            ner_tag = token.get('ner', 'O')

            if ner_tag != 'O':
                if current_entity == ner_tag:
                    current_text.append(token['word'])
                else:
                    if current_entity:
                        entities.append({'text': ' '.join(current_text), 'type': current_entity})
                    current_entity = ner_tag
                    current_text = [token['word']]
            else:
                if current_entity:
                    entities.append({'text': ' '.join(current_text), 'type': current_entity})
                    current_entity = None
                    current_text = []

        if current_entity:
            entities.append({'text': ' '.join(current_text), 'type': current_entity})

        return entities

    def get_dependencies(self, sentence: Dict) -> List[Dict]:
        """Extract dependency relations from sentence annotation."""
        deps = sentence.get('basicDependencies', [])
        result = []
        for dep in deps:
            result.append({
                'relation': dep.get('dep', ''),
                'governor': dep.get('governorGloss', ''),
                'dependent': dep.get('dependentGloss', ''),
                'dep': dep.get('dep', ''),  # Keep for compatibility
            })
        return result

    def close(self):
        """Close resources (no-op for HTTP client)."""
        pass
