# Writes and recovery

## Before writing

Build the complete change set for exactly one root and validate final bodies. A mixed-scope request
produces independent plans. Record an operation ID, selected root,
relative path, base SHA-256 (or `null` for creates), intended SHA-256, mode, and phase. Re-read current
targets and stop if a base hash changed. This detects some stale plans but is not compare-and-swap.

Prefer exact-substring MCP edit for one local page change, followed by read-back validation. For a
multi-page update use at most three batches: content pages; index shards; root index plus log.
Read back and verify each earlier batch before sending the next. Combine the root index and log
only after knowledge pages and index shards verify. The log records verified knowledge changes;
it must not claim that navigation, the whole operation, or search is complete until final read-back
and processing checks pass. A partially saved final batch still requires recovery.

OpenViking batch preflight/tree locking does not make the write transactional. There is no expected
hash/CAS field. A batch can partially write, and refresh may fail after content was saved. Operate as
a single writer per root until the server offers a concurrency primitive.

The helper creates or evaluates a plan; it never calls OpenViking:

```bash
python scripts/wiki_plan.py plan CURRENT DESIRED \
  --root-uri viking://user/alice/resources/wiki --authenticated-actor alice
python scripts/wiki_plan.py recover PLAN.json READBACK \
  --authenticated-actor alice
```

For shared scope, omit `--authenticated-actor`.

## After writing

With `wait=true`, wait for processing, then read every target and compare its SHA-256 with the plan. On a refresh error,
read first; do not replay writes blindly. Search visibility is checked only after content verification.

## Recovery

Run `scripts/wiki_plan.py recover PLAN SNAPSHOT` on a read-back snapshot. It returns a separate
`retry_action` for each target and a `retry_operations` subset. Execute only the subset in `ready_batches`, in phase order; `retry_operations` is an inventory,
not authorization to submit later phases early. Never replay the original batch. Statuses are `intended`, `base`, `missing`, or `unexpected`:

- `intended`: `skip` — no write needed;
- `base`: `retry_replace` or `retry_append` after revalidation;
- `missing`: `retry_create` only when the planned mode was create;
- `unexpected`: stop for manual reconciliation.

Create/replace operations are idempotent only with content verification. Log append requires the
operation marker embedded in the planned entry; if the marker already exists, do not append it again.

## Timing and correlation

Use the plan's `operation_id` for the logical change and a fresh `X-Request-ID` for every HTTP
attempt (for example `wiki-<operation_id>-p<phase>-a<attempt>`). Send `telemetry: true` when the
HTTP endpoint supports it. Record request ID, telemetry ID, client start/end, phase, file count,
HTTP status, queue result and read-back hashes in a private execution report. Do not put keys or
full prompts in timing reports. Keep logical operation markers stable across retries.

Do not issue a second synchronous refresh merely to check a completed write. `wait=false` means
processing is pending and can change directory freshness behavior; do not silently substitute it
for `wait=true`. Batching reduces repeated refresh cycles; it does not guarantee one LLM call or
atomic writes. Preserve legacy plan phases when recovering an operation already in progress.
