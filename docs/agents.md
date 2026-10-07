# Integrating with Laya Local

Laya evaluates a state against typed questions. It returns distributions and typed values: a `choice` label, an ordinal expected `score`, or `noul` (probability of yes). It does not generate prose. This service uses the reference Python/PyTorch model on CUDA.

## Connect

On the host PC use `http://127.0.0.1:8000`. On another LAN device use the PC's LAN address printed by `start.ps1`. HTTP API: `/api/v1`; MCP: `/mcp/` (Streamable HTTP). The trailing slash avoids a redirect for MCP clients.

Read the project `.env` locally to obtain `LAYA_API_KEY`. Send `Authorization: Bearer <key>`. Never put the real key into documentation, source, prompts, URLs, or shared screenshots. The browser portal keeps the key in session storage for the current tab. The service exposes no third-party browser CORS access.

Fetch `/llms.txt`, this Markdown file, `/docs/api.md`, and `/openapi.json` without authentication. Documentation contains generic examples and no credentials or private raw reports. `/docs/operations.md` covers startup/LAN access; `/docs/development.md` covers builds and verification. Swagger at `/docs` has an **Authorize** button. Add the bearer key there to execute examples.

## HTTP example (Python)

Install `requests` in your client application's environment. Set `LAYA_API_KEY` for that process.

```python
import os
import requests

payload = {
    "state": "Please refund the duplicate payment.",
    "model": "auto",
    "questions": {
        "department": {
            "type": "choice",
            "instructions": "Which department should handle this?",
            "criteria": {"billing": "payments and refunds", "technical": "bugs and outages"},
        }
    },
}
response = requests.post(
    "http://127.0.0.1:8000/api/v1/predict",
    headers={"Authorization": "Bearer " + os.environ["LAYA_API_KEY"]},
    json=payload, timeout=180,
)
response.raise_for_status()
result = response.json()
print(result["answers"]["department"]["choice"])
print(result["runtime"]["device"])
```

The project environment already contains `requests`. A cold model load can take substantially longer than a warm prediction; use a timeout that permits loading.

## PowerShell

```powershell
$apiKey = $env:LAYA_API_KEY
$payload = @{
    state = 'Please refund the duplicate payment.'
    model = 'auto'
    questions = @{
        department = @{
            type = 'choice'
            instructions = 'Which department should handle this?'
            criteria = @{ billing = 'payments and refunds'; technical = 'bugs and outages' }
        }
    }
} | ConvertTo-Json -Depth 10
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/predict' -Method Post `
    -Headers @{ Authorization = "Bearer $apiKey" } -ContentType 'application/json; charset=utf-8' `
    -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -TimeoutSec 180
```

## JavaScript HTTP client

This runs in backend JavaScript; Python still performs inference.

```javascript
const response = await fetch('http://127.0.0.1:8000/api/v1/predict', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${process.env.LAYA_API_KEY}`,
  },
  body: JSON.stringify({
    state: 'Please refund my payment.',
    questions: {
      refund: { type: 'choice', instructions: 'Is a refund requested?',
        criteria: { A: 'yes, a refund is requested', B: 'no refund is requested' } },
    },
  }),
});
const result = await response.json();
if (!response.ok) throw new Error(result.error.message);
console.log(result.answers.refund.choice);
```

## MCP clients and agents

Configure a Streamable HTTP client with the URL and bearer header. Read `laya://integration` before inference. Tools:

- `laya_predict`: argument `request` is the same object accepted by HTTP prediction.
- `laya_predict_batch`: argument `request` contains `requests`, `batch_size`, and `sort_by_length`.
- `laya_models` and `laya_status`: no arguments.
- `laya_model_info`: optional `model` (english, multilingual or typed-decisions); returns detailed capabilities, hosted budgets, examples and caveats without GPU work.
- `laya_set_default_model`: argument `model`; changes the shared persistent default. Prefer per-request overrides when testing.

Python example for the pinned MCP SDK 2.2.0:

