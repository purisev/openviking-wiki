---
name: openviking-wiki
description: Build, query, validate, and maintain an LLM-authored Markdown wiki stored in OpenViking. Use when the user refers to their OpenViking wiki, asks to ingest knowledge into it, query it, lint it, initialize it, or recover an interrupted wiki update. Do not use for ordinary OpenViking memories or bulk resource import.
---

# OpenViking Wiki

Maintain a linked Markdown wiki while using OpenViking only for durable storage and retrieval.
Codex or the current agent reads evidence, reasons, and authors every canonical page. Do not invoke
VikingBot, `ov compile`, a second vector index, or another recall/capture hook.

## Root selection

Resolve one root for each independent write plan:

- private (default): `viking://user/<authenticated-user>/resources/wiki`
- shared (only when explicitly selected for the specific information or set): `viking://resources/wiki`

Use the authenticated identity exposed by the existing connector/session. Never guess a username or
copy a user identifier from an unrelated URI. Every new standalone “save to the wiki” request without
a scope starts private, even if an earlier operation used shared. An explicit shared scope persists
only while continuing or retrying that same authorized operation, so do not ask for it again there.

If one request assigns different subsets to private and shared, build two independent plans, each with
one root. Put only the explicitly named subset in shared, plus the minimum index and log maintenance.
Do not disclose private dependencies to make shared links resolve. Sanitize or omit those references,
or ask for an allowed source when the shared page cannot stand alone. A query is read-only unless the
user also asks to file its result.

## Route the operation

Read only the reference needed for the current operation:

- initialize or understand page conventions: [schema.md](references/schema.md)
- ingest or update sources/pages: [ingest.md](references/ingest.md)
- answer from the wiki: [query.md](references/query.md)
- validate or inspect health: [validation.md](references/validation.md)
- plan writes or recover an interrupted batch: [writes-and-recovery.md](references/writes-and-recovery.md)
- reason about root boundaries or publication: [privacy.md](references/privacy.md)
- map runtime capabilities and optional HTTP batching: [transport.md](references/transport.md)

## Invariants

Read `SCHEMA.md` and `index.md` from the selected root before changing knowledge. Preserve its
conventions when they differ from defaults. Use `source`, `entity`, `concept`, and `synthesis` as
distinct page roles; keep frontmatter `sources:` as bare source-page slugs and body links as
`[[wikilinks]]`. Keep `log.md` as the short append-only human index of completed operations.

Read a full page before editing it. Prefer an exact-substring MCP edit for a local change. For a
validated multi-page operation, construct final page bodies and use batch create/replace, with the
index and log together in the final batch after earlier phases verify (see writes-and-recovery). Validate before writes and read back afterward. OpenViking has no compare-and-
swap and batch writes can partially succeed, so never claim atomicity.

Treat search results as candidates. Read the selected pages and relevant source material before
relying on them. If evidence is missing, say so rather than filling gaps from general knowledge.
