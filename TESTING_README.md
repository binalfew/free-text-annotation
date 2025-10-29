# Testing Guide - Violent Event Annotation System

## Quick Start

### Show All Test Examples
```bash
./test_examples.sh
```

### Test Individual Stages

**Stage 1: Article Parsing**
```bash
python3 test_pipeline_stages.py --stage 1
```

**Stage 2: NLP Pipeline**
```bash
python3 test_pipeline_stages.py --stage 2 --article 1 --verbose
```

**Stage 3: Event Extraction**
```bash
python3 test_pipeline_stages.py --stage 3 --article 1 --verbose
```

**Stage 5: CSV Output**
```bash
python3 test_pipeline_stages.py --stage 5
```

**All Stages**
```bash
python3 test_pipeline_stages.py --stage all --verbose
```

---

## Testing Documentation

### Comprehensive Guide
📖 **STEP_BY_STEP_TESTING.md** - Detailed testing guide with:
- Manual test scripts for each stage
- What to expect at each stage
- Debugging tips
- Validation checklists

### Quick Reference
📖 **QUICK_START_GUIDE.md** - User-friendly overview:
- 5-minute system overview
- Visual flow diagram
- Example walk-through
- Performance metrics

### Technical Workflow
📖 **SYSTEM_WORKFLOW.md** - Technical deep dive:
- Complete architecture
- Stage-by-stage code walkthrough
- Data structures at each step
- File locations and line numbers

---

## Test Script Options

### Basic Usage
```bash
python3 test_pipeline_stages.py --stage <STAGE> [OPTIONS]
```

### Stages
- `--stage 1` - Article parsing
- `--stage 2` - NLP pipeline
- `--stage 3` - Event extraction
- `--stage 4` - Post-processing (message only)
- `--stage 5` - CSV output
- `--stage all` - Run complete pipeline

### Options
- `--article N` - Test specific article (1-5)
- `--verbose` - Show detailed output

### Examples
```bash
# Test Article 1 parsing only
python3 test_pipeline_stages.py --stage 1 --article 1

# Test Article 2 with full NLP details
python3 test_pipeline_stages.py --stage 2 --article 2 --verbose

# Extract events from all articles with details
python3 test_pipeline_stages.py --stage 3 --verbose

# Run complete pipeline for Article 3
python3 test_pipeline_stages.py --stage all --article 3 --verbose
```

---

## Output Files

All test outputs are saved to the `output/` directory:

| File | Description |
|------|-------------|
| `stage1_parsed_articles.json` | Parsed article metadata and body |
| `stage2_nlp_annotated.json` | NLP annotations (tokens, entities, dependencies) |
| `stage3_extracted_events.json` | Extracted events with 5W1H |
| `test_extracted_events.csv` | CSV output format |

---

## Quick Component Tests

### Test Date Normalization
```bash
python3 -c "
from utils.date_normalizer import DateNormalizer
n = DateNormalizer()
print('Friday (ref: March 15, 2024) →', n.normalize_date('Friday', 'March 15, 2024'))
print('Tuesday (ref: March 18, 2024) →', n.normalize_date('Tuesday', 'March 18, 2024'))
"
```

Expected output:
```
Friday (ref: March 15, 2024) → 2024-03-08
Tuesday (ref: March 18, 2024) → 2024-03-12
```

### Test Taxonomy Classification
```bash
python3 -c "
from taxonomy_classifier import TaxonomyClassifier
c = TaxonomyClassifier()

# Test terrorism event
event = {
    'trigger': {'lemma': 'attack'},
    'who': {'text': 'Al-Shabaab', 'type': 'TERRORIST'},
    'whom': {'text': 'civilians'},
    'how': {'weapons': ['explosive'], 'tactics': ['suicide']}
}

l1, l2, l3 = c.classify(event)
print(f'Taxonomy: {l1} > {l2} > {l3}')
"
```

Expected output:
```
Taxonomy: Political Violence > Terrorism > Suicide Bombing
```

### Test Actor Validation
```bash
python3 -c "
from event_extraction import FiveW1HExtractor
from domain.african_ner import AfricanNER

extractor = FiveW1HExtractor(AfricanNER())

# Test valid actors
print('Al-Shabaab:', extractor._is_likely_actor('Al-Shabaab'))
print('Police officers:', extractor._is_likely_actor('Police officers'))
print('Armed gang:', extractor._is_likely_actor('Armed gang'))

# Test invalid actors (should reject)
print('Bakara (market):', extractor._is_likely_actor('Bakara'))
print('The (article):', extractor._is_likely_actor('The'))
print('Violent (adjective):', extractor._is_likely_actor('Violent'))
"
```

Expected output:
```
Al-Shabaab: True
Police officers: True
Armed gang: True
Bakara (market): False
The (article): False
Violent (adjective): False
```

---

## Viewing Results

### Pretty-print JSON
```bash
cat output/stage3_extracted_events.json | python3 -m json.tool | less
```

### View CSV as Table
```bash
cat output/test_extracted_events.csv | column -t -s, | less
```

### Count Events
```bash
cat output/test_extracted_events.csv | wc -l
```

