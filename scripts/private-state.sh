#!/bin/sh
# Sourced before launching the application; fail closed if modes cannot be set.
umask 077
export STATE_DIR="${STATE_DIR:-/var/lib/gutenprint-printer-app}"
export SPOOL_DIR="${SPOOL_DIR:-/var/spool/gutenprint-printer-app}"
export CUPS_SERVERROOT="${CUPS_SERVERROOT:-/etc/cups}"

for private_dir in "$STATE_DIR" "$SPOOL_DIR" "$CUPS_SERVERROOT/ssl"; do
    # Do not chmod a symlink target supplied by a volume.
    if [ -L "$private_dir" ]; then
        echo "Private state directory must not be a symlink: $private_dir" >&2
        exit 1
    fi
    mkdir -p "$private_dir" || exit 1
    chmod 0700 "$private_dir" || exit 1
done
