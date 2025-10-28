from stanford_nlp.corenlp_wrapper import CoreNLPWrapper


def test_lightweight_annotation_provides_tokens_and_entities():
    wrapper = CoreNLPWrapper('./missing-directory')

    text = "Maiduguri, Nigeria. The army intervened quickly."
    annotation = wrapper.annotate(text)

    assert len(annotation['sentences']) == 2

    first_sentence = annotation['sentences'][0]
    tokens = wrapper.get_tokens(first_sentence)
    assert tokens[0]['word'] == 'Maiduguri'

    entities = wrapper.get_entities(first_sentence)
    assert any(entity['type'] == 'LOCATION' for entity in entities)

    second_sentence = annotation['sentences'][1]
    dependencies = wrapper.get_dependencies(second_sentence)
    assert dependencies[0]['relation'] == 'root'
