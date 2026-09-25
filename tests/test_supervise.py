"""Real subprocess lifecycle tests; these do not validate printing or IPP."""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "supervise", Path(__file__).resolve().parents[1] / "scripts/supervise.py")
supervise = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervise)


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.supervisor = supervise.Supervisor()
        self.addCleanup(self.supervisor.close, 0.1)

    def start(self, code):
        self.supervisor.start("test child", [sys.executable, "-c", code])
        return self.supervisor.children[-1][1]

    def test_required_child_exit_including_success_is_failure(self):
        for status in (0, 7):
            with self.subTest(status=status):
                self.supervisor = supervise.Supervisor()
                child = self.start(f"raise SystemExit({status})")
                child.wait(timeout=5)
                with self.assertRaisesRegex(RuntimeError, "exited unexpectedly"):
                    self.supervisor.wait()
                self.supervisor.close()

    def test_shutdown_stops_all_children(self):
        children = [self.start("import time; time.sleep(60)") for _ in range(3)]
        self.supervisor.stop()
        self.supervisor.close(0.1)
        self.assertTrue(all(child.poll() is not None for child in children))

    def test_shutdown_kills_child_ignoring_term(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / "ready"
            child = self.start(
                "import signal,time,pathlib; "
                "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                f"pathlib.Path({str(ready)!r}).touch(); time.sleep(60)")
            self.supervisor.ready("test", [sys.executable, "-c",
                f"import pathlib; exit(not pathlib.Path({str(ready)!r}).exists())"], 5)
            self.supervisor.close(0.1)
            self.assertEqual(child.returncode, -signal.SIGKILL)

    def test_signal_to_supervisor_terminates_children(self):
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / "ready"
            harness = f"""
import importlib.util, signal, pathlib, sys
spec = importlib.util.spec_from_file_location('supervise', {str(Path(supervise.__file__).resolve())!r})
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
s = m.Supervisor()
signal.signal(signal.SIGTERM, s.stop)
try:
    for i in range(3):
        s.start(str(i), [sys.executable, '-c', 'import time; time.sleep(60)'])
    pathlib.Path({str(ready)!r}).write_text(' '.join(str(p.pid) for _, p in s.children))
    s.wait()
finally:
    s.close(0.1)
"""
            process = subprocess.Popen([sys.executable, "-c", harness])
            try:
                deadline = time.monotonic() + 5
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(ready.exists())
                pids = [int(pid) for pid in ready.read_text().split()]
                process.terminate()
                self.assertEqual(process.wait(timeout=5), 0)
                for pid in pids:
                    with self.assertRaises(ProcessLookupError):
                        os.kill(pid, 0)
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)

    def test_readiness_timeout_and_failure_cleanup(self):
        child = self.start("import time; time.sleep(60)")
        with self.assertRaisesRegex(RuntimeError, "did not become ready"):
            self.supervisor.ready("test", [sys.executable, "-c", "exit(1)"], 0.1)
        self.supervisor.close(0.1)
        self.assertIsNotNone(child.poll())

    def test_readiness_detects_required_child_exit(self):
        child = self.start("raise SystemExit(0)")
        child.wait(timeout=5)
        with self.assertRaisesRegex(RuntimeError, "exited unexpectedly"):
            self.supervisor.ready("test", [sys.executable, "-c", "exit(0)"], 5)

    def test_stop_during_startup_does_not_launch_next_child(self):
        self.supervisor.stop()
        self.supervisor.ready("test", ["/does/not/exist"])
        self.supervisor.start("test", ["/does/not/exist"])
        self.assertEqual(self.supervisor.children, [])

    def test_port_validation(self):
        for port in ("0", "631", "65536", "-1", "8 632", "", "１２３４"):
            with self.subTest(port=port), patch.dict(os.environ, PORT=port):
                with self.assertRaises(ValueError):
                    supervise.application_command()
        with patch.dict(os.environ, PORT="18632"):
            self.assertIn("server-port=18632", supervise.application_command())
        with patch.dict(os.environ, {}, clear=True):
            self.assertIn("server-port=8632", supervise.application_command())


if __name__ == "__main__":
    unittest.main()
