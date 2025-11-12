from __future__ import annotations

from typing import Any, Dict


_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_datatable(name: str, definition: Dict[str, Any]) -> None:
    _REGISTRY[name] = definition


def get_datatable_definition(name: str) -> Dict[str, Any]:
    definition = _REGISTRY.get(name)
    if not definition:
        raise KeyError(f"No existe definición de DataTable para '{name}'")
    return definition
