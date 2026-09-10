---
name: openviking-wiki-onboarding
description: Set up purisev/openviking-wiki and help agents work correctly with shared and private knowledge in OpenViking. Use for initial client setup or shared workflow guidance, not instead of the full wiki skill for every write.
metadata:
  version: '1.0.2'
---

# OpenViking Wiki Onboarding

This shared guide supports agents whose users have requested access to the wiki.
It does not grant permission to install software, change settings, or publish private
information. Respect authorization already given by the user without requesting it again.

## Repositories and compatibility

- Wiki plugin: https://github.com/purisev/openviking-wiki
- Optional Codex memory plugin: https://github.com/purisev/openviking-memory
- Wiki baseline: 0.1.0; memory plugin baseline: upstream 0.8.3 with the local session-policy extension.
- The session-policy extension was tested with OpenViking 0.4.19.

These baselines were checked on 2026-09-10. They do not guarantee that every future main
revision is compatible. Before installing, resolve and record the selected release or
commit and inspect its manifests and instructions. Do not rely on historical commit
links after repository history has been rewritten.

The full workflow lives in `skills/openviking-wiki/SKILL.md` and its relative references
in the wiki repository. Read the installed revision and the selected knowledge base's
`SCHEMA.md`; do not duplicate the full schema in this onboarding guide.

## Client setup

1. Identify the client: Codex, Claude Code, or another agent. Inspect existing plugins
   and the available OpenViking connector to avoid duplicate capture hooks or MCP servers.
2. When installation is authorized, obtain the wiki repository at the selected revision.
   It contains `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and the shared
   `skills/openviking-wiki/` directory with references, templates, and Python helpers.
   Keep the complete skill directory, not just SKILL.md. Other agents can load that
   directory through their own skill mechanism and use an existing OpenViking connector.
3. Use the client's supported local plugin or skill installation workflow. The baseline
   wiki package has no marketplace manifest: do not assume its GitHub URL can be passed
   directly to a marketplace installation command. Check the client's CLI help and
   documentation. A marketplace called `personal` may not exist on another user's machine.
4. Obtain the server endpoint and credentials from the connection owner. Use an authorized
   non-administrative identity; do not copy another user's ID or use admin/root credentials
   for ordinary work. Never store keys in the wiki, this shared skill, Git, or logs.
5. Verify the authenticated identity and list/read/find or search capabilities, plus
   write/edit for updates. An unauthenticated `/health` response does not prove access.
   Read the available `SCHEMA.md` and `index.md`. A missing wiki requires initialization
   within the user's requested scope. Do not create shared test pages merely to probe access.
6. Reload the installed version as required by the client. If the optional memory plugin
   is installed, approve native lifecycle hooks when requested. Do not fabricate trust records.

The wiki plugin bundles no MCP server, embedding model, index, VikingBot, or conversation
capture mechanism. The current agent reasons and authors pages; OpenViking stores and
indexes them. Do not use the legacy `llm-wiki` / `ov compile` workflow for this wiki.

## Scope and working rules

- Default private root: `viking://user/<authenticated-user>/resources/wiki`.
  Resolve the user from the current authenticated connection; never hard-code another user.
- Shared root: `viking://resources/wiki`. Shared means within the OpenViking account,
  not publicly accessible on the internet.
- Each new unscoped request to save to the wiki means a private write. A previous shared
  operation does not change that default. Continuing or retrying the same explicitly
  authorized shared operation retains its scope.
- Share only the explicitly authorized material and the necessary index/log maintenance.
  Build separate write plans for different scopes.
- Do not retrieve private sources for shared publication or add shared links to private
  documents. Do not copy private dependencies to make a shared page more complete.
- Before editing, read `SCHEMA.md`, `index.md`, and the target pages in full. Preserve
  provenance; distinguish source/entity/concept/synthesis pages. Represent repositories
  using the entity type supported by the schema. Resolve contradictions through sources;
  retain unresolved accounts with attribution and date changes over time.
- Search returns candidates: read the selected pages before answering. A search request
  does not itself authorize saving the answer to the wiki.
- Validate prepared pages, write in phases, and read back the results. Update the index
  and completed-operation log in the final phase after verifying content. Batch writes
  can partially succeed; use the recovery plan and do not promise transaction semantics.

## Optional memory plugin

`purisev/openviking-memory` provides automatic conversation capture and memory extraction
for Codex. It is not a required wiki dependency and does not claim Claude Code support.
If selected, read `LOCAL_CHANGES.md` at the chosen revision. Its extension establishes a
server-side `auto_commit_policy` before session writes. Enable it separately through
`plugin.codex.serverAutoCommit` on a compatible OpenViking server.

A threshold of 20K estimated message tokens is not a hard cap on the complete model
request. The server does not split a single oversized message internally. Do not change
models or global server policies merely to install the wiki plugin.

## Server publication

Canonical server copy: `viking://agent/skills/openviking-wiki-onboarding/SKILL.md`.
This is a native account-shared skill visible in Studio → Skills. Register it through
the skills API with `target_uri: viking://agent/skills`; writing SKILL.md beneath
`viking://resources/` does not register it in that list.

Clients still need to read the skill. Visibility in Studio does not automatically install
a local plugin or grant permission to execute instructions.

Maintain the source at `server-skills/openviking-wiki-onboarding/SKILL.md` in the wiki
repository. Repository changes do not automatically update the server copy: publish a
validated version separately and verify its full content after publication.
