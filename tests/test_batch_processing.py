from pathlib import Path

from batch_processing import (
    AnnotationFormatter,
    BatchProcessor,
)
from domain.african_ner import AfricanNER
from domain.violence_lexicon import ViolenceLexicon
from event_extraction import EventExtractor
from pipeline import ViolentEventNLPPipeline


def test_batch_processor_handles_invalid_articles(tmp_path):
    config = {'stanford_corenlp': {'path': './fallback'}}
    pipeline = ViolentEventNLPPipeline(config)
    extractor = EventExtractor(ViolenceLexicon(), AfricanNER())
    formatter = AnnotationFormatter()

    processor = BatchProcessor(pipeline, extractor, formatter, output_dir=tmp_path)

    articles = [
        {'id': 'ART_001', 'text': 'Militants killed three people in Maiduguri.'},
        {'text': 'Missing id should fail'},
    ]

    summary = processor.process_articles(articles, batch_name='test_batch')

    assert summary['processed'] == 1
    assert summary['failed'] == 1

    summary_files = list(Path(tmp_path).glob('*_summary.json'))
    assert summary_files, 'Expected a summary JSON file to be written.'
    assert summary_files[0].exists()
