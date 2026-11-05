from pathlib import Path
import tempfile
import unittest

from sync_skills import sync


class SkillsTest(unittest.TestCase):
    def test_prefix_and_claude_compatibility(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / ".agents/skills/sandbox-test/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: sandbox-test\ndescription: Contrôle local.\n---\n\nConsignes.\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                sync(root)
            self.assertEqual(sync(root, write=True), 1)
            self.assertEqual(sync(root), 1)
            source.write_text(source.read_text(encoding="utf-8").replace("name: sandbox-test", "name: test"), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SANDBOX"):
                sync(root, write=True)

    def test_vendor_collections_stay_out_of_discovery(self):
        # External skills keep their upstream names and are loaded through the onboarding catalog only.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / ".agents/skills/sandbox-test/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: sandbox-test\ndescription: Test.\n---\n", encoding="utf-8")
            vendor = root / ".agents/vendor/craft/skills/story-shape/SKILL.md"
            vendor.parent.mkdir(parents=True)
            vendor.write_text("---\nname: story-shape\ndescription: Amont.\n---\n", encoding="utf-8")
            self.assertEqual(sync(root, write=True), 1)
            self.assertFalse((root / ".claude/skills/story-shape").exists())

    def test_unmanaged_wrapper_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / ".agents/skills/sandbox-test/SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("---\nname: sandbox-test\ndescription: Test.\n---\n", encoding="utf-8")
            target = root / ".claude/skills/sandbox-test/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("Entrée personnalisée", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "non géré"):
                sync(root, write=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "Entrée personnalisée")

    def test_registered_portable_skill_is_preserved_without_a_canonical_wrapper(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / '.agents/skills/sandbox-test/SKILL.md'
            source.parent.mkdir(parents=True)
            source.write_text('---\nname: sandbox-test\ndescription: Test.\n---\n', encoding='utf-8')
            target = root / '.claude/skills/haxprox-youtube-thumbnail-loop/SKILL.md'
            target.parent.mkdir(parents=True)
            content = '---\nname: haxprox-youtube-thumbnail-loop\ndescription: Skill autonome.\n---\n\nConsignes locales.\n'
            target.write_text(content, encoding='utf-8')
            self.assertEqual(sync(root, write=True), 1)
            self.assertEqual(target.read_text(encoding='utf-8'), content)
            self.assertFalse((root / '.agents/skills/haxprox-youtube-thumbnail-loop').exists())
            target.write_text(content.replace('name: haxprox-youtube-thumbnail-loop', 'name: wrong'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'autonome invalide'):
                sync(root)

    def test_unregistered_orphan_still_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / '.agents/skills/sandbox-test/SKILL.md'
            source.parent.mkdir(parents=True)
            source.write_text('---\nname: sandbox-test\ndescription: Test.\n---\n', encoding='utf-8')
            orphan = root / '.claude/skills/unregistered/SKILL.md'
            orphan.parent.mkdir(parents=True)
            orphan.write_text('Consignes.', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'sans skill canonique'):
                sync(root, write=True)
