# Validation and health checks

Use `scripts/wiki_validate.py` against a local synthetic/exported snapshot when deterministic lint is
needed. The script is read-only and accepts no `viking://` URI. An agent can perform the equivalent
checks on pages read through MCP without persisting private bodies.

The helpers require Python 3 and PyYAML 6.0.3, declared in each script's PEP 723 header. Prefer
`uv run scripts/wiki_validate.py ...`, which resolves the pinned dependency by itself. Without `uv`,
`python3 -c "import yaml"` shows whether plain `python3 scripts/wiki_validate.py ...` can run. When
neither works, say which tool is missing and offer to install `uv` with the user's consent; do not
install anything unasked. The MCP-based checks described above need no local tooling and remain
available meanwhile. It rejects malformed YAML and duplicate
mapping keys. The default machine policy implements the four standard page types; if `SCHEMA.md`
defines custom types, pass an explicit reviewed JSON policy with `--policy` rather than assuming prose
schema changes can be inferred safely by a deterministic script.

Checks include page placement/type, required frontmatter, reduced `repo-entity` schema, bare source
slugs, duplicate slugs, broken body links, orphan pages, index coverage, missing source targets,
fenced-code link exclusion, size caps, and forbidden private URIs in a shared snapshot.

## How links resolve

A wikilink names a page by slug. `[[slug|label]]`, `[[slug#heading]]` and `[[slug.md]]` all name
`slug`; `[[#heading]]` points into its own page. A directory prefix is a constraint, not decoration:
`[[entities/foo]]` resolves only if `entities/foo.md` exists, and never binds to `sources/foo.md`.
Slugs are case-sensitive. A broken-link finding names the target it could not resolve.

## Validating only what changes

Do not export a whole root to check one operation. Put the final bodies of the pages being changed
into a directory, list the root once, and pass the listing:

```bash
# listing.txt: the recursive output of the OpenViking list tool for the root, or one path per line
uv run scripts/wiki_validate.py CHANGED_PAGES_DIR \
  --listing listing.txt --root-uri viking://user/alice/resources/wiki
```

Links and `sources:` references then resolve against every page of the root, and a new page whose
slug collides with a listed one is a duplicate, while only the changed bodies are read. A listed
page's type is taken from its directory. The report says `partial` and names the checks it could not
make: `orphan` always, because inbound links live in bodies it does not hold, and `not-indexed`
unless the changed `index.md` is part of the directory. Run those two over a full snapshot as an
occasional health check, not on every write.

Structural lint reports findings; it does not rewrite pages. Semantic lint reads bounded pages and
their evidence to find contradictions, stale claims, duplicates, and gaps. Proposed fixes remain
separate until the user requested a corrective write.

Use `--json` for machine-readable output. Exit status is 0 when no errors exist, 1 for validation
errors, and 2 for bad invocation or unreadable input. Warnings such as soft-cap pages do not alone
make the command fail.
