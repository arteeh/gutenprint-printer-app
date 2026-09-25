#!/usr/bin/python3
"""Supervise the foreground printer stack as one container service."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import time


class Supervisor:
    def __init__(self):
        self.children = []
        self.stopping = False

    def stop(self, _signum=None, _frame=None):
        self.stopping = True

    def check(self):
        for name, child in self.children:
            status = child.poll()
            if status is not None:
                raise RuntimeError(f"{name} exited unexpectedly (status {status})")
        return not self.stopping

    def start(self, name, command):
        if not self.check():
            return
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                 start_new_session=True)
        self.children.append((name, child))

    def ready(self, name, command, timeout=30):
        deadline = time.monotonic() + timeout
        while self.check():
            try:
                result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, timeout=1)
                if result.returncode == 0:
                    return
            except subprocess.TimeoutExpired:
                pass
            if time.monotonic() >= deadline:
                raise RuntimeError(f"{name} did not become ready within {timeout}s")
            time.sleep(0.1)

    def wait(self):
        while self.check():
            time.sleep(0.1)

    def close(self, timeout=5):
        # Stop consumers before their dependencies. Signal entire sessions so
        # print filters/backends cannot outlive the application on shutdown.
        for _name, child in reversed(self.children):
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()


def application_command():
    port = os.environ.get("PORT", "8632")
    if not port.isascii() or not port.isdecimal() or not 1024 <= int(port) <= 65535:
        raise ValueError("PORT must be an unprivileged port between 1024 and 65535")
    return ["/usr/bin/gutenprint-printer-app", "-o", "log-file=-",
            "-o", f"server-port={int(port)}", "server"]


def main():
    supervisor = Supervisor()
    signal.signal(signal.SIGTERM, supervisor.stop)
    signal.signal(signal.SIGINT, supervisor.stop)
    try:
        command = application_command()
        # These directories are private to the container and owned by its
        # numeric runtime user. State under /var/lib is never removed.
        for directory in ("/run/dbus", "/run/avahi-daemon"):
            Path(directory).mkdir(parents=True, exist_ok=True)
        Path("/run/avahi-daemon/pid").unlink(missing_ok=True)
        supervisor.start("D-Bus", ["/usr/bin/dbus-daemon", "--system",
                                    "--nofork", "--nopidfile"])
        supervisor.ready("D-Bus", ["/usr/bin/dbus-send", "--system",
                                   "--print-reply", "--reply-timeout=500",
                                   "--dest=org.freedesktop.DBus", "/",
                                   "org.freedesktop.DBus.GetId"])
        supervisor.start("Avahi", ["/usr/sbin/avahi-daemon", "--no-drop-root",
                                   "--no-chroot", "--no-rlimits"])
        supervisor.ready("Avahi", ["/usr/bin/dbus-send", "--system",
                                   "--print-reply", "--reply-timeout=500",
                                   "--dest=org.freedesktop.Avahi", "/",
                                   "org.freedesktop.Avahi.Server.GetVersionString"])
        supervisor.start("gutenprint-printer-app", command)
        supervisor.wait()
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"printer supervisor: {error}", file=sys.stderr, flush=True)
        return 1
    finally:
        supervisor.close()


if __name__ == "__main__":
    sys.exit(main())
