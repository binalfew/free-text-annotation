# Stanford CoreNLP: Complete Guide

**Date:** 2025-10-29
**Purpose:** Comprehensive guide to understanding how Stanford CoreNLP works and how we use it

---

## Table of Contents

1. [What is Stanford CoreNLP?](#what-is-stanford-corenlp)
2. [How It Works: The Processing Pipeline](#how-it-works-the-processing-pipeline)
3. [Core Annotators Explained](#core-annotators-explained)
4. [How We Use It in This Project](#how-we-use-it-in-this-project)
5. [Example Walkthrough](#example-walkthrough)
6. [Configuration & Setup](#configuration--setup)

---

## What is Stanford CoreNLP?

Stanford CoreNLP is a **natural language processing (NLP) toolkit** developed by Stanford University. It takes raw text and transforms it into structured linguistic data that machines can understand.

### What Does It Do?

**Input:** Raw text (e.g., "A suicide bomber detonated a device in Mogadishu.")

**Output:** Structured annotations including:
- Individual words (tokens)
- Part-of-speech tags (noun, verb, adjective, etc.)
- Named entities (people, places, organizations)
- Sentence structure (dependencies)
- Coreferences (pronouns linking back to entities)

### Why We Need It

To extract violent events from news articles, we need to:
1. **Identify words** - Break text into analyzable units
2. **Understand grammar** - Know which words are verbs (potential triggers)
3. **Find entities** - Identify actors, victims, and locations
4. **Parse structure** - Understand who did what to whom

Stanford CoreNLP provides all these capabilities in one unified toolkit.

---

## How It Works: The Processing Pipeline

Stanford CoreNLP processes text through a **series of annotators**, where each annotator adds a layer of analysis. Think of it like an assembly line where each station adds more information.

### The Pipeline Flow

```
Raw Text
   ↓
[1] Tokenization ────→ Words split into tokens
   ↓
[2] Sentence Splitting ────→ Text divided into sentences
   ↓
[3] POS Tagging ────→ Each word tagged with part-of-speech
   ↓
[4] Lemmatization ────→ Words reduced to base forms
   ↓
[5] Named Entity Recognition ────→ Entities identified and classified
   ↓
[6] Dependency Parsing ────→ Grammatical relationships mapped
   ↓
[7] Coreference Resolution ────→ Pronouns linked to entities
   ↓
Fully Annotated Document
```

### Processing Levels

**Level 1: Word-Level** (Tokenization, POS, Lemmatization)
- Breaks text into individual words
- Tags each word's grammatical role
- Reduces words to their dictionary form

**Level 2: Entity-Level** (NER)
- Identifies and classifies named entities
- Groups multi-word entities (e.g., "Al-Shabaab", "Bakara market")

**Level 3: Sentence-Level** (Dependency Parsing)
- Maps relationships between words
- Identifies subjects, objects, modifiers

**Level 4: Document-Level** (Coreference)
- Tracks entities across sentences
- Resolves pronouns ("he" → "John Smith")

---

## Core Annotators Explained

### 1. Tokenization

**What:** Splits text into individual words (tokens)

**How:** Uses whitespace and punctuation as delimiters

**Example:**
```
Input: "A suicide bomber detonated a device."

Output:
["A", "suicide", "bomber", "detonated", "a", "device", "."]
```

**Why It Matters:** Every subsequent analysis operates on tokens

---

### 2. Sentence Splitting

**What:** Divides text into sentence boundaries

**How:** Uses punctuation (periods, exclamation marks, question marks) and capitalization patterns

**Example:**
```
Input: "The attack killed 15 people. Al-Shabaab claimed responsibility."

Output:
Sentence 0: "The attack killed 15 people."
Sentence 1: "Al-Shabaab claimed responsibility."
```

**Why It Matters:** Events are extracted per-sentence in our pipeline

---

### 3. POS (Part-of-Speech) Tagging

**What:** Labels each word with its grammatical category

**How:** Uses machine learning models trained on millions of hand-tagged sentences

**Tags Used:** Penn Treebank tagset (NN, VBD, JJ, etc.)

**Example:**
```
"A suicide bomber detonated an explosive device"
 ↓    ↓      ↓        ↓        ↓      ↓       ↓
DT   NN     NN      VBD      DT     JJ      NN

DT  = Determiner ("a", "an", "the")
NN  = Noun, singular ("bomber", "device")
VBD = Verb, past tense ("detonated")
JJ  = Adjective ("explosive")
```

**Why It Matters:**
- We look for **verbs** (VBD, VBG, VBN) as violence triggers
- We look for **nouns** (NN, NNS, NNP) as actors/victims

---

### 4. Lemmatization

**What:** Reduces words to their dictionary base form (lemma)

**How:** Uses morphological rules and lookup tables

**Example:**
```
Word        → Lemma
"killed"    → "kill"
"killing"   → "kill"
"bombs"     → "bomb"
"went"      → "go"
"better"    → "good"
```

**Why It Matters:**
- Our violence lexicon stores base forms ("kill", "attack")
- Lemmatization lets us match "killed", "killing", "kills" all to "kill"

---

### 5. Named Entity Recognition (NER)

**What:** Identifies and classifies named entities in text

**How:** Uses Conditional Random Fields (CRF) trained on annotated corpora

**Entity Types:**
- **PERSON** - People's names
- **LOCATION** - Geographic locations
- **ORGANIZATION** - Companies, institutions, groups
- **DATE** - Time expressions
- **NUMBER** - Numeric values
- **MONEY, PERCENT, TIME** - Other specialized types

**Example:**
```
"Al-Shabaab attacked Mogadishu on Friday, killing 15 civilians."

Entities:
- "Al-Shabaab" → ORGANIZATION
- "Mogadishu" → LOCATION
- "Friday" → DATE
- "15" → NUMBER
```

**How NER Works:**

1. **Contextual Clues:**
   - Capitalization: "Al-Shabaab" (capitalized → likely entity)
   - Position: Words after "in"/"at" often locations
   - Prefixes: "Mr.", "Dr." → PERSON

2. **Sequence Modeling:**
   - Models learn patterns like: [PERSON] "was killed by" [ORGANIZATION]
   - Multi-word entities: "Bakara market" tagged as single LOCATION

3. **Gazetteer Lookup:**
   - Dictionary of known entities (cities, countries, organizations)
   - "Mogadishu" recognized from gazetteer as LOCATION

**Why It Matters:**
- **WHO** extraction: We look for ORGANIZATION, PERSON entities as actors
- **WHOM** extraction: We look for PERSON entities as victims
- **WHERE** extraction: We look for LOCATION entities
- **WHEN** extraction: We look for DATE entities

---

### 6. Dependency Parsing

**What:** Maps grammatical relationships between words in a sentence

**How:** Uses neural network parsers to build dependency trees

**Relationship Types:**
- **nsubj** - nominal subject (who is doing the action)
- **dobj** - direct object (what is being acted upon)
- **nmod** - nominal modifier (additional info about nouns)
- **amod** - adjectival modifier (adjectives describing nouns)
- **compound** - compound noun (e.g., "suicide bomber")

**Example:**
```
"A suicide bomber detonated an explosive device at the market."

Dependencies:
bomber ──nsubj──→ detonated (bomber is the subject)
device ──dobj───→ detonated (device is the direct object)
market ──nmod───→ detonated (location modifier)
suicide ──compound──→ bomber (compound noun)
explosive ──amod──→ device (adjective modifier)
```

**Visual Representation:**
```
        detonated (ROOT)
       /    |    \
  bomber  device  market
    |       |       |
 suicide explosive "at the"
```

**Why It Matters:**
- **WHO** extraction: Find nsubj (subject) of violence verbs
- **WHOM** extraction: Find dobj (direct object) of violence verbs
- **WHERE** extraction: Find nmod with prepositions (at, in, near)
- **HOW** extraction: Find amod (adjectives describing weapons)

---

### 7. Coreference Resolution

**What:** Links pronouns and noun phrases to the entities they refer to

**How:** Uses neural coreference models that consider entity mentions, gender, number, and discourse context

**Example:**
```
Sentence 0: "Al-Shabaab attacked a market in Mogadishu."
Sentence 1: "The group claimed responsibility for the attack."
Sentence 2: "They have carried out similar attacks before."

Coreferences:
- "The group" → refers to "Al-Shabaab"
- "They" → refers to "Al-Shabaab"
- "the attack" → refers to the attack mentioned in Sentence 0
```

**How It Works:**

1. **Entity Detection:**
   - Identifies all noun phrases and pronouns

2. **Feature Extraction:**
   - Gender: "he" likely refers to male person
   - Number: "they" likely refers to plural entity
   - Distance: Closer mentions more likely to be referents
   - Semantic compatibility: "the group" compatible with "Al-Shabaab"

3. **Cluster Formation:**
   - Groups all mentions referring to same entity
   - Creates coreference chains

**Coreference Chain Example:**
```
Chain 1: ["Al-Shabaab", "the group", "they"]
Chain 2: ["a market", "the market"]
Chain 3: ["the attack", "it"]
```

**Why It Matters:**
- Extract actor from responsibility claims: "The group claimed..." → "Al-Shabaab"
- Track entities across sentences for event clustering
- Resolve ambiguous references in multi-sentence events

---

## How We Use It in This Project

### Our Configuration

```python
config = {
    'stanford_corenlp': {
        'path': './stanford-corenlp-4.5.5',
        'memory': '4g'
    }
}
```

**Annotators We Enable:**
1. `tokenize` - Split text into words
2. `ssplit` - Split into sentences
3. `pos` - Tag parts of speech
4. `lemma` - Get base word forms
5. `ner` - Identify named entities
6. `depparse` - Parse dependencies
7. `coref` - Resolve coreferences

### Integration Flow

```
User Input (articles.md)
   ↓
[Stage 1: Article Parsing]
   ↓
Raw article text
   ↓
[Stage 2: NLP Pipeline] ← Stanford CoreNLP runs here
   ↓
Annotated sentences with:
- Tokens + POS tags
- Named entities
- Dependencies
- Coreferences
   ↓
[Stage 3: Event Extraction]
   ↓
Events with 5W1H fields
   ↓
[Stage 5: CSV Output]
```

### What We Extract from CoreNLP Annotations

**From Tokenization:**
- Violence trigger words

**From POS Tagging:**
- Filter to verb triggers (VBD, VBG, VBN)
- Identify noun phrases for actors/victims

**From NER:**
- **WHO**: ORGANIZATION, PERSON entities
- **WHOM**: PERSON entities
- **WHERE**: LOCATION entities
- **WHEN**: DATE entities

**From Dependencies:**
- Find subjects (nsubj) for WHO
- Find objects (dobj) for WHOM
- Find location modifiers (nmod) for WHERE
- Find weapon descriptors (amod) for HOW

**From Coreferences:**
- Extract actor from "The group claimed..." → resolve to organization name
- Cluster events referring to same incident across sentences

---

## Example Walkthrough

Let's process a real sentence through Stanford CoreNLP:

### Input Sentence
```
"A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu on Friday morning, killing at least 15 civilians and injuring 23 others."
```

---

### Step 1: Tokenization
```
Tokens (28 total):
[1]  A
[2]  suicide
[3]  bomber
[4]  detonated
[5]  an
[6]  explosive
[7]  device
[8]  at
[9]  the
[10] busy
[11] Bakara
[12] market
[13] in
[14] Mogadishu
[15] on
[16] Friday
[17] morning
[18] ,
[19] killing
[20] at
[21] least
[22] 15
[23] civilians
[24] and
[25] injuring
[26] 23
[27] others
[28] .
```

---

### Step 2: POS Tagging
```
Token       | POS  | Meaning
------------|------|---------------------------
A           | DT   | Determiner
suicide     | NN   | Noun (compound modifier)
bomber      | NN   | Noun
detonated   | VBD  | Verb, past tense ← TRIGGER
an          | DT   | Determiner
explosive   | JJ   | Adjective ← WEAPON
device      | NN   | Noun ← WEAPON
at          | IN   | Preposition
the         | DT   | Determiner
busy        | JJ   | Adjective
Bakara      | NNP  | Proper noun ← LOCATION
market      | NN   | Noun ← LOCATION
in          | IN   | Preposition
Mogadishu   | NNP  | Proper noun ← LOCATION
on          | IN   | Preposition
Friday      | NNP  | Proper noun ← DATE
morning     | NN   | Noun ← TIME
,           | ,    | Comma
killing     | VBG  | Verb, gerund ← OUTCOME
at          | IN   | Preposition
least       | JJS  | Superlative adjective
15          | CD   | Cardinal number ← CASUALTIES
civilians   | NNS  | Noun, plural ← VICTIM
and         | CC   | Coordinating conjunction
injuring    | VBG  | Verb, gerund ← OUTCOME
23          | CD   | Cardinal number ← CASUALTIES
others      | NNS  | Noun, plural
.           | .    | Period
```

---

### Step 3: Lemmatization
```
Word       → Lemma
detonated  → detonate
killing    → kill
injuring   → injure
civilians  → civilian
others     → other
```

---

### Step 4: Named Entity Recognition
```
Entity          | Type      | Tokens
----------------|-----------|----------------
Bakara market   | LOCATION  | [11-12]
Mogadishu       | LOCATION  | [14]
Friday          | DATE      | [16]
15              | NUMBER    | [22]
23              | NUMBER    | [26]
```

**How NER Tagged "Bakara market":**
- "Bakara" is capitalized → likely proper noun
- "market" follows proper noun → likely part of location name
- Context: "at the ... market in Mogadishu" → location pattern
- Result: Tagged as multi-word LOCATION entity

---

### Step 5: Dependency Parsing
```
Relationship    | Governor  | Dependent   | What It Means
----------------|-----------|-------------|----------------------------------
nsubj           | detonated | bomber      | "bomber" is the subject
compound        | bomber    | suicide     | "suicide bomber" is compound noun
dobj            | detonated | device      | "device" is the direct object
amod            | device    | explosive   | "explosive" modifies "device"
nmod            | detonated | market      | "market" is location modifier
compound        | market    | Bakara      | "Bakara market" is compound
nmod            | detonated | Mogadishu   | "Mogadishu" is location modifier
nmod:tmod       | detonated | Friday      | "Friday" is temporal modifier
advcl           | detonated | killing     | "killing" is adverbial clause
dobj            | killing   | civilians   | "civilians" is object of "killing"
nummod          | civilians | 15          | "15" modifies "civilians"
conj            | killing   | injuring    | "injuring" is conjoined action
dobj            | injuring  | others      | "others" is object of "injuring"
nummod          | others    | 23          | "23" modifies "others"
```

**Dependency Tree:**
```
                    detonated (ROOT)
                   /    |    |    \
              bomber device market Mogadishu
                |      |      |
             suicide explosive Bakara
                              |
                           Friday
                              |
                          killing ── injuring
                             |           |
                        civilians     others
                             |           |
                            15          23
```

---

### Step 6: Event Extraction (Our Code Using CoreNLP Output)

Using the annotations above, our event extractor identifies:

**Trigger:** "detonated" (VBD, violence verb from lexicon)

**WHO (Actor):**
- From dependencies: nsubj of "detonated" = "bomber"
- Type: Not a named entity (generic noun)
- Check responsibility claims in document...
- Found: "Al-Shabaab claimed responsibility" in later sentence
- Coreference resolution links claim to this event
- **Result: WHO = "Al-Shabaab" (ORGANIZATION)**

**WHAT (Violence Type):**
- Trigger: "detonated"
- Lemma: "detonate"
- **Result: WHAT = "violence" (preliminary type)**

**WHOM (Victim):**
- From dependencies: dobj of "killing" = "civilians"
- Casualties: nummod of "civilians" = 15 (deaths)
- Additional: nummod of "others" = 23 (injuries)
- **Result: WHOM = "civilians", deaths=15, injuries=23**

**WHERE (Location):**
- From NER: "Bakara market" (LOCATION)
- Broader location: "Mogadishu" (LOCATION)
- **Result: WHERE = "Bakara market"**

**WHEN (Time):**
- From NER: "Friday" (DATE)
- Article date: "March 15, 2024"
- Normalize: Friday before March 15, 2024 = March 8, 2024
- **Result: WHEN = "Friday", normalized = "2024-03-08"**

**HOW (Method):**
- From dependencies: amod + compound → "explosive device"
- From trigger context: "suicide bomber"
- **Result: HOW = ["explosive", "device", "suicide bomb"]**

---

### Final Extracted Event

```json
{
  "article_id": "article_1",
  "sentence_index": 0,
  "trigger": {
    "word": "detonated",
    "lemma": "detonate",
    "pos": "VBD",
    "index": 4
  },
  "who": {
    "text": "Al-Shabaab",
    "type": "ORGANIZATION",
    "from_responsibility_claim": true
  },
  "what": {
    "type": "violence",
    "trigger_word": "detonated"
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
    "weapons": ["explosive", "device", "suicide bomb"],
    "tactics": ["suicide"],
    "text": "explosive, device, suicide bomb"
  },
  "confidence": 1.0,
  "completeness": 1.0
}
```

---

## Configuration & Setup

### Installation

1. **Download Stanford CoreNLP:**
```bash
wget https://nlp.stanford.edu/software/stanford-corenlp-4.5.5.zip
unzip stanford-corenlp-4.5.5.zip
```

2. **Start the Server:**
```bash
cd stanford-corenlp-4.5.5
java -mx4g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer \
  -port 9000 -timeout 15000
```

3. **Configure Python Client:**
```python
from pipeline import ViolentEventNLPPipeline

config = {
    'stanford_corenlp': {
        'path': './stanford-corenlp-4.5.5',
        'memory': '4g'
    }
}

pipeline = ViolentEventNLPPipeline(config)
```

### Memory Requirements

- **Minimum:** 2GB RAM
- **Recommended:** 4GB RAM
- **Large documents:** 6-8GB RAM

### Performance

**Processing Time (per article):**
- Tokenization: ~10ms
- POS Tagging: ~50ms
- NER: ~100ms
- Dependency Parsing: ~200ms
- Coreference: ~500ms
- **Total:** ~1-2 seconds per article

### Annotator Properties

You can customize annotators with properties:

```python
props = {
    'annotators': 'tokenize,ssplit,pos,lemma,ner,depparse,coref',
    'tokenize.language': 'en',
    'ner.useSUTime': 'true',  # Enable temporal expression recognition
    'coref.algorithm': 'statistical',  # Use statistical coreference
}
```

---

## Stanford CoreNLP Resources

### Official Documentation
- **Main Site:** https://stanfordnlp.github.io/CoreNLP/
- **API Docs:** https://stanfordnlp.github.io/CoreNLP/api.html
- **Tutorial:** https://stanfordnlp.github.io/CoreNLP/corenlp-tutorial.html

### Papers
1. **Stanford CoreNLP Toolkit:**
   Manning et al. (2014) "The Stanford CoreNLP Natural Language Processing Toolkit"

2. **Dependency Parsing:**
   Chen & Manning (2014) "A Fast and Accurate Dependency Parser using Neural Networks"

3. **Coreference Resolution:**
   Clark & Manning (2016) "Deep Reinforcement Learning for Mention-Ranking Coreference Models"

### Penn Treebank POS Tags
- Full list: https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html

---

## Summary

Stanford CoreNLP transforms raw text into structured linguistic data through a multi-stage pipeline:

1. **Tokenization** → Splits text into words
2. **Sentence Splitting** → Divides into sentences
3. **POS Tagging** → Labels grammatical roles
4. **Lemmatization** → Reduces to base forms
5. **NER** → Identifies named entities
6. **Dependency Parsing** → Maps word relationships
7. **Coreference** → Links pronouns to entities

In our pipeline, we use these annotations to:
- **Identify triggers** (verbs from POS)
- **Extract actors** (entities from NER + dependencies)
- **Extract victims** (entities from NER + dependencies)
- **Extract locations** (LOCATION entities)
- **Extract times** (DATE entities)
- **Extract methods** (weapon descriptors from dependencies)

Stanford CoreNLP provides the linguistic foundation that makes automatic event extraction possible.

---

**Document Created:** 2025-10-29
**Version:** 1.0
**For:** Violent Event Annotation Pipeline
