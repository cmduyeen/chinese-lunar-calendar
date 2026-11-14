import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.files import publish_staged, safe_filename
from src.maintenance import maintain
from src.publish_release import publish_release
from src.release_state import digest, fingerprint, write_state
from src.user_config import MAX_CONFIG_BYTES, load_config_mapping


class SecurityTests(unittest.TestCase):
    def test_portable_filenames_block_traversal_streams_and_device_names(self):
        for name in (
            "../escape.ics",
            "a/b.ics",
            "a\\b.ics",
            "a.ics:secret",
            "CON.ics",
            "NUL.json",
            "LPT1.zip",
            ".git",
            "script.py",
            "..",
            ".ics",
        ):
            with self.subTest(name=name):
                self.assertFalse(safe_filename(name))
        for name in (
            "index.json",
            ".build-state.json",
            "lunar_zh-Hant_latest.ics",
            "custom_family_2026.ics",
        ):
            self.assertTrue(safe_filename(name))

    def test_duplicate_keys_and_nonfinite_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            for raw in (
                '{"country":"VN","country":"CN"}',
                '{"colors":{"holiday":"#000000","holiday":"#FFFFFF"}}',
                '{"start_year":NaN}',
                '{"start_year":Infinity}',
            ):
                path.write_text(raw)
                with self.assertRaises(ValueError):
                    load_config_mapping(path)

    def test_configuration_size_is_bounded_before_parse(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            path.write_bytes(b" " * (MAX_CONFIG_BYTES + 1))
            with self.assertRaisesRegex(ValueError, "256 KiB"):
                load_config_mapping(path)

    def symlink(self, target, link):
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("OS does not grant symlink creation")

    def test_staged_symlink_cannot_read_private_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage"
            stage.mkdir()
            private = root / "private"
            private.write_bytes(b"private")
            self.symlink(private, stage / "feed.ics")
            with self.assertRaisesRegex(ValueError, "Invalid staged"):
                publish_staged(stage, root / "out")
            self.assertFalse((root / "out/feed.ics").exists())

    def test_destination_symlink_cannot_modify_outside_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage"
            out = root / "out"
            stage.mkdir()
            out.mkdir()
            private = root / "private"
            private.write_bytes(b"private")
            self.symlink(private, out / "feed.ics")
            (stage / "feed.ics").write_bytes(b"new")
            with self.assertRaises(ValueError):
                publish_staged(stage, out)
            self.assertEqual(private.read_bytes(), b"private")

    def artifact(self, stage):
        stage.mkdir()
        (stage / "feed.ics").write_bytes(b"verified candidate")
        (stage / "index.json").write_text(
            json.dumps([{"file": "feed.ics", "sha256": digest(b"verified candidate")}])
        )
        write_state(stage, fingerprint())

    def test_publisher_rejects_changed_or_missing_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage"
            self.artifact(stage)
            (stage / "feed.ics").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "Refusing"):
                publish_release(stage, root / "out")
            self.assertFalse((root / "out").exists())

    def test_publisher_ignores_unrecorded_artifact_extras(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stage = root / "stage"
            self.artifact(stage)
            (stage / "extra.ics").write_bytes(b"unverified")
            publish_release(stage, root / "out")
            self.assertEqual((root / "out/feed.ics").read_bytes(), b"verified candidate")
            self.assertFalse((root / "out/extra.ics").exists())
            self.assertEqual(publish_release(stage, root / "out"), [])

    def test_invalid_repository_names_never_reach_github(self):
        for repo in ("../..", "./repo", "-owner/repo", "owner/repo --flag", "owner/.."):
            with self.subTest(repo=repo), patch("src.maintenance.GitHub") as client:
                with self.assertRaises(ValueError):
                    maintain(repo, client, 2026)
                client.api.assert_not_called()

    def test_external_actions_use_immutable_commit_pins(self):
        import re

        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/main.yml").read_text(
            encoding="utf-8"
        )
        references = re.findall(r"uses:\s+([^\s#]+)", workflow)
        self.assertTrue(references)
        for reference in references:
            self.assertRegex(reference, r"^[A-Za-z0-9_./-]+@[a-f0-9]{40}$")

    def test_untrusted_build_has_no_repository_write_permission(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/main.yml").read_text(
            encoding="utf-8"
        )
        build = workflow.split("  verify-and-build:", 1)[1].split("  publish:", 1)[0]
        self.assertIn("contents: read", build)
        self.assertNotIn("contents: write", build)
        publisher = workflow.split("  publish:", 1)[1]
        self.assertIn("github.ref == 'refs/heads/main'", publisher)
        self.assertIn("github.event_name != 'pull_request'", publisher)
        self.assertNotIn("pull_request_target", workflow)

    def test_interrupted_temp_write_does_not_leak_files_or_change_output(self):
        from contextlib import contextmanager
        from types import SimpleNamespace

        from src.files import atomic_write

        real_temporary_file = tempfile.NamedTemporaryFile

        @contextmanager
        def failing_file(*args, **kwargs):
            with real_temporary_file(*args, **kwargs) as file:

                def fail_write(raw):
                    raise OSError("simulated disk full")

                yield SimpleNamespace(name=file.name, write=fail_write)

        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "feed.ics"
            target.write_bytes(b"old")
            with patch("src.files.tempfile.NamedTemporaryFile", side_effect=failing_file):
                with self.assertRaises(OSError):
                    atomic_write(target, b"new")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual([p.name for p in Path(temp).iterdir()], ["feed.ics"])
