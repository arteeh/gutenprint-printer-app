#!/bin/sh
# Sourced by start-server.sh; also usable by a future OCI supervisor.
PORT=${PORT:-8000}
case "$PORT" in
    *[!0-9]*|'') echo "PORT must be an integer from 1024 to 65535" >&2; exit 1 ;;
esac
if [ "${#PORT}" -gt 5 ] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    echo "PORT must be an integer from 1024 to 65535" >&2
    exit 1
fi

STATE_DIR=${STATE_DIR:-/var/lib/gutenprint-printer-app}
case "$STATE_DIR" in
    /*) ;;
    *) echo "STATE_DIR must be an absolute path" >&2; exit 1 ;;
esac
export STATE_DIR
export STATE_FILE="$STATE_DIR/gutenprint-printer-app.state"
export SPOOL_DIR="$STATE_DIR/spool"
export USB_QUIRK_DIR="$STATE_DIR"
export CUPS_SERVERROOT="$STATE_DIR/cups"
export TMPDIR="$STATE_DIR/tmp"
export PPD_PATHS="/usr/share/ppd:$STATE_DIR/ppd"
export BACKEND_DIR="${BACKEND_DIR:-/usr/lib/gutenprint-printer-app/backend}"

umask 077
mkdir -p "$SPOOL_DIR" "$USB_QUIRK_DIR/usb" "$CUPS_SERVERROOT/ssl" \
    "$TMPDIR" "$STATE_DIR/ppd"

# Seed missing defaults only. Never rewrite user configuration on restart or
# image upgrade, including deliberately empty files and existing symlinks.
for source in "$BACKEND_DIR"/*.usb-quirks "$BACKEND_DIR/snmp.conf"; do
    [ -f "$source" ] || continue
    case "$source" in
        *.usb-quirks) destination="$USB_QUIRK_DIR/usb/${source##*/}" ;;
        *) destination="$CUPS_SERVERROOT/snmp.conf" ;;
    esac
    if [ ! -e "$destination" ] && [ ! -L "$destination" ]; then
        cp "$source" "$destination"
    fi
done
