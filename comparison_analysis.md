# Annotation Comparison: Automated vs Manual Expert Annotation

## Overview
This document compares the output of the automated NLP pipeline (`extracted_events.csv`) with the expert manual annotation (`annotated.csv`) for the same 5 articles from `articles.md`.

## Summary Statistics

### Manual Expert Annotation (annotated.csv)
- **Total Events**: 8 events from 5 articles
- **Articles with multiple events**: 2 articles (ART_003 and ART_005)
- **Average events per article**: 1.6

### Automated Extraction (extracted_events.csv)
- **Total Events**: 6 events from 5 articles  
- **Articles with multiple events**: 1 article (article_1)
- **Average events per article**: 1.2

## Key Differences

### 1. Event Detection Quality
| Aspect | Manual Expert | Automated |
|--------|---------------|-----------|
| Event count | 8 events | 6 events |
| Missed events | - | 2 events (Article 3: 2 separate ethnic group perspectives) |
| Multiple event detection | Identified in 2 articles | Identified in 1 article |

### 2. Actor Identification

**Article 1 - Mogadishu Attack:**
- **Manual**: Al-Shabaab ✓
- **Automated**: "Bakara" (market name) ✗

**Article 2 - Police Violence:**
- **Manual**: Nigerian Police Officers ✓
- **Automated**: "State Police Command" (partial) ~

**Article 5 - Election Violence:**
- **Manual**: Opposition Supporters AND Police Officers (2 events) ✓
- **Automated**: "Violent" (adjective, not actor) ✗

### 3. Victim Identification

**Article 1:**
- **Manual**: Civilians ✓
- **Automated**: "civilians" (lowercase, correct concept) ✓

**Article 3:**
- **Manual**: Hema Community AND Lendu Community (2 perspectives) ✓
- **Automated**: "12 people" (count only, no group identity) ✗

### 4. Location Detail

| Field | Manual Expert | Automated |
|-------|---------------|-----------|
| Format | Separated fields | Single text field |
| Country | ✓ (e.g., "Somalia") | ✗ Missing |
| City | ✓ (e.g., "Mogadishu") | ✓ Basic |
| Coordinates | ✓ (e.g., "2.0469,15.3182") | ✗ Missing |
| Location type | Implicit in structure | UNKNOWN/INFERRED tags |

### 5. Date Normalization

| Article | Manual Format | Automated Format |
|---------|---------------|------------------|
| Article 1 | 2024-03-15 | "Friday" |
| Article 2 | 2024-03-18 | "Tuesday" |
| Article 3 | 2024-03-20 | (missing) |
| Article 4 | 2024-03-22 | (missing) |
| Article 5 | 2024-03-25 | (missing) |

**Issue**: Automated system extracts relative dates but doesn't normalize to ISO format.

### 6. Event Classification/Taxonomy

**Manual Expert Annotation** has 3-level taxonomy:
- Taxonomy_L1: High-level (e.g., "Political Violence")
- Taxonomy_L2: Mid-level (e.g., "Terrorism")  
- Taxonomy_L3: Specific (e.g., "Suicide Bombing")

**Automated Extraction** has:
- Simple type classification (e.g., "armed_attack", "violence")
- No hierarchical taxonomy
- Less specific categorization

### 7. Casualty Information

| Article | Deaths (Manual) | Deaths (Auto) | Injuries (Manual) | Injuries (Auto) |
|---------|----------------|---------------|-------------------|-----------------|
| 1 | 15 | 15 ✓ | 23 | 23 ✓ |
| 2 | 1 | missing ✗ | 4 | missing ✗ |
| 3 | 8/4 (2 events) | 12 | 0/0 | missing |
| 4 | 1 | missing ✗ | 1 | missing ✗ |
| 5 | 3/0 (2 events) | 3 ✓ | 47/12 | 47 ✓ |

**Casualty extraction rate**: ~40% complete in automated vs 100% in manual

### 8. Weapon/Tactic Information

**Article 1 - Manual:**
- Weapon_Category: Explosives ✓

