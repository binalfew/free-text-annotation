import yaml


def test_yaml_dump_and_safe_load_roundtrip(tmp_path):
    data = {
        'stanford_corenlp': {
            'path': './corenlp',
            'memory': '4g',
        },
        'features': {'use_word_embeddings': True},
    }

    config_file = tmp_path / 'config.yaml'
    with config_file.open('w') as handle:
        yaml.dump(data, handle)

    with config_file.open() as handle:
        loaded = yaml.safe_load(handle)

    assert loaded == data


def test_yaml_safe_load_raises_on_invalid_content():
    invalid = 'stanford_corenlp: [unclosed'
    try:
        yaml.safe_load(invalid)
    except yaml.YAMLError:
        pass
    else:
        raise AssertionError('Expected yaml.YAMLError to be raised')
