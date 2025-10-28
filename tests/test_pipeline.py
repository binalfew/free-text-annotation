import pytest

from pipeline import ViolentEventNLPPipeline


def test_missing_corenlp_config_raises_key_error():
    with pytest.raises(KeyError):
        ViolentEventNLPPipeline({})


def test_absolute_missing_path_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        ViolentEventNLPPipeline({'stanford_corenlp': {'path': '/nonexistent'}})


def test_article_processing_returns_enriched_sentence():
    pipeline = ViolentEventNLPPipeline({'stanford_corenlp': {'path': './fallback'}})
    article = "MAIDUGURI, Nigeria - Militants killed five civilians on Tuesday."

    result = pipeline.process_article(article, article_id='ART_001')

    assert result['num_sentences'] == 1
    sentence = result['sentences'][0]

    assert sentence['lexical_features']['has_death_terms'] is True
    assert sentence['is_violence_sentence'] is True
    assert any(entity['type'] == 'LOCATION' for entity in sentence['entities'])
