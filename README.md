# Violent Event Extraction Pipeline

**Master's Thesis Project**  
**Author:** Binalfew Kassa Mekonnen  
**Institution:** Addis Ababa University  
**Advisor:** Fekade Getrahun  
**Title:** "Knowledge Discovery from Free Text: Extraction of Violent Events"

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [The Big Picture](#the-big-picture)
3. [System Architecture](#system-architecture)
4. [Directory Structure](#directory-structure)
5. [Component Details](#component-details)
6. [Installation & Setup](#installation--setup)
7. [Usage Examples](#usage-examples)
8. [Timeline Integration](#timeline-integration)
9. [Troubleshooting](#troubleshooting)

---

## Project Overview

### Goal

Develop an automated system for the **African Union Continental Early Warning System (AU-CEWS)** that extracts, classifies, and makes queryable violent event information from news articles.

### Input

Raw news articles from African sources

**Example:**

```
"Armed militants from Boko Haram killed 15 civilians in Maiduguri
on Tuesday morning. The attack occurred near the central market."
```

### Output

Structured event data

**Example:**

```json
{
  "event_type": "Armed Attack",
  "who": "Boko Haram",
  "what": "killed",
  "whom": "15 civilians",
  "where": "Maiduguri, Nigeria",
  "when": "Tuesday morning",
  "how": "armed attack",
  "location_detail": "near central market",
  "casualties": {
    "killed": 15,
    "wounded": 0
  }
}
```

---

## The Big Picture

### Problem Statement

AU-CEWS analysts manually read thousands of news articles to track violent events across Africa. This is:

- ⏰ **Time-consuming:** Takes hours per day
- 🔍 **Inconsistent:** Different analysts may extract different information
- 📊 **Not scalable:** Cannot process all available news sources
- 🔗 **Hard to query:** Information trapped in documents

### Solution

**Automated NLP pipeline that:**

1. Reads news articles
2. Identifies violent events
3. Extracts structured information (Who, What, Whom, Where, When, How)
4. Classifies events into 95-category taxonomy
5. Stores in queryable knowledge base

### Approach

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: Rule-Based Baseline (Weeks 3-6)              │
│  - Build NLP pipeline using lexicons and patterns      │
│  - Expected accuracy: 60-70%                           │
│  - Deliverable: Working prototype                      │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: Human Annotation (Weeks 1-8, parallel)       │
│  - 3-4 annotators label 2,500-3,500 events            │
│  - Create ground truth for training                    │
│  - Deliverable: Annotated dataset                      │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 3: Machine Learning (Weeks 9-12)                │
│  - Train models on annotated data                      │
│  - Expected accuracy: 85-95%                           │
│  - Deliverable: Production-ready ML system             │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│  PHASE 4: Integration & Deployment (Weeks 13-16)       │
│  - Build knowledge base (PostgreSQL + Neo4j)           │
│  - Develop Q&A system                                  │
│  - Create web interface                                │
│  - Deliverable: Deployed AU-CEWS system                │
└─────────────────────────────────────────────────────────┘
```

---

## System Architecture

### High-Level Pipeline

```
┌─────────────┐
│ Raw Article │
└──────┬──────┘
       ↓
┌──────────────────┐
│  Text Cleaning   │  ← preprocessing/text_cleaner.py
│  & Normalization │
└──────┬───────────┘
       ↓
┌──────────────────┐
│  Stanford        │  ← stanford_nlp/corenlp_wrapper.py
│  CoreNLP         │
│  Analysis        │
└──────┬───────────┘
       ↓
┌──────────────────┐
│  Feature         │  ← features/lexical_features.py
│  Extraction      │     features/syntactic_features.py
└──────┬───────────┘
       ↓
┌──────────────────┐
│  Domain-Specific │  ← domain/violence_lexicon.py
│  Processing      │     domain/african_ner.py
└──────┬───────────┘
       ↓
┌──────────────────┐
│  Event Detection │  ← Main pipeline logic
│  & 5W1H Extract  │
└──────┬───────────┘
       ↓
┌──────────────────┐
│  Structured      │
│  Output          │
│  (JSON/Excel)    │
└──────────────────┘
```

### Data Flow Example

```
INPUT: "Boko Haram militants killed 15 people in Maiduguri on Tuesday."

↓ [Text Cleaning]
Normalized: "Boko Haram militants killed 15 people in Maiduguri on Tuesday."

↓ [CoreNLP]
Tokens: ["Boko", "Haram", "militants", "killed", "15", "people", ...]
POS: [NNP, NNP, NNS, VBD, CD, NNS, ...]
NER: [ORGANIZATION, ORGANIZATION, O, O, NUMBER, O, LOCATION, ...]
Dependencies: [nsubj(killed, militants), dobj(killed, people), ...]

↓ [Feature Extraction]
Violence keywords: ["killed"]
Actor mention: ["Boko Haram militants"]
Numbers: [15]

↓ [Domain Processing]
Violence detected: True (lexicon match: "killed")
African entity: "Maiduguri" → Nigeria, Borno State

↓ [Event Detection]
Event trigger: "killed" at position 4
Event type: Armed Attack

↓ [5W1H Extraction]
Who: "Boko Haram militants"
What: "killed"
Whom: "15 people"
Where: "Maiduguri"
When: "Tuesday"
How: [inferred from context: "attack"]

OUTPUT: Structured event record
```

---

## Directory Structure

```
nlp_pipeline/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── config.yaml                        # Configuration settings
│
├── preprocessing/                     # Text cleaning modules
│   ├── __init__.py
│   ├── text_cleaner.py               # HTML removal, normalization
│   └── sentence_splitter.py          # Sentence tokenization
│
├── stanford_nlp/                      # CoreNLP integration
│   ├── __init__.py
│   └── corenlp_wrapper.py            # Java CoreNLP interface
│
├── features/                          # Feature extraction
│   ├── __init__.py
│   ├── lexical_features.py           # Word-level features
│   └── syntactic_features.py         # Parse tree features
│
├── domain/                   # African violence context
│   ├── __init__.py
│   ├── violence_lexicon.py           # Violence keywords
│   └── african_ner.py                # African entity recognition
│
├── output/                            # Generated results
│   ├── extracted_events.json
│   └── extracted_events.xlsx
│
├── logs/                              # System logs
│   └── pipeline.log
│
├── resources/                         # Data files
│   ├── violence_keywords.txt
│   ├── african_locations.txt
│   └── actor_gazetteers.txt
│
├── stanford-corenlp-4.5.5/           # CoreNLP installation
│   └── [JAR files]
│
├── pipeline.py                        # Main orchestrator
├── test_corenlp.py                   # CoreNLP test
└── test_pipeline.py                  # Full pipeline test
```

---

## Component Details

### 1. Text Preprocessing (`preprocessing/`)

#### `text_cleaner.py`

**Purpose:** Clean and normalize raw news text before NLP processing.

**What it does:**

- Removes HTML tags (`<p>`, `<div>`, etc.)
- Fixes encoding issues (converts `&#233;` → `é`)
- Normalizes whitespace (multiple spaces → single space)
- Removes special characters that confuse NLP
- Handles African-specific text issues

**Example Input:**

```html
<p>
  Armed militants from Boko&nbsp;Haram killed 15&#160;civilians in
  Maiduguri&#8230;
</p>
```

**Example Output:**

```
Armed militants from Boko Haram killed 15 civilians in Maiduguri...
```

**Key Functions:**

```python
def clean_html(text: str) -> str:
    """Remove HTML tags and entities"""

def normalize_whitespace(text: str) -> str:
    """Fix spacing issues"""

def fix_encoding(text: str) -> str:
    """Handle unicode and encoding problems"""
```

**Usage:**

```python
from preprocessing.text_cleaner import TextCleaner

cleaner = TextCleaner()
clean_text = cleaner.clean(raw_article)
```

---

#### `sentence_splitter.py`

**Purpose:** Split article into sentences for analysis.

**What it does:**

- Handles abbreviations (Dr., Mr., U.S.)
- Respects quotes and dialogue
- African name handling (Al-Shabaab, Boko Haram)
- Splits on periods, exclamation marks, question marks

**Example Input:**

```
Dr. Ahmed said militants attacked Maiduguri. 15 people died.
The U.N. condemned the violence.
```

**Example Output:**

```python
[
  "Dr. Ahmed said militants attacked Maiduguri.",
  "15 people died.",
  "The U.N. condemned the violence."
]
```

**Usage:**

```python
from preprocessing.sentence_splitter import SentenceSplitter

splitter = SentenceSplitter()
sentences = splitter.split(clean_text)
```

---

### 2. Stanford CoreNLP Integration (`stanford_nlp/`)

#### `corenlp_wrapper.py`

**Purpose:** Interface to Stanford CoreNLP for fundamental NLP tasks.

**What it does:**

- **Tokenization:** Splits text into words
- **POS Tagging:** Labels parts of speech (noun, verb, adjective)
- **Lemmatization:** Finds word roots (killed → kill)
- **Named Entity Recognition (NER):** Finds people, places, organizations
- **Dependency Parsing:** Shows grammatical relationships
- **Constituency Parsing:** Creates parse trees

**Example:**

**Input:**

```
"Armed militants killed 15 civilians in Maiduguri on Tuesday."
```

**Output:**

```python
{
  "sentences": [{
    "tokens": [
      {"word": "Armed", "pos": "JJ", "ner": "O", "lemma": "armed"},
      {"word": "militants", "pos": "NNS", "ner": "O", "lemma": "militant"},
      {"word": "killed", "pos": "VBD", "ner": "O", "lemma": "kill"},
      {"word": "15", "pos": "CD", "ner": "NUMBER", "lemma": "15"},
      {"word": "civilians", "pos": "NNS", "ner": "O", "lemma": "civilian"},
      {"word": "in", "pos": "IN", "ner": "O", "lemma": "in"},
      {"word": "Maiduguri", "pos": "NNP", "ner": "LOCATION", "lemma": "Maiduguri"},
      {"word": "on", "pos": "IN", "ner": "O", "lemma": "on"},
      {"word": "Tuesday", "pos": "NNP", "ner": "DATE", "lemma": "Tuesday"}
    ],
    "basicDependencies": [
      {"dep": "amod", "governor": "militants", "dependent": "Armed"},
      {"dep": "nsubj", "governor": "killed", "dependent": "militants"},
      {"dep": "dobj", "governor": "killed", "dependent": "civilians"},
      {"dep": "nummod", "governor": "civilians", "dependent": "15"},
      {"dep": "case", "governor": "Maiduguri", "dependent": "in"},
      {"dep": "nmod", "governor": "killed", "dependent": "Maiduguri"}
    ]
  }]
}
```

**Key Methods:**

```python
def annotate(text: str) -> Dict:
    """Run full CoreNLP pipeline"""

def get_tokens(sentence: Dict) -> List[Dict]:
    """Extract token information"""

def get_entities(sentence: Dict) -> List[Dict]:
    """Extract named entities"""

def get_dependencies(sentence: Dict) -> List[Dict]:
    """Extract dependency relations"""
```

**Usage:**

```python
from stanford_nlp.corenlp_wrapper import CoreNLPWrapper

nlp = CoreNLPWrapper('./stanford-corenlp-4.5.5')
annotation = nlp.annotate(text)

for sentence in annotation['sentences']:
    tokens = nlp.get_tokens(sentence)
    entities = nlp.get_entities(sentence)
    deps = nlp.get_dependencies(sentence)

nlp.close()
```

---

### 3. Feature Extraction (`features/`)

#### `lexical_features.py`

**Purpose:** Extract word-level features for machine learning.

**What it does:**

- Counts violence-related keywords
- Identifies actor mentions (who)
- Extracts casualty numbers
- Finds weapon mentions
- Computes word frequencies
- Creates bag-of-words representations

**Example:**

**Input Sentence:**

```
"Armed militants with AK-47 rifles killed 15 civilians."
```

**Extracted Features:**

```python
{
  "violence_keywords": ["armed", "killed"],
  "violence_keyword_count": 2,
  "weapon_mentions": ["AK-47", "rifles"],
  "weapon_count": 2,
  "actor_keywords": ["militants"],
  "casualty_numbers": [15],
  "has_casualty_info": True,
  "word_count": 8,
  "violence_density": 0.25,  # 2 violence words / 8 total
  "contains_death_verb": True,  # "killed"
  "contains_weapon": True
}
```

**Key Functions:**

```python
def extract_violence_keywords(text: str) -> List[str]:
    """Find violence-related words"""

def extract_numbers(text: str) -> List[int]:
    """Extract numeric values (casualties, dates)"""

def extract_actor_mentions(text: str, entities: List) -> List[str]:
    """Identify perpetrators and victims"""

def compute_violence_density(text: str) -> float:
    """Ratio of violence words to total words"""
```

**Usage:**

```python
from features.lexical_features import LexicalFeatureExtractor

extractor = LexicalFeatureExtractor()
features = extractor.extract(text, entities)
```

---

#### `syntactic_features.py`

**Purpose:** Extract grammatical structure features.

**What it does:**

- Analyzes sentence structure
- Finds subject-verb-object patterns
- Identifies action-target relationships
- Extracts prepositional phrases (location, time)
- Computes parse tree depth
- Identifies passive vs. active voice

**Example:**

**Input:**

```
Sentence: "Militants killed civilians in Maiduguri."
Dependencies: [
  nsubj(killed, militants),
  dobj(killed, civilians),
  nmod(killed, Maiduguri)
]
```

**Extracted Features:**

```python
{
  "has_violence_predicate": True,
  "violence_verb": "killed",
  "subject": "militants",
  "object": "civilians",
  "subject_object_pair": ("militants", "civilians"),
  "location_phrase": "in Maiduguri",
  "location": "Maiduguri",
  "parse_tree_depth": 4,
  "voice": "active",
  "has_temporal_modifier": False,
  "dependency_patterns": ["nsubj-VBD-dobj"]
}
```

**Key Functions:**

```python
def extract_svo_triples(dependencies: List) -> List[Tuple]:
    """Find subject-verb-object patterns"""

def find_violence_predicates(dependencies: List, pos_tags: List) -> List[str]:
    """Identify violent action verbs"""

def extract_modifiers(dependencies: List) -> Dict:
    """Find location, time, manner modifiers"""

def compute_tree_depth(parse_tree: Dict) -> int:
    """Calculate parse tree complexity"""
```

**Usage:**

```python
from features.syntactic_features import SyntacticFeatureExtractor

extractor = SyntacticFeatureExtractor()
features = extractor.extract(sentence_annotation)
```

---

### 4. Domain-Specific Modules (`domain/`)

#### `violence_lexicon.py`

**Purpose:** African conflict-specific violence terminology.

**What it does:**

- Maintains violence keyword lexicons
- Categorizes violence types
- Handles African conflict terminology
- Supports multi-language (English, French, Arabic terms)

**Lexicon Categories:**

1. **Death Verbs:**

```python
DEATH_VERBS = [
    "killed", "murdered", "slaughtered", "massacred",
    "executed", "assassinated", "slain"
]
```

2. **Attack Verbs:**

````python
ATTACK_VERBS = [
    "attacked", "raided", "ambushed", "stormed",
    "assaulted", "struck", "bombed"
]

3. **Displacement:**
```python
DISPLACEMENT_TERMS = [
    "fled", "displaced", "evacuated", "forced to leave",
    "refugees", "internally displaced"
]
````

4. **African Groups:**

```python
AFRICAN_GROUPS = [
    "Boko Haram", "Al-Shabaab", "AQIM", "Seleka",
    "Anti-Balaka", "M23", "FDLR", "Janjaweed"
]
```

5. **Weapons:**

```python
WEAPONS = [
    "AK-47", "machete", "IED", "suicide bomb",
    "rocket", "grenade", "rifle"
]
```

**Example:**

**Input:**

```
"Al-Shabaab militants launched a mortar attack on the base."
```

**Lexicon Matches:**

```python
{
  "violence_type": "attack",
  "matched_keywords": ["attack", "mortar"],
  "actor_group": "Al-Shabaab",
  "weapon": "mortar",
  "is_violent_event": True,
  "confidence": 0.95
}
```

**Usage:**

```python
from domain.violence_lexicon import ViolenceLexicon

lexicon = ViolenceLexicon()
matches = lexicon.match(text)
is_violent = lexicon.is_violent_event(text)
```

---

#### `african_ner.py`

**Purpose:** Enhanced named entity recognition for African contexts.

**What it does:**

- Augments CoreNLP with African place names
- Recognizes African organizations
- Handles ethnic groups
- Knows regional terminology
- Disambiguates location names

**Gazetteers:**

1. **Locations:**

```python
AFRICAN_CITIES = {
    "Maiduguri": {"country": "Nigeria", "region": "Borno"},
    "Mogadishu": {"country": "Somalia", "region": "Banaadir"},
    "Goma": {"country": "DRC", "region": "North Kivu"},
    # ... 500+ cities
}
```

2. **Ethnic Groups:**

```python
ETHNIC_GROUPS = [
    "Hutu", "Tutsi", "Fulani", "Hausa",
    "Oromo", "Amhara", "Tigray"
]
```

3. **Organizations:**

```python
ORGANIZATIONS = [
    "AMISOM", "ECOWAS", "MONUSCO",
    "African Union", "IGAD"
]
```

**Example:**

**Input:**

```
"Violence erupted in Goma between Hutu and Tutsi groups."
CoreNLP NER: [("Goma", "LOCATION")]  # Misses ethnic groups
```

**Enhanced Output:**

```python
{
  "entities": [
    {
      "text": "Goma",
      "type": "LOCATION",
      "country": "DRC",
      "region": "North Kivu",
      "latitude": -1.6740,
      "longitude": 29.2288
    },
    {
      "text": "Hutu",
      "type": "ETHNIC_GROUP"
    },
    {
      "text": "Tutsi",
      "type": "ETHNIC_GROUP"
    }
  ]
}
```

**Usage:**

```python
from domain.african_ner import AfricanNER

aner = AfricanNER()
entities = aner.enhance_entities(corenlp_entities, text)
location_info = aner.get_location_details("Maiduguri")
```

---

### 5. Main Pipeline (`pipeline.py`)

**Purpose:** Orchestrate all components into end-to-end system.

**What it does:**

- Coordinates all pipeline stages
- Manages data flow between components
- Implements event detection logic
- Extracts 5W1H information
- Outputs structured results

**Pipeline Stages:**

```python
class ViolentEventNLPPipeline:
    def __init__(self, config):
        self.text_cleaner = TextCleaner()
        self.corenlp = CoreNLPWrapper(config['stanford_path'])
        self.lexical_extractor = LexicalFeatureExtractor()
        self.syntactic_extractor = SyntacticFeatureExtractor()
        self.violence_lexicon = ViolenceLexicon()
        self.african_ner = AfricanNER()

    def process_article(self, article_text, article_id):
        """
        Process one article through full pipeline.

        Returns:
        {
          "article_id": "ART_001",
          "events": [
            {
              "event_id": "EVT_001",
              "who": "Boko Haram",
              "what": "killed",
              "whom": "15 civilians",
              "where": "Maiduguri, Nigeria",
              "when": "Tuesday",
              "how": "armed attack",
              "event_type": "Armed Attack",
              "confidence": 0.89
            }
          ]
        }
        """
```

**Event Detection Algorithm:**

```python
def detect_events(self, sentences):
    """
    1. For each sentence:
       - Check if violence lexicon matches
       - Look for violence predicates (killed, attacked, etc.)
       - Verify casualty numbers or victim mentions

    2. If violence detected:
       - Extract subject (WHO)
       - Extract object (WHOM)
       - Extract location modifiers (WHERE)
       - Extract temporal modifiers (WHEN)
       - Infer method (HOW)

    3. Create event record
    """
```

**Usage:**

```python
from pipeline import ViolentEventNLPPipeline

# Initialize
config = {'stanford_path': './stanford-corenlp-4.5.5'}
pipeline = ViolentEventNLPPipeline(config)

# Process article
article = """
Armed militants from Boko Haram killed 15 civilians
in Maiduguri on Tuesday morning.
"""

result = pipeline.process_article(article, "ART_001")

# Output
print(result['events'])
# [{
#   "who": "Boko Haram militants",
#   "what": "killed",
#   "whom": "15 civilians",
#   ...
# }]

pipeline.close()
```

---

## Installation & Setup

### Prerequisites

- **Python:** 3.8 or higher
- **Java:** JDK 8 or higher (for CoreNLP)
- **Memory:** 8GB RAM minimum (16GB recommended)
- **Disk:** 10GB free space

### Step 1: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

**requirements.txt:**

```
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=0.24.0
openpyxl>=3.0.0
```

### Step 2: Download Stanford CoreNLP

```bash
# Download CoreNLP 4.5.5
wget http://nlp.stanford.edu/software/stanford-corenlp-4.5.5.zip

# Extract
unzip stanford-corenlp-4.5.5.zip

# Verify
ls stanford-corenlp-4.5.5/
# Should see: stanford-corenlp-4.5.5.jar and other files
```

### Step 3: Verify Java Installation

```bash
java -version
# Should show: java version "1.8.0" or higher
```

If Java not installed:

- **Mac:** `brew install openjdk@11`
- **Ubuntu:** `sudo apt install openjdk-11-jdk`
- **Windows:** Download from [java.com](https://www.java.com)

### Step 4: Test Installation

```bash
# Test CoreNLP
python3 test_corenlp.py

# Expected output:
# Initializing CoreNLP (may take 30 seconds)...
# CoreNLP initialized at: ./stanford-corenlp-4.5.5
# Annotating text...
# ✓ Tokens (12): ['Armed', 'militants', 'killed', '15', 'civilians']...
# ✓ Entities: [{'text': 'Maiduguri', 'type': 'LOCATION'}, ...]
# ✓ Dependencies (12): [{'relation': 'nsubj', ...}, ...]
# ✅ CoreNLP test passed!
```

---

## Usage Examples

### Example 1: Process Single Article

```python
from pipeline import ViolentEventNLPPipeline

# Initialize pipeline
config = {
    'stanford_corenlp': {'path': './stanford-corenlp-4.5.5'},
    'violence_lexicon': {'path': './resources/violence_keywords.txt'}
}

pipeline = ViolentEventNLPPipeline(config)

# Process article
article = """
Suspected Al-Shabaab militants ambushed a convoy near Mogadishu
on Monday, killing 8 soldiers and wounding 12 others. The attack
occurred on the road to Afgoye. Security forces returned fire
but the attackers escaped.
"""

result = pipeline.process_article(article, article_id='ART_001')

# Print results
for event in result['events']:
    print(f"Event: {event['what']}")
    print(f"  Who: {event['who']}")
    print(f"  Whom: {event['whom']}")
    print(f"  Where: {event['where']}")
    print(f"  When: {event['when']}")
    print()

pipeline.close()
```

**Output:**

```
Event: killed
  Who: Al-Shabaab militants
  Whom: 8 soldiers
  Where: near Mogadishu, road to Afgoye
  When: Monday

Event: wounded
  Who: Al-Shabaab militants
  Whom: 12 others
  Where: near Mogadishu
  When: Monday
```

---

### Example 2: Batch Process Multiple Articles

```python
import pandas as pd
from pipeline import ViolentEventNLPPipeline

# Load articles
articles_df = pd.read_excel('input_articles.xlsx')

# Initialize pipeline
pipeline = ViolentEventNLPPipeline(config)

# Process all articles
all_events = []

for idx, row in articles_df.iterrows():
    print(f"Processing article {idx+1}/{len(articles_df)}...")

    result = pipeline.process_article(
        article_text=row['article_text'],
        article_id=row['article_id']
    )

    all_events.extend(result['events'])

# Save results
events_df = pd.DataFrame(all_events)
events_df.to_excel('extracted_events.xlsx', index=False)

print(f"Extracted {len(all_events)} events from {len(articles_df)} articles")

pipeline.close()
```

---

### Example 3: Extract Features for ML Training

```python
from features.lexical_features import LexicalFeatureExtractor
from features.syntactic_features import SyntacticFeatureExtractor
from stanford_nlp.corenlp_wrapper import CoreNLPWrapper

# Initialize
nlp = CoreNLPWrapper('./stanford-corenlp-4.5.5')
lex_extractor = LexicalFeatureExtractor()
syn_extractor = SyntacticFeatureExtractor()

# Process text
text = "Armed militants killed 15 civilians in Maiduguri."
annotation = nlp.annotate(text)

# Extract features
sentence = annotation['sentences'][0]
lexical_features = lex_extractor.extract(text, sentence)
syntactic_features = syn_extractor.extract(sentence)

# Combine features for ML
features = {**lexical_features, **syntactic_features}

print(f"Total features: {len(features)}")
print(f"Violence keywords: {features['violence_keywords']}")
print(f"SVO pattern: {features['subject_object_pair']}")

nlp.close()
```

**Output:**

```
Total features: 24
Violence keywords: ['armed', 'killed']
SVO pattern: ('militants', 'civilians')
```

---

### Example 4: Test Violence Detection

```python
from domain.violence_lexicon import ViolenceLexicon

lexicon = ViolenceLexicon()

# Test cases
test_sentences = [
    "Armed militants killed 15 civilians.",  # Violence
    "The president visited the hospital.",    # Not violence
    "Boko Haram attacked the village.",      # Violence
    "Farmers harvested crops yesterday.",     # Not violence
]

for sentence in test_sentences:
    is_violent = lexicon.is_violent_event(sentence)
    matches = lexicon.match(sentence)

    print(f"'{sentence}'")
    print(f"  Violent: {is_violent}")
    print(f"  Matches: {matches['matched_keywords']}")
    print()
```

**Output:**

```
'Armed militants killed 15 civilians.'
  Violent: True
  Matches: ['armed', 'killed', 'militants']

'The president visited the hospital.'
  Violent: False
  Matches: []

'Boko Haram attacked the village.'
  Violent: True
  Matches: ['Boko Haram', 'attacked']

'Farmers harvested crops yesterday.'
  Violent: False
  Matches: []
```

---

### Example 5: Enhanced African NER

```python
from stanford_nlp.corenlp_wrapper import CoreNLPWrapper
from domain.african_ner import AfricanNER

nlp = CoreNLPWrapper('./stanford-corenlp-4.5.5')
aner = AfricanNER()

text = "Violence erupted in Goma between Hutu and Tutsi groups."

# Standard CoreNLP NER
annotation = nlp.annotate(text)
corenlp_entities = nlp.get_entities(annotation['sentences'][0])

print("CoreNLP entities:")
for ent in corenlp_entities:
    print(f"  {ent['text']} → {ent['type']}")

# Enhanced with African NER
enhanced_entities = aner.enhance_entities(corenlp_entities, text)

print("\nEnhanced entities:")
for ent in enhanced_entities:
    print(f"  {ent['text']} → {ent['type']}")
    if 'country' in ent:
        print(f"    Country: {ent['country']}, Region: {ent['region']}")

nlp.close()
```

**Output:**

```
CoreNLP entities:
  Goma → LOCATION

Enhanced entities:
  Goma → LOCATION
    Country: DRC, Region: North Kivu
  Hutu → ETHNIC_GROUP
  Tutsi → ETHNIC_GROUP
```

---

## Timeline Integration

### How Components Map to 16-Week Timeline

| Weeks     | Phase                     | Components Used                                                                            |
| --------- | ------------------------- | ------------------------------------------------------------------------------------------ |
| **1-2**   | Annotation Infrastructure | - Excel templates<br>- Validation scripts<br>- Annotation guidelines                       |
| **3-6**   | Build NLP Pipeline        | - `preprocessing/`<br>- `stanford_nlp/`<br>- `features/`<br>- `domain/`<br>- `pipeline.py` |
| **7-8**   | Database Design           | - PostgreSQL schema<br>- Neo4j graph<br>- API specs                                        |
| **9-12**  | Machine Learning          | - Use extracted features<br>- Train on annotated data<br>- SVM, Random Forest, BERT        |
| **13-15** | System Integration        | - Full pipeline<br>- Knowledge base<br>- Q&A system<br>- Web interface                     |
| **16**    | Final Evaluation          | - Comprehensive testing<br>- Performance analysis<br>- Thesis writing                      |

### Current Status: Week 3-6 (NLP Pipeline)

**Completed:**

- ✅ CoreNLP integration
- ✅ Text preprocessing
- ✅ Feature extraction framework
- ✅ Violence lexicon
- ✅ African NER

**Next Steps:**

1. Test on real African news articles
2. Evaluate baseline accuracy
3. Identify improvement areas
4. Use for annotation guidance (help annotators)
5. Prepare for ML training (Weeks 9-12)

---

## Performance Expectations

### Baseline System (Current - Weeks 3-6)

**Approach:** Rule-based with lexicons and patterns

**Expected Accuracy:**

- Event Detection: 65-75%
- 5W1H Extraction: 60-70%
- Event Classification: 55-65%

**Strengths:**

- ✅ Fast (processes 1 article/second)
- ✅ Interpretable (can see why it made decision)
- ✅ No training data needed
- ✅ Good for common patterns

**Weaknesses:**

- ❌ Misses implicit violence
- ❌ Struggles with context
- ❌ Cannot generalize to new patterns
- ❌ Brittle (small changes break rules)

### ML System (After Weeks 9-12)

**Approach:** Supervised learning on annotated data

**Expected Accuracy:**

- Event Detection: 85-92%
- 5W1H Extraction: 82-88%
- Event Classification: 80-90%

**Improvements:**

- ✅ Learns from examples
- ✅ Handles context better
- ✅ Generalizes to new patterns
- ✅ Improves with more data

---

## Troubleshooting

### Issue 1: CoreNLP Won't Start

**Symptoms:**

```
RuntimeError: CoreNLP failed with return code 1
```

**Solutions:**

1. **Check Java version:**

```bash
java -version
# Need Java 8 or higher
```

2. **Increase memory:**

```python
nlp = CoreNLPWrapper('./stanford-corenlp-4.5.5', memory='8g')
```

3. **Verify JAR files exist:**

```bash
ls stanford-corenlp-4.5.5/*.jar
# Should see stanford-corenlp-4.5.5.jar
```

---

### Issue 2: Slow Processing

**Symptoms:** Takes >5 seconds per article

**Solutions:**

1. **First run is slow (model loading):**

   - First article: 30-45 seconds (loads models)
   - Subsequent articles: 1-2 seconds each
   - Keep pipeline object alive for batch processing

2. **Reduce CoreNLP annotators:**

```python
# In corenlp_wrapper.py, change annotators:
'annotators': 'tokenize,ssplit,pos,ner'  # Remove parse,depparse
```

3. **Process in batches:**

```python
# Don't create new pipeline for each article
pipeline = ViolentEventNLPPipeline(config)
for article in articles:  # Process many
    result = pipeline.process_article(article)
pipeline.close()  # Close once at end
```

---

### Issue 3: Low Accuracy on Test Articles

**Symptoms:** Missing obvious violent events

**Solutions:**

1. **Check violence lexicon:**

```python
# Add missing keywords
lexicon.add_violence_keyword("massacred")
lexicon.add_actor_group("ISWAP")
```

2. **Examine false negatives:**

```python
# Log what was missed
if not event_detected:
    print(f"Missed: {sentence}")
    print(f"Tokens: {tokens}")
    print(f"Entities: {entities}")
```

3. **Adjust detection thresholds:**

```python
# Lower confidence threshold
MIN_CONFIDENCE = 0.5  # Instead of 0.7
```

---

### Issue 4: Memory Errors

**Symptoms:**

```
java.lang.OutOfMemoryError: Java heap space
```

**Solutions:**

1. **Increase Java heap:**

```python
nlp = CoreNLPWrapper('./stanford-corenlp-4.5.5', memory='8g')
```

2. **Process smaller batches:**

```python
# Process 50 articles at a time instead of all
for i in range(0, len(articles), 50):
    batch = articles[i:i+50]
    # Process batch
```

3. **Close and restart pipeline periodically:**

```python
for i, article in enumerate(articles):
    if i % 100 == 0:  # Every 100 articles
        pipeline.close()
        pipeline = ViolentEventNLPPipeline(config)
```

---

### Issue 5: African Entities Not Recognized

**Symptoms:** "Maiduguri" not detected as location

**Solutions:**

1. **Add to gazetteer:**

```python
# In african_ner.py
AFRICAN_CITIES["Maiduguri"] = {
    "country": "Nigeria",
    "region": "Borno State"
}
```

2. **Use fuzzy matching:**

```python
# Handle misspellings
"Maidugri" → "Maiduguri"
"Al Shabaab" → "Al-Shabaab"
```

3. **Check CoreNLP language:**

```python
# Ensure English model is used
props = {'annotators': 'tokenize,ssplit,pos,ner',
         'ner.model': 'edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz'}
```

---

## Next Steps

### Immediate (This Week)

1. **Test on real articles:**

   - Download 50 African news articles
   - Run through pipeline
   - Manually verify accuracy

2. **Measure baseline performance:**

   - Calculate precision, recall, F1
   - Identify error patterns
   - Document limitations

3. **Start annotator recruitment:**
   - Review annotation guidelines
   - Recruit 3-4 annotators
   - Schedule training session

### Short-term (Weeks 4-6)

1. **Refine pipeline based on tests:**

   - Add missing violence keywords
   - Expand African gazetteers
   - Improve 5W1H extraction

2. **Support annotation team:**

   - Use pipeline to pre-label articles
   - Help annotators work faster
   - Collect 500+ annotated events

3. **Prepare for ML phase:**
   - Feature engineering
   - Dataset splitting
   - Model selection research

### Medium-term (Weeks 9-12)

1. **Train ML models:**

   - Use annotated data
   - Try multiple algorithms
   - Optimize hyperparameters

2. **Evaluate improvements:**

   - Compare: Baseline vs. ML
   - Statistical significance tests
   - Error analysis

3. **Prepare for deployment:**
   - Optimize inference speed
   - Package for production
   - Write documentation

---

## Contact & Support

**Author:** Binalfew Kassa Mekonnen  
**Advisor:** Fekade Getrahun  
**Institution:** Addis Ababa University  
**Project:** Master's Thesis - Knowledge Discovery from Free Text

**For issues or questions:**

1. Check this README first
2. Review code comments in each module
3. Contact advisor for guidance

---

## References

- Stanford CoreNLP: https://stanfordnlp.github.io/CoreNLP/
- African Union CEWS: https://www.peaceau.org/en/page/28-early-warning-system-continental-early-warning-system
- Violence Categorization: Armed Conflict Location & Event Data Project (ACLED)
- NLP for Conflict Analysis: Leetaru, K. (2012). "Data Mining Methods for Conflict Prediction"

---

**Last Updated:** October 19, 2025  
**Version:** 1.0 - Baseline Pipeline  
**Status:** Week 3 of 16-week timeline
