# Step-by-Step Testing Guide

## Overview

This guide shows how to run each stage of the pipeline separately to inspect intermediate results.

---

## Quick Test Script

**Run individual stages:**
```bash
python3 test_pipeline_stages.py --stage [1|2|3|4|5|all]
```

**Options:**
- `--stage 1` - Test Article Parsing only
- `--stage 2` - Test NLP Pipeline only
- `--stage 3` - Test Event Extraction only
- `--stage 4` - Test Post-Processing only
- `--stage 5` - Test CSV Output only
- `--stage all` - Run all stages (same as full pipeline)
- `--article N` - Test specific article number (1-5)
- `--verbose` - Show detailed output

---

## Stage-by-Stage Manual Testing

### STAGE 1: Article Parsing

**Purpose:** Parse markdown articles into structured Python objects

**Test Command:**
```bash
python3 test_pipeline_stages.py --stage 1 --article 1 --verbose
```

**What You'll See:**
```python
==================== STAGE 1: ARTICLE PARSING ====================

Input File: articles.md
Parsing article 1...

OUTPUT:
{
    'title': 'Suicide Bombing Kills 15 in Mogadishu Market Attack',
    'source': 'BBC News Africa',
    'date': 'March 15, 2024',
    'location': 'Mogadishu, Somalia',
    'type': 'Political Violence - Terrorism',
    'body': 'A suicide bomber detonated an explosive device at the busy...'
}

Body length: 823 characters
Metadata extracted: ✓
```

**Manual Test (Python):**
```python
# test_stage1.py
from process_articles_to_csv import parse_articles

articles = parse_articles('articles.md')
print(f"Found {len(articles)} articles")

# Inspect first article
article = articles[0]
print("\n=== Article 1 ===")
print(f"Title: {article['title']}")
print(f"Source: {article['source']}")
print(f"Date: {article['date']}")
print(f"Location: {article['location']}")
print(f"Type: {article['type']}")
print(f"\nBody Preview: {article['body'][:200]}...")
```

**Run:**
```bash
python3 test_stage1.py
```

**Expected Output:**
```
Found 5 articles

=== Article 1 ===
Title: Suicide Bombing Kills 15 in Mogadishu Market Attack
Source: BBC News Africa
Date: March 15, 2024
Location: Mogadishu, Somalia
Type: Political Violence - Terrorism

Body Preview: A suicide bomber detonated an explosive device at the busy Bakara
market in Mogadishu on Friday morning, killing at least 15 civilians and injuring
23 others...
```

---

### STAGE 2: NLP Pipeline

**Purpose:** Process text through NLP pipeline (tokenization, NER, parsing)

**Test Command:**
```bash
python3 test_pipeline_stages.py --stage 2 --article 1 --verbose
```

**What You'll See:**
```python
==================== STAGE 2: NLP PIPELINE ====================

Processing article: article_1
Original text length: 823 characters
Cleaned text length: 820 characters

Sentences found: 10

=== Sentence 1 ===
Text: "A suicide bomber detonated an explosive device at the busy Bakara market."

Tokens (first 5):
  [1] A (DT) - determiner
  [2] suicide (NN) - noun
  [3] bomber (NN) - noun
  [4] detonated (VBD) - verb past tense
  [5] an (DT) - determiner

Named Entities:
  - "Bakara market" (LOCATION)

Dependencies (first 3):
  bomber --nsubj-> detonated
  device --dobj-> detonated
  market --nmod-> detonated

Lexical Features:
  - violence_term_count: 1
  - has_casualty_mention: False

Is Violence Sentence: True ✓
```

**Manual Test (Python):**
```python
# test_stage2.py
from pipeline import ViolentEventNLPPipeline
from process_articles_to_csv import parse_articles
import json

# Parse articles
articles = parse_articles('articles.md')
article = articles[0]

# Initialize pipeline
config = {
    'stanford_corenlp': {
        'path': './stanford-corenlp-4.5.5',
        'memory': '4g'
    }
}
pipeline = ViolentEventNLPPipeline(config)

# Process article
result = pipeline.process_article(article['body'], 'article_1')

print("=== NLP Pipeline Output ===")
print(f"Article ID: {result['article_id']}")
print(f"Number of sentences: {result['num_sentences']}")
print(f"\n=== First Sentence ===")

sentence = result['sentences'][0]
print(f"Text: {sentence['text']}")
print(f"\nTokens ({len(sentence['tokens'])} total):")
for token in sentence['tokens'][:5]:
    print(f"  {token['word']} ({token['pos']}) - {token['lemma']}")

print(f"\nEntities:")
for entity in sentence.get('entities', []):
    print(f"  - {entity['text']} ({entity['type']})")

print(f"\nIs Violence Sentence: {sentence['is_violence_sentence']}")

# Save to file for inspection
with open('output/stage2_nlp_output.json', 'w') as f:
    json.dump(result, f, indent=2)
print("\nFull output saved to: output/stage2_nlp_output.json")
```

