import tempfile
import unittest
from pathlib import Path
from server.migrate import migrate_legacy_secrets


class MigrationTests(unittest.TestCase):
    def test_exclusive_secret_copy_preserves_source_and_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".streamlit").mkdir()
            source = root / ".streamlit/secrets.toml"
            source.write_text('OPENAI_API_KEY = "migration-test-only"')
            self.assertTrue(migrate_legacy_secrets(root))
            destination = root / "config/secrets.toml"
            self.assertEqual(source.read_text(), destination.read_text())
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
            destination.write_text('OPENAI_API_KEY = "existing-test-only"')
            self.assertFalse(migrate_legacy_secrets(root))
            self.assertIn("existing-test-only", destination.read_text())
