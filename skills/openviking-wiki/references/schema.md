# Wiki schema

## Default layout

```text
<selected-root>/
├── SCHEMA.md
├── index.md
├── log.md
├── indexes/
├── sources/
├── entities/
├── concepts/
└── synthesis/
```

These are OpenViking virtual paths, not filesystem paths. Initialize only missing control files and
directories. Existing `SCHEMA.md` is authoritative.

## Page roles

- `source`: faithful digest of one source or, for a dense source when the schema permits, a parent
  record plus meaningful thematic sections. Never make mechanical chunk pages.
- `entity`: a named thing with a stable identity, boundary, role, and relationships.
- `concept`: an idea, mechanism, pattern, policy, or model.
- `synthesis`: a cross-source analysis, comparison, or query result deliberately filed back.

Every ordinary page requires `type`, `title`, `tags`, `created`, and `updated`. Source pages also use
`authors`, `url` when applicable, `raw`, and `ingested`. Non-source pages use `sources`, whose values
are bare source-page slugs. Do not put `[[wikilinks]]` or `viking://` URIs in `sources:`. Body links
use `[[slug]]` or `[[slug|label]]`.

## Repository entities

Pages marked `kind: repo-entity` are inventory anchors. Require exactly the compatible reduced core:
`kind`, `type`, `name`, `origin`, `web_url`, and `description`; `type` must be `entity`. Optional
ordinary fields remain optional. Such pages may be linked only from `index.md` and are exempt from
the ordinary orphan warning.

A legacy `repo-*.md` without `kind: repo-entity` remains an ordinary entity. Do not mass-convert it:
legacy pages can contain substantial sourced knowledge and normal backlinks.

## Editorial form

Pages open with a neutral encyclopedic definition. Keep source claims distinct from established
facts and agent inference. Preserve conflicting claims together with both citations and their
version, time, or scope when known. Keep pages atomic: 400 lines is a soft cap; 800 is a hard cap.
Crossing the hard cap requires a meaningful split with updated links and index entries.

`index.md` is a compact catalog. Shard it after roughly 150 pages or 300 lines, while preserving
stable page slugs. `log.md` entries use `## [YYYY-MM-DD] <operation> | <description>` and contain one
or two sentences plus one primary-artifact wikilink. The operation vocabulary belongs in its header.
