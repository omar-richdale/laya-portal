"""Validated, shared contracts for REST endpoints and MCP tool arguments."""
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ModelName = Literal["auto", "english", "multilingual", "typed-decisions"]
CheckpointName = Literal["english", "multilingual", "typed-decisions"]


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["choice", "score", "noul"]
    instructions: str = Field(min_length=1, max_length=4000)
    criteria: dict[str, str] | list[str] | None = None

    @model_validator(mode="after")
    def check_criteria(self):
        if self.type == "choice":
            if not isinstance(self.criteria, dict) or not 1 <= len(self.criteria) <= 100:
                raise ValueError("choice criteria must be an object with 1 to 100 options")
            if any(not key.strip() or not value.strip() for key, value in self.criteria.items()):
                raise ValueError("choice labels and descriptions must not be blank")
        elif self.type == "score":
            if not isinstance(self.criteria, list) or not 2 <= len(self.criteria) <= 32:
                raise ValueError("score criteria must be an ordered list of 2 to 32 descriptions")
            if any(not value.strip() for value in self.criteria):
                raise ValueError("score descriptions must not be blank")
        elif self.criteria is not None:
            raise ValueError("noul questions do not take criteria")
        return self


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Any
    questions: dict[str, Question] = Field(min_length=1, max_length=64)
    model: ModelName | None = None
    max_len: int | None = Field(default=None, ge=64, le=8192, strict=True)
    head_max_len: int | None = Field(default=None, ge=16, le=1024, strict=True)
    min_confidence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def check_limits(self):
        if not isinstance(self.state, (str, dict, list)):
            raise ValueError("state must be text, a JSON object, or a JSON list")
        serialized = json.dumps(self.state, ensure_ascii=False, allow_nan=False)
        if len(serialized) > 50_000:
            raise ValueError("state exceeds 50,000 serialized characters")
        if any(not key.strip() or len(key) > 128 for key in self.questions):
            raise ValueError("question names must contain 1 to 128 characters")
        total = sum(2 if q.type == "noul" else len(q.criteria or []) for q in self.questions.values())
        if total > 512:
            raise ValueError("questions exceed 512 total options")
        if self.head_max_len is not None and self.max_len is not None and self.head_max_len >= self.max_len - 8:
            raise ValueError("head_max_len must leave at least 8 tokens for the state")
        return self


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requests: list[PredictRequest] = Field(min_length=1, max_length=32)
    batch_size: int = Field(default=2, ge=1, le=2, strict=True)
    sort_by_length: bool = True


class ModelSetting(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: ModelName


class PredictionResponse(BaseModel):
    """Typed outer envelope; upstream answer fields remain intact inside the maps."""
    model_config = ConfigDict(extra="allow")
    model: str
    answers: dict[str, dict[str, Any]]
    routing: dict[str, Any]
    usage: dict[str, Any]
    runtime: dict[str, Any]


class BatchResponse(BaseModel):
    results: list[PredictionResponse]
    runtime: dict[str, Any]


class ModelsResponse(BaseModel):
    default_model: ModelName
    resident_model: str | None
    models: list[dict[str, Any]]


class ModelMetadataResponse(BaseModel):
    """Static learning metadata; an explicit envelope keeps MCP output structured."""
    schema_version: str
    reviewed_at: str
    checkpoint_revision: str
    family: dict[str, Any]
    service: dict[str, Any]
    models: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    provenance: str
    links: dict[str, str]


class StatusResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    ready: bool
    phase: str
    device: str | None
    default_model: ModelName
    resident_model: str | None
    gpu: dict[str, Any] | None
    versions: dict[str, str]
    revision: str
    outstanding_jobs: int
    max_jobs: int
