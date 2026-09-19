#!/usr/bin/env python3
# /// script
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Deterministic structural validator for an LLM Wiki snapshot."""
from __future__ import annotations
import argparse, json, re, sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import yaml

FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
FENCE_RE = re.compile(
    r"(?ms)^[ \t]*(?P<fence>`{3,}|~{3,})[^\n]*\n.*?^[ \t]*(?P=fence)[ \t]*$"
)
INLINE_CODE_RE = re.compile(r"(?P<ticks>`+).*?(?P=ticks)", re.S)
CONTROL = {"SCHEMA.md", "index.md", "log.md"}
DEFAULT_POLICY = {
    "types": {
        "source": "sources",
        "entity": "entities",
        "concept": "concepts",
        "synthesis": "synthesis",
    },
    "ordinary_required": ["type", "title", "tags", "created", "updated"],
    "repo_required": ["kind", "type", "name", "origin", "web_url", "description"],
    "source_required": ["authors", "raw", "ingested"],
    "reference_fields": {
        "sources": "source",
        "entities": "entity",
        "concepts": "concept",
        "sources_consulted": ["source", "entity", "concept", "synthesis"],
    },
}


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    out = {}
    for kn, vn in node.value:
        key = loader.construct_object(kn, deep=deep)
        if key in out:
            raise yaml.constructor.ConstructorError(
                "mapping", node.start_mark, f"duplicate key: {key}", kn.start_mark
            )
        out[key] = loader.construct_object(vn, deep=deep)
    return out


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def parse_frontmatter(text):
    match = FM_RE.match(text)
    if not match:
        return None, text
    data = yaml.load(match.group(1), Loader=UniqueKeyLoader)
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data, text[match.end() :]


def link_key(target):
    """The page a wikilink names: its text without a heading anchor or a `.md` suffix."""
    key = target.split("#", 1)[0].strip()
    return key[:-3] if key.endswith(".md") else key


def links(text):
    without_fences = FENCE_RE.sub("", text)
    without_code = INLINE_CODE_RE.sub("", without_fences)
    keys = (link_key(m.group(1)) for m in LINK_RE.finditer(without_code))
    # An anchor-only link points into the page that holds it.
    return [key for key in keys if key]


def resolve(key, rel_by_slug, rels):
    """Relative path of the page a link key names, or None.

    A directory prefix is a constraint, not decoration: `sources/foo` resolves only
    if that exact path exists, so it can never bind to `entities/foo`.
    """
    if "/" in key:
        rel = f"{key}.md"
        return rel if rel in rels else None
    return rel_by_slug.get(key)


def read_listing(path, root_uri=None):
    """Relative Markdown paths of a whole wiki root, one per line.

    Accepts bare relative paths, full URIs and the `[file] <uri>` lines of the
    OpenViking list tool; `root_uri` is the prefix to strip from URIs.
    """
    prefix = root_uri.rstrip("/") + "/" if root_uri else None
    rels = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = line.strip()
        if entry.startswith("[dir]"):
            continue
        if entry.startswith("[file]"):
            entry = entry[len("[file]") :].strip()
        if prefix and entry.startswith(prefix):
            entry = entry[len(prefix) :]
        if "://" in entry:
            raise ValueError(f"listing entry is outside the root: {entry}")
        if entry.startswith("./"):
            entry = entry[2:]
        if entry.endswith(".md"):
            rels.add(entry)
    return rels


def finding(level, code, path, message, **extra):
    return {"level": level, "code": code, "path": path, "message": message, **extra}


def load_policy(path):
    if path is None:
        return DEFAULT_POLICY
    data = json.loads(path.read_text(encoding="utf-8"))
    required = set(DEFAULT_POLICY)
    if (
        not isinstance(data, dict)
        or not required.issubset(data)
        or not isinstance(data["types"], dict)
    ):
        raise ValueError("invalid machine policy")
    return data


def inventory(root, findings):
    result = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            findings.append(
                finding("error", "symlink", rel, "snapshot must not contain symlinks")
            )
        elif path.is_file():
            if path.suffix != ".md":
                findings.append(
                    finding(
                        "error",
                        "unexpected-file",
                        rel,
                        "snapshot contains a non-Markdown file",
                    )
                )
            else:
                result.append(path)
    return result


def validate(root: Path, scope="private", policy_path=None, listing=None):
    """Validate a snapshot.

    With `listing` (every Markdown path of the wiki root) the snapshot may hold only
    the pages being changed: links and references resolve against the listing, and
    the checks that need every page body are skipped and named in the report.
    """
    findings = []
    pages = []
    inbound = defaultdict(list)
    docs = {}
    partial = listing is not None
    listed = set(listing or ())
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"snapshot is not a real directory: {root}")
    policy = load_policy(policy_path)
    for control in sorted(CONTROL):
        if not (root / control).is_file() and control not in listed:
            findings.append(
                finding(
                    "error",
                    "missing-control",
                    control,
                    "required control page is missing",
                )
            )
    for path in inventory(root, findings):
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            findings.append(finding("error", "unreadable", rel, str(exc)))
            continue
        docs[rel] = text
        if scope == "shared" and (
            "viking://user/" in text or "viking://~/" in text
        ):
            findings.append(
                finding(
                    "error",
                    "private-uri-in-shared",
                    rel,
                    "shared content contains a private user URI",
                )
            )
        if rel in CONTROL or rel.startswith("indexes/") or path.name.startswith("."):
            continue
        try:
            meta, body = parse_frontmatter(text)
        except (yaml.YAMLError, ValueError) as exc:
            findings.append(finding("error", "malformed-frontmatter", rel, str(exc)))
            continue
        if meta is None:
            findings.append(
                finding(
                    "error",
                    "missing-frontmatter",
                    rel,
                    "knowledge page has no YAML frontmatter",
                )
            )
            continue
        slug = path.stem
        kind = meta.get("kind")
        page_type = meta.get("type")
        required = (
            policy["repo_required"]
            if kind == "repo-entity"
            else policy["ordinary_required"]
        )
        missing = sorted(
            k for k in required if k not in meta or meta[k] is None or meta[k] == ""
        )
        if missing:
            findings.append(
                finding(
                    "error",
                    "missing-frontmatter-fields",
                    rel,
                    "required fields are missing",
                    fields=missing,
                )
            )
        for key in (
            "tags",
            "sources",
            "authors",
            "entities",
            "concepts",
            "sources_consulted",
        ):
            if key in meta and not isinstance(meta[key], list):
                findings.append(
                    finding(
                        "error",
                        "frontmatter-list-type",
                        rel,
                        f"{key} must be a YAML list",
                        field=key,
                    )
                )
        string_fields = {
            "type",
            "title",
            "kind",
            "name",
            "origin",
            "web_url",
            "description",
        }
        for key in sorted(string_fields & set(required)):
            if key in meta and not isinstance(meta[key], str):
                findings.append(
                    finding(
                        "error",
                        "frontmatter-scalar-type",
                        rel,
                        f"{key} must be a string",
                        field=key,
                    )
                )
        for key in ("created", "updated"):
            if key in meta and not isinstance(meta[key], (str, date)):
                findings.append(
                    finding(
                        "error",
                        "frontmatter-scalar-type",
                        rel,
                        f"{key} must be a date scalar",
                        field=key,
                    )
                )
        if kind == "repo-entity" and page_type != "entity":
            findings.append(
                finding(
                    "error", "repo-entity-type", rel, "repo-entity type must be entity"
                )
            )
        expected = (
            policy["types"].get(page_type) if isinstance(page_type, str) else None
        )
        if expected is None:
            findings.append(
                finding(
                    "error",
                    "unknown-type",
                    rel,
                    "type is absent from the active machine policy",
                    value=page_type,
                )
            )
        elif rel.split("/", 1)[0] != expected:
            findings.append(
                finding(
                    "error",
                    "type-directory-mismatch",
                    rel,
                    "page type does not match directory",
                    expected=expected,
                )
            )
        if page_type == "source":
            missing = sorted(
                k
                for k in policy["source_required"]
                if k not in meta or meta[k] is None or meta[k] == ""
            )
            if missing:
                findings.append(
                    finding(
                        "error",
                        "missing-source-fields",
                        rel,
                        "source fields are missing",
                        fields=missing,
                    )
                )
            if "authors" in meta and not isinstance(meta["authors"], list):
                findings.append(
                    finding(
                        "error",
                        "frontmatter-list-type",
                        rel,
                        "authors must be a YAML list",
                        field="authors",
                    )
                )
            if "raw" in meta and not isinstance(meta["raw"], str):
                findings.append(
                    finding(
                        "error",
                        "frontmatter-scalar-type",
                        rel,
                        "raw must be a string",
                        field="raw",
                    )
                )
            if "ingested" in meta and not isinstance(meta["ingested"], (str, date)):
                findings.append(
                    finding(
                        "error",
                        "frontmatter-scalar-type",
                        rel,
                        "ingested must be a date scalar",
                        field="ingested",
                    )
                )
            if "## Where this fits" not in body:
                findings.append(
                    finding(
                        "error",
                        "missing-where-this-fits",
                        rel,
                        "source page must map pages it informs",
                    )
                )
        elif kind != "repo-entity" and (
            not isinstance(meta.get("sources"), list) or not meta["sources"]
        ):
            findings.append(
                finding(
                    "error",
                    "missing-sources-list",
                    rel,
                    "non-source page needs a non-empty sources list",
                )
            )
        refs = []
        for field, target_types in policy["reference_fields"].items():
            if isinstance(target_types, str):
                target_types = [target_types]
            values = meta.get(field, [])
            if not isinstance(values, list):
                continue
            for value in values:
                if (
                    not isinstance(value, str)
                    or "[[" in value
                    or "://" in value
                    or "/" in value
                    or value.endswith(".md")
                ):
                    findings.append(
                        finding(
                            "error",
                            "non-bare-reference",
                            rel,
                            f"{field} entries must be bare slugs",
                            field=field,
                            value=value,
                        )
                    )
                else:
                    refs.append((field, value, target_types))
        n = text.count("\n") + 1
        if n > 800:
            findings.append(
                finding("error", "hard-cap", rel, "page exceeds 800 lines", lines=n)
            )
        elif n > 400:
            findings.append(
                finding("warning", "soft-cap", rel, "page exceeds 400 lines", lines=n)
            )
        pages.append(
            {
                "rel": rel,
                "slug": slug,
                "kind": kind,
                "type": page_type if isinstance(page_type, str) else None,
                "refs": refs,
                "links": links(body),
            }
        )
    by_slug = defaultdict(list)
    for page in pages:
        by_slug[page["slug"]].append(page)
    type_by_dir = {directory: name for name, directory in policy["types"].items()}
    for rel in sorted(listed - set(docs)):
        if rel in CONTROL or rel.startswith("indexes/"):
            continue
        directory = rel.split("/", 1)[0] if "/" in rel else ""
        by_slug[Path(rel).stem].append(
            {"rel": rel, "slug": Path(rel).stem, "type": type_by_dir.get(directory)}
        )
    for slug, matches in sorted(by_slug.items()):
        if len(matches) > 1:
            findings.append(
                finding(
                    "error",
                    "duplicate-slug",
                    matches[0]["rel"],
                    "slug is not unique",
                    slug=slug,
                    paths=[p["rel"] for p in matches],
                )
            )
    rels = set(docs) | listed
    rel_by_slug = {slug: matches[0]["rel"] for slug, matches in by_slug.items()}
    for rel, text in docs.items():
        for target in links(text):
            resolved = resolve(target, rel_by_slug, rels)
            if resolved:
                inbound[resolved].append(rel)
    for rel, text in sorted(docs.items()):
        if rel in CONTROL or rel.startswith("indexes/"):
            for target in links(text):
                if resolve(target, rel_by_slug, rels) is None:
                    findings.append(
                        finding(
                            "error",
                            "broken-control-link",
                            rel,
                            "control/index wikilink target is missing",
                            target=target,
                        )
                    )
    for page in pages:
        for target in page["links"]:
            if resolve(target, rel_by_slug, rels) is None:
                findings.append(
                    finding(
                        "error",
                        "broken-link",
                        page["rel"],
                        "wikilink target is missing",
                        target=target,
                    )
                )
        for field, target, target_types in page["refs"]:
            if not any(p["type"] in target_types for p in by_slug.get(target, [])):
                findings.append(
                    finding(
                        "error",
                        "missing-reference",
                        page["rel"],
                        f"{field} slug does not resolve to an allowed page type",
                        target=target,
                    )
                )
        external = [src for src in inbound.get(page["rel"], []) if src != page["rel"]]
        if partial:
            # Inbound links live in page bodies the partial snapshot does not hold.
            if "index.md" in docs and not any(
                src == "index.md" or src.startswith("indexes/") for src in external
            ):
                findings.append(
                    finding(
                        "warning",
                        "not-indexed",
                        page["rel"],
                        "page is absent from index links",
                    )
                )
            continue
        if not external and page["kind"] != "repo-entity":
            findings.append(
                finding(
                    "warning",
                    "orphan",
                    page["rel"],
                    "page has no inbound wikilink from another page",
                )
            )
        if not any(src == "index.md" or src.startswith("indexes/") for src in external):
            findings.append(
                finding(
                    "warning",
                    "not-indexed",
                    page["rel"],
                    "page is absent from index links",
                )
            )
    findings.sort(
        key=lambda x: (
            x["level"] != "error",
            x["code"],
            x["path"],
            str(x.get("target", "")),
        )
    )
    counts = Counter(p["type"] for p in pages)
    return {
        "root": str(root),
        "scope": scope,
        "policy": str(policy_path) if policy_path else "default",
        "pages": len(pages),
        "partial": partial,
        "skipped": ["orphan"] + ([] if "index.md" in docs else ["not-indexed"]) if partial else [],
        "by_type": dict(sorted(counts.items(), key=lambda x: str(x[0]))),
        "errors": sum(x["level"] == "error" for x in findings),
        "warnings": sum(x["level"] == "warning" for x in findings),
        "findings": findings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--scope", choices=("private", "shared"), default="private")
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--listing",
        type=Path,
        help="file listing every Markdown path of the wiki root; the snapshot may then "
        "hold only the pages being changed",
    )
    parser.add_argument("--root-uri", help="URI prefix to strip from --listing entries")
    args = parser.parse_args()
    try:
        listing = read_listing(args.listing, args.root_uri) if args.listing else None
        report = validate(args.snapshot, args.scope, args.policy, listing)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            f"pages={report['pages']} errors={report['errors']} warnings={report['warnings']}"
        )
        if report["skipped"]:
            print(f"partial snapshot; not checked: {', '.join(report['skipped'])}")
        for item in report["findings"]:
            target = f" -> {item['target']}" if item.get("target") else ""
            print(
                f"{item['level'].upper()} {item['code']} {item['path']}: {item['message']}{target}"
            )
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
