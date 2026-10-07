"""Read the reviewed offline catalog without loading models or accessing the network.

The portal, REST metadata and MCP resources use the same versioned source. Live
readiness belongs to the runtime status endpoint, not this learning document.
"""
from functools import lru_cache

from .config import ROOT
from .schemas import CheckpointName, ModelMetadataResponse


@lru_cache(maxsize=1)
def _read():
    return ModelMetadataResponse.model_validate_json((ROOT / "docs/models.json").read_text(encoding="utf-8"))


def metadata(model: CheckpointName | None = None) -> ModelMetadataResponse:
    result = _read().model_copy(deep=True)
    if model is not None:
        result.models = [entry for entry in result.models if entry["id"] == model]
    return result


def catalog_json() -> str:
    return metadata().model_dump_json(indent=2)
