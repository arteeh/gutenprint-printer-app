#!/usr/bin/env bash
# Inspect a real `bst artifact checkout` of core-runtime.bst.
set -euo pipefail
root="${1:?usage: runtime-closure.sh ARTIFACT_DIRECTORY}"
for file in usr/bin/gutenprint-printer-app usr/bin/gs usr/bin/bash \
    usr/share/ppd/gutenprint.5.3 usr/lib/cups/filter/rastertogutenprint.5.3 \
    usr/lib/cups/backend/socket usr/lib/cups/backend/usb; do
    test -x "$root/$file"
done
test "$(readlink "$root/usr/lib/gutenprint-printer-app")" = /usr/lib/cups
test -d "$root/usr/share/gutenprint"
test -s "$root/usr/share/gutenprint-printer-app/testpage.pdf"
for command in cc gcc g++ clang make apt apt-get dpkg rpm dnf; do
    for directory in usr/bin usr/sbin bin sbin; do
        test ! -e "$root/$directory/$command"
    done
done
# One actual libcups implementation; SONAME and linker symlinks do not count.
mapfile -t cups < <(find "$root/usr/lib" -type f -name 'libcups.so.*')
[[ ${#cups[@]} == 1 ]]
echo 'OK: staged runtime contains Gutenprint, CUPS and a shell without build tools'
