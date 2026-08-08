# API Contracts

**Conversational Memory Intelligence System — Deliverable 4**
Abhijeet Hiwale · August 2026

Expands system_design.pdf, Section 10. Three endpoints, matching the two online flows (write,
read) plus explicit deletion. Full request/response schemas with status codes and error semantics.

---

## Design principles carried from Section 10

1. **"Nothing relevant found" and "tenant isolation prevented a match" are not errors.**
   They are valid, expected outcomes with their own response shape. Only genuine failures
   (storage unavailable, malformed input) are represented as HTTP errors.
2. **Deletion returns once propagation completes** — or an explicit in-progress status for
   large lineage chains, rather than a false-positive immediate success.
3. **Every request carries a `tenant_id`** — enforced at the API boundary, never inferred
   from content similarity. (Week 4's deterministic isolation requirement.)

---

## Endpoint 1: `POST /memory/turns`

**Purpose:** admits a conversation turn. Triggers the write flow
(architecture.pdf, diagram 2).

### Request

```json
POST /memory/turns
Content-Type: application/json

{
  "tenant_id":  "string, required — authenticated upstream, trusted here",
  "user_id":    "string, required",
  "text":       "string, required — the turn content",
  "turn_type":  "user | assistant",
  "timestamp":  "ISO 8601 datetime, required — used for valid_from and supersession ordering"
}
```

**`turn_type`** drives provenance tagging at Admission: `user` → initial provenance
`user_stated`; `assistant` → initial provenance `assistant_generated`. The Admission
component may further refine provenance based on content patterns (e.g. detected tool
output within an assistant turn → `tool_derived`).

### Response — success

```json
HTTP 200 OK

{
  "record_id":     "UUID | null — null if admission_op is NOOP or DELETE",
  "admission_op":  "ADD | UPDATE | DELETE | NOOP",
  "provenance":    "user_stated | assistant_generated | tool_derived | retrieved_document",
  "pii_scan_result": "pass | flag | redacted",
  "superseded_id": "UUID | null — the prior record whose valid_until was set, if any"
}
```

### Response — errors

| Status | Condition |
|---|---|
| `400 Bad Request` | Missing required fields, invalid `turn_type`, unparseable timestamp |
| `401 Unauthorized` | `tenant_id` not authenticated by upstream (caller responsibility, but surfaced here if header is missing) |
| `422 Unprocessable Entity` | Text too long (implementation-defined max), embedding service returned an error during write |
| `503 Service Unavailable` | Storage unreachable |

**What is NOT a 4xx/5xx:** a NOOP admission (turn was judged not worth storing) returns
`HTTP 200` with `admission_op: NOOP`. This is a valid, expected outcome, not an error.

---

## Endpoint 2: `POST /memory/query`

**Purpose:** the read flow — retrieves, ranks, and injects memory into a context
block for a given query. Triggers the read flow (architecture.pdf, diagram 2).

### Request

```json
POST /memory/query
Content-Type: application/json

{
  "tenant_id":    "string, required",
  "user_id":      "string, required",
  "query_text":   "string, required",
  "token_budget": "integer, required — total tokens available for the injected context block",
  "zone_budgets": {
    "system_prompt":      "integer, optional — defaults applied if omitted",
    "retrieved_memory":   "integer, optional",
    "history":            "integer, optional",
    "tool_output":        "integer, optional",
    "input":              "integer, optional",
    "output_reserve":     "integer, optional"
  }
}
```

`zone_budgets` is optional — the Context Builder applies sensible per-zone defaults derived
from the Week 2 research (roughly: 40% of total budget to retrieved memory, 50% reserved
for output on large windows) if the caller omits them. Explicit values override defaults.
The sum of zone budgets must not exceed `token_budget`; a `400` is returned if it does.

### Response — memories found

```json
HTTP 200 OK

{
  "result_type":       "memory_found",
  "injected_context":  "string — the formatted memory block ready for prompt injection",
  "tokens_used":       "integer",
  "zones_used": {
    "system_prompt":    "integer",
    "retrieved_memory": "integer",
    "history":          "integer",
    "tool_output":      "integer",
    "input":            "integer",
    "output_reserve":   "integer"
  },
  "memories": [
    {
      "record_id":   "UUID",
      "text":        "string",
      "final_score": "float — the ranked score (system_design.pdf Section 9 formula)",
      "provenance":  "string",
      "superseded":  "boolean"
    }
  ]
}
```

### Response — nothing relevant (not an error)

```json
HTTP 200 OK

{
  "result_type":      "no_relevant_memory",
  "injected_context": null,
  "tokens_used":      0,
  "memories":         []
}
```

This is the first-class "nothing relevant" signal added specifically in response to
Deliverable 3's Failure 3. A caller MUST handle this shape — it is not safe to assume
`result_type` is always `memory_found`. The calling application should proceed without
memory context when it receives this response, not treat it as a retrieval failure.

### Response — errors

| Status | Condition |
|---|---|
| `400 Bad Request` | Missing required fields, zone budgets exceed total budget |
| `422 Unprocessable Entity` | Embedding service unavailable — retrieval falls back to BM25-only for this request (system_design.pdf Section 16 fallback), this status is returned only if BM25-only also fails |
| `503 Service Unavailable` | Storage unreachable |

**What is NOT a 4xx/5xx:** tenant isolation filtering out all candidates returns
`result_type: no_relevant_memory` with `HTTP 200`, not a `403` or `404`. The caller
does not learn whether there are memories that were filtered vs. no memories at all —
by design, per the isolation invariant (system_design.pdf, Section 4).

---

## Endpoint 3: `DELETE /memory/{id}`

**Purpose:** triggers eviction of a specific memory record and propagates through
`consolidation_lineage` to all derived artifacts (Week 4's backflow-prevention requirement).

### Request

```
DELETE /memory/{id}
X-Tenant-ID: string, required
X-User-ID:   string, required
```

Tenant and user are passed as headers rather than body for idempotency — repeated DELETE
requests on the same `{id}` must be safe to retry.

### Response — deletion complete

```json
HTTP 200 OK

{
  "deleted_id":         "UUID",
  "propagated_ids":     ["UUID", "..."],
  "propagation_status": "complete"
}
```

`propagated_ids` lists every derived/consolidated record whose `consolidation_lineage`
included the deleted record and which was consequently re-consolidated or evicted.

### Response — deletion in progress (large lineage chains)

```json
HTTP 202 Accepted

{
  "deleted_id":         "UUID",
  "propagation_status": "in_progress",
  "check_url":          "/memory/deletion-status/{job_id}"
}
```

Rather than a false-positive `200` implying complete deletion when lineage propagation
is still running, the API returns `202` with a status-check URL. This is the explicit
choice flagged in Section 10: honest async status beats a confident lie.

### Response — errors

| Status | Condition |
|---|---|
| `400 Bad Request` | Invalid UUID format |
| `403 Forbidden` | `{id}` exists but belongs to a different tenant |
| `404 Not Found` | `{id}` does not exist or is already evicted/deleted |
| `503 Service Unavailable` | Storage unreachable |

---

## Versioning and future surface

This API is intentionally minimal for MVP scope (system_design.pdf, Section 2: "good for MVP,
limited for production" was an acknowledged trade-off, not an oversight). Endpoints not included
here but expected in later iterations: `GET /memory/{id}` (inspect a specific record), `GET
/memory/user/{user_id}` (list a user's memories — needed for user-facing privacy controls,
Deliverable 1's Open Question 7), and a bulk-ingest endpoint for backfilling existing
conversations. All three are compatible with this schema and endpoint structure; none require
a breaking change to add.

All endpoints should be versioned under `/v1/` in production. Omitted here since no versioning
decision has been made yet — adding the prefix is a non-breaking change, removing it would be.
