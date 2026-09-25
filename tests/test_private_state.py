"""Filesystem regressions; these do not substitute for an OCI print test."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/private-state.sh"


class PrivateState(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state with spaces"
        self.spool = self.state / "spool"
        self.cups = self.state / "cups"

    def prepare(self):
        return subprocess.run(
            ["sh", "-ec", '. "$1"; touch "$SPOOL_DIR/new-job"', "sh", str(SCRIPT)],
            env=dict(os.environ, STATE_DIR=str(self.state),
                     SPOOL_DIR=str(self.spool), CUPS_SERVERROOT=str(self.cups)),
            capture_output=True, text=True, umask=0,
        )

    def test_fresh_volume_and_inherited_umask(self):
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        for path in (self.state, self.spool, self.cups / "ssl"):
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.spool / "new-job").stat().st_mode & 0o777, 0o600)

    def test_restart_repairs_modes_without_rewriting_data(self):
        self.assertEqual(self.prepare().returncode, 0)
        files = {self.spool / "pending-job": "print data",
                 self.cups / "ssl/key": "private key",
                 self.cups / "snmp.conf": "user settings",
                 self.state / "gutenprint-printer-app.state": "saved printer"}
        for path, content in files.items():
            path.write_text(content)
        for path in (self.state, self.spool, self.cups / "ssl"):
            path.chmod(0o777)
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        for path, content in files.items():
            self.assertEqual(path.read_text(), content)
        for path in (self.state, self.spool, self.cups / "ssl"):
            self.assertEqual(path.stat().st_mode & 0o777, 0o700)

    def test_symlink_is_rejected_without_changing_target(self):
        target = self.root / "outside"
        target.mkdir(mode=0o755)
        self.state.symlink_to(target)
        result = self.prepare()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.stat().st_mode & 0o777, 0o755)
        self.assertFalse((target / "spool").exists())

    @unittest.skipIf(os.geteuid() == 0, "requires an unprivileged user")
    def test_unwritable_volume_fails_before_creating_jobs(self):
        self.root.chmod(0o500)
        self.addCleanup(self.root.chmod, 0o700)
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertFalse(self.spool.exists())

    def test_non_directory_fails_closed(self):
        self.state.write_text("keep me")
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertEqual(self.state.read_text(), "keep me")


if __name__ == "__main__":
    unittest.main()
