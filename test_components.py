# test_components.py

def test_text_cleaner():
    """Test text cleaning."""
    from preprocessing.text_cleaner import TextCleaner
    
    cleaner = TextCleaner()
    
    raw_text = """
    <html><body>
    <h1>Breaking News</h1>
    <p>Armed militants attacked a village in Mali.</p>
    Advertisement
    </body></html>
    """
    
    cleaned = cleaner.clean(raw_text)
    print("Cleaned text:", cleaned)
    assert "Armed militants" in cleaned
    assert "<html>" not in cleaned
    print("✓ Text cleaner works!")

def test_violence_lexicon():
    """Test violence lexicon."""
    from domain_specific.violence_lexicon import ViolenceLexicon
    
    lexicon = ViolenceLexicon()
    
    assert lexicon.is_violence_term('killed')
    assert lexicon.is_violence_term('attack')
    assert not lexicon.is_violence_term('happy')
    
    print(f"✓ Violence lexicon loaded: {len(lexicon.all_terms)} terms")

def test_african_ner():
    """Test African NER."""
    from domain_specific.african_ner import AfricanNER
    
    ner = AfricanNER()
    
    text = "Boko Haram attacked a village in Maiduguri, Nigeria"
    
    actors = ner.recognize_actor(text)
    locations = ner.recognize_location(text)
    
    print(f"Actors found: {actors}")
    print(f"Locations found: {locations}")
    
    assert len(actors) > 0
    assert len(locations) > 0
    print("✓ African NER works!")

if __name__ == '__main__':
    test_text_cleaner()
    test_violence_lexicon()
    test_african_ner()
    print("\n✅ All component tests passed!")