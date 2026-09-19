#!/usr/bin/env python3
# /// script
# dependencies = ["PyYAML==6.0.3"]
# ///
"""Create deterministic OpenViking write plans and classify recovery per operation."""
from __future__ import annotations
import argparse, hashlib, json, posixpath, re, sys
from pathlib import Path
from wiki_validate import validate

SHARED_ROOT = "viking://resources/wiki"
PRIVATE_PREFIX = "viking://user/"
ACTOR_RE = re.compile(r"^[A-Za-z0-9._@-]+$")
ENCODED_TRAVERSAL_RE = re.compile(r"%(?:2e|2f|5c)", re.I)


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def valid_root(root, authenticated_actor=None):
    if any(c in root for c in ("?", "#", "%", "\\")) or any(ord(c) < 32 for c in root):
        raise ValueError("root contains forbidden URI characters")
    if root == SHARED_ROOT:
        return "shared"
    if root.startswith(PRIVATE_PREFIX) and root.endswith("/resources/wiki"):
        actor = root[len(PRIVATE_PREFIX) : -len("/resources/wiki")]
        if ACTOR_RE.fullmatch(actor) and actor not in {".", ".."}:
            if not authenticated_actor:
                raise ValueError(
                    "private root requires the authenticated actor identity"
                )
            if actor != authenticated_actor:
                raise ValueError(
                    "private root actor does not match the authenticated identity"
                )
            return "private"
    raise ValueError(
        "root must be viking://resources/wiki or viking://user/<authenticated-user>/resources/wiki"
    )


def safe_rel(path, root):
    rel = path.relative_to(root).as_posix()
    normalized = posixpath.normpath(rel)
    if (
        normalized != rel
        or normalized.startswith("../")
        or normalized.startswith("/")
        or normalized in {"", ".", ".."}
        or "://" in normalized
        or "\\" in normalized
        or any(c in normalized for c in ("?", "#"))
        or ENCODED_TRAVERSAL_RE.search(normalized)
        or any(ord(c) < 32 for c in normalized)
    ):
        raise ValueError(f"unsafe relative path: {rel}")
    return normalized


def files(root):
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"snapshot is not a real directory: {root}")
    result = {}
    for path in sorted(root.rglob("*")):
        rel = safe_rel(path, root)
        if path.is_symlink():
            raise ValueError(f"snapshot contains symlink: {rel}")
        if path.is_file():
            if path.suffix != ".md":
                raise ValueError(f"snapshot contains unexpected file: {rel}")
            result[rel] = path.read_bytes()
    return result


def phase(rel):
    return (
        2 if rel in {"index.md", "log.md"}
        else 1 if rel.startswith("indexes/") else 0
    )


def batches(operations, operation_id):
    """Describe ordered batches; dependencies require successful content read-back."""
    groups = []
    verified_paths = []
    for number in sorted({op["phase"] for op in operations}):
        paths = [op["relative_path"] for op in operations if op["phase"] == number]
        groups.append({
            "batch_id": f"{operation_id}:phase-{number}",
            "phase": number,
            "relative_paths": paths,
            "requires_verified_paths": list(verified_paths),
        })
        verified_paths.extend(paths)
    return groups


