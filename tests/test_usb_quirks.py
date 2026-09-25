"""Exercise the real seeder against the supported installed-file layouts."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/seed-usb-quirks.sh"
TABLES = ("org.cups.usb-quirks", "net.sf.gimp-print.usb-quirks")


class USBQuirksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state"
        self.cups = self.root / "share/cups"
        self.backend = self.root / "backend"
        (self.cups / "usb").mkdir(parents=True)
        self.backend.mkdir()

    def seed(self):
        result = subprocess.run(
            ["sh", "-ec", '. "$1"; printf "%s" "$USB_QUIRK_DIR"', "sh", str(SCRIPT)],
            env={**os.environ, "STATE_DIR": str(self.state),
                 "CUPS_DATADIR": str(self.cups), "BACKEND_DIR": str(self.backend)},
            check=True, text=True, capture_output=True,
        )
        self.assertEqual(result.stdout, str(self.state))

    def test_installed_layouts(self):
        for layout in ("rockcraft", "fsdk"):
            with self.subTest(layout=layout):
                for name in TABLES:
                    source_dir = self.backend if layout == "rockcraft" else self.cups / "usb"
                    (source_dir / name).write_text("# upstream defaults\n")
                self.seed()
                for name in TABLES:
                    target = self.state / "usb" / name
                    self.assertEqual(target.read_text(), "# upstream defaults\n")
                    self.assertTrue(os.access(target, os.R_OK))
                    target.unlink()
                    (source_dir / name).unlink()

    def test_split_installed_layout(self):
        (self.cups / "usb" / TABLES[0]).write_text("# CUPS defaults\n")
        (self.backend / TABLES[1]).write_text("# Gutenprint defaults\n")
        self.seed()
        self.assertEqual((self.state / "usb" / TABLES[0]).read_text(), "# CUPS defaults\n")
        self.assertEqual((self.state / "usb" / TABLES[1]).read_text(), "# Gutenprint defaults\n")

    def test_restart_and_upgrade_preserve_edits_and_empty_files(self):
        for name in TABLES:
            (self.backend / name).write_text("# original\n")
        self.seed()
        for name, content in zip(TABLES, ("# user override\n", "")):
            (self.state / "usb" / name).write_text(content)
            (self.backend / name).write_text("# upgraded defaults\n")
        self.seed()
        self.assertEqual((self.state / "usb" / TABLES[0]).read_text(), "# user override\n")
        self.assertEqual((self.state / "usb" / TABLES[1]).read_text(), "")

    def test_missing_optional_defaults_and_later_install(self):
        self.seed()
        self.assertEqual(list((self.state / "usb").iterdir()), [])
        (self.backend / TABLES[1]).write_text("# newly installed\n")
        self.seed()
        self.assertEqual((self.state / "usb" / TABLES[1]).read_text(), "# newly installed\n")

    def test_existing_symlinks_are_preserved(self):
        (self.state / "usb").mkdir(parents=True)
        external = self.root / "override"
        external.write_text("# user override\n")
        for name, link in zip(TABLES, (external, self.root / "missing")):
            (self.state / "usb" / name).symlink_to(link)
            (self.backend / name).write_text("# default\n")
        self.seed()
        self.assertEqual(external.read_text(), "# user override\n")
        for name in TABLES:
            self.assertTrue((self.state / "usb" / name).is_symlink())
        self.assertFalse((self.root / "missing").exists())

    def test_standard_data_path_takes_precedence(self):
        for name in TABLES:
            (self.cups / "usb" / name).write_text("# standard path\n")
            (self.backend / name).write_text("# relocated path\n")
        self.seed()
        for name in TABLES:
            self.assertEqual((self.state / "usb" / name).read_text(), "# standard path\n")
