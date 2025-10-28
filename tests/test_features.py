from features.lexical_features import LexicalFeatureExtractor
from features.lexical_features import LexicalFeatureExtractor
from features.syntactic_features import SyntacticFeatureExtractor
from domain.violence_lexicon import ViolenceLexicon


def test_lexical_feature_extractor_recognises_violence_terms():
    lexicon = ViolenceLexicon()
    extractor = LexicalFeatureExtractor(list(lexicon.all_terms))

    text = "Militants killed five civilians with rifles in Maiduguri."
    tokens = text.split()
    features = extractor.extract_features(tokens, text)

    assert features['violence_term_count'] >= 2
    assert features['has_death_terms'] is True
    assert features['has_actor_terms'] is True
    assert features['has_weapon_terms'] is True


def test_syntactic_feature_extractor_counts_dependency_signals():
    extractor = SyntacticFeatureExtractor()
    tokens = [
        {'lemma': 'militant', 'pos': 'NN'},
        {'lemma': 'kill', 'pos': 'VBD'},
        {'lemma': 'civilian', 'pos': 'NN'},
    ]
    dependencies = [
        {'dep': 'nsubj', 'governor': 2, 'dependent': 1},
        {'dep': 'dobj', 'governor': 2, 'dependent': 3},
    ]

    features = extractor.extract_features(tokens, dependencies)

    assert features['num_verbs'] == 1
    assert features['num_nouns'] == 2
    assert features['has_violence_verb'] is True
    assert features['has_agent_patient'] is True
