#!/usr/bin/env bash
# Run on each native architecture; graph mode also supports cross-architecture inspection.
set -euo pipefail
arch="${ARCH:-$(uname -m)}"
bst="${BST:-bst}"
target=printer-app/core-runtime.bst
cups=freedesktop-sdk.bst:components/_private/cups-base.bst
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

"$bst" --no-interactive -o arch "$arch" show --deps all --format '%{name}' "$target" > "$work/graph"
"$bst" --no-interactive -o arch "$arch" show --deps all --format '%{state}' "$target" > "$work/states"
if grep -q 'no reference' "$work/states"; then
    echo 'Unpinned source in printing graph' >&2
    exit 1
fi
# Link aliases must converge on the shared junction's single CUPS source owner.
[[ $(grep -c ':components/_private/cups-base.bst$' "$work/graph") == 1 ]]
"$bst" --no-interactive -o arch "$arch" show --deps none --format '%{public}' "$cups" > "$work/public"
grep -q cups-libs "$work/public"
grep -q cups-license "$work/public"
"$bst" --no-interactive -o arch "$arch" show --deps run --format '%{name}' printer-app/core-stack.bst > "$work/runtime"
if grep -E '/(gcc|clang|apt|dpkg|rpm|dnf|flatpak|buildsystem-[^/]*)\.bst$' "$work/runtime"; then
    echo 'Unexpected build tool or package manager in runtime closure' >&2
    exit 1
fi

if [[ ${1:-} == --sources ]]; then
    "$bst" --no-interactive -o arch "$arch" source checkout --directory "$work/cups" "$cups"
    mapfile -t usb_sources < <(find "$work/cups" -path '*/backend/usb-libusb.c')
    [[ ${#usb_sources[@]} == 1 ]]
    grep -q 'getenv("USB_QUIRK_DIR")' "${usb_sources[0]}"
    grep -q 'browsers = /\*6\*/1' "${usb_sources[0]%usb-libusb.c}dnssd.c"
    "$bst" --no-interactive -o arch "$arch" source checkout --directory "$work/gutenprint" printer-app/gutenprint.bst
fi
printf 'OK: %s printing graph has one CUPS owner and no runtime toolchain\n' "$arch"
