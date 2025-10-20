# test_batch.py

from batch_processing import IntegratedPipeline

def test_batch_processing():
    """Test batch article processing."""
    
    config = {
        'stanford_corenlp': {
            'path': './stanford-corenlp-4.5.5',
            'memory': '4g'
        },
        'output': {
            'directory': './output'
        }
    }
    
    print("Initializing integrated pipeline...")
    pipeline = IntegratedPipeline(config)
    
    print("\nProcessing batch of articles...")
    results = pipeline.process_from_file('test_articles.json', file_type='json')
    
    print("\n" + "="*70)
    print("BATCH PROCESSING RESULTS")
    print("="*70)
    print(f"Total articles: {results['total_articles']}")
    print(f"Processed: {results['processed']}")
    print(f"Failed: {results['failed']}")
    print(f"Total events: {results['total_events']}")
    print(f"Output: {results.get('output_file', 'N/A')}")
    print("="*70)
    
    pipeline.close()
    
    # Check output file exists
    if results.get('output_file'):
        import os
        assert os.path.exists(results['output_file'])
        print(f"\n✓ Output file created: {results['output_file']}")
    
    print("\n✅ Batch processing test passed!")
    return True

if __name__ == '__main__':
    test_batch_processing()