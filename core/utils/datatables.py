from __future__ import annotations

import json
from typing import Any, Dict


_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_datatable(name: str, definition: Dict[str, Any]) -> None:
    _REGISTRY[name] = definition


def get_datatable_definition(name: str) -> Dict[str, Any]:
    definition = _REGISTRY.get(name)
    if not definition:
        raise KeyError(f"No existe definición de DataTable para '{name}'")
    return definition


def get_datatable_context(name: str) -> Dict[str, Any]:
    definition = get_datatable_definition(name)
    return {
        "definition": definition,
        "options_json": json.dumps(definition.get("options", {})),
        "filters": {
            filtro["element_id"]: filtro
            for filtro in definition.get("filters", [])
            if filtro.get("element_id")
        },
    }
