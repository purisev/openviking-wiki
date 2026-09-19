# ov-wiki

A Codex and Claude Code plugin for maintaining an agent-authored Markdown LLM Wiki in an existing
OpenViking account. The agent performs source reading, reasoning, synthesis, and editing; OpenViking
provides storage and retrieval.

The plugin has one shared skill under `skills/ov-wiki/`, manifests for both clients, thin
Claude Code slash commands, compatible templates, and deterministic snapshot validation and write
planning/recovery helpers. It bundles no MCP server, recall hooks, embeddings, or local search index.

Supported roots are `viking://resources/wiki` for explicitly shared work and
`viking://user/<authenticated-user>/resources/wiki` for private work. Private is the default.

The plugin and its skill are named `ov-wiki`; this repository keeps the name `openviking-wiki`.

This repository contains mechanics only. It does not contain or migrate a real wiki.

## Install

The plugin registers no OpenViking tools of its own. The session must expose OpenViking's read, search
and write tools; under Claude Code the [openviking-memory](https://github.com/purisev/openviking-memory)
dependency provides them. Without them the commands stop and name the missing capability.

The deterministic helpers (`wiki_validate.py`, `wiki_plan.py`) need Python 3 with PyYAML 6.0.3;
`uv run` resolves it from the scripts' PEP 723 headers. They are optional: the agent can run the same
checks over MCP.

Claude Code — the plugin is published in the `purisev` marketplace
([purisev/agent-plugins](https://github.com/purisev/agent-plugins)):

```
/plugin marketplace add purisev/agent-plugins
/plugin install ov-wiki@purisev
```

The manifest declares `openviking-memory` as a dependency, so Claude Code installs and enables it from
the same marketplace; that plugin's MCP proxy supplies the OpenViking tools and asks for the server
connection when it is enabled.

This adds the `ov-wiki` skill and the `/wiki-init`, `/wiki-ingest`, `/wiki-query`,
`/wiki-lint` and `/wiki-recover` commands. From a checkout, use `claude --plugin-dir <checkout>` for
one session.

Codex reads `.codex-plugin/plugin.json`; add the checkout to a Codex marketplace and install
`ov-wiki` from it.

## Development checks

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python /path/to/skill-creator/scripts/quick_validate.py skills/ov-wiki
python /path/to/plugin-creator/scripts/validate_plugin.py .
```

Both bundled scripts also declare the pinned PyYAML dependency in PEP 723 metadata for compatible
runners.

Claude Code can additionally validate the package with `claude plugin validate .` when its CLI is
available. Passing static/package validation is not a live OpenViking or Claude Code end-to-end test.
