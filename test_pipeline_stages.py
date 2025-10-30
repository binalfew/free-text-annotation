#!/usr/bin/env python3
"""
Test Pipeline Stages Separately
================================

Run individual stages of the violent event annotation pipeline
to inspect intermediate results.

Usage:
    python3 test_pipeline_stages.py --stage [1|2|3|4|all]
    python3 test_pipeline_stages.py --stage 3 --article 2 --verbose

Author: Binalfew Kassa Mekonnen
Date: October 2025
"""

import argparse
import json
import sys
from pathlib import Path

# Import pipeline components
from process_articles_to_csv import parse_articles
from pipeline import ViolentEventNLPPipeline
from event_extraction import EventExtractor
from domain.violence_lexicon import ViolenceLexicon
from domain.african_ner import AfricanNER


def print_separator(title):
    """Print a nice separator with title."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def stage1_parse_articles(args):
    """STAGE 1: Parse articles from markdown."""
    print_separator("STAGE 1: ARTICLE PARSING")

    articles_file = 'articles.md'
    print(f"Input File: {articles_file}")

    # Parse all articles
    articles = parse_articles(articles_file)
    print(f"✓ Found {len(articles)} articles\n")

    # Filter to specific article if requested
    if args.article:
        articles = [articles[args.article - 1]]
        print(f"Testing article {args.article} only\n")

    # Show results
    for i, article in enumerate(articles, 1):
        print(f"{'─' * 70}")
        print(f"ARTICLE {i}")
        print(f"{'─' * 70}")
        print(f"Title: {article.get('title', 'N/A')}")
        print(f"Source: {article.get('source', 'N/A')}")
        print(f"Date: {article.get('date', 'N/A')}")
        print(f"Location: {article.get('location', 'N/A')}")
        print(f"Type: {article.get('type', 'N/A')}")
        print(f"Body Length: {len(article.get('body', ''))} characters")

        if args.verbose:
            print(f"\nBody Preview:")
            preview = article.get('body', '')[:300]
            print(f"  {preview}...")

        print()

    # Save to file
    output_file = 'output/stage1_parsed_articles.json'
    Path('output').mkdir(exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(articles, f, indent=2)
    print(f"✓ Saved to: {output_file}")

    return articles


def stage2_nlp_pipeline(args, articles=None):
    """STAGE 2: NLP Pipeline processing."""
    print_separator("STAGE 2: NLP PIPELINE")

    # Load articles if not provided
    if articles is None:
        articles = parse_articles('articles.md')

    # Filter to specific article if requested (only if not already filtered)
    if args.article and len(articles) > 1:
        articles = [articles[args.article - 1]]
        print(f"Processing article {args.article} only\n")

    # Initialize pipeline
    config = {
        'stanford_corenlp': {
            'path': './stanford-corenlp-4.5.5',
            'memory': '4g'
        }
    }
    print("Initializing NLP pipeline...")
    pipeline = ViolentEventNLPPipeline(config)
    print("✓ Pipeline initialized\n")

    # Process each article
    results = []
    for i, article in enumerate(articles, 1):
        article_id = f"article_{i if not args.article else args.article}"

        print(f"{'─' * 70}")
        print(f"PROCESSING: {article.get('title', 'Unknown')[:50]}...")
        print(f"{'─' * 70}")

        # Process through pipeline
        result = pipeline.process_article(article['body'], article_id)

        print(f"Original text: {len(article['body'])} characters")
        print(f"Cleaned text: {len(result.get('cleaned_text', ''))} characters")
        print(f"Sentences: {result['num_sentences']}")
        print(f"Violence sentences: {result['article_features']['num_violence_sentences']}")

        if args.verbose:
            # Show first 3 sentences
            print(f"\n{'─' * 70}")
            print("SENTENCES (first 3):")
            print(f"{'─' * 70}")
            for sent_idx, sentence in enumerate(result['sentences'][:3], 1):
                print(f"\n[Sentence {sent_idx}]")
                print(f"Text: {sentence['text']}")
                print(f"Tokens: {len(sentence['tokens'])}")
                print(f"Entities: {len(sentence.get('entities', []))}")

                # Show entities
                if sentence.get('entities'):
                    print(f"\nEntities:")
                    for entity in sentence['entities']:
                        print(f"  • {entity['text']} ({entity['type']})")

                # Show first 5 tokens
                print(f"\nTokens (first 5):")
                for token in sentence['tokens'][:5]:
                    print(f"  [{token['index']}] {token['word']} ({token['pos']}) "
                          f"lemma={token['lemma']}, ner={token.get('ner', 'O')}")

                print(f"\nIs Violence: {sentence.get('is_violence_sentence', False)}")

        results.append(result)
        print()

    # Save to file
    output_file = 'output/stage2_nlp_annotated.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"✓ Saved to: {output_file}")

    return results


def stage3_event_extraction(args, nlp_results=None):
    """STAGE 3: Event extraction with 5W1H."""
    print_separator("STAGE 3: EVENT EXTRACTION")

    # Load NLP results if not provided
    if nlp_results is None:
        articles = parse_articles('articles.md')
        if args.article and len(articles) > 1:
            articles = [articles[args.article - 1]]

        config = {'stanford_corenlp': {'path': './stanford-corenlp-4.5.5', 'memory': '4g'}}
        pipeline = ViolentEventNLPPipeline(config)

        nlp_results = []
        for i, article in enumerate(articles, 1):
            article_id = f"article_{i if not args.article else args.article}"
            result = pipeline.process_article(article['body'], article_id)
            nlp_results.append((result, article))

    # Initialize event extractor
    print("Initializing event extractor...")
    violence_lexicon = ViolenceLexicon()
    african_ner = AfricanNER()
    extractor = EventExtractor(violence_lexicon, african_ner)
    print("✓ Extractor initialized\n")

    # Extract events
    all_events = []
    for i, item in enumerate(nlp_results, 1):
        if isinstance(item, tuple):
            article_annotation, article = item
        else:
            article_annotation = item
            article = {'date': '', 'title': 'Unknown'}

        print(f"{'─' * 70}")
        print(f"EXTRACTING EVENTS: {article.get('title', 'Unknown')[:50]}...")
        print(f"{'─' * 70}")

        # Extract events
        events = extractor.extract_events(article_annotation, article.get('date', ''))

        print(f"✓ Extracted {len(events)} event(s)\n")

        if args.verbose and events:
            for j, event in enumerate(events, 1):
                print(f"{'─' * 70}")
                print(f"EVENT {j}")
                print(f"{'─' * 70}")
                print(f"Trigger: {event['trigger']['word']} (lemma: {event['trigger']['lemma']})")
                print(f"Sentence: {event['sentence_text'][:100]}...")

                print(f"\n5W1H:")
                # WHO
                if event['who']:
                    print(f"  WHO (Actor):")
                    print(f"    Text: {event['who']['text']}")
                    print(f"    Type: {event['who']['type']}")
                    if event['who'].get('from_responsibility_claim'):
                        print(f"    Source: Responsibility claim ✓")
                    elif event['who'].get('from_title_pattern'):
                        print(f"    Source: Title pattern ✓")
                else:
                    print(f"  WHO (Actor): ❌ Not found")

                # WHAT
                print(f"  WHAT (Type): {event['what']['preliminary_type']}")

                # WHOM
                if event['whom']:
                    print(f"  WHOM (Victim): {event['whom']['text']}")
                    if event['whom'].get('deaths'):
                        print(f"    Deaths: {event['whom']['deaths']}")
                    if event['whom'].get('injuries'):
                        print(f"    Injuries: {event['whom']['injuries']}")
                else:
                    print(f"  WHOM (Victim): ❌ Not found")

                # WHERE
                if event['where']:
                    print(f"  WHERE (Location): {event['where']['text']}")
                else:
                    print(f"  WHERE (Location): ❌ Not found")

                # WHEN
                if event['when']:
                    print(f"  WHEN (Time): {event['when']['text']}")
                    if event['when'].get('normalized'):
                        print(f"    Normalized: {event['when']['normalized']} ✓")
                else:
                    print(f"  WHEN (Time): ❌ Not found")

                # HOW
                if event['how']:
                    if event['how'].get('weapons'):
                        print(f"  HOW (Weapons): {', '.join(event['how']['weapons'])}")
                    if event['how'].get('tactics'):
                        print(f"  HOW (Tactics): {', '.join(event['how']['tactics'])}")
                else:
                    print(f"  HOW (Method): ❌ Not found")

                print(f"\nTaxonomy:")
                print(f"  L1: {event.get('taxonomy_l1', 'N/A')}")
                print(f"  L2: {event.get('taxonomy_l2', 'N/A')}")
                print(f"  L3: {event.get('taxonomy_l3', 'N/A')}")

                print(f"\nQuality Metrics:")
                print(f"  Confidence: {event['confidence']:.2f}")
                print(f"  Completeness: {event['completeness']:.2f}")

                print()

        all_events.extend(events)

    # Save to file
    output_file = 'output/stage3_extracted_events.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, default=str)
    print(f"✓ Saved to: {output_file}")
    print(f"✓ Total events extracted: {len(all_events)}")

    return all_events


def stage4_csv_output(args, events=None):
    """STAGE 4: CSV output generation."""
    print_separator("STAGE 4: CSV OUTPUT")

    # Load events if not provided
    if events is None:
        output_file = 'output/stage3_extracted_events.json'
        if Path(output_file).exists():
            with open(output_file, 'r') as f:
                events = json.load(f)
            print(f"Loaded {len(events)} events from: {output_file}\n")
        else:
            print("❌ No events found. Run Stage 3 first!")
            return

    # Convert events to CSV rows
    print(f"Converting {len(events)} event(s) to CSV format...")

    import csv
    csv_file = 'output/test_extracted_events.csv'

    fieldnames = [
        'article_id', 'event_id', 'trigger_word', 'trigger_lemma', 'sentence_index',
        'who_actor', 'who_type',
        'what_event_type',
        'whom_victim', 'whom_type', 'deaths', 'injuries',
        'where_location', 'where_type',
        'when_time', 'when_type', 'when_normalized',
        'how_weapons', 'how_tactics',
        'taxonomy_l1', 'taxonomy_l2', 'taxonomy_l3',
        'confidence', 'completeness'
    ]

    rows = []
    for i, event in enumerate(events, 1):
        row = {
            'article_id': event.get('article_id', f"article_{i}"),
            'event_id': f"event_{i}",
            'trigger_word': event['trigger']['word'],
            'trigger_lemma': event['trigger']['lemma'],
            'sentence_index': event['sentence_index'],

            'who_actor': event['who']['text'] if event['who'] else '',
            'who_type': event['who']['type'] if event['who'] else '',

            'what_event_type': event['what']['preliminary_type'],

            'whom_victim': event['whom']['text'] if event['whom'] else '',
            'whom_type': event['whom']['type'] if event['whom'] else '',
            'deaths': event['whom'].get('deaths', '') if event['whom'] else '',
            'injuries': event['whom'].get('injuries', '') if event['whom'] else '',

            'where_location': event['where']['text'] if event['where'] else '',
            'where_type': event['where']['type'] if event['where'] else '',

            'when_time': event['when']['text'] if event['when'] else '',
            'when_type': event['when']['type'] if event['when'] else '',
            'when_normalized': event['when'].get('normalized', '') if event['when'] else '',

            'how_weapons': ', '.join(event['how'].get('weapons', [])) if event['how'] else '',
            'how_tactics': ', '.join(event['how'].get('tactics', [])) if event['how'] else '',

            'taxonomy_l1': event.get('taxonomy_l1', ''),
            'taxonomy_l2': event.get('taxonomy_l2', ''),
            'taxonomy_l3': event.get('taxonomy_l3', ''),

            'confidence': f"{event['confidence']:.2f}",
            'completeness': f"{event['completeness']:.2f}",
        }
        rows.append(row)

        if args.verbose:
            print(f"\n{'─' * 70}")
            print(f"CSV ROW {i}")
            print(f"{'─' * 70}")
            for key, value in row.items():
                if value:  # Only show non-empty fields
                    print(f"  {key}: {value}")

    # Write CSV
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ CSV file created: {csv_file}")
    print(f"✓ Total rows: {len(rows)}")

    # Show preview
    print(f"\n{'─' * 70}")
    print("CSV PREVIEW (first row):")
    print(f"{'─' * 70}")
    if rows:
        for key, value in rows[0].items():
            print(f"  {key}: {value}")


def run_all_stages(args):
    """Run all stages in sequence."""
    print_separator("RUNNING ALL STAGES")

    # Stage 1
    articles = stage1_parse_articles(args)

    # Stage 2
    nlp_results = []
    for i, article in enumerate(articles, 1):
        # Need to wrap in args object simulation
        # Always use i as the article number when processing all articles
        article_args = argparse.Namespace(article=i, verbose=args.verbose)
        result = stage2_nlp_pipeline(article_args, [article])
        nlp_results.append((result[0], article))

    # Stage 3
    events = stage3_event_extraction(args, nlp_results)

    # Stage 4
    stage4_csv_output(args, events)

    print_separator("ALL STAGES COMPLETE")
    print("✓ Check the output/ folder for intermediate results")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test individual stages of the violent event annotation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test article parsing only
  python3 test_pipeline_stages.py --stage 1

  # Test event extraction for article 2 with verbose output
  python3 test_pipeline_stages.py --stage 3 --article 2 --verbose

  # Run all stages
  python3 test_pipeline_stages.py --stage all --verbose
        """
    )

    parser.add_argument('--stage', type=str, required=True,
                        choices=['1', '2', '3', '4', 'all'],
                        help='Which stage to test (1-4 or all)')

    parser.add_argument('--article', type=int, choices=[1, 2, 3, 4, 5],
                        help='Test specific article number (1-5)')

    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed output')

    args = parser.parse_args()

    # Create output directory
    Path('output').mkdir(exist_ok=True)

    # Run requested stage
    try:
        if args.stage == '1':
            stage1_parse_articles(args)
        elif args.stage == '2':
            stage2_nlp_pipeline(args)
        elif args.stage == '3':
            stage3_event_extraction(args)
        elif args.stage == '4':
            stage4_csv_output(args)
        elif args.stage == 'all':
            run_all_stages(args)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
