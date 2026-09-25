#!/usr/bin/env python3
"""Check auto-selection against a built app and its real expert PPD inventory."""

import argparse
import shlex
import subprocess


def drivers(command, device_id=None):
    args = [*command, "drivers"]
    if device_id is not None:
        args += ["-o", f"device-id={device_id}"]
    result = subprocess.run(args, check=True, text=True, capture_output=True, timeout=120)
    rows = [shlex.split(line) for line in result.stdout.splitlines() if line.strip()]
    if any(len(row) != 3 for row in rows):
        raise RuntimeError(f"Unexpected driver listing: {result.stdout!r}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="app command (optionally prefixed by an OCI runtime)")
    command = parser.parse_args().command or ["gutenprint-printer-app"]
    if command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("missing application command after --")

    # A failed/empty inventory must not make the negative cases pass vacuously.
    inventory = drivers(command)
    if not inventory:
        raise RuntimeError("No drivers registered")

    for command_set in ("PCL", "PCL5", "PCL5c", "PCLXL", "PCL6", "PCL,PCL5c,PCLXL"):
        device_id = f"MFG:HiveUnknown;MDL:Unsupported PCL device;CMD:{command_set};"
        selected = drivers(command, device_id)
        if selected:
            raise RuntimeError(f"Unsupported device {device_id!r} selected {selected!r}")

    # IDs from Gutenprint's escp2.xml and canon.xml, not generic PCL fixtures.
    for device_id, model, driver_prefix in (
        ("MFG:EPSON;MDL:Stylus Photo R300;DES:EPSON Stylus Photo R300;",
         "Epson Stylus Photo R300", "epson-stylus-photo-r300--"),
        ("MFG:Canon;MDL:iP4000;CMD:BJL,BJRaster3,BSCCe;", "Canon PIXMA iP4000", "canon-ip4000--"),
    ):
        selected = drivers(command, device_id)
        if len(selected) != 1:
            raise RuntimeError(f"Expected one {model} driver, got {selected!r}")
        row = selected[0]
        if (row not in inventory or
                not row[0].startswith(driver_prefix) or
                "simplified" in row[1].lower()):
            raise RuntimeError(f"Expected registered {model} PPD, got {row!r}")
        # Advertising PCL must not displace an otherwise supported model.
        pcl_id = device_id.split("CMD:")[0] + "CMD:PCL,PCL5c,PCLXL;"
        if drivers(command, pcl_id) != selected:
            raise RuntimeError(f"PCL command set changed selection for {model}")
        print(f"PASS: {model}: {row[0]}")
    print("PASS: unknown PCL devices select no driver")


if __name__ == "__main__":
    main()
