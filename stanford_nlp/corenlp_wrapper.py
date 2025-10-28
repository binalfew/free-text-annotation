import re
from pathlib import Path
from typing import Dict, List


class CoreNLPWrapper:
    """Lightweight stand-in for the Stanford CoreNLP pipeline."""

    _TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)
    _LOCATION_TERMS = {
        'africa', 'nigeria', 'kenya', 'somalia', 'ethiopia', 'mali',
        'sudan', 'south', 'uganda', 'ghana', 'maiduguri', 'lagos',
        'nairobi', 'mogadishu'
    }
    _ORGANISATION_TERMS = {
        'un', 'au', 'boko', 'haram', 'al-shabaab', 'army', 'military'
    }

    def __init__(self, corenlp_path: str, memory: str = '4g', *, allow_fallback: bool | None = None):
        self.corenlp_path = Path(corenlp_path).expanduser()
        self.memory = memory

        if allow_fallback is None:
            allow_fallback = not self.corenlp_path.is_absolute()

        if not self.corenlp_path.exists() and not allow_fallback:
            raise FileNotFoundError(f"CoreNLP not found at: {self.corenlp_path}")

        self._has_real_corenlp = self.corenlp_path.exists()

    def annotate(self, text: str) -> Dict:
        if not text or not text.strip():
            return {'sentences': []}

        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        return {
            'sentences': [
                self._annotate_sentence(sentence, idx)
                for idx, sentence in enumerate(sentences)
            ]
        }

    def _annotate_sentence(self, sentence: str, sentence_idx: int) -> Dict:
        tokens = []
        for idx, token in enumerate(self._TOKEN_PATTERN.findall(sentence), start=1):
            lemma = token.lower()
            pos = self._guess_pos(token)
            ner = self._guess_ner(token)
            tokens.append({
                'index': idx,
                'word': token,
                'originalText': token,
                'lemma': lemma,
                'pos': pos,
                'ner': ner,
            })

        dependencies = self._build_dependencies(tokens)
        return {
            'index': sentence_idx,
            'tokens': tokens,
            'basicDependencies': dependencies,
        }

    def _guess_pos(self, token: str) -> str:
        if token.isdigit():
            return 'CD'
        if token.isupper() and len(token) > 1:
            return 'NNP'
        if token[0].isupper():
            return 'NNP'
        if token.lower() in {'kill', 'killed', 'attacked', 'attack', 'shot', 'bombed'}:
            return 'VBD'
        if token.lower() in {'is', 'are', 'was', 'were'}:
            return 'VBZ'
        if re.match(r"[,.!?]", token):
            return '.'
        return 'NN'

    def _guess_ner(self, token: str) -> str:
        lower = token.lower()
        if lower in self._LOCATION_TERMS:
            return 'LOCATION'
        if lower in self._ORGANISATION_TERMS:
            return 'ORGANIZATION'
        if token.istitle():
            return 'PERSON'
        return 'O'

    def _build_dependencies(self, tokens: List[Dict]) -> List[Dict]:
        deps: List[Dict] = []
        for idx, token in enumerate(tokens, start=1):
            if idx == 1:
                deps.append({
                    'dep': 'root',
                    'governor': 0,
                    'governorGloss': 'ROOT',
                    'dependent': idx,
                    'dependentGloss': token['word'],
                })
            else:
                deps.append({
                    'dep': 'dep',
                    'governor': idx - 1,
                    'governorGloss': tokens[idx - 2]['word'],
                    'dependent': idx,
                    'dependentGloss': token['word'],
                })
        return deps

    def get_tokens(self, sentence: Dict) -> List[Dict]:
        return sentence.get('tokens', [])

    def get_entities(self, sentence: Dict) -> List[Dict]:
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
        deps = sentence.get('basicDependencies', [])
        return [
            {
                'relation': dep['dep'],
                'governor': dep['governorGloss'],
                'dependent': dep['dependentGloss'],
            }
            for dep in deps
        ]

    def close(self):
        return None
