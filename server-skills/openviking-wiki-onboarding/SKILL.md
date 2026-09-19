---
name: openviking-wiki-onboarding
description: Set up the ov-wiki plugin and help agents work correctly with shared and private knowledge in OpenViking. Use for initial client setup or shared workflow guidance, not instead of the full wiki skill for every write.
metadata:
  version: '1.1.0'
---

# OpenViking Wiki Onboarding

This shared guide supports agents whose users have requested access to the wiki.
It does not grant permission to install software, change settings, or publish private
information. Respect authorization already given by the user without requesting it again.

## Repositories and compatibility

- Marketplace, installers and user documentation: https://github.com/purisev/agent-plugins,
  published at https://ai-plugins.purisev.com. The marketplace is named `purisev`.
- Wiki plugin `ov-wiki`: https://github.com/purisev/openviking-wiki. The repository keeps
  the plugin's former name; an install made as `openviking-wiki` is the same plugin.
- Memory plugin `openviking-memory`: https://github.com/purisev/openviking-memory. It supplies
  the OpenViking tools the wiki plugin works through, for Claude Code and Codex alike.
- Baselines: `ov-wiki` 0.4.0, `openviking-memory` 0.10.0, tested with OpenViking 0.4.19.

These baselines were checked on 2026-09-19. They do not guarantee that every future main
revision is compatible. Before installing, resolve and record the selected release or
commit and inspect its manifests and instructions. Do not rely on historical commit
links after repository history has been rewritten.

The full workflow lives in `skills/ov-wiki/SKILL.md` and its relative references
in the wiki repository. Read the installed revision and the selected knowledge base's
`SCHEMA.md`; do not duplicate the full schema in this onboarding guide.

## Client setup

1. Identify the client: Codex, Claude Code, or another agent. Inspect existing plugins
   and the available OpenViking connector to avoid duplicate capture hooks or MCP servers.
   The same plugin enabled from two marketplaces runs every hook twice.
2. When installation is authorized, install from the `purisev` marketplace. An installed
   plugin has the same id under both hosts, `<plugin>@purisev`.
   - Claude Code: `/plugin marketplace add purisev/agent-plugins`, then
     `/plugin install ov-wiki@purisev`. The manifest declares `openviking-memory` as a
     dependency, so Claude Code installs and enables it as well, and keeps `ov-wiki`
     disabled while that plugin is missing.
   - Codex: `codex plugin marketplace add purisev/agent-plugins`, then `codex plugin add`
     for `openviking-memory@purisev` and for `ov-wiki@purisev`. Codex resolves no
     dependency here, so both are added by hand.
   - The installers at https://ai-plugins.purisev.com do the same for every supported
     host on `PATH`, and support a dry run. Run one only when the user asked for it.
   - Another agent can load the complete `skills/ov-wiki/` directory, not just SKILL.md,
     through its own skill mechanism and use an existing OpenViking connector.
3. `openviking-memory` needs Node.js 18 or newer on the `PATH` of the environment that
   launches the client; without it neither its hooks nor its tools start. Offer to install
   it, and install nothing unasked.
4. Obtain the server endpoint and credentials from the connection owner. Use an authorized
   non-administrative identity; do not copy another user's ID or use admin/root credentials
   for ordinary work. Never store keys in the wiki, this shared skill, Git, or logs. One
   file, `~/.openviking/ovcli.conf` with `url` and `api_key`, mode 600, serves both hosts.
   Claude Code also offers connection prompts when the plugin is enabled; leave them empty
   when both hosts are used, or the two will read the connection from different places.
5. Verify the authenticated identity and list/read/find or search capabilities, plus
   write/edit for updates. An unauthenticated `/health` response does not prove access.
   Read the available `SCHEMA.md` and `index.md`. A missing wiki requires initialization
   within the user's requested scope. Do not create shared test pages merely to probe access.
6. Restart or reload the client as it requires. Codex asks once, in `/hooks`, to approve
   the lifecycle hooks `openviking-memory` brings, and again when an update changes them.
   Do not fabricate trust records. The `ov-memory-doctor` skill checks the result.
7. Offer the stanza from `skills/ov-wiki/references/agent-instructions.md` for the host's
   standing instructions — `CLAUDE.md` or `AGENTS.md` — so the wiki is consulted in every
   session. Write it only with the user's consent.

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
- Validate prepared pages, write in phases, and read back the results. Validate only the
  pages being changed against a listing of the root; do not export a whole root for one
  operation. Update the index and completed-operation log in the final phase after
  verifying content. Batch writes can partially succeed; use the recovery plan and do not
  promise transaction semantics.
- A `viking://` URI is not a local path. Read and write it with the OpenViking tools, never
  with the client's file tools; `openviking-memory` denies such a call and names the tool
  to use instead.

## Memory plugin

`purisev/openviking-memory` provides automatic recall, conversation capture and memory
extraction under Claude Code and Codex, and exposes the OpenViking tools through a local
MCP proxy. Under Claude Code it is a declared dependency of `ov-wiki`; under Codex it is
installed next to it.

Its tuning lives under `plugin` in `ovcli.conf`. Keys directly under `plugin` apply to both
hosts; `plugin.codex` applies under Codex only and `plugin.claude_code` under Claude Code
only. The session-batching extension described in `LOCAL_CHANGES.md` establishes a
server-side `auto_commit_policy` before session writes and is enabled with
`serverAutoCommit` on a compatible OpenViking server.

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
