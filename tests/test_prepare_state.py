"""Launcher regression tests, not OCI or physical printer validation."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/prepare-state.sh"


class PersistentState(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.backend = self.root / "backend"
        self.backend.mkdir()
        (self.backend / "vendor.usb-quirks").write_text("factory quirks\n")
        (self.backend / "snmp.conf").write_text("factory snmp\n")
        self.state = self.root / "state with spaces"

    def prepare(self, **overrides):
        env = dict(os.environ, STATE_DIR=str(self.state),
                   BACKEND_DIR=str(self.backend), PORT="18080")
        env.update(overrides)
        return subprocess.run(["sh", "-ec", '. "$1"; env', "sh", str(SCRIPT)],
                              env=env, text=True, capture_output=True)

    def test_restart_and_upgrade_preserve_user_data(self):
        self.assertEqual(self.prepare().returncode, 0)
        self.assertEqual((self.state / "cups/snmp.conf").read_text(), "factory snmp\n")
        files = {"cups/snmp.conf": "", "usb/vendor.usb-quirks": "user quirks\n",
                 "gutenprint-printer-app.state": "saved printers\n",
                 "ppd/custom.ppd": "custom driver\n", "cups/ssl/server.crt": "certificate\n",
                 "spool/job.prn": "pending job\n"}
        for name, value in files.items():
            (self.state / name).write_text(value)
        (self.backend / "vendor.usb-quirks").write_text("new factory quirks\n")
        (self.backend / "new.usb-quirks").write_text("new device\n")
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        for name, value in files.items():
            self.assertEqual((self.state / name).read_text(), value)
        self.assertEqual((self.state / "usb/new.usb-quirks").read_text(), "new device\n")
        for key, suffix in {"STATE_FILE": "gutenprint-printer-app.state",
                            "SPOOL_DIR": "spool", "CUPS_SERVERROOT": "cups",
                            "TMPDIR": "tmp"}.items():
            self.assertIn(f"{key}={self.state / suffix}\n", result.stdout)

    def test_instances_have_separate_state(self):
        self.assertEqual(self.prepare().returncode, 0)
        other = self.root / "second"
        self.assertEqual(self.prepare(STATE_DIR=str(other), PORT="18081").returncode, 0)
        (self.state / "cups/snmp.conf").write_text("first only")
        self.assertEqual((other / "cups/snmp.conf").read_text(), "factory snmp\n")

    def test_invalid_configuration_fails_before_creating_state(self):
        for port in ("0", "1023", "65536", "999999999999999999999", "abc", "12 34", "-1"):
            with self.subTest(port=port):
                self.assertNotEqual(self.prepare(PORT=port).returncode, 0)
                self.assertFalse(self.state.exists())
        self.assertNotEqual(self.prepare(STATE_DIR="relative").returncode, 0)

    def test_missing_defaults_are_optional(self):
        self.assertEqual(self.prepare(BACKEND_DIR=str(self.root / "missing")).returncode, 0)
        self.assertTrue((self.state / "cups/ssl").is_dir())

    def test_dangling_user_symlink_is_not_replaced(self):
        (self.state / "cups").mkdir(parents=True)
        target = self.state / "cups/snmp.conf"
        target.symlink_to(self.root / "not-mounted")
        self.assertEqual(self.prepare().returncode, 0)
        self.assertTrue(target.is_symlink())
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
