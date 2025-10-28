"""
Process articles and output events to CSV format.

This script:
1. Parses articles from articles.md
2. Runs the NLP pipeline on each article
3. Extracts violent events
4. Outputs results to CSV file in output folder
"""

import os
import sys
import csv
import json
import re
from pathlib import Path
from pipeline import ViolentEventNLPPipeline
from event_extraction import EventExtractor
from domain.violence_lexicon import ViolenceLexicon
from domain.african_ner import AfricanNER


def parse_articles(file_path):
    """Parse articles from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by article headers using regex to find "## Article X:"
    articles = []
    article_pattern = r'## Article \d+:([^\n]+)\n(.*?)(?=## Article \d+:|$)'
    matches = re.finditer(article_pattern, content, re.DOTALL)

    for match in matches:
        article_type = match.group(1).strip()
        article_content = match.group(2).strip()

        # Parse metadata and body
        lines = article_content.split('\n')
        article_data = {
            'type': article_type,
            'raw_text': article_content
        }

        # Extract metadata
        for line in lines:
            if line.startswith('### '):
                article_data['title'] = line.replace('### ', '').strip()
            elif line.startswith('**Source:**'):
                article_data['source'] = line.replace('**Source:**', '').strip()
            elif line.startswith('**Date:**'):
                article_data['date'] = line.replace('**Date:**', '').strip()
            elif line.startswith('**Location:**'):
                article_data['location'] = line.replace('**Location:**', '').strip()

        # Extract body text (all paragraphs after the title)
        body_lines = []
        found_title = False
        for line in lines:
            if line.startswith('### '):
                found_title = True
                continue
            if found_title:
                # Skip metadata lines and separator lines
                if (line.strip() and
                    not line.startswith('**') and
                    not line.startswith('---') and
                    not line.startswith('##')):
                    body_lines.append(line.strip())

        article_data['body'] = ' '.join(body_lines)

        if 'title' in article_data and article_data['body']:
            articles.append(article_data)

    return articles


def process_articles_to_csv(articles_file, output_file):
    """Process articles and save events to CSV."""

    print("=" * 80)
    print("PROCESSING ARTICLES TO CSV")
    print("=" * 80)

    # Parse articles
    print(f"\nParsing articles from: {articles_file}")
    articles = parse_articles(articles_file)
    print(f"Found {len(articles)} articles\n")

    # Initialize pipeline
    print("Initializing NLP pipeline...")
    config = {
        'stanford_corenlp': {
            'path': './stanford-corenlp-4.5.5',
            'memory': '4g'
        }
    }

    pipeline = ViolentEventNLPPipeline(config)
    violence_lexicon = ViolenceLexicon()
    african_ner = AfricanNER()
    extractor = EventExtractor(violence_lexicon, african_ner)
    print("Pipeline initialized successfully\n")

    # Process each article and collect events
    all_events = []

    for i, article in enumerate(articles, 1):
        article_id = f"article_{i}"
        title = article.get('title', 'Unknown')

        print(f"Processing Article {i}/{len(articles)}: {title[:60]}...")

        # Process through NLP pipeline
        article_annotation = pipeline.process_article(article['body'], article_id)

        # Extract events
        events = extractor.extract_events(article_annotation)

        print(f"  ✓ Extracted {len(events)} event(s)")

        # Convert events to CSV rows
        for event_num, event in enumerate(events, 1):
            row = {
                'article_id': article_id,
                'event_id': f"{article_id}_event_{event_num}",
                'article_title': title,
                'article_source': article.get('source', ''),
                'article_date': article.get('date', ''),
                'article_location': article.get('location', ''),
                'article_type': article.get('type', ''),

                # Event details
                'trigger_word': event.get('trigger', {}).get('word', ''),
                'trigger_lemma': event.get('trigger', {}).get('lemma', ''),
                'sentence_index': event.get('trigger', {}).get('sentence_index', ''),

                # 5W1H
                'who_actor': event.get('who', {}).get('text', '') if event.get('who') else '',
                'who_type': event.get('who', {}).get('type', '') if event.get('who') else '',

                'what_event_type': event.get('what', {}).get('preliminary_type', '') if event.get('what') else '',

                'whom_victim': event.get('whom', {}).get('text', '') if event.get('whom') else '',
                'whom_type': event.get('whom', {}).get('type', '') if event.get('whom') else '',
                'deaths': event.get('whom', {}).get('deaths', '') if event.get('whom') else '',
                'injuries': event.get('whom', {}).get('injuries', '') if event.get('whom') else '',

                'where_location': event.get('where', {}).get('text', '') if event.get('where') else '',
                'where_type': event.get('where', {}).get('type', '') if event.get('where') else '',

                'when_time': event.get('when', {}).get('text', '') if event.get('when') else '',
                'when_type': event.get('when', {}).get('type', '') if event.get('when') else '',

                'how_weapons': ', '.join(event.get('how', {}).get('weapons', [])) if event.get('how') else '',
                'how_tactics': ', '.join(event.get('how', {}).get('tactics', [])) if event.get('how') else '',

                # Quality metrics
                'confidence': f"{event.get('confidence', 0):.2f}",
                'completeness': f"{event.get('completeness', 0):.2f}",
            }

            all_events.append(row)

    # Write to CSV
    print(f"\nWriting {len(all_events)} events to CSV: {output_file}")

    fieldnames = [
        'article_id', 'event_id', 'article_title', 'article_source', 'article_date',
        'article_location', 'article_type',
        'trigger_word', 'trigger_lemma', 'sentence_index',
        'who_actor', 'who_type',
        'what_event_type',
        'whom_victim', 'whom_type', 'deaths', 'injuries',
        'where_location', 'where_type',
        'when_time', 'when_type',
        'how_weapons', 'how_tactics',
        'confidence', 'completeness'
    ]

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_events)

    print(f"✓ CSV file created successfully!")
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total articles processed: {len(articles)}")
    print(f"Total events extracted: {len(all_events)}")
    print(f"Average events per article: {len(all_events) / len(articles):.1f}")
    print(f"Output file: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    # Set paths
    base_dir = Path(__file__).parent
    articles_file = base_dir / 'articles.md'
    output_file = base_dir / 'output' / 'extracted_events.csv'

    # Process
    process_articles_to_csv(articles_file, output_file)
