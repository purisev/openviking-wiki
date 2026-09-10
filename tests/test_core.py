from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "openviking-wiki" / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


wiki_validate = load("wiki_validate")
wiki_plan = load("wiki_plan")


SOURCE = """---
type: source
title: "Synthetic source"
tags: [test]
authors: [Example Author]
url: "https://example.invalid/source"
raw: synthetic-input.md
ingested: 2026-09-10
created: 2026-09-10
updated: 2026-09-10
---
# Synthetic source

An artificial test record.

## Where this fits

- [[sample-concept]]
"""

CONCEPT = """---
type: concept
title: "Sample concept"
tags: [test]
sources: [synthetic-source]
created: 2026-09-10
updated: 2026-09-10
---
# Sample concept

Artificial content. See [[synthetic-source]].

```toml
literal = "[[not-a-wikilink]]"
```
"""

REPO = """---
kind: repo-entity
type: entity
name: sample-repo
origin: git@example.invalid:sample/repo.git
web_url: https://example.invalid/sample/repo
description: Synthetic repository inventory anchor.
---
# sample-repo
"""

LEGACY = """---
type: entity
title: "Legacy repository"
tags: [test]
sources: [synthetic-source]
created: 2026-09-10
updated: 2026-09-10
---
# Legacy repository

Substantive legacy page linked to [[sample-concept]].
"""


