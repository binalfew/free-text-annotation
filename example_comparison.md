# Detailed Event Comparison: Article 1 - Mogadishu Attack

## Article Source Text
```
A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu 
on Friday morning, killing at least 15 civilians and injuring 23 others...

Al-Shabaab claimed responsibility for the attack in a statement released through their 
media channels.
```

## Manual Expert Annotation

```
Event_ID: ART_001_EVT_01
Article_ID: ART_001

Actor_Normalized: Al-Shabaab
Actor_Type: Non-state armed group
Actor_Confidence: 0.95

Victim_Normalized: Civilians  
Victim_Type: Civilian
Victim_Confidence: 0.9

Location_Country: Somalia
Location_City: Mogadishu
Location_Coordinates: "2.0469,15.3182"
Location_Confidence: 0.95

Date_Normalized: 2024-03-15
Date_Confidence: 0.95

Taxonomy_L1: Political Violence
Taxonomy_L2: Terrorism
Taxonomy_L3: Suicide Bombing

Weapon_Category: Explosives

Deaths: 15
Injuries: 23

Event_Description: Suicide bomber detonated explosive device at Bakara market 
killing 15 civilians and injuring 23 others

Classification_Confidence: 0.9
Flagged_for_Review: False
Annotator_Name: Expert Annotator
Notes: Al-Shabaab claimed responsibility for the attack
```

## Automated Extraction

### Event 1
```
article_id: article_1
event_id: article_1_event_1

trigger_word: attack
trigger_lemma: attack
sentence_index: 2

who_actor: Bakara                    ⚠️ WRONG - This is the market, not the actor
who_type: PERSON                     ⚠️ WRONG - Not a person

what_event_type: armed_attack        ✓ Partially correct

whom_victim: civilians               ✓ CORRECT
whom_type: civilian                  ✓ CORRECT

deaths: 15                           ✓ CORRECT
injuries: 23                         ✓ CORRECT

where_location: Mogadishu            ✓ CORRECT (but incomplete)
where_type: UNKNOWN                  ⚠️ Missing specificity

when_time: Friday                    ⚠️ Not normalized (should be 2024-03-15)
when_type: RELATIVE                  ⚠️ Need absolute date

how_weapons: explosive, suicide bomb, device, explosive device
how_tactics: suicide                 ✓ CORRECT (but verbose)

confidence: 1.00
completeness: 0.00                   ⚠️ Bug - should not be 0%
```

### Event 2 (Spurious extraction)
```
article_id: article_1
event_id: article_1_event_2

trigger_word: attack
trigger_lemma: attack
sentence_index: 2

who_actor: The                       ❌ WRONG - Parsing error
who_type: PERSON                     ❌ WRONG

whom_victim: Somali National         ⚠️ Partial/unclear

where_location: Somalia              ✓ CORRECT
when_time: (empty)                   ❌ Missing

confidence: 0.80
completeness: 0.00                   ⚠️ Bug
```

## Comparison Summary

| Field | Expert Annotation | Automated | Status |
|-------|------------------|-----------|--------|
| **Actor** | Al-Shabaab | "Bakara" (market) | ❌ CRITICAL ERROR |
| **Actor Type** | Non-state armed group | PERSON | ❌ WRONG |
| **Victim** | Civilians | civilians | ✓ CORRECT |
| **Location** | Somalia, Mogadishu, Coordinates | Mogadishu | ⚠️ INCOMPLETE |
| **Date** | 2024-03-15 (normalized) | "Friday" (relative) | ⚠️ NOT NORMALIZED |
| **Taxonomy** | 3-level: Political Violence > Terrorism > Suicide Bombing | armed_attack | ⚠️ SHALLOW |
| **Deaths** | 15 | 15 | ✓ CORRECT |
| **Injuries** | 23 | 23 | ✓ CORRECT |
| **Weapons** | Explosives | explosive, suicide bomb, etc. | ✓ CORRECT (verbose) |
| **Event Count** | 1 real event | 2 events (1 spurious) | ⚠️ FALSE POSITIVE |
| **Description** | Rich human summary + notes | Trigger words only | ⚠️ INCOMPLETE |

## Key Problems Identified

### 1. Actor Misidentification ❌ CRITICAL
The most serious error: **"Bakara"** (the market location) was identified as the actor instead of **"Al-Shabaab"** (the actual perpetrator). 

**Why this happened:**
- The sentence structure: "bomber detonated... at the busy **Bakara** market"
- NLP likely found "Bakara" as the nearest proper noun to the violence trigger
- Failed to resolve that Al-Shabaab (mentioned later) claimed responsibility

**Impact**: Makes the data unusable for actor-based analysis (e.g., tracking Al-Shabaab attacks)

### 2. Spurious Event Detection ⚠️
Event 2 is not a real separate event - it's a parsing error that extracted "The" as an actor.

### 3. Missing Context ⚠️
The automated system doesn't capture:
- The fact that Al-Shabaab claimed responsibility  
- The reason for the attack (retaliation for government operations)
- The context of ongoing conflict

### 4. Date Not Normalized ⚠️
"Friday" is not useful for temporal analysis. Need the actual date: 2024-03-15.

## What Would Make It Better?

1. **Coreference Resolution**: Link "Al-Shabaab claimed responsibility" to the attack event
2. **Entity Filtering**: Validate actors - "Bakara" is a location, not an actor  
3. **Event Deduplication**: Merge the two extractions into one real event
4. **Date Resolution**: Use article metadata date + relative day → absolute date
5. **Taxonomy Training**: Learn the violence taxonomy hierarchy
6. **Geocoding**: Add coordinates for locations automatically
7. **Summary Generation**: Create event descriptions, not just trigger words
