"""Stable advisory questions shared by real-data benchmarks and sibling clients.

These decisions describe investigation work, never authorization, risk acceptance
or vulnerability verification. Deterministic policies retain those responsibilities.
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .schemas import ModelName, PredictRequest

QUESTIONS = {
    "issue_lane": {"decision": {
        "type": "choice", "instructions": "Which remediation workflow matches the issue description? Classify the work, not whether the finding is true.",
        "criteria": {
            "A": "vulnerable package dependency: investigate a dependency update",
            "B": "exposed secret or credential: owner review and possible rotation",
            "C": "application source-code defect: source review and regression reproduction",
            "D": "business, marketing or informational report: no code repair task",
        },
    }},
    "qa_cause": {"decision": {
        "type": "choice", "instructions": "Classify observed test failure using evidence and the trusted product contract. A changed requirement with an obsolete assertion is a test defect. A timeout alone does not establish a product defect.",
        "criteria": {
            "PRODUCT_BUG": "application demonstrably violates the current product contract",
            "TEST_BUG": "outdated assertion, incorrect test setup or harness defect",
            "INFRA": "network, runner, test inbox or external infrastructure failure",
            "UNKNOWN": "evidence cannot distinguish product behavior from test or infrastructure cause",
        },
    }},
    "security_specialist": {"decision": {
        "type": "choice", "instructions": "Which specialist should investigate this source-code finding? This is topic routing, not a security verdict.",
        "criteria": {
            "A": "authentication/session: JWT, tokens, login and session validation",
            "B": "secret handling: credential exposure or sensitive material in logs",
            "C": "code correctness: duplicated branches or copy-paste logic errors",
            "D": "another security topic requiring investigation",
        },
    }},
}

LABELS = {
    "issue_lane": {"A": "dependency_update", "B": "credential_review", "C": "source_review", "D": "business_report"},
    "qa_cause": {name: name for name in ("PRODUCT_BUG", "TEST_BUG", "INFRA", "UNKNOWN")},
    "security_specialist": {"A": "authentication-session", "B": "crypto-secret-handling", "C": "code-correctness", "D": "other"},
}


class WorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    state: Any
    model: ModelName | None = None
    min_confidence: float = Field(default=0.8, ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_state(self):
        if self.state is None or self.state == {} or self.state == [] or (isinstance(self.state, str) and not self.state.strip()):
            raise ValueError("Advisory workflows require non-empty evidence")
        self.prediction("issue_lane")
        return self

    def prediction(self, workflow: str):
        return PredictRequest(state=self.state, questions=QUESTIONS[workflow], model=self.model,
                              min_confidence=self.min_confidence, max_len=512, head_max_len=192)


def advice(workflow: str, response: dict) -> dict:
    answer = response["answers"]["decision"]
    usage = response.get("usage", {})
    review = bool(answer.get("low_confidence") or usage.get("truncated") or usage.get("options") or usage.get("truncated_questions"))
    return {
        "workflow": workflow, "label": LABELS[workflow][answer["choice"]],
        "answer_confidence": answer.get("answer_confidence"), "review_required": review,
        "advisory_only": True, "authorization": False,
    }
