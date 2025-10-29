"""Test POS tagging accuracy comprehensively."""

from process_articles_to_csv import parse_articles
from pipeline import ViolentEventNLPPipeline

# Test sentences with expected POS tags (from various linguistic patterns)
test_cases = [
    # Sentence 1 from Article 1
    {
        'text': 'A suicide bomber detonated an explosive device at the busy Bakara market in Mogadishu on Friday morning, killing at least 15 civilians and injuring 23 others.',
        'expected': [
            ('A', 'DT'), ('suicide', 'NN'), ('bomber', 'NN'), ('detonated', 'VBD'),
            ('an', 'DT'), ('explosive', 'JJ'), ('device', 'NN'), ('at', 'IN'),
            ('the', 'DT'), ('busy', 'JJ'), ('Bakara', 'NNP'), ('market', 'NN'),
            ('in', 'IN'), ('Mogadishu', 'NNP'), ('on', 'IN'), ('Friday', 'NNP'),
            ('morning', 'NN'), (',', '.'), ('killing', 'VBG'), ('at', 'IN'),
            ('least', 'JJS'), ('15', 'CD'), ('civilians', 'NNS'), ('and', 'CC'),
            ('injuring', 'VBG'), ('23', 'CD'), ('others', 'NNS'), ('.', '.')
        ]
    },
    # Passive voice sentence
    {
        'text': 'The injured were transported to nearby hospitals.',
        'expected': [
            ('The', 'DT'), ('injured', 'JJ'), ('were', 'VBD'), ('transported', 'VBN'),
            ('to', 'IN'), ('nearby', 'JJ'), ('hospitals', 'NNS'), ('.', '.')
        ]
    },
    # Complex sentence with modals
    {
        'text': 'Security forces have cordoned off the area and are conducting investigations.',
        'expected': [
            ('Security', 'NN'), ('forces', 'NNS'), ('have', 'VBP'), ('cordoned', 'VBN'),
            ('off', 'RP'), ('the', 'DT'), ('area', 'NN'), ('and', 'CC'),
            ('are', 'VBP'), ('conducting', 'VBG'), ('investigations', 'NNS'), ('.', '.')
        ]
    },
]

def test_pos_accuracy():
    """Test POS tagging accuracy."""
    config = {'stanford_corenlp': {'path': './stanford-corenlp-4.5.5', 'memory': '4g'}}
    pipeline = ViolentEventNLPPipeline(config)

    total_correct = 0
    total_tokens = 0

    for i, test in enumerate(test_cases, 1):
        print(f'\n{"="*70}')
        print(f'TEST CASE {i}')
        print(f'{"="*70}')
        print(f'Text: {test["text"][:60]}...')
        print()

        # Process sentence
        result = pipeline.process_article(test['text'], f'test_{i}')
        actual = [(t['word'], t['pos']) for t in result['sentences'][0]['tokens']]
        expected = test['expected']

        # Compare
        correct = 0
        errors = []

        for j, (exp_word, exp_pos) in enumerate(expected):
            if j < len(actual):
                act_word, act_pos = actual[j]
                if exp_word == act_word and exp_pos == act_pos:
                    correct += 1
                else:
                    errors.append((j+1, exp_word, exp_pos, act_pos))

        accuracy = (correct / len(expected)) * 100 if expected else 0
        total_correct += correct
        total_tokens += len(expected)

        print(f'Accuracy: {correct}/{len(expected)} = {accuracy:.1f}%')

        if errors:
            print(f'\nErrors ({len(errors)} total):')
            for idx, word, exp, act in errors[:10]:  # Show first 10 errors
                print(f'  [{idx}] {word:15} Expected: {exp:5} | Got: {act:5}')

    print(f'\n{"="*70}')
    print(f'OVERALL ACCURACY')
    print(f'{"="*70}')
    overall = (total_correct / total_tokens) * 100 if total_tokens else 0
    print(f'Total: {total_correct}/{total_tokens} = {overall:.1f}%')
    print()

    if overall >= 90:
        print('✓ TARGET ACHIEVED: 90%+ accuracy')
    else:
        print(f'✗ BELOW TARGET: Need {90 - overall:.1f}% improvement')

if __name__ == '__main__':
    test_pos_accuracy()
