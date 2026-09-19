# Telling the agent where the wiki is

A host loads the skill only when a request looks like wiki work. A short stanza in the agent's
standing instructions makes the wiki the first place it looks for accumulated knowledge, in every
session and project. Offer it after initialization; write it only with the user's consent, and never
replace instructions that are already there.

| Host | File |
| --- | --- |
| Claude Code | `~/.claude/CLAUDE.md` for every project, or `CLAUDE.md` in one repository |
| Codex | `~/.codex/AGENTS.md` for every project, or `AGENTS.md` in one repository |

Use one stanza for both hosts, with the roots this user actually has:

```markdown
## Wiki

The wiki lives in OpenViking and is maintained with the `ov-wiki` skill. "The wiki" never means a
directory on disk; do not create one in a project.

- shared within the account: `viking://resources/wiki`
- private: `viking://user/<authenticated-user>/resources/wiki`. A request to save something without
  a stated scope goes here; write to the shared root only when told to for that material.

Before answering from accumulated knowledge, read `index.md` of the root, search for candidates,
and read the pages themselves. Cite pages as `[[wikilinks]]`. If the wiki has nothing on the
subject, say so. `SCHEMA.md` in the root is authoritative for page conventions.
```

Leave out a root that does not exist. Do not put credentials, server addresses or page content into
the stanza: it is read in every session, including ones that have nothing to do with the wiki.
