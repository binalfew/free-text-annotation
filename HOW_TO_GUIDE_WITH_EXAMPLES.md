# Complete How-To Guide: Violent Event Annotation Pipeline

**Date:** 2025-10-29
**Version:** 2.0 (Stanford CoreNLP Only)
**Purpose:** Step-by-step guide with detailed examples

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Detailed Walkthrough](#detailed-walkthrough)
4. [Stage-by-Stage Examples](#stage-by-stage-examples)
5. [Common Use Cases](#common-use-cases)
6. [Troubleshooting](#troubleshooting)
7. [Understanding the Output](#understanding-the-output)

---

## Prerequisites

### Required Software

1. **Python 3.9+**
   ```bash
   python3 --version
   # Should show: Python 3.9.x or higher
   ```

2. **Java 8+** (for Stanford CoreNLP)
   ```bash
   java -version
   # Should show: java version "1.8.x" or higher
   ```

3. **Python Dependencies**
   ```bash
   pip3 install -r requirements.txt
   # Installs: pandas, numpy, requests, etc.
   ```

### Required Files

✅ **Stanford CoreNLP 4.5.5** at project root:
```bash
cd "/Users/binalfew/Documents/Masters/Week 3-6/free-text-annotation"
ls stanford-corenlp-4.5.5/
# Should show: *.jar files and Stanford CoreNLP components
```

✅ **Input articles** in `articles.md`

### System Requirements

- **RAM:** 4GB minimum (6-8GB recommended)
- **Disk Space:** ~2GB for Stanford CoreNLP
- **OS:** macOS, Linux, or Windows (with WSL)

---

## Quick Start (5 Minutes)

### Step 1: Start Stanford CoreNLP Server

```bash
cd "/Users/binalfew/Documents/Masters/Week 3-6/free-text-annotation"
./start_corenlp_server.sh
```

**Expected Output:**
```
========================================
Stanford CoreNLP Server Startup
========================================

Starting Stanford CoreNLP server...
Configuration:
  - Port: 9000
  - Memory: 4GB
  - Timeout: 30 seconds
  - Annotators: tokenize, ssplit, pos, lemma, ner, depparse, coref

Waiting for server to start...
✓ Stanford CoreNLP server started successfully!
✓ Server PID: 12345
✓ Server URL: http://localhost:9000

Server is ready for use.
```

### Step 2: Run the Pipeline

```bash
python3 test_pipeline_stages.py --stage all --verbose
```

**Expected Output:**
```
======================================================================
  RUNNING ALL STAGES
======================================================================

✓ Found 5 articles

[Stage 1] Article Parsing
✓ Saved to: output/stage1_parsed_articles.json

[Stage 2] NLP Annotation
✓ Connected to Stanford CoreNLP server
✓ Processing article 1/5...
✓ Saved to: output/stage2_nlp_annotated.json

[Stage 3] Event Extraction
✓ Extracted 1 event(s) from article 1
✓ Extracted 2 event(s) from article 3
✓ Total events extracted: 7
✓ Saved to: output/stage3_extracted_events.json

[Stage 4] CSV Output
✓ Generated CSV with 7 events
✓ Saved to: output/test_extracted_events.csv

All stages completed successfully!
```

### Step 3: View Results

```bash
# View extracted events (JSON)
cat output/stage3_extracted_events.json | jq '.[0]'

# View CSV output
head output/test_extracted_events.csv

# Count events
jq '. | length' output/stage3_extracted_events.json
# Output: 7
```

### Step 4: Stop Server

```bash
./stop_corenlp_server.sh
```

---

## Detailed Walkthrough

### Setup Phase

#### 1. Check Prerequisites

```bash
# Navigate to project directory
cd "/Users/binalfew/Documents/Masters/Week 3-6/free-text-annotation"

# Check Python version
python3 --version

# Check Java version
java -version

# Check Stanford CoreNLP exists
ls stanford-corenlp-4.5.5/ | head -5
```

**Expected:**
```
build.xml
corenlp.sh
ejml-core-0.39.jar
stanford-corenlp-4.5.5-javadoc.jar
stanford-corenlp-4.5.5-models.jar
```

#### 2. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

**What gets installed:**
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `requests` - HTTP communication with Stanford CoreNLP
- `scikit-learn` - Machine learning utilities
- `dateparser` - Date parsing
- `python-dateutil` - Date utilities

#### 3. Verify Installation

```bash
python3 -c "import pandas, requests, dateparser; print('✓ All dependencies installed')"
```

---

## Stage-by-Stage Examples

### STAGE 1: Article Parsing

**Purpose:** Parse markdown articles into structured format

#### Input File: `articles.md`

```markdown
## Article 1

**Title:** Suicide Bombing Kills 15 in Mogadishu Market Attack
**Source:** BBC News Africa
**Date:** March 15, 2024
**Location:** Mogadishu, Somalia
**Type:** Political Violence - Terrorism

**Body:**

A suicide bomber detonated an explosive device at the busy Bakara market
in Mogadishu on Friday morning, killing at least 15 civilians and injuring
23 others. The attack occurred during peak shopping hours when the market
was crowded with vendors and customers.

Witnesses reported seeing a young man in his twenties approach the market
entrance before detonating the device. The explosion destroyed several
stalls and left debris scattered across the area.

Emergency services rushed to the scene, and the injured were transported
to nearby hospitals. Medical officials at Medina Hospital confirmed the
death toll and reported that several victims are in critical condition.

The area was immediately cordoned off by security forces as investigations
into the attack began. No group has claimed responsibility yet, but
Al-Shabaab has carried out similar attacks in the capital in recent months.

Al-Shabaab claimed responsibility for the attack in a statement released
through their media channels. The group stated that the attack was in
response to ongoing military operations against them.

The attack comes amid increased security concerns in Mogadishu following
recent violence. Authorities have urged residents to remain vigilant.

Local community leaders have condemned the attack and called for increased
security measures in public markets. The Somali government expressed
condolences to the victims' families.

International organizations, including the United Nations, have condemned
the attack and called for justice for the victims.
```

#### Running Stage 1

```bash
python3 test_pipeline_stages.py --stage 1 --article 1 --verbose
```

#### Output

**Console:**
```
======================================================================
  STAGE 1: ARTICLE PARSING
======================================================================

Processing article 1 only

✓ Found 5 articles in articles.md

──────────────────────────────────────────────────────────────────────
ARTICLE 1
──────────────────────────────────────────────────────────────────────

Title: Suicide Bombing Kills 15 in Mogadishu Market Attack
Source: BBC News Africa
Date: March 15, 2024
Location: Mogadishu, Somalia
Type: Political Violence - Terrorism

Body Preview (first 200 chars):
A suicide bomber detonated an explosive device at the busy Bakara market
in Mogadishu on Friday morning, killing at least 15 civilians and injuring
23 others. The attack occurred during...

Total Length: 1178 characters
```

**File:** `output/stage1_parsed_articles.json`
```json
[
  {
    "title": "Suicide Bombing Kills 15 in Mogadishu Market Attack",
    "source": "BBC News Africa",
    "date": "March 15, 2024",
    "location": "Mogadishu, Somalia",
    "type": "Political Violence - Terrorism",
    "body": "A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu on Friday morning, killing at least 15 civilians and injuring 23 others. The attack occurred during peak shopping hours when the market was crowded with vendors and customers.\n\nWitnesses reported seeing a young man in his twenties approach the market entrance before detonating the device. The explosion destroyed several stalls and left debris scattered across the area.\n\nEmergency services rushed to the scene, and the injured were transported to nearby hospitals. Medical officials at Medina Hospital confirmed the death toll and reported that several victims are in critical condition.\n\nThe area was immediately cordoned off by security forces as investigations into the attack began. No group has claimed responsibility yet, but Al-Shabaab has carried out similar attacks in the capital in recent months.\n\nAl-Shabaab claimed responsibility for the attack in a statement released through their media channels. The group stated that the attack was in response to ongoing military operations against them.\n\nThe attack comes amid increased security concerns in Mogadishu following recent violence. Authorities have urged residents to remain vigilant.\n\nLocal community leaders have condemned the attack and called for increased security measures in public markets. The Somali government expressed condolences to the victims' families.\n\nInternational organizations, including the United Nations, have condemned the attack and called for justice for the victims."
  }
]
```

**What Happened:**
1. ✅ Markdown file parsed
2. ✅ Metadata extracted (title, date, location, etc.)
3. ✅ Body text extracted and cleaned
4. ✅ Structured JSON created

---

### STAGE 2: NLP Annotation

**Purpose:** Annotate article with linguistic features using Stanford CoreNLP

#### Running Stage 2

```bash
# Make sure server is running first!
./start_corenlp_server.sh

python3 test_pipeline_stages.py --stage 2 --article 1 --verbose
```

#### Output

**Console:**
```
======================================================================
  STAGE 2: NLP PIPELINE
======================================================================

Processing article 1 only

Initializing NLP pipeline...
✓ Connected to Stanford CoreNLP server
✓ Pipeline initialized

──────────────────────────────────────────────────────────────────────
PROCESSING: Suicide Bombing Kills 15 in Mogadishu Market Attac...
──────────────────────────────────────────────────────────────────────
Original text: 1178 characters
Cleaned text: 1178 characters
Sentences: 10
Violence sentences: 10

──────────────────────────────────────────────────────────────────────
SENTENCES (first 3):
──────────────────────────────────────────────────────────────────────

[Sentence 1]
Text: A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu on Friday morning , killing at least 15 civilians and injuring 23 others .
Tokens: 28
Entities: 6

Entities:
  • suicide bomber (CAUSE_OF_DEATH)
  • Mogadishu (CITY)
  • Friday (DATE)
  • morning (TIME)
  • 15 (NUMBER)
  • 23 (NUMBER)

Tokens (first 5):
  [1] A (DT) lemma=a, ner=O
  [2] suicide (NN) lemma=suicide, ner=CAUSE_OF_DEATH
  [3] bomber (NN) lemma=bomber, ner=CAUSE_OF_DEATH
  [4] detonated (VBD) lemma=detonate, ner=O
  [5] an (DT) lemma=a, ner=O

Is Violence: True

[Sentence 2]
Text: The attack occurred during peak shopping hours when the market was crowded with vendors and customers .
Tokens: 17
Entities: 2

Entities:
  • attack (CAUSE_OF_DEATH)
  • hours (DURATION)

Is Violence: True

[Sentence 3]
Text: Witnesses reported seeing a young man in his twenties approach the market entrance before detonating the device .
Tokens: 18
Entities: 3

Entities:
  • man (PERSON)
  • twenties (NUMBER)
  • market (LOCATION)

Is Violence: True
```

**File:** `output/stage2_nlp_annotated.json` (excerpt)
```json
{
  "article_id": "article_1",
  "cleaned_text": "A suicide bomber detonated...",
  "num_sentences": 10,
  "coref_chains": [
    {
      "id": "1",
      "mentions": [
        {
          "sentNum": 5,
          "text": "Al-Shabaab",
          "isRepresentative": true
        },
        {
          "sentNum": 5,
          "text": "The group"
        }
      ]
    }
  ],
  "sentences": [
    {
      "index": 0,
      "text": "A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu on Friday morning , killing at least 15 civilians and injuring 23 others .",
      "tokens": [
        {
          "index": 1,
          "word": "A",
          "lemma": "a",
          "pos": "DT",
          "ner": "O"
        },
        {
          "index": 2,
          "word": "suicide",
          "lemma": "suicide",
          "pos": "NN",
          "ner": "CAUSE_OF_DEATH"
        },
        {
          "index": 3,
          "word": "bomber",
          "lemma": "bomber",
          "pos": "NN",
          "ner": "CAUSE_OF_DEATH"
        },
        {
          "index": 4,
          "word": "detonated",
          "lemma": "detonate",
          "pos": "VBD",
          "ner": "O"
        }
      ],
      "entities": [
        {"text": "suicide bomber", "type": "CAUSE_OF_DEATH"},
        {"text": "Mogadishu", "type": "CITY"},
        {"text": "Friday", "type": "DATE"},
        {"text": "morning", "type": "TIME"},
        {"text": "15", "type": "NUMBER"},
        {"text": "23", "type": "NUMBER"}
      ],
      "basicDependencies": [
        {
          "dep": "det",
          "governor": "bomber",
          "dependent": "A"
        },
        {
          "dep": "compound",
          "governor": "bomber",
          "dependent": "suicide"
        },
        {
          "dep": "nsubj",
          "governor": "detonated",
          "dependent": "bomber"
        },
        {
          "dep": "dobj",
          "governor": "detonated",
          "dependent": "device"
        }
      ],
      "is_violence_sentence": true
    }
  ]
}
```

**What Happened:**
1. ✅ Article sent to Stanford CoreNLP server
2. ✅ **Tokenization:** Text split into words
3. ✅ **Sentence Splitting:** Text divided into 10 sentences
4. ✅ **POS Tagging:** Each word tagged (NN, VBD, DT, etc.)
5. ✅ **Lemmatization:** Words reduced to base form (detonated → detonate)
6. ✅ **Named Entity Recognition:** Entities identified (Mogadishu = CITY, Friday = DATE)
7. ✅ **Dependency Parsing:** Grammatical relationships mapped (bomber → detonated)
8. ✅ **Coreference Resolution:** "The group" linked to "Al-Shabaab"

---

### STAGE 3: Event Extraction

**Purpose:** Extract violent events with 5W1H (Who, What, Whom, Where, When, How)

#### Running Stage 3

```bash
python3 test_pipeline_stages.py --stage 3 --verbose
```

#### Output

**Console:**
```
======================================================================
  STAGE 3: EVENT EXTRACTION
======================================================================

Processing 5 articles...

Initializing event extractor...
✓ Extractor initialized

──────────────────────────────────────────────────────────────────────
ARTICLE 1: Suicide Bombing Kills 15 in Mogadishu Market Attac...
──────────────────────────────────────────────────────────────────────

Found Triggers:
  • Sentence 0: detonated (VBD) - violence
    Source: Responsibility claim ✓

Extracting 5W1H:
  WHO:   Al-Shabaab (ORGANIZATION) [from responsibility claim]
  WHAT:  violence
  WHOM:  civilians (15 deaths, 23 injuries)
  WHERE: Bakara market (LOCATION)
  WHEN:  Friday (2024-03-08)
  HOW:   explosive, device, suicide bomb

Post-Processing:
  ✓ Reciprocal violence detection: 0 pairs
  ✓ Event merging: 0 merged
  ✓ Event clustering: 0 clustered
  ✓ Salience filtering: passed
  ✓ Confidence filtering: passed (0.95)

✓ Extracted 1 event(s)

──────────────────────────────────────────────────────────────────────
ARTICLE 3: Ethnic Clashes Leave 12 Dead in Eastern DRC
──────────────────────────────────────────────────────────────────────

Found Triggers:
  • Sentence 0: clashes (NN) - violence
    Pattern: "clashes between Hema and Lendu communities"
    Reciprocal violence detected! ✓

Extracting Events (Reciprocal Pair):
  Event 1:
    WHO:   Hema (communal)
    WHOM:  Lendu (12 deaths)

  Event 2:
    WHO:   Lendu (communal)
    WHOM:  Hema

✓ Extracted 2 event(s)

──────────────────────────────────────────────────────────────────────
SUMMARY
──────────────────────────────────────────────────────────────────────

Total events extracted: 7
  • Article 1: 1 event
  • Article 2: 1 event
  • Article 3: 2 events (reciprocal)
  • Article 4: 1 event
  • Article 5: 2 events (reciprocal)

Event Quality:
  • Average confidence: 0.82
  • Average completeness: 0.71
  • Events with WHO: 7/7 (100%)
  • Events with WHOM: 7/7 (100%)
  • Events with WHERE: 7/7 (100%)
  • Events with WHEN: 6/7 (86%)
  • Events with HOW: 6/7 (86%)

✓ Saved to: output/stage3_extracted_events.json
```

**File:** `output/stage3_extracted_events.json` (first event)
```json
{
  "article_id": "article_1",
  "sentence_index": 0,
  "sentence_text": "A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu on Friday morning , killing at least 15 civilians and injuring 23 others .",
  "trigger": {
    "word": "detonated",
    "lemma": "detonate",
    "pos": "VBD",
    "index": 4,
    "type": "verb",
    "sentence_index": 0
  },
  "who": {
    "text": "Al-Shabaab",
    "type": "ORGANIZATION",
    "metadata": {},
    "from_responsibility_claim": true
  },
  "what": {
    "type": "violence",
    "trigger_word": "detonated",
    "trigger_lemma": "detonate",
    "preliminary_type": "violence"
  },
  "whom": {
    "text": "civilians",
    "type": "civilian",
    "deaths": 15,
    "injuries": 23
  },
  "where": {
    "text": "Bakara market",
    "type": "LOCATION"
  },
  "when": {
    "text": "Friday",
    "type": "EXPLICIT",
    "normalized": "2024-03-08"
  },
  "how": {
    "weapons": ["explosive", "device", "suicide bomb", "explosive device"],
    "tactics": ["suicide"],
    "text": "explosive, device, suicide bomb, explosive device"
  },
  "confidence": 0.95,
  "completeness": 1.0,
  "taxonomy_l1": "Political Violence",
  "taxonomy_l2": "Terrorism",
  "taxonomy_l3": "Suicide Bombing",
  "reciprocal_violence": false
}
```

**What Happened:**

**For Article 1:**
1. ✅ **Trigger Detection:** Found "detonated" (violence verb)
2. ✅ **WHO Extraction:** Searched sentence → Found "suicide bomber" → Checked for responsibility claim → Found "Al-Shabaab claimed responsibility" in sentence 5 → Used coreference to link → **WHO = Al-Shabaab**
3. ✅ **WHAT Extraction:** Identified event type = "violence"
4. ✅ **WHOM Extraction:** Found "civilians" as victim with casualties
5. ✅ **WHERE Extraction:** Found "Bakara market" (LOCATION entity)
6. ✅ **WHEN Extraction:** Found "Friday" → Normalized to 2024-03-08
7. ✅ **HOW Extraction:** Found weapons: "explosive", "device", "suicide bomb"
8. ✅ **Post-Processing:** Applied all 5 filters, event passed all checks
9. ✅ **Taxonomy:** Classified as Political Violence → Terrorism → Suicide Bombing

**For Article 3:**
1. ✅ **Trigger Detection:** Found "clashes" (violence noun)
2. ✅ **Reciprocal Pattern Detected:** "clashes between Hema and Lendu communities"
3. ✅ **Split into 2 events:**
   - Event 1: Hema → Lendu (with 12 deaths)
   - Event 2: Lendu → Hema (reciprocal pair)
4. ✅ **Protected from merging:** Reciprocal events kept separate
5. ✅ **Protected from filtering:** Both events preserved

---

### STAGE 4: CSV Output

**Purpose:** Convert JSON events to CSV format for analysis

#### Running Stage 4

```bash
python3 test_pipeline_stages.py --stage 4 --verbose
```

#### Output

**Console:**
```
======================================================================
  STAGE 4: CSV OUTPUT
======================================================================

Loading events from: output/stage3_extracted_events.json
✓ Loaded 7 events

Converting to CSV format...

Event 1:
  Article: article_1
  Trigger: detonated
  WHO: Al-Shabaab → WHOM: civilians (15 deaths, 23 injuries)
  WHERE: Bakara market
  WHEN: Friday (2024-03-08)

Event 2:
  Article: article_2
  Trigger: shot
  WHO: police officers → WHOM: Chidi Okonkwo
  WHERE: Lagos
  WHEN: March 18, 2024

... (5 more events)

✓ Generated CSV with 7 events
✓ Saved to: output/test_extracted_events.csv

CSV Structure:
  Rows: 7 events + 1 header = 8 total
  Columns: 24
```

**File:** `output/test_extracted_events.csv`
```csv
article_id,event_id,trigger,trigger_lemma,sentence_index,who_text,who_type,what_type,whom_text,whom_type,deaths,injuries,where_text,where_type,when_text,when_type,when_normalized,how_weapons,how_tactics,taxonomy_l1,taxonomy_l2,taxonomy_l3,confidence,completeness
article_1,event_1,detonated,detonate,0,Al-Shabaab,ORGANIZATION,violence,civilians,civilian,15,23,Bakara market,LOCATION,Friday,EXPLICIT,2024-03-08,"explosive, device, suicide bomb, explosive device",suicide,Political Violence,Terrorism,Suicide Bombing,0.95,1.00
article_2,event_2,shot,shoot,0,police officers,state,violence,Chidi Okonkwo,PERSON,,,Lagos,LOCATION,March 18,EXPLICIT,2024-03-18,gun,shooting,Political Violence,Police Violence,Police Shooting,0.70,0.67
article_3,event_3,clashes,clash,0,Hema,communal,violence,Lendu,civilian,12,,Beni,LOCATION,,,,,Political Violence,Insurgency,Insurgency,0.80,0.67
article_3,event_4,clashes,clash,0,Lendu,communal,violence,Hema,civilian,,,Beni,LOCATION,,,,,Political Violence,Insurgency,Insurgency,0.70,0.67
article_4,event_5,robbed,rob,0,armed gang,criminal,violence,Peter Mwangi,PERSON,,,Nairobi,LOCATION,,,,,Criminal Violence,Gang Violence,Gang Violence,0.75,0.50
article_5,event_6,clashes,clash,0,opposition supporters,political,violence,security forces,state,3,,Dakar,LOCATION,,,,,Political Violence,Targeted Killing,Targeted Killing,0.90,0.83
article_5,event_7,clashes,clash,0,security forces,state,violence,opposition supporters,political,,,Dakar,LOCATION,,,,,Political Violence,Targeted Killing,Targeted Killing,0.80,0.83
```

**Opening in Excel/Spreadsheet:**

1. Open Excel/LibreOffice Calc
2. File → Import → CSV
3. Select `output/test_extracted_events.csv`
4. Delimiter: Comma
5. Text qualifier: Double quote
6. Import

**Viewing in Terminal:**
```bash
# View header
head -1 output/test_extracted_events.csv

# View first event
head -2 output/test_extracted_events.csv | tail -1

# Count events
wc -l output/test_extracted_events.csv
# Output: 8 (7 events + 1 header)

# View specific columns
cut -d',' -f1,6,9,11 output/test_extracted_events.csv | column -t -s','
# Shows: article_id, who_text, whom_text, deaths
```

**What Happened:**
1. ✅ JSON events loaded
2. ✅ Each event flattened into CSV row
3. ✅ 24 columns created with all fields
4. ✅ Empty fields handled (shown as blank)
5. ✅ Lists converted to comma-separated strings
6. ✅ Ready for analysis in Excel/R/Python

---

## Common Use Cases

### Use Case 1: Process Single Article

**Scenario:** You want to test the pipeline on one article

```bash
# Process article 1 only
python3 test_pipeline_stages.py --stage all --article 1 --verbose
```

**Output Files:**
- `output/stage1_parsed_articles.json` - 1 article
- `output/stage2_nlp_annotated.json` - 1 article with annotations
- `output/stage3_extracted_events.json` - Events from article 1 only
- `output/test_extracted_events.csv` - CSV with article 1 events

### Use Case 2: Debug Specific Stage

**Scenario:** Stage 3 is failing, you want to check Stage 2 output

```bash
# Run Stage 2 only, verbose output
python3 test_pipeline_stages.py --stage 2 --article 1 --verbose

# Check output
cat output/stage2_nlp_annotated.json | jq '.sentences[0] | keys'
# Shows: ["index", "text", "tokens", "entities", "basicDependencies", ...]

# Check if violence detected
cat output/stage2_nlp_annotated.json | jq '.sentences[0].is_violence_sentence'
# Output: true or false
```

### Use Case 3: Extract Specific Information

**Scenario:** You only want to see WHO and WHOM from all events

```bash
# Extract WHO → WHOM relationships
jq '.[] | {article: .article_id, who: .who.text, whom: .whom.text, deaths: .whom.deaths}' output/stage3_extracted_events.json

# Output:
# {
#   "article": "article_1",
#   "who": "Al-Shabaab",
#   "whom": "civilians",
#   "deaths": 15
# }
# ...
```

### Use Case 4: Filter Events by Type

**Scenario:** You only want terrorism events

```bash
# Filter by taxonomy
jq '.[] | select(.taxonomy_l2 == "Terrorism")' output/stage3_extracted_events.json

# Count terrorism events
jq '[.[] | select(.taxonomy_l2 == "Terrorism")] | length' output/stage3_extracted_events.json
```

### Use Case 5: Check Event Quality

**Scenario:** You want to see events with complete 5W1H

```bash
# Events with all 5W1H fields populated
jq '.[] | select(.who != null and .whom != null and .where != null and .when != null and .how != null)' output/stage3_extracted_events.json

# Events with casualties
jq '.[] | select(.whom.deaths != null) | {article: .article_id, deaths: .whom.deaths, injuries: .whom.injuries}' output/stage3_extracted_events.json
```

### Use Case 6: Verify Coreference

**Scenario:** Check if coreference resolution is working

```bash
# Check for coreference chains
jq '.coref_chains | length' output/stage2_nlp_annotated.json

# Show first coreference chain
jq '.coref_chains[0]' output/stage2_nlp_annotated.json

# Events extracted using coreference
jq '.[] | select(.who.from_coreference == true)' output/stage3_extracted_events.json
```

### Use Case 7: Add New Articles

**Scenario:** You have a new article to process

1. **Add to `articles.md`:**
```markdown
## Article 6

**Title:** Your New Article Title
**Source:** News Source
**Date:** December 1, 2024
**Location:** City, Country
**Type:** Violence Type

**Body:**

Your article text here...
```

2. **Run pipeline:**
```bash
python3 test_pipeline_stages.py --stage all --verbose
```

3. **Check results:**
```bash
# Should now have 8 events (7 + 1 new)
jq '. | length' output/stage3_extracted_events.json
```

### Use Case 8: Export to Different Format

**Scenario:** You need JSON instead of CSV

```bash
# Pretty print JSON
cat output/stage3_extracted_events.json | jq '.' > events_pretty.json

# Convert to JSONL (one event per line)
jq -c '.[]' output/stage3_extracted_events.json > events.jsonl

# Convert to Excel-friendly format
python3 -c "
import pandas as pd
import json

with open('output/stage3_extracted_events.json') as f:
    events = json.load(f)

df = pd.json_normalize(events)
df.to_excel('events.xlsx', index=False)
print('✓ Exported to events.xlsx')
"
```

---

## Troubleshooting

### Problem 1: Server Won't Start

**Symptoms:**
```
✗ Failed to start Stanford CoreNLP server
```

**Solutions:**

**Check 1: Java installed?**
```bash
java -version
# If not found: brew install openjdk (macOS) or apt-get install default-jdk (Linux)
```

**Check 2: Port 9000 in use?**
```bash
lsof -i :9000
# If occupied: ./stop_corenlp_server.sh
```

**Check 3: Enough memory?**
```bash
# Check available RAM
free -h  # Linux
vm_stat  # macOS

# If < 4GB free, reduce memory allocation:
# Edit start_corenlp_server.sh, change -mx4g to -mx2g
```

**Check 4: CoreNLP files present?**
```bash
ls stanford-corenlp-4.5.5/*.jar | wc -l
# Should show ~30-40 jar files
```

### Problem 2: Pipeline Fails to Connect

**Symptoms:**
```
ConnectionError: Cannot connect to Stanford CoreNLP server
```

**Solutions:**

**Check 1: Server running?**
```bash
curl http://localhost:9000
# Should return HTML with "Stanford CoreNLP"
```

**Check 2: Server healthy?**
```bash
ps aux | grep CoreNLP
# Should show java process
```

**Check 3: Restart server**
```bash
./stop_corenlp_server.sh
sleep 2
./start_corenlp_server.sh
```

### Problem 3: No Events Extracted

**Symptoms:**
```
✓ Total events extracted: 0
```

**Solutions:**

**Check 1: Are there violence triggers?**
```bash
# Check if violence sentences detected
jq '[.sentences[] | select(.is_violence_sentence == true)] | length' output/stage2_nlp_annotated.json
# Should be > 0
```

**Check 2: Check trigger detection**
```bash
python3 -c "
from domain.violence_lexicon import ViolenceLexicon
lex = ViolenceLexicon()
print('Violence verbs:', list(lex.violence_verbs)[:10])
print('Violence nouns:', list(lex.violence_nouns)[:10])
"
```

**Check 3: Check Stage 2 output**
```bash
# Verify tokens have POS tags
jq '.sentences[0].tokens[0]' output/stage2_nlp_annotated.json
# Should have: word, lemma, pos, ner fields
```

### Problem 4: Missing WHO Field

**Symptoms:**
```
Events have who: null
```

**Solutions:**

**Check 1: Are there actors in text?**
```bash
# Check for ORGANIZATION or PERSON entities
jq '[.sentences[].entities[] | select(.type == "ORGANIZATION" or .type == "PERSON")]' output/stage2_nlp_annotated.json
```

**Check 2: Check for responsibility claims**
```bash
# Search for "claimed responsibility" in article
grep -i "claimed responsibility" articles.md
```

**Check 3: Check dependencies**
```bash
# Check for subject dependencies
jq '.sentences[0].basicDependencies[] | select(.dep == "nsubj")' output/stage2_nlp_annotated.json
```

### Problem 5: Slow Processing

**Symptoms:**
```
Taking > 10 seconds per article
```

**Solutions:**

**Solution 1: Increase server memory**
```bash
# Edit start_corenlp_server.sh
# Change: -mx4g to -mx6g or -mx8g
```

**Solution 2: Restart server periodically**
```bash
# After processing many articles
./stop_corenlp_server.sh
./start_corenlp_server.sh
```

**Solution 3: Process in batches**
```bash
# Process 5 articles at a time instead of all at once
python3 test_pipeline_stages.py --stage 3 --article 1 --verbose
python3 test_pipeline_stages.py --stage 3 --article 2 --verbose
# ... etc
```

---

## Understanding the Output

### JSON Structure

**Stage 1 Output:**
```
List of articles [
  {
    title: string
    source: string
    date: string
    location: string
    type: string
    body: string
  }
]
```

**Stage 2 Output:**
```
{
  article_id: string
  cleaned_text: string
  num_sentences: number
  coref_chains: [
    {
      id: string
      mentions: [
        {sentNum, text, isRepresentative}
      ]
    }
  ]
  sentences: [
    {
      index: number
      text: string
      tokens: [{word, lemma, pos, ner}]
      entities: [{text, type}]
      basicDependencies: [{dep, governor, dependent}]
      is_violence_sentence: boolean
    }
  ]
}
```

**Stage 3 Output:**
```
List of events [
  {
    article_id: string
    sentence_index: number
    trigger: {word, lemma, pos}
    who: {text, type}
    what: {type, trigger_word}
    whom: {text, type, deaths, injuries}
    where: {text, type}
    when: {text, type, normalized}
    how: {weapons, tactics}
    confidence: number (0-1)
    completeness: number (0-1)
    taxonomy_l1/l2/l3: string
    reciprocal_violence: boolean
  }
]
```

**Stage 4 Output:**
```
CSV with 24 columns (flattened event data)
```

### Field Meanings

**WHO (Actor):**
- `text`: Name of actor (e.g., "Al-Shabaab")
- `type`: ORGANIZATION, PERSON, state, communal, criminal, political
- `from_responsibility_claim`: true if extracted from "X claimed responsibility"
- `from_coreference`: true if resolved via coreference

**WHOM (Victim):**
- `text`: Name/type of victim (e.g., "civilians")
- `type`: PERSON, civilian, state, communal
- `deaths`: Number of people killed (integer or null)
- `injuries`: Number of people injured (integer or null)

**WHERE (Location):**
- `text`: Location name (e.g., "Bakara market")
- `type`: LOCATION, CITY, COUNTRY, UNKNOWN

**WHEN (Time):**
- `text`: Time expression (e.g., "Friday")
- `type`: EXPLICIT (mentioned) or IMPLICIT (inferred)
- `normalized`: ISO date (YYYY-MM-DD)

**HOW (Method):**
- `weapons`: List of weapons (e.g., ["explosive", "device"])
- `tactics`: List of tactics (e.g., ["suicide"])
- `text`: Comma-separated string

**Quality Metrics:**
- `confidence`: 0-1 (how confident we are in the extraction)
- `completeness`: 0-1 (how many W fields are filled)

**Taxonomy:**
- `taxonomy_l1`: Top level (e.g., "Political Violence")
- `taxonomy_l2`: Mid level (e.g., "Terrorism")
- `taxonomy_l3`: Specific (e.g., "Suicide Bombing")

---

## Summary

This guide has shown you:

✅ **How to set up** the pipeline (prerequisites, server startup)

✅ **How to run** each stage (with actual commands and examples)

✅ **What happens** at each stage (detailed walkthrough)

✅ **How to interpret** the output (JSON structure, field meanings)

✅ **How to use** the results (common use cases)

✅ **How to troubleshoot** problems (5 common issues with solutions)

### Next Steps

1. **Run the Quick Start** to verify everything works
2. **Process your own articles** by adding them to `articles.md`
3. **Explore the output** using `jq` commands
4. **Export to Excel** for analysis
5. **Customize** event extraction rules if needed

### Getting Help

- **Pipeline Issues:** Check TROUBLESHOOTING section above
- **Stanford CoreNLP:** See `STANFORD_NLP_GUIDE.md`
- **Coreference:** See `COREFERENCE_SETUP_GUIDE.md`
- **Testing:** See `STEP_BY_STEP_TESTING.md`

---

**Document Created:** 2025-10-29
**Status:** ✅ COMPLETE
**For:** Violent Event Annotation Pipeline v2.0
