from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, MutableMapping


def _freeze(value):
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), _freeze(item)) for key, item in value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted((_freeze(item) for item in value), key=repr))
    return value


def region_selection_key(
    image_id: str,
    selected_parts: Iterable[str],
    detection_settings: Mapping,
) -> str:
    payload = repr(
        (
            image_id,
            tuple(selected_parts),
            _freeze(detection_settings),
        )
    ).encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:20]


def save_selected_ids(
    store: MutableMapping[str, tuple[str, ...]],
    selection_key: str,
    selected_ids: Iterable[str],
) -> None:
    store[selection_key] = tuple(dict.fromkeys(selected_ids))


def effective_selected_ids(
    store: Mapping[str, tuple[str, ...]],
    selection_key: str,
    available_ids: Iterable[str],
) -> set[str]:
    available = tuple(available_ids)
    if selection_key not in store:
        return set(available)
    return set(store[selection_key]).intersection(available)


def region_selection_signature(
    store: Mapping[str, tuple[str, ...]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (selection_key, tuple(selected_ids))
        for selection_key, selected_ids in sorted(store.items())
    )
