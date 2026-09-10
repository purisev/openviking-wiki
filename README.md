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