def make_plan(current, desired, root_uri, authenticated_actor=None, policy_path=None):
    scope = valid_root(root_uri, authenticated_actor)
    old, new = files(current), files(desired)
    removed = sorted(set(old) - set(new))
    if removed:
        raise ValueError("planner refuses deletions: " + ", ".join(removed))
    report = validate(desired, scope, policy_path)
    if report["errors"]:
        raise ValueError(f"desired snapshot has {report['errors']} validation error(s)")
    operations = []
    for rel in sorted(new, key=lambda x: (phase(x), x)):
        if old.get(rel) == new[rel]:
            continue
        mode, content = (
            ("create", new[rel]) if rel not in old else ("replace", new[rel])
        )
        marker = None
        if rel == "log.md" and rel in old:
            if not new[rel].startswith(old[rel]):
                raise ValueError("log.md changes must be append-only")
            content, mode = new[rel][len(old[rel]) :], "append"
            marker = next(
                (
                    line.strip()
                    for line in content.decode().splitlines()
                    if "operation-id:" in line
                ),
                None,
            )
            if not marker:
                raise ValueError("log.md append must contain an operation-id marker")
        op = {
            "relative_path": rel,
            "uri": root_uri + "/" + rel,
            "mode": mode,
            "phase": phase(rel),
            "base_sha256": digest(old.get(rel)),
            "intended_sha256": digest(new[rel]),
            "content": content.decode(),
        }
        if marker:
            op["operation_marker"] = marker
        operations.append(op)
    seed = json.dumps(
        [
            {
                k: op[k]
                for k in ("relative_path", "base_sha256", "intended_sha256", "mode")
            }
            for op in operations
        ],
        sort_keys=True,
    ).encode()
    operation_id = hashlib.sha256(root_uri.encode() + b"\0" + seed).hexdigest()[:24]
    return {
        "version": 2,
        "operation_id": operation_id,
        "root_uri": root_uri,
        "scope": scope,
        "atomic": False,
        "requires_single_writer": True,
        "validation": {"warnings": report["warnings"]},
        "operations": operations,
        "batches": batches(operations, operation_id),
    }


def recover(plan_path, snapshot, authenticated_actor=None):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    valid_root(plan["root_uri"], authenticated_actor)
    state = files(snapshot)
    results = []
    retry = []
    for op in plan["operations"]:
        actual = digest(state.get(op["relative_path"]))
        mode = op["mode"]
        if actual == op["intended_sha256"]:
            status, action = "intended", "skip"
        elif actual is None and mode == "create":
            status, action = "missing", "retry_create"
        elif actual == op["base_sha256"] and mode == "replace":
            status, action = "base", "retry_replace"
        elif actual == op["base_sha256"] and mode == "append":
            status, action = "base", "retry_append"
        else:
            status, action = "unexpected", "block"
        item = {
            "relative_path": op["relative_path"],
            "mode": mode,
            "status": status,
            "retry_action": action,
            "actual_sha256": actual,
        }
        results.append(item)
        if action.startswith("retry_"):
            retry.append({"relative_path": op["relative_path"], "retry_action": action})
    blocked = any(x["retry_action"] == "block" for x in results)
    # Retain legacy plan phases during recovery; do not merge an in-flight v1 plan.
    states = {item["relative_path"]: item for item in results}
    ready = []
    if not blocked:
        for batch in batches(plan["operations"], plan["operation_id"]):
            pending = [path for path in batch["relative_paths"]
                       if states[path]["retry_action"].startswith("retry_")]
            if pending:
                if all(states[path]["status"] == "intended"
                       for path in batch["requires_verified_paths"]):
                    ready.append({**batch, "relative_paths": pending})
                break
    return {
        "operation_id": plan["operation_id"],
        "root_uri": plan["root_uri"],
        "safe_to_retry_remaining": not blocked,
        "retry_operations": retry,
        "ready_batches": ready,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("plan")
    create.add_argument("current", type=Path)
    create.add_argument("desired", type=Path)
    create.add_argument("--root-uri", required=True)
    create.add_argument("--authenticated-actor")
    create.add_argument("--policy", type=Path)
    recovery = sub.add_parser("recover")
    recovery.add_argument("plan", type=Path)
    recovery.add_argument("snapshot", type=Path)
    recovery.add_argument("--authenticated-actor")
    args = parser.parse_args()
    try:
        result = (
            make_plan(
                args.current,
                args.desired,
                args.root_uri,
                args.authenticated_actor,
                args.policy,
            )
            if args.command == "plan"
            else recover(args.plan, args.snapshot, args.authenticated_actor)
        )
    except (OSError, UnicodeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