### Extract Specific Fields
```bash
# Show all actors
cat output/test_extracted_events.csv | cut -d, -f11 | tail -n +2

# Show all taxonomy L1 categories
cat output/test_extracted_events.csv | cut -d, -f23 | tail -n +2 | sort | uniq -c
```

---

## Testing Checklist

### After Each Test Run

**Stage 1 ✓**
- [ ] All 5 articles parsed
- [ ] Title, source, date, location extracted
- [ ] Body text present (>500 characters)
- [ ] JSON file created in output/

**Stage 2 ✓**
- [ ] Sentences split correctly
- [ ] Tokens have POS tags
- [ ] Named entities identified
- [ ] Dependencies extracted
- [ ] Violence sentences marked

**Stage 3 ✓**
- [ ] Violence triggers detected
- [ ] Actors extracted (check: NOT "Bakara", "The", etc.)
- [ ] Victims extracted
- [ ] Casualties extracted (deaths/injuries)
- [ ] Dates normalized to ISO format
- [ ] Taxonomy classified (3 levels)
- [ ] Confidence scores: 0.4-1.0
- [ ] Completeness scores: 0.5-1.0 (NOT 0.00!)

**Stage 5 ✓**
- [ ] CSV file created
- [ ] All 27 columns present
- [ ] Headers match data
- [ ] No parsing errors

---

## Debugging

### Enable Verbose Logging
```bash
python3 test_pipeline_stages.py --stage 3 --verbose 2>&1 | tee debug.log
```

### Check Specific Article
```bash
# Focus on problematic article
python3 test_pipeline_stages.py --stage all --article 3 --verbose
```

### Trace Function Calls
```bash
python3 -m trace --trace test_pipeline_stages.py --stage 3 --article 1 2>&1 | grep "_extract"
```

### Profile Performance
```bash
python3 -m cProfile -s cumtime test_pipeline_stages.py --stage 3 | head -30
```

---

## Common Issues

### Issue: No events extracted
**Check:**
```bash
# Verify violence triggers detected
python3 test_pipeline_stages.py --stage 2 --article 1 --verbose | grep "Violence: True"
```

### Issue: Wrong actors
**Check:**
```bash
# View actor extraction details
python3 test_pipeline_stages.py --stage 3 --article 1 --verbose | grep -A 5 "WHO"
```

### Issue: Dates not normalized
**Check:**
```bash
# Test date normalizer directly
python3 -c "from utils.date_normalizer import DateNormalizer; print(DateNormalizer().normalize_date('Friday', 'March 15, 2024'))"
```

### Issue: Import errors
**Fix:**
```bash
# Install dependencies
pip3 install dateparser python-dateutil pandas numpy
```

---

## Performance Benchmarks

### Expected Processing Times
- Stage 1 (Parsing): < 0.1s per article
- Stage 2 (NLP): ~0.5-1s per article
- Stage 3 (Extraction): ~0.2-0.5s per article
- Full pipeline: ~1-2s per article

### Memory Usage
- Peak: ~200-300 MB for 5 articles
- Per article: ~40-60 MB

### Accuracy Targets
- Actor extraction: 50% (current)
- Taxonomy classification: 33% (current)
- Date normalization: 33% (when dates present)
- Completeness scores: 100% valid (fixed!)

---

## Compare with Expert Annotation

### Load Expert Annotations
```bash
cat annotated.csv | head
```

### Side-by-Side Comparison
```bash
# Show Article 1 - Expert vs Automated
echo "=== EXPERT ==="
grep "ART_001" annotated.csv | cut -d, -f3,4,5,10,11,12

echo -e "\n=== AUTOMATED ==="
grep "article_1" output/test_extracted_events.csv | cut -d, -f11,13,15,23,24,25
```

---

## Next Steps

1. **Run full test suite:**
   ```bash
   python3 test_pipeline_stages.py --stage all --verbose > full_test.log 2>&1
   ```

2. **Review results:**
   - Check `output/*.json` files
   - Review `full_test.log`
   - Compare with expert annotations

3. **Iterate:**
   - Identify missing actors
   - Check wrong taxonomy classifications
   - Review date normalization accuracy

4. **Customize:**
   - Add patterns to `event_extraction.py`
   - Extend taxonomy in `taxonomy_classifier.py`
   - Adjust confidence scoring

---

## Success Criteria

**System is working correctly if:**
- ✅ Events extracted with actor names (NOT "Bakara", "The")
- ✅ Dates normalized to ISO format (YYYY-MM-DD)
- ✅ Completeness scores 0.5-1.0 (NOT 0.00)
- ✅ Taxonomy with 3 levels
- ✅ No critical errors in logs

**Example of GOOD output:**
```
Actor: Al-Shabaab ✓
Taxonomy: Political Violence > Terrorism > Suicide Bombing ✓
Date: 2024-03-08 ✓
Completeness: 1.00 ✓
```

**Example of BAD output (should NOT see):**
```
Actor: Bakara ❌
Taxonomy: Unknown > Unknown > Unknown ❌
Date: Friday ❌
Completeness: 0.00 ❌
```

---

## Support

- **Technical docs:** SYSTEM_WORKFLOW.md
- **User guide:** QUICK_START_GUIDE.md
- **Testing guide:** STEP_BY_STEP_TESTING.md
- **Results:** final_results_summary.md
- **Examples:** ./test_examples.sh
