# test_extraction.py

from pipeline import ViolentEventNLPPipeline
from event_extraction import EventExtractor
from domain.violence_lexicon import ViolenceLexicon
from domain.african_ner import AfricanNER

def test_event_extraction():
    """Test full event extraction pipeline."""
    
    # Sample article
    article_text = """
    Maiduguri, Nigeria - At least 15 people were killed when suspected 
    Boko Haram militants attacked a village in northeastern Nigeria on 
    Tuesday. The attackers arrived at dawn and opened fire on residents. 
    Witnesses said the gunmen burned several houses before fleeing.
    """
    
    # Initialize pipeline
    config = {
        'stanford_corenlp': {
            'path': './stanford-corenlp-4.5.5',
            'memory': '4g'
        }
    }
    
    print("Initializing pipeline...")
    pipeline = ViolentEventNLPPipeline(config)
    
    # Initialize event extractor
    print("Initializing event extractor...")
    lexicon = ViolenceLexicon()
    ner = AfricanNER()
    extractor = EventExtractor(lexicon, ner)
    
    # Process article
    print("\nProcessing article...")
    nlp_result = pipeline.process_article(article_text, 'TEST_001')
    
    print(f"✓ Processed {nlp_result['num_sentences']} sentences")
    
    # Extract events
    print("\nExtracting events...")
    events = extractor.extract_events(nlp_result)
    
    print(f"✓ Extracted {len(events)} events")
    
    # Display first event
    if events:
        event = events[0]
        print("\nFirst Event:")
        print(f"  Trigger: {event['trigger']['word']}")
        print(f"  Who: {event['who']}")
        print(f"  Whom: {event['whom']}")
        print(f"  Where: {event['where']}")
        print(f"  When: {event['when']}")
        print(f"  How: {event['how']}")
        print(f"  Confidence: {event['confidence']}")
    
    pipeline.close()
    print("\n✅ Event extraction test passed!")
    return len(events) > 0

if __name__ == '__main__':
    success = test_event_extraction()
    if not success:
        print("❌ No events extracted - check configuration")