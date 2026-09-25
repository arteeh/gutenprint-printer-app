#!/bin/sh
# Source before starting the app. CUPS appends /usb to USB_QUIRK_DIR.
export USB_QUIRK_DIR="${STATE_DIR:-/var/lib/gutenprint-printer-app}"
mkdir -p "$USB_QUIRK_DIR/usb"

# FSDK installs CUPS data in /usr/share/cups/usb; Rockcraft relocates both
# tables to BACKEND_DIR. Accept either layout and optional upstream tables.
for quirk_name in org.cups.usb-quirks net.sf.gimp-print.usb-quirks; do
    quirk_target="$USB_QUIRK_DIR/usb/$quirk_name"
    # An empty file or dangling symlink can be an intentional user override.
    if [ -e "$quirk_target" ] || [ -L "$quirk_target" ]; then
        continue
    fi
    for quirk_dir in "${CUPS_DATADIR:-/usr/share/cups}/usb" \
        "${BACKEND_DIR:-/usr/lib/gutenprint-printer-app/backend}"; do
        quirk_source="$quirk_dir/$quirk_name"
        [ -f "$quirk_source" ] || continue
        cp "$quirk_source" "$quirk_target" || return 1
        break
    done
done
unset quirk_name quirk_target quirk_dir quirk_source