**Run:**
```bash
python3 test_stage2.py
```

**Inspect Output:**
```bash
cat output/stage2_nlp_output.json | head -50
```

---

### STAGE 3: Event Extraction

**Purpose:** Extract violent events with 5W1H from annotated text

**Test Command:**
```bash
python3 test_pipeline_stages.py --stage 3 --article 1 --verbose
```

**What You'll See:**
```python
==================== STAGE 3: EVENT EXTRACTION ====================

Processing article_1...
Scanning 10 sentences for violence triggers...

=== Sentence 1: Violence Detected ===
Trigger: "detonated" (verb, index 3)

Extracting 5W1H:
  WHO (Actor):
    Strategy 0: Checking responsibility claims in article...
    ✓ Found: "Al-Shabaab" (from "Al-Shabaab claimed responsibility")

  WHAT (Event Type):
    ✓ Type: "bombing" (from trigger: detonate)

  WHOM (Victim):
    Strategy 1: Searching for object dependencies...
    Strategy 2: Extracting casualties from sentence...
    ✓ Found: "civilians" (deaths: 15, injuries: 23)

  WHERE (Location):
    ✓ Found: "Mogadishu" (LOCATION entity)

  WHEN (Date/Time):
    ✓ Found: "Friday" (DATE entity)
    Normalizing: "Friday" + ref_date "March 15, 2024"
    ✓ Normalized: "2024-03-08"

  HOW (Method/Weapon):
    ✓ Weapons: [explosive, suicide bomb, device]
    ✓ Tactics: [suicide]

Calculating Quality:
  Confidence: 0.95 (has all 6 components)
  Completeness: 1.00 (6/6 components present)

Classifying Taxonomy:
  Level 1: Political Violence (actor type: TERRORIST)
  Level 2: Terrorism (has suicide tactic)
  Level 3: Suicide Bombing (suicide + explosive)

EVENT EXTRACTED:
{
  "trigger": "detonated",
  "who": {"text": "Al-Shabaab", "type": "TERRORIST"},
  "whom": {"text": "civilians", "deaths": 15, "injuries": 23},
  "where": {"text": "Mogadishu", "type": "CITY"},
  "when": {"text": "Friday", "normalized": "2024-03-08"},
  "how": {"weapons": ["explosive", "suicide bomb"], "tactics": ["suicide"]},
  "taxonomy_l1": "Political Violence",
  "taxonomy_l2": "Terrorism",
  "taxonomy_l3": "Suicide Bombing",
  "confidence": 0.95,
  "completeness": 1.00
}

Total events extracted: 1
```

**Note:** Article 1 extracts 1 event (after post-processing filters out background events)

**Manual Test (Python):**
```python
# test_stage3.py
from pipeline import ViolentEventNLPPipeline
from event_extraction import EventExtractor
from domain.violence_lexicon import ViolenceLexicon
from domain.african_ner import AfricanNER
from process_articles_to_csv import parse_articles
import json

# Parse articles
articles = parse_articles('articles.md')
article = articles[0]

# Initialize components
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

# Process through pipeline
article_annotation = pipeline.process_article(article['body'], 'article_1')

# Extract events
events = extractor.extract_events(article_annotation, article['date'])

print(f"=== Event Extraction Results ===")
print(f"Total events extracted: {len(events)}")

for i, event in enumerate(events, 1):
    print(f"\n=== Event {i} ===")
    print(f"Trigger: {event['trigger']['word']}")
    print(f"Sentence: {event['sentence_text'][:80]}...")

    print(f"\n5W1H:")
    print(f"  WHO: {event['who']['text'] if event['who'] else 'N/A'}")
    print(f"  WHAT: {event['what']['preliminary_type']}")
    print(f"  WHOM: {event['whom']['text'] if event['whom'] else 'N/A'}")
    if event['whom'] and (event['whom'].get('deaths') or event['whom'].get('injuries')):
        print(f"    Deaths: {event['whom'].get('deaths', 'N/A')}")
        print(f"    Injuries: {event['whom'].get('injuries', 'N/A')}")
    print(f"  WHERE: {event['where']['text'] if event['where'] else 'N/A'}")
    print(f"  WHEN: {event['when']['text'] if event['when'] else 'N/A'} → {event['when']['normalized'] if event['when'] else 'N/A'}")
    print(f"  HOW: {event['how']['text'] if event['how'] else 'N/A'}")

    print(f"\nTaxonomy:")
    print(f"  L1: {event['taxonomy_l1']}")
    print(f"  L2: {event['taxonomy_l2']}")
    print(f"  L3: {event['taxonomy_l3']}")

    print(f"\nQuality:")
    print(f"  Confidence: {event['confidence']}")
    print(f"  Completeness: {event['completeness']}")

# Save events
with open('output/stage3_events.json', 'w') as f:
    json.dump(events, f, indent=2, default=str)
print("\n\nFull output saved to: output/stage3_events.json")
```

