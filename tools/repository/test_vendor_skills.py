import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from vendor_skills import (LOCK, CATALOG, CATALOG_MD, ROOT, check, find, first_paragraph, frontmatter, install,
                           render_catalog, selected, tree_summary)

SKILL = "---\nname: {name}\ndescription: \"{description}\"\n---\n\nVoir [référence](reference.md).\n"


def git(directory, *arguments):
    return subprocess.run(["git", "-C", str(directory), *arguments], check=True, capture_output=True, text=True).stdout.strip()


def upstream(directory):
    """A synthetic upstream repository with requested and excluded files."""
    files = {
        "LICENSE": "MIT License\n",
        "plugins/craft/skills/story-shape/SKILL.md": SKILL.format(name="story-shape", description="Structure d'un récit."),
        "plugins/craft/skills/story-shape/reference.md": "Référence\r\n",
        "plugins/craft/skills/story-shape/story-shape.evals.json": "{}",
        "hooks/post-tool.md": "---\nname: hook\n---\n",
        "scripts/install.sh": "echo installed\n",
    }
    for name, content in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8"))
    git(directory, "init", "-q")
    git(directory, "add", ".")
    git(directory, "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-q", "-m", "fixture")
    return git(directory, "rev-parse", "HEAD")


def lock(root, repository, commit, **changes):
    value = {"version": 1, "collections": [{
        "id": "craft", "repository": repository, "commit": commit, "license": "MIT", "license_files": ["LICENSE"],
        "include": ["LICENSE", "plugins/craft/skills/**/*.md"], "map": {"plugins/craft/skills/": "skills/"}, **changes}]}
    path = root / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class VendorSkillsTest(unittest.TestCase):
    def test_pinned_install_copies_only_requested_text_and_detects_changes(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as target:
            source, root = Path(source), Path(target)
            commit = upstream(source)
            lock(root, source.as_uri(), commit)
            summary = install(root)["craft"]
            installed = root / ".agents/vendor/craft"
            self.assertEqual(sorted(p.relative_to(installed).as_posix() for p in installed.rglob("*") if p.is_file()),
                             ["LICENSE", "skills/story-shape/SKILL.md", "skills/story-shape/reference.md"])
            self.assertEqual((installed / "skills/story-shape/reference.md").read_bytes(), "Référence\n".encode("utf-8"))
            self.assertEqual(summary["skills"], 1)
            self.assertEqual(check(root)["craft"], summary)
            catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
            self.assertEqual(catalog["entries"][0]["id"], "craft/story-shape")
            self.assertEqual(catalog["collections"]["craft"]["commit"], commit)
            self.assertEqual([e["id"] for e in find(root, "récit")], ["craft/story-shape"])
            markdown = (root / CATALOG_MD).read_text(encoding="utf-8")
            self.assertIn("| [story-shape](craft/skills/story-shape/SKILL.md) | Structure d'un récit. |", markdown)
            # A stale Markdown catalogue is reported like a stale JSON catalogue.
            (root / CATALOG_MD).write_text(markdown.replace("récit", "film"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Catalogue à régénérer"):
                check(root)
            install(root)
            check(root)
            # A local edit is reported and protected from a silent reinstall.
            (installed / "skills/story-shape/SKILL.md").write_text("modifié", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "révision installée"):
                check(root)
            with self.assertRaisesRegex(ValueError, "modifiée"):
                install(root)
            install(root, replace_modified=True)
            check(root)

    def test_unknown_commit_and_missing_license_are_refused(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as target:
            source, root = Path(source), Path(target)
            commit = upstream(source)
            lock(root, source.as_uri(), "0" * 40)
            with self.assertRaisesRegex(ValueError, "Git"):
                install(root)
            lock(root, source.as_uri(), commit, include=["plugins/craft/skills/**/*.md"])
            with self.assertRaisesRegex(ValueError, "Licence"):
                install(root)
            self.assertFalse((root / ".agents/vendor/craft").exists())

    def test_selection_rejects_executables_and_unexpected_vendor_files(self):
        collection = {"include": ["**"], "map": {}}
        self.assertEqual(selected("skills/a/SKILL.md", collection), "skills/a/SKILL.md")
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as target:
            source, root = Path(source), Path(target)
            commit = upstream(source)
            lock(root, source.as_uri(), commit, include=["LICENSE", "scripts/*"])
            with self.assertRaisesRegex(ValueError, "Seuls les textes"):
                install(root)
            lock(root, source.as_uri(), commit)
            install(root)
            (root / ".agents/vendor/autre").mkdir()
            with self.assertRaisesRegex(ValueError, "sans collection"):
                check(root)

    def test_frontmatter_reads_quoted_and_folded_descriptions(self):
        self.assertEqual(frontmatter('---\nname: a\ndescription: "Dit \\"oui\\""\n---\n')["description"], 'Dit "oui"')
        self.assertEqual(frontmatter("---\ndescription: >\n  deux\n  lignes\nname: b\n---\n"), {"description": "deux lignes", "name": "b"})

    def test_agent_without_description_uses_its_first_paragraph(self):
        agent = "---\nname: a-agent\nskills:\n  - x\n---\n\n# A Agent\n\n## What this agent does\nBuilds a\nfull package.\n\n- item\n"
        self.assertEqual(first_paragraph(agent), "Builds a full package.")
        self.assertEqual(first_paragraph("---\nname: b\n---\n\n# Titre\n\n- liste seule\n"), "")

    def test_markdown_catalogue_escapes_table_cells(self):
        catalog = {"collections": {"craft": {"repository": "https://github.com/o/craft.git", "commit": "a" * 40, "license": "MIT"}},
                   "entries": [{"name": "pipe", "collection": "craft", "kind": "skill", "language": "en", "category": "",
                                "path": ".agents/vendor/craft/skills/pipe/SKILL.md", "description": "a | b <c>"}]}
        markdown = render_catalog(catalog)
        self.assertIn("| [pipe](craft/skills/pipe/SKILL.md) | a \\| b &lt;c> |", markdown)
        self.assertIn("[o/craft](https://github.com/o/craft) · commit `aaaaaaa` · licence MIT", markdown)

    def test_tree_digest_uses_posix_order_on_every_platform(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("LICENSE", "agents/a-agent.md", "skills/x/SKILL.md", "skills/x/reference.md"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_text(name, encoding="utf-8")
            rows = sorted((n, hashlib.sha256(n.encode("utf-8")).hexdigest())
                          for n in ("LICENSE", "agents/a-agent.md", "skills/x/SKILL.md", "skills/x/reference.md"))
            expected = hashlib.sha256("".join(f"{n}\0{h}\n" for n, h in rows).encode("utf-8")).hexdigest()
            self.assertEqual(tree_summary(root)["tree_sha256"], expected)

    def test_no_ignore_rule_hides_an_installed_file(self):
        # Upstream folders such as data-journalism/analysis collide with local output rules.
        names = [p.relative_to(ROOT).as_posix() for p in (ROOT / ".agents/vendor").rglob("*") if p.is_file()]
        ignored = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin"], input="\n".join(names),
                                 capture_output=True, text=True).stdout.split()
        self.assertEqual(ignored, [])

    def test_repository_collections_match_their_lock(self):
        result = check(ROOT)
        self.assertEqual(result["screenwriting-skills"]["skills"], 26)
        self.assertEqual(result["cc-skills"]["skills"], 1)
        self.assertGreaterEqual(result["autopunk-media-skills"]["skills"], 400)


if __name__ == "__main__":
    unittest.main()