**Article 1 - Automated:**
- how_weapons: "explosive, suicide bomb, device, explosive device" (verbose) ~
- how_tactics: "suicide" ✓

### 9. Confidence Scoring

**Manual Expert Annotation:**
- Actor_Confidence: 0.85-0.95
- Victim_Confidence: 0.80-0.90
- Location_Confidence: 0.90-0.95
- Date_Confidence: 0.90-0.95
- Classification_Confidence: 0.80-0.90
- **Granular per-field confidence scores**

**Automated Extraction:**
- confidence: 0.70-1.00 (overall)
- completeness: 0.00 (all events marked incomplete!)
- **Single aggregate score, less informative**

### 10. Metadata and Quality Control

**Manual Expert Annotation includes:**
- ✓ Flagged_for_Review (quality control)
- ✓ Annotator_Name (accountability)
- ✓ Notes (contextual information)
- ✓ Event descriptions (human-written summaries)

**Automated Extraction:**
- ✗ No review flags
- ✗ No provenance tracking
- ✗ No contextual notes
- ✗ Relies on trigger words instead of descriptions

## Critical Issues in Automated Extraction

### 1. **Wrong Actor Identification**
- "Bakara" (market) identified as actor instead of "Al-Shabaab"
- "The" and "Violent" identified as actors (parsing errors)
- "During" identified as actor (preposition)

### 2. **Missing Multiple Event Detection**
- Article 3: Failed to detect conflict from both Hema and Lendu perspectives
- Article 5: Failed to detect both protest violence and police response as separate events

### 3. **Poor Date Extraction**
- Only extracting relative dates ("Friday", "Tuesday")
- Not converting to normalized ISO format
- Missing dates in 3 out of 5 articles

### 4. **Incomplete Casualty Extraction**
- Missing deaths/injuries in 60% of events
- Not extracting numbers from complex sentences

### 5. **No Hierarchical Classification**
- Lacks the structured 3-level taxonomy
- Generic "violence" category not useful for analysis

## Recommendations for Improvement

1. **Actor/Entity Extraction**
   - Implement coreference resolution to track entities across sentences
   - Use context window to find actual perpetrator (not location/adjective)
   - Add validation rules to filter out non-actor entities

2. **Multiple Event Detection**
   - Implement event clustering to detect distinct violent events
   - Recognize reciprocal violence (A attacks B, B counterattacks A)
   - Split events by different actor-victim pairs

3. **Date Normalization**
   - Add date parsing library (e.g., dateparser, python-dateutil)
   - Extract article publication date as reference
   - Convert relative dates to absolute dates

4. **Casualty Extraction**
   - Add numeric extraction patterns for deaths/injuries
   - Look for keywords: "killed", "dead", "injured", "wounded"
   - Extract from broader context, not just trigger sentence

5. **Taxonomy Classification**
   - Implement multi-level classification model
   - Train on expert annotations to learn hierarchy
   - Add rule-based categorization for clear cases

6. **Completeness Score**
   - Fix the completeness calculation (currently always 0.00)
   - Weight by presence of key fields (5W1H)
   - Flag incomplete events for manual review

## Conclusion

The automated extraction shows **significant gaps** compared to expert manual annotation:

- ✗ **Accuracy**: Many actor/victim misidentifications
- ✗ **Completeness**: Missing ~25% of events, 60% of casualty data
- ✗ **Normalization**: Dates not standardized, locations lack detail
- ✗ **Classification**: No hierarchical taxonomy
- ✗ **Context**: No event descriptions or notes

**Recommendation**: The automated system is **not yet ready** to replace expert annotation. It can serve as a **first-pass extraction** to assist annotators, but requires significant manual correction and enrichment to match the quality of `annotated.csv`.

### Suggested Workflow:
1. Run automated extraction as initial pass
2. Present results to expert annotators for review
3. Experts correct, enrich, and validate extractions
4. Use corrected data to retrain/improve the NLP models
5. Iterate until automated quality approaches expert level
