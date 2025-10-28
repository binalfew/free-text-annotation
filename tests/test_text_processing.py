from preprocessing.text_cleaner import TextCleaner
from preprocessing.sentence_splitter import SentenceSplitter


def test_text_cleaner_strips_html_and_extracts_metadata():
    cleaner = TextCleaner()
    raw = """
    <html><body><h1>NEWS</h1>MAIDUGURI, Nigeria - Militants attacked a base.<br/>Advertisement</body></html>
    """

    cleaned = cleaner.clean(raw)
    assert 'Advertisement' not in cleaned

    metadata = cleaner.extract_metadata(cleaned)
    assert metadata['dateline_location']
    assert metadata['dateline_location'].endswith('MAIDUGURI, Nigeria')
    assert metadata['has_violence_content'] is True


def test_sentence_splitter_preserves_african_context():
    splitter = SentenceSplitter()
    text = "Dr. Smith visited the U.N. headquarters. Boko Haram was mentioned in the briefing."

    sentences = splitter.split(text)
    assert len(sentences) == 2
    assert any('Boko Haram' in sentence for sentence in sentences)