**Run:**
```bash
python3 test_stage3.py
```

---

### STAGE 4: Post-Processing

**Purpose:** Merge, filter, and refine extracted events

**Test Command:**
```bash
python3 test_pipeline_stages.py --stage 4 --article 1 --verbose
```

**What You'll See:**
```python
==================== STAGE 4: POST-PROCESSING ====================

Input: 2 raw events

=== Pass 1: Reciprocal Violence Detection ===
Checking for "clashes between X and Y" patterns...
No reciprocal violence patterns detected.
Events after Pass 1: 2

=== Pass 2: Merge Similar Events ===
Checking event similarity...
Event 1 (sent 1, trigger: detonated)
Event 2 (sent 8, trigger: attack)
  Same location: Mogadishu ✓
  Related triggers: detonate/attack ✓
  → MERGE: Yes

Merged event:
  - Takes actor from Event 1 (Al-Shabaab)
  - Takes casualties from Event 1 (15 deaths, 23 injuries)
  - Takes weapons from both events
  - Confidence recalculated: 0.95

Events after Pass 2: 1

=== Pass 3: Cluster Coreferent Events ===
Only 1 event remaining, no clustering needed.
Events after Pass 3: 1

=== Pass 4: Filter by Salience ===
Calculating salience scores:
  Event 1:
    + Early in article (sent 1): +3
    + Has casualties: +4
    + Has specific victim: +2
    + High completeness: +2
    + High confidence: +2
    = Total: 13 (threshold: 7)
    → KEEP ✓

Events after Pass 4: 1

OUTPUT: 1 high-quality event
```

**Manual Test:**
```python
# test_stage4.py
# This is harder to test manually since it's internal to EventExtractor
# Use the test script instead:
# python3 test_pipeline_stages.py --stage 4 --article 1 --verbose
```

---

### STAGE 5: CSV Output

**Purpose:** Format events as CSV with all fields

**Test Command:**
```bash
python3 test_pipeline_stages.py --stage 5 --article 1 --verbose
```

**What You'll See:**
```python
==================== STAGE 5: CSV OUTPUT ====================

Converting 1 event to CSV format...

CSV Row 1:
  article_id: article_1
  event_id: article_1_event_1
  article_title: Suicide Bombing Kills 15...
  article_source: BBC News Africa
  article_date: March 15, 2024
  article_location: Mogadishu, Somalia

  trigger_word: detonated
  trigger_lemma: detonate
  sentence_index: 1

  who_actor: Al-Shabaab
  who_type: TERRORIST
  what_event_type: bombing

  whom_victim: civilians
  whom_type: civilian
  deaths: 15
  injuries: 23

  where_location: Mogadishu
  where_type: CITY

  when_time: Friday
  when_type: RELATIVE
  when_normalized: 2024-03-08

  how_weapons: explosive, suicide bomb, device
  how_tactics: suicide

  taxonomy_l1: Political Violence
  taxonomy_l2: Terrorism
  taxonomy_l3: Suicide Bombing

  confidence: 0.95
  completeness: 1.00

Writing to: output/test_events.csv
✓ CSV file created

Preview:
article_id,event_id,article_title,article_source,...,confidence,completeness
article_1,article_1_event_1,"Suicide Bombing...",...,0.95,1.00
```

**Manual Test:**
```bash
# View the generated CSV
cat output/test_events.csv

# Or open in a spreadsheet viewer
open output/test_events.csv  # macOS
xdg-open output/test_events.csv  # Linux
```

---

## Testing Specific Articles

### Test Article 1 (Terrorism - Responsibility Claim)
```bash
python3 test_pipeline_stages.py --article 1 --verbose
```
**Should extract:** Al-Shabaab as actor (from responsibility claim)

### Test Article 2 (State Violence - Title Pattern)
```bash
python3 test_pipeline_stages.py --article 2 --verbose
```
**Should extract:** Police officers as actor (from title pattern)

### Test Article 3 (Ethnic Conflict - Reciprocal Violence)
```bash
python3 test_pipeline_stages.py --article 3 --verbose
```
**Should extract:** 2 events (Hema vs Lendu)

### Test Article 4 (Criminal Violence)
```bash
python3 test_pipeline_stages.py --article 4 --verbose
```
**Should extract:** Armed gang as actor

### Test Article 5 (Election Violence - Multiple Events)
```bash
python3 test_pipeline_stages.py --article 5 --verbose
```
**Should extract:** 2 events (protesters vs police)

---

## Debugging Tips