def write_snapshot(root: Path, *, concept=CONCEPT, log_suffix=""):
    values = {
        "SCHEMA.md": "# Wiki Schema\n",
        "index.md": "# Wiki Index\n\n- [[synthetic-source]]\n- [[sample-concept]]\n- [[sample-repo]]\n- [[legacy-repo]]\n",
        "log.md": "# Wiki Log\n" + log_suffix,
        "sources/synthetic-source.md": SOURCE,
        "concepts/sample-concept.md": concept,
        "entities/sample-repo.md": REPO,
        "entities/legacy-repo.md": LEGACY,
    }
    for rel, text in values.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        write_snapshot(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_valid_fixture_and_fenced_code(self):
        report = wiki_validate.validate(self.tmp)
        self.assertEqual(report["errors"], 0, report["findings"])
        self.assertFalse(
            any(f.get("target") == "not-a-wikilink" for f in report["findings"])
        )

    def test_inline_and_tilde_code_are_not_links(self):
        page = self.tmp / "concepts/sample-concept.md"
        page.write_text(
            CONCEPT
            + "\n`[[inline-example]]`\n"
            + "\n~~~text\n[[tilde-fence-example]]\n~~~\n",
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp)
        targets = {f.get("target") for f in report["findings"]}
        self.assertNotIn("inline-example", targets)
        self.assertNotIn("tilde-fence-example", targets)

    def test_bare_source_and_shared_boundary(self):
        page = self.tmp / "concepts/sample-concept.md"
        page.write_text(
            CONCEPT.replace(
                "sources: [synthetic-source]", "sources: ['[[synthetic-source]]']"
            )
            + "\nviking://user/example/resources/private\n",
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp, "shared")
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("non-bare-reference", codes)
        self.assertIn("private-uri-in-shared", codes)

    def test_duplicate_yaml_key_and_nonempty_sources(self):
        page = self.tmp / "concepts/sample-concept.md"
        page.write_text(
            CONCEPT.replace("tags: [test]", "tags: []\ntags: [duplicate]"),
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp)
        self.assertIn("malformed-frontmatter", {f["code"] for f in report["findings"]})
        page.write_text(
            CONCEPT.replace("sources: [synthetic-source]", "sources: []"),
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp)
        self.assertIn("missing-sources-list", {f["code"] for f in report["findings"]})

    def test_non_scalar_type_is_reported_without_crashing(self):
        page = self.tmp / "concepts/sample-concept.md"
        page.write_text(
            CONCEPT.replace("type: concept", "type: [concept]"), encoding="utf-8"
        )
        report = wiki_validate.validate(self.tmp)
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("frontmatter-scalar-type", codes)
        self.assertIn("unknown-type", codes)

    def test_sources_consulted_accepts_multiple_page_types(self):
        page = self.tmp / "concepts/sample-concept.md"
        page.write_text(
            CONCEPT.replace(
                "sources: [synthetic-source]",
                "sources: [synthetic-source]\nsources_consulted: [synthetic-source, legacy-repo]",
            ),
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp)
        errors = [
            f
            for f in report["findings"]
            if f["path"] == "concepts/sample-concept.md" and f["level"] == "error"
        ]
        self.assertEqual(errors, [])

    def test_control_linksdevelopers_private_uris_and_typed_refs_are_checked(self):
        (self.tmp / "index.md").write_text(
            "# Index\n[[missing-page]]\nviking://user/alice/resources/private\n",
            encoding="utf-8",
        )
        concept = CONCEPT.replace(
            "sources: [synthetic-source]", "sources: [wrong-source]"
        )
        (self.tmp / "concepts/sample-concept.md").write_text(concept, encoding="utf-8")
        report = wiki_validate.validate(self.tmp, "shared")
        codes = {f["code"] for f in report["findings"]}
        self.assertIn("broken-control-link", codes)
        self.assertIn("private-uri-in-shared", codes)
        self.assertIn("missing-reference", codes)

    def test_shared_rejects_private_alias_in_control_page(self):
        schema = self.tmp / "SCHEMA.md"
        schema.write_text("# Schema\n\nviking://~/resources/private\n", encoding="utf-8")
        report = wiki_validate.validate(self.tmp, "shared")
        matches = [
            f
            for f in report["findings"]
            if f["code"] == "private-uri-in-shared" and f["path"] == "SCHEMA.md"
        ]
        self.assertEqual(len(matches), 1)

    def test_sharded_index_target_and_page_links_are_valid(self):
        indexes = self.tmp / "indexes"
        indexes.mkdir()
        (self.tmp / "index.md").write_text(
            "# Wiki Index\n\n- [[indexes/concepts|Concepts]]\n"
            "- [[synthetic-source]]\n- [[sample-repo]]\n- [[legacy-repo]]\n",
            encoding="utf-8",
        )
        (indexes / "concepts.md").write_text(
            "# Concepts\n\n- [[sample-concept]]\n", encoding="utf-8"
        )
        report = wiki_validate.validate(self.tmp)
        errors = [f for f in report["findings"] if f["level"] == "error"]
        self.assertEqual(errors, [])

    def test_actual_control_templates_initialize_cleanly(self):
        templates = ROOT / "skills/openviking-wiki/assets"
        fresh = self.tmp / "fresh"
        fresh.mkdir()
        for source, destination in (
            ("SCHEMA.md.template", "SCHEMA.md"),
            ("index.md.template", "index.md"),
            ("log.md.template", "log.md"),
            ("page.md.template", ".page-template.md"),
        ):
            shutil.copy2(templates / source, fresh / destination)
        report = wiki_validate.validate(fresh)
        self.assertEqual(report["errors"], 0, report["findings"])

    def test_page_template_can_form_a_valid_page(self):
        template = (ROOT / "skills/openviking-wiki/assets/page.md.template").read_text()
        rendered = (
            template.replace("<source|entity|concept|synthesis>", "concept")
            .replace('title: ""', 'title: "Rendered concept"')
            .replace("tags: []", "tags: [test]")
            .replace("sources: []", "sources: [synthetic-source]")
            .replace("YYYY-MM-DD", "2026-09-10")
            .replace("# Title", "# Rendered concept")
            .replace("`[[wikilinks]]`", "[[synthetic-source]]")
        )
        (self.tmp / "concepts/rendered-concept.md").write_text(
            rendered, encoding="utf-8"
        )
        (self.tmp / "index.md").write_text(
            (self.tmp / "index.md").read_text()
            + "\n- [[rendered-concept]]\n",
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp)
        errors = [
            f
            for f in report["findings"]
            if f["path"] == "concepts/rendered-concept.md" and f["level"] == "error"
        ]
        self.assertEqual(errors, [])

    def test_self_link_does_not_prevent_orphan_warning(self):
        page = self.tmp / "entities/legacy-repo.md"
        page.write_text(
            LEGACY.replace("[[sample-concept]]", "[[legacy-repo]]"), encoding="utf-8"
        )
        (self.tmp / "index.md").write_text(
            (self.tmp / "index.md").read_text().replace("- [[legacy-repo]]\n", ""),
            encoding="utf-8",
        )
        report = wiki_validate.validate(self.tmp)
        matches = [
            f
            for f in report["findings"]
            if f["code"] == "orphan" and f["path"] == "entities/legacy-repo.md"
        ]
        self.assertEqual(len(matches), 1)

    def test_repo_reduced_schema_and_legacy_entity(self):
        report = wiki_validate.validate(self.tmp)
        repo_errors = [
            f
            for f in report["findings"]
            if f["path"] == "entities/sample-repo.md" and f["level"] == "error"
        ]
        legacy_errors = [
            f
            for f in report["findings"]
            if f["path"] == "entities/legacy-repo.md" and f["level"] == "error"
        ]
        self.assertEqual(repo_errors, [])
        self.assertEqual(legacy_errors, [])


class PlannerTests(unittest.TestCase):
    def setUp(self):
        base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, base)
        self.current, self.desired = base / "current", base / "desired"
        self.current.mkdir()
        self.desired.mkdir()
        write_snapshot(self.current)
        write_snapshot(
            self.desired,
            concept=CONCEPT.replace(
                "Artificial content.", "Artificial revised content."
            ),
            log_suffix="\n## [2026-09-10] update | Revised [[sample-concept]]. <!-- operation-id: synthetic-1 -->\n",
        )

    def test_deterministic_plan_order_and_log_append(self):
        first = wiki_plan.make_plan(
            self.current, self.desired, "viking://user/tester/resources/wiki", "tester"
        )
        second = wiki_plan.make_plan(
            self.current, self.desired, "viking://user/tester/resources/wiki", "tester"
        )
        self.assertEqual(first, second)
        self.assertFalse(first["atomic"])
        self.assertEqual(
            [op["relative_path"] for op in first["operations"]],
            ["concepts/sample-concept.md", "log.md"],
        )
        self.assertEqual(first["operations"][-1]["mode"], "append")

    def test_recovery_classifies_partial_write(self):
        plan = wiki_plan.make_plan(
            self.current, self.desired, "viking://resources/wiki"
        )
        base = self.current.parent
        plan_path = base / "plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        partial = base / "partial"
        shutil.copytree(self.current, partial)
        shutil.copy2(
            self.desired / "concepts/sample-concept.md",
            partial / "concepts/sample-concept.md",
        )
        result = wiki_plan.recover(plan_path, partial)
        statuses = {x["relative_path"]: x["status"] for x in result["results"]}
        actions = {x["relative_path"]: x["retry_action"] for x in result["results"]}
        self.assertEqual(statuses["concepts/sample-concept.md"], "intended")
        self.assertEqual(statuses["log.md"], "base")
        self.assertEqual(actions["concepts/sample-concept.md"], "skip")
        self.assertEqual(actions["log.md"], "retry_append")
        self.assertTrue(result["safe_to_retry_remaining"])
        self.assertEqual(
            result["retry_operations"],
            [{"relative_path": "log.md", "retry_action": "retry_append"}],
        )

    def test_final_batch_waits_for_verified_content_and_combines_index_log(self):
        index = self.desired / "index.md"
        index.write_text(index.read_text() + "\nUpdated navigation.\n")
        plan = wiki_plan.make_plan(self.current, self.desired, "viking://resources/wiki")
        self.assertEqual(plan["batches"][-1]["relative_paths"], ["index.md", "log.md"])
        plan_path = self.current.parent / "plan.json"
        plan_path.write_text(json.dumps(plan))
        pending = wiki_plan.recover(plan_path, self.current)
        self.assertEqual(pending["ready_batches"][0]["relative_paths"], ["concepts/sample-concept.md"])
        shutil.copy2(self.desired / "concepts/sample-concept.md", self.current / "concepts/sample-concept.md")
        pending = wiki_plan.recover(plan_path, self.current)
        self.assertEqual(pending["ready_batches"][0]["relative_paths"], ["index.md", "log.md"])
        # A partial final batch must not append the log twice.
        shutil.copy2(self.desired / "log.md", self.current / "log.md")
        pending = wiki_plan.recover(plan_path, self.current)
        self.assertEqual(pending["ready_batches"][0]["relative_paths"], ["index.md"])

    def test_legacy_recovery_preserves_log_phase(self):
        plan = wiki_plan.make_plan(self.current, self.desired, "viking://resources/wiki")
        plan["version"] = 1
        plan.pop("batches")
        for op in plan["operations"]:
            if op["relative_path"] == "log.md":
                op["phase"] = 3
        path = self.current.parent / "legacy-plan.json"
        path.write_text(json.dumps(plan))
        shutil.copy2(self.desired / "concepts/sample-concept.md", self.current / "concepts/sample-concept.md")
        result = wiki_plan.recover(path, self.current)
        self.assertEqual(result["ready_batches"][0]["phase"], 3)

    def test_refuses_deletion_and_invalid_root(self):
        (self.desired / "entities/legacy-repo.md").unlink()
        with self.assertRaisesRegex(ValueError, "refuses deletions"):
            wiki_plan.make_plan(self.current, self.desired, "viking://resources/wiki")
        with self.assertRaisesRegex(ValueError, "root must be"):
            wiki_plan.valid_root("viking://resources/not-wiki")

    def test_private_root_identity_and_uri_characters(self):
        with self.assertRaisesRegex(ValueError, "authenticated actor"):
            wiki_plan.valid_root("viking://user/tester/resources/wiki")
        with self.assertRaisesRegex(ValueError, "does not match"):
            wiki_plan.valid_root("viking://user/tester/resources/wiki", "someone-else")
        for root in (
            "viking://user/test%2fer/resources/wiki",
            "viking://resources/wiki?x=1",
            "viking://resources/wiki#x",
        ):
            with self.assertRaises(ValueError):
                wiki_plan.valid_root(root, "tester")
        for actor in (".", ".."):
            with self.assertRaises(ValueError):
                wiki_plan.valid_root(
                    f"viking://user/{actor}/resources/wiki", actor
                )

    def test_init_plan_from_actual_templates_for_both_roots(self):
        base = self.current.parent
        empty = base / "empty"
        empty.mkdir()
        desired = base / "templates"
        desired.mkdir()
        templates = ROOT / "skills/openviking-wiki/assets"
        for source, destination in (
            ("SCHEMA.md.template", "SCHEMA.md"),
            ("index.md.template", "index.md"),
            ("log.md.template", "log.md"),
            ("page.md.template", ".page-template.md"),
        ):
            shutil.copy2(templates / source, desired / destination)
        shared = wiki_plan.make_plan(empty, desired, "viking://resources/wiki")
        private = wiki_plan.make_plan(
            empty,
            desired,
            "viking://user/tester/resources/wiki",
            "tester",
        )
        expected = [".page-template.md", "SCHEMA.md", "index.md", "log.md"]
        self.assertEqual([op["relative_path"] for op in shared["operations"]], expected)
        self.assertEqual([op["relative_path"] for op in private["operations"]], expected)
        self.assertTrue(all(op["mode"] == "create" for op in shared["operations"]))

    def test_rejects_symlink_and_non_markdown_file(self):
        target = self.current / "concepts/sample-concept.md"
        link = self.current / "concepts/link.md"
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "symlink"):
            wiki_plan.files(self.current)
        link.unlink()
        (self.current / "unexpected.bin").write_bytes(b"x")
        with self.assertRaisesRegex(ValueError, "unexpected file"):
            wiki_plan.files(self.current)

    def test_rejects_encoded_traversal_filename(self):
        path = self.current / "concepts/%2e%2 playable.md"
        path.write_text(CONCEPT, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsafe relative path"):
            wiki_plan.files(self.current)


class PackagingTests(unittest.TestCase):
    def test_codex_and_claude_manifests_share_the_same_skill(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(codex["name"], "openviking-wiki")
        self.assertEqual(claude["name"], codex["name"])
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["skills"], "./skills/")
        self.assertEqual(claude["skills"], "./skills/")
        self.assertTrue((ROOT / "skills/openviking-wiki/SKILL.md").is_file())

    def test_claude_commands_are_thin_and_do_not_define_transport(self):
        commands = sorted((ROOT / "commands").glob("*.md"))
        self.assertGreaterEqual(len(commands), 5)
        for command in commands:
            text = command.read_text()
            self.assertIn("openviking-wiki", text)
            self.assertNotIn("mcp__openviking", text)

    def test_codex_and_claude_manifests_share_skill(self):
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(codex["name"], ROOT.name)
        self.assertEqual(claude["name"], ROOT.name)
        self.assertEqual(codex["version"], claude["version"])
        self.assertEqual(codex["skills"], "./skills/")
        self.assertEqual(claude["skills"], "./skills/")
        self.assertTrue((ROOT / "skills/openviking-wiki/SKILL.md").is_file())

    def test_no_bundled_mcp_or_hooks(self):
        self.assertFalse((ROOT / ".mcp.json").exists())
        self.assertFalse((ROOT / "hooks").exists())
        for manifest in (
            ROOT / ".codex-plugin/plugin.json",
            ROOT / ".claude-plugin/plugin.json",
        ):
            data = json.loads(manifest.read_text())
            self.assertNotIn("mcpServers", data)
            self.assertNotIn("hooks", data)


if __name__ == "__main__":
    unittest.main()
