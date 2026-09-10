---
description: Reconcile a partially completed OpenViking wiki write plan.
argument-hint: <operation plan or operation id>
---

Use the `openviking-wiki` skill's writes-and-recovery workflow for `$ARGUMENTS`. Read back every target
before retrying anything. Stop on unexpected content; do not promise transactional recovery.
