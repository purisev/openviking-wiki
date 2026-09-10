# Validation and health checks

Use `scripts/wiki_validate.py` against a local synthetic/exported snapshot when deterministic lint is
needed. The script is read-only and accepts no `viking://` URI. An agent can perform the equivalent
checks on pages read through MCP without persisting private bodies.

The helper requires PyYAML 6.0.3. Run it through a PEP 723-capable runner or install the pinned
`requirements-dev.txt` dependency in an isolated environment. It rejects malformed YAML and duplicate
mapping keys. The default machine policy implements the four standard page types; if `SCHEMA.md`
defines custom types, pass an explicit reviewed JSON policy with `--policy` rather than assuming prose
schema changes can be inferred safely by a deterministic script.

Checks include page placement/type, required frontmatter, reduced `repo-entity` schema, bare source
slugs, duplicate slugs, broken body links, orphan pages, index coverage, missing source targets,
fenced-code link exclusion, size caps, and forbidden private URIs in a shared snapshot.

Structural lint reports findings; it does not rewrite pages. Semantic lint reads bounded pages and
their evidence to find contradictions, stale claims, duplicates, and gaps. Proposed fixes remain
separate until the user requested a corrective write.

Use `--json` for machine-readable output. Exit status is 0 when no errors exist, 1 for validation
errors, and 2 for bad invocation or unreadable input. Warnings such as soft-cap pages do not alone
make the command fail.
