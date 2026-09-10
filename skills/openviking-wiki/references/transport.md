# OpenViking transport capabilities

Use the OpenViking tools already registered in the current Codex or Claude Code session. Tool names
may carry a harness/server prefix; match them by capability and schema rather than hard-coding that
prefix. If a required capability is absent, report it and stop the dependent operation. This plugin
does not install a second MCP server.

| Capability | Use |
| --- | --- |
| `list` | Enumerate a root or directory before planning. |
| `read` | Read full pages, controls, and post-write content; batch reads when supported. |
| `find` / semantic `search` | Rank candidates; never treat snippets as final evidence. |
| `grep` / `glob` | Resolve exact slugs, aliases, backlinks, and paths. |
| `write` | Create, replace, or append one page using the registered schema. |
| `edit` | Preferred exact-substring surgical edit for one already-read page. |
| `wait` or write wait option | Wait for processing before checking search visibility. |

The authenticated-user alias `viking://~` may be used only to discover or resolve the current user
space through the connector. Before planning writes, expand it to the canonical
`viking://user/<authenticated-user>/resources/wiki` and pass that same authenticated identity to the
planner. Never persist `~` as an account-independent owner ID.

When only per-file writes are registered, execute validated operations phase by phase and read back
each phase. With an explicitly configured HTTP adapter, the batch payload is:

```json
{
  "root_uri": "viking://resources/wiki",
  "operations": [
    {"uri": "viking://resources/wiki/concepts/example.md", "content": "...", "mode": "replace"}
  ],
  "wait": true,
  "telemetry": true
}
```

Translate only the planner's currently `ready_batches` subset during recovery; do not submit all
`retry_operations` at once. Tree locking and preflight
do not provide transactions or CAS. Batch does not accept `processing_mode`; derived processing uses
server defaults.
