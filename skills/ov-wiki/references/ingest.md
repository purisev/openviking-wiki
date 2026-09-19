# Ingest and update workflow

1. Resolve one root for this plan and read its `SCHEMA.md`, `index.md`, and relevant shard. For a
   mixed-scope request, create independent evidence and write plans per root; never move private
   dependencies into the shared plan automatically.
2. Read the source in bounded chunks, each no more than 25% of the available context budget. Prefer
   semantic section boundaries and a small overlap. Maintain a coverage ledger; do not equate words
   with tokens.
3. Build an evidence ledger mapping source sections to candidate claims, target pages, confidence,
   and provenance. Separate the source's claims, corroborated facts, and agent inference.
4. Survey the selected root for canonical subjects, aliases, source slugs, and backlinks before
   creating pages. Use index/list first, semantic search for fuzzy candidates, and grep for exact
   slugs. Read every page that may be changed.
5. Re-read available raw evidence behind an existing claim before merging. If it is missing or
   unreadable, preserve the claim with a provenance-gap note; do not increase its confidence merely
   because it already appears in the wiki.
6. Create or update one canonical source record. Include `## Where this fits` with deduplicated links
   to affected entities and concepts. Dense-source child pages must represent stable themes, never
   ingestion chunks.
7. Update entity and concept pages surgically. Create synthesis only when requested or when the
   operation explicitly calls for a durable cross-source analysis.
8. Preserve contradictions with citations to both sides. Do not overwrite one account silently.
9. Split any page that would cross the 800-line hard cap during this operation. Add backlinks so new
   pages are not orphans.
10. Build a deterministic change set; run the validator; then follow `writes-and-recovery.md`.
11. After verified content and index writes, append one short `log.md` entry pointing to the primary
   artifact. A rerun updates the existing source record rather than producing another summary.

Never use `add_resource(to=<wiki-root>)` for page updates: directory synchronization can delete
target files absent from the input. Importing an immutable source, if explicitly requested, must use
a dedicated source destination whose synchronization behavior is understood.
