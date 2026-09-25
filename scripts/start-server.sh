#!/bin/sh
set -eux

# Keep every mutable application resource in the instance's persistent volume.
# shellcheck source=scripts/prepare-state.sh
. "$(dirname "$0")/prepare-state.sh"

# Wait for avahi-daemon to initialize
while true; do
    if [ -f "/var/run/avahi-daemon/pid" ] || [ -f "/run/avahi-daemon/pid" ]; then
        echo "avahi-daemon is active. Starting gutenprint-printer-app..."
        break
    fi

    echo "Waiting for avahi-daemon to initialize..."
    sleep 1
done

# An explicit port prevents PAPPL from selecting another instance's port.
# Saved system/printer names take precedence after the first startup.
exec gutenprint-printer-app -o log-file=- -o server-port="$PORT" \
    -o system-name="${SYSTEM_NAME:-Gutenprint Printer Application ($PORT)}" server
