# Query workflow

1. Resolve the root. Search both roots only when explicitly requested, and label results by root.
2. Read `index.md`, then the relevant shard. Use OpenViking search/find when the catalog is
   insufficient and grep for exact names or slugs.
3. Treat hits and snippets as routing evidence only. Read full candidate pages and the provenance
   needed for material claims.
4. Answer from the retrieved evidence with page wikilinks or explicit URIs. Preserve disagreements,
   time bounds, and uncertainty.
5. If coverage is insufficient, name the gap and propose a source to ingest. Do not fill the wiki's
   answer from unstated model knowledge.
6. Do not write during an ordinary query. Filing the answer into `synthesis/` is a distinct requested
   operation and then follows the ingest/write validation workflow.
