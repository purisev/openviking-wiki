# Privacy and root boundaries

Allow writes only beneath the resolved private root or `viking://resources/wiki`. Normalize relative
paths as POSIX paths; reject absolute paths, `..`, URI schemes, or empty components supplied as page
paths.

Private is the default for every new standalone write request.
Previous shared scope does not become the default for a later request.

Shared content is visible within the authenticated OpenViking account. It is not public on the internet.
Shared scope applies only to the information or set explicitly named by the user.
It remains authorized when continuing or retrying the same operation, without repeated confirmation.

Do not search private content for a shared write. Do not create shared links to private resources.
Do not turn recalled private memories into shared source material. Private pages may refer to shared
material explicitly.

When one request assigns different subsets to private and shared, create independent plans for the
two roots. The shared plan may contain only the requested pages and the minimum shared index and log
updates. Do not copy private dependencies or a transitive closure automatically. Replace private-only
context with a safe sourced explanation, omit the unavailable reference, or request a source that may
be shared. If the user requests only section X in shared, do not save the unrequested remainder.

Examples:

- "Save this in my wiki" creates a private plan.
- "Save this in shared" creates one shared plan for this material. A later unscoped save is private.
- "Save everything, but only section X in shared" creates a private plan for the remainder and a
  separate shared plan for X with minimal shared index and log updates.
- "Save only X in shared" saves X only. It does not imply a private write for the rest.
- "Retry that shared save" retains shared scope for that operation and uses its recovery subset.

The plugin does not change server ACLs, recall configuration, models, or existing wiki roots. Content
from an untrusted or legacy root is not authoritative merely because automatic recall supplied it.