### Save Intermediate Results
```bash
# Save each stage output to file
python3 test_pipeline_stages.py --stage 1 --article 1 > output/stage1.txt
python3 test_pipeline_stages.py --stage 2 --article 1 > output/stage2.txt
python3 test_pipeline_stages.py --stage 3 --article 1 > output/stage3.txt
```

### Compare Before/After Processing
```bash
# Before post-processing (raw extraction)
python3 test_pipeline_stages.py --stage 3 --article 1 --verbose

# After post-processing (refined)
python3 test_pipeline_stages.py --stage 4 --article 1 --verbose
```

### Check Specific Components

**Check only actor extraction:**
```python
# test_actor_extraction.py
from event_extraction import FiveW1HExtractor
from domain.african_ner import AfricanNER

extractor = FiveW1HExtractor(AfricanNER())

# Test sentence
sentence_annotation = {
    'text': 'Al-Shabaab claimed responsibility for the attack.',
    'tokens': [...],
    'entities': [{'text': 'Al-Shabaab', 'type': 'ORGANIZATION'}]
}

trigger = {'word': 'attack', 'lemma': 'attack', 'sentence_index': 5}
article_text = "...full article text..."

actor = extractor._extract_who(trigger, sentence_annotation, article_text)
print(f"Extracted actor: {actor}")
```

**Check only date normalization:**
```python
# test_date_normalization.py
from utils.date_normalizer import DateNormalizer

normalizer = DateNormalizer()

test_dates = [
    ("Friday", "March 15, 2024"),
    ("Tuesday", "March 18, 2024"),
    ("yesterday", "March 16, 2024")
]

for date_text, ref_date in test_dates:
    normalized = normalizer.normalize_date(date_text, ref_date)
    print(f"{date_text} (ref: {ref_date}) → {normalized}")
```

**Check only taxonomy classification:**
```python
# test_taxonomy.py
from taxonomy_classifier import TaxonomyClassifier

classifier = TaxonomyClassifier()

event = {
    'trigger': {'lemma': 'attack'},
    'who': {'text': 'Al-Shabaab', 'type': 'TERRORIST'},
    'whom': {'text': 'civilians'},
    'how': {'weapons': ['explosive'], 'tactics': ['suicide']}
}

l1, l2, l3 = classifier.classify(event)
print(f"Taxonomy: {l1} > {l2} > {l3}")
```

---

## Performance Testing

### Time Each Stage
```bash
time python3 test_pipeline_stages.py --stage 1
time python3 test_pipeline_stages.py --stage 2
time python3 test_pipeline_stages.py --stage 3
time python3 test_pipeline_stages.py --stage 4
time python3 test_pipeline_stages.py --stage 5
```

### Profile Memory Usage
```bash
python3 -m memory_profiler test_pipeline_stages.py --stage 2
```

---

## Validation Checklist

After running each stage, verify:

### Stage 1 ✓
- [ ] All 5 articles parsed
- [ ] Metadata extracted (title, source, date, location)
- [ ] Body text cleaned and readable

### Stage 2 ✓
- [ ] Sentences split correctly
- [ ] Tokens include POS tags
- [ ] Named entities identified (LOCATION, ORGANIZATION, DATE)
- [ ] Dependencies extracted

### Stage 3 ✓
- [ ] Violence triggers detected
- [ ] Actors identified (not "Bakara" or "The")
- [ ] Casualties extracted (deaths/injuries)
- [ ] Dates normalized to ISO format
- [ ] Taxonomy classified

### Stage 4 ✓
- [ ] Similar events merged
- [ ] Low-salience events filtered
- [ ] Quality scores calculated

### Stage 5 ✓
- [ ] CSV file generated
- [ ] All 27 columns present
- [ ] No missing required fields
- [ ] Data matches input articles

---

## Common Issues and Solutions

### Issue: No events extracted
**Check:** Are violence triggers being detected?
```bash
python3 test_pipeline_stages.py --stage 2 --article 1 --verbose | grep "is_violence"
```

### Issue: Wrong actor extracted
**Debug:** Check actor extraction strategy
```bash
python3 test_pipeline_stages.py --stage 3 --article 1 --verbose | grep -A 10 "WHO"
```

### Issue: Dates not normalized
**Debug:** Check date normalization
```bash
python3 -c "from utils.date_normalizer import DateNormalizer; n = DateNormalizer(); print(n.normalize_date('Friday', 'March 15, 2024'))"
```

### Issue: Completeness always 0.00
**This is fixed!** Should now show realistic scores 0.5-1.0

---

## Next Steps

1. **Run all stages:** `python3 test_pipeline_stages.py --stage all --verbose`
2. **Inspect outputs:** Check `output/` folder for JSON files
3. **Compare with expert:** Look at `annotated.csv` for comparison
4. **Review summary:** Check `final_results_summary.md`
5. **Iterate:** Adjust extraction patterns based on results
