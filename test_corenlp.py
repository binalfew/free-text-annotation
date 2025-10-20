# test_corenlp.py
from stanford_nlp.corenlp_wrapper import CoreNLPWrapper

def test_corenlp():
    """Test CoreNLP wrapper."""
    
    print("Initializing CoreNLP (may take 30 seconds)...")
    nlp = CoreNLPWrapper('./stanford-corenlp-4.5.5', memory='4g')
    
    text = "Armed militants killed 15 civilians in Maiduguri on Tuesday."
    
    print("\nAnnotating text...")
    annotation = nlp.annotate(text)
    
    if 'sentences' in annotation:
        sent = annotation['sentences'][0]
        
        # Test token extraction
        tokens = nlp.get_tokens(sent)
        print(f"✓ Tokens ({len(tokens)}): {[t['word'] for t in tokens[:5]]}...")
        
        # Test entity extraction
        entities = nlp.get_entities(sent)
        print(f"✓ Entities: {entities}")
        
        # Test dependencies
        deps = nlp.get_dependencies(sent)
        print(f"✓ Dependencies ({len(deps)}): {deps[:3]}...")
        
        print("\n✅ CoreNLP test passed!")
        nlp.close()
        return True
    else:
        print("❌ CoreNLP annotation failed")
        print(f"Annotation response: {annotation}")
        nlp.close()
        return False

if __name__ == '__main__':
    test_corenlp()