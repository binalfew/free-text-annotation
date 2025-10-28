from domain.african_ner import AfricanNER
from domain.violence_lexicon import ViolenceLexicon
from event_extraction import EventExtractor
from pipeline import ViolentEventNLPPipeline


def test_event_extractor_detects_trigger_and_entities():
    pipeline = ViolentEventNLPPipeline({'stanford_corenlp': {'path': './fallback'}})
    lexicon = ViolenceLexicon()
    ner = AfricanNER()
    extractor = EventExtractor(lexicon, ner)

    article = "Maiduguri, Nigeria - Militants killed five civilians on Tuesday morning."
    nlp_result = pipeline.process_article(article, article_id='EVT001')

    events = extractor.extract_events(nlp_result)
    assert events, 'Expected at least one event to be extracted.'

    event = events[0]
    assert event['trigger']['lemma'].startswith('kill')
    assert event['where']['text'] == 'Maiduguri'
    assert event['when']['text']
