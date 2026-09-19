# OpenViking Wiki

A Codex and Claude Code plugin for maintaining an agent-authored Markdown LLM Wiki in an existing
OpenViking account. The agent performs source reading, reasoning, synthesis, and editing; OpenViking
provides storage and retrieval.

The plugin has one shared skill under `skills/openviking-wiki/`, manifests for both clients, thin
Claude Code slash commands, compatible templates, and deterministic snapshot validation and write
planning/recovery helpers. It bundles no MCP server, recall hooks, embeddings, or local search index.

Supported roots are `viking://resources/wiki` for explicitly shared work and
`viking://user/<authenticated-user>/resources/wiki` for private work. Private is the default.

This repository contains mechanics only. It does not contain or migrate a real wiki.

## Install

The plugin registers no OpenViking tools of its own. The session must already expose OpenViking's
read, search and write tools — for example through the MCP proxy of the
[openviking-memory](https://github.com/purisev/openviking-memory) plugin. Without them the commands
stop and name the missing capability.

Claude Code — the repository root is a marketplace whose single plugin is the repository itself:

```
/plugin marketplace add purisev/openviking-wiki
/plugin install openviking-wiki@openviking-wiki
```

This adds the `openviking-wiki` skill and the `/wiki-init`, `/wiki-ingest`, `/wiki-query`,
`/wiki-lint` and `/wiki-recover` commands. From a checkout, use `claude --plugin-dir <checkout>` for
one session.

Codex reads `.codex-plugin/plugin.json`; add the checkout to a Codex marketplace and install
`openviking-wiki` from it.

## Development checks

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python /path/to/skill-creator/scripts/quick_validate.py skills/openviking-wiki
python /path/to/plugin-creator/scripts/validate_plugin.py .
```

Both bundled scripts also declare the pinned PyYAML dependency in PEP 723 metadata for compatible
runners.

Claude Code can additionally validate the package with `claude plugin validate .` when its CLI is
available. Passing static/package validation is not a live OpenViking or Claude Code end-to-end test.