```python
import asyncio, os, httpx2
from mcp import Client
from mcp.client.streamable_http import streamable_http_client

async def main():
    async with httpx2.AsyncClient(headers={
        'Authorization': 'Bearer ' + os.environ['LAYA_API_KEY']
    }, timeout=180) as http:
        transport = streamable_http_client('http://127.0.0.1:8000/mcp/', http_client=http)
        async with Client(transport, read_timeout_seconds=180) as client:
            guide = await client.read_resource('laya://integration')
            result = await client.call_tool('laya_predict', {
                'request': {
                    'state': 'Please refund the duplicate payment.',
                    'model': 'auto',
                    'questions': {'refund': {
                        'type': 'choice', 'instructions': 'Is a refund requested?',
                        'criteria': {'A': 'a refund is requested', 'B': 'no refund requested'},
                    }},
                },
            })
            if result.is_error:
                raise RuntimeError(result.content)
            print(result.structured_content)

asyncio.run(main())
```

Hostnames and LAN IPs are checked by MCP's DNS-rebinding protection. Add custom addresses to `LAYA_ALLOWED_HOSTS` in `.env` and restart; values are bare hostnames/IPs, comma-separated, without paths or schemes.

## Model selection and limits

Omit `model` to use the saved default. Explicit `model` applies only to that request. `auto` selects English or multilingual from the state. Typed-decisions is always an explicit choice. A control-panel or settings API change persists across restarts; named models are loaded successfully before a new default is saved.

One checkpoint stays on CUDA. Changing checkpoints unloads the old one before loading the next. GPU work is serialized. A batch groups checkpoints and restores original request order. A prediction error fails the whole batch; there are no silent partial results.

English context defaults/caps at 512; typed-decisions at 1,024. Multilingual defaults to 1,024 and accepts up to 8,192. These token budgets include the question head and state. Increasing `head_max_len` leaves less space for state. More questions, longer inputs, and larger batches consume more VRAM. Use a one-state microbatch for long inputs. Input truncation and collapsed options are reported in `usage` and `runtime.warnings`; never ignore those when making decisions.

## Confidence and accuracy

Use `answer_confidence` with the optional `min_confidence` threshold; low-confidence answers get `low_confidence: true`. Raw `confidence` and `answer_confidence` are different upstream measures. A high value does not establish accuracy in your domain. `action.act_probability` is not a reliable acceptance gate. Ordinal scoring and large label sets need validation. If `noul` appears stuck, test a two-option `choice` with neutral labels and descriptive yes/no meanings.

The shipped checkpoints may be overconfident; the runtime can clamp invalid stored temperatures and warns which entries were affected. Validate and fit domain calibration before trusting probabilities. Fine-tuning and calibration training are outside this portal's first version. See the upstream model card: https://huggingface.co/convaiinnovations/laya/blob/main/README.md.

## Errors and retry policy

REST errors are `{ "error": { "code": "...", "message": "..." } }`; validation errors also include field details. `401` means missing/incorrect authentication; `400` invalid JSON/duplicate keys; `413` body too large; `422` invalid request or budget. `503` covers busy, GPU OOM, missing model, shutdown, and runtime failure; `Retry-After: 2` accompanies it. Retry `busy` with backoff. For GPU OOM, reduce request size before retrying. Fix setup for missing models. Read local logs for runtime failures. CPU inference is forbidden.

MCP tool errors use `is_error: true` and a message beginning with the same code; retriable service errors include `retry_after_seconds=2`. HTTP authentication still returns `401` before the MCP protocol runs.

## Fixed local advisory workflows

Read `/docs/system-one-integrations.md` for `issue_lane`, `qa_cause` and `security_specialist` on `POST /api/v1/workflows/{workflow}`. They return normal distributions plus a readable advisory label, never an action authorization. `GET /api/v1/benchmark` exposes the frozen local real-data study and replay inputs with bearer authentication. Existing MCP tools use the same worker and accept the equivalent typed questions.


## Model capability discovery

Read `/docs/models.md` or the public `/models.json` before choosing a checkpoint or token budget. The versioned offline catalog separates published claims, pinned configuration and measured RTX 4050 reference agreement. It includes examples, languages, architecture, exact hosted limits, context/head/state explanations, truncation and calibration caveats. It contains no keys, raw issue inputs or live runtime state.

Authenticated clients can use `/api/v1/model-metadata` or `/api/v1/models/{model}/metadata`. MCP exposes `laya_model_info`, `laya://models` (JSON) and `laya://model-guide` (Markdown). None starts GPU work. Use `/api/v1/status` or `laya_status` separately to check current readiness and residency.
