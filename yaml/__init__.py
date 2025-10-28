"""A tiny subset of the PyYAML interface used in the tests."""

from __future__ import annotations

import json
from typing import Any, IO, Union


class YAMLError(Exception):
    """Exception raised for YAML parsing errors."""


def _read_stream(stream_or_string: Union[str, IO[str]]) -> str:
    if hasattr(stream_or_string, 'read'):
        return stream_or_string.read()
    return str(stream_or_string)


def safe_load(stream: Union[str, IO[str]]) -> Any:
    """Parse a YAML string.

    The implementation supports the JSON subset that the project requires and
    raises :class:`YAMLError` for malformed input.
    """
    text = _read_stream(stream)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise YAMLError(str(exc)) from exc


def dump(data: Any, stream: IO[str] | None = None, **_: Any) -> str | None:
    """Serialise *data* to YAML.

    Only the arguments used in the tests are implemented; additional keyword
    arguments are accepted for compatibility but ignored.
    """
    text = json.dumps(data, indent=2)
    if stream is None:
        return text
    stream.write(text)
    return None
