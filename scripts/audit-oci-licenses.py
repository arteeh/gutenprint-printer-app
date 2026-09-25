#!/usr/bin/env python3
"""Report SPDX package licensing and compare captured OCI licensing metadata.

Read-only evidence aid, not a completeness or legal compatibility validator.
"""

import argparse
import json
from pathlib import Path
import sys

LICENSE_KEY = "org.opencontainers.image.licenses"


def audit(sbom, index, configs, expected):
    if sbom.get("spdxVersion") not in ("SPDX-2.2", "SPDX-2.3"):
        raise ValueError("expected an SPDX 2.2 or 2.3 JSON document")
    packages = sbom.get("packages", [])
    if not packages:
        raise ValueError("SBOM contains no packages")
    errors = []
    inventory = []
    for package in packages:
        name = package.get("name")
        identifier = package.get("SPDXID")
        if not name or not identifier:
            raise ValueError("each package must have name and SPDXID")
        declared = package.get("licenseDeclared", "NOASSERTION")
        concluded = package.get("licenseConcluded", "NOASSERTION")
        inventory.append({
            "name": name,
            "SPDXID": identifier,
            "versionInfo": package.get("versionInfo"),
            "licenseDeclared": declared,
            "licenseConcluded": concluded,
            "licenseInfoFromFiles": package.get("licenseInfoFromFiles", []),
            "licenseComments": package.get("licenseComments"),
            "copyrightText": package.get("copyrightText"),
            "reviewRequired": declared in ("NOASSERTION", "NONE", "")
                or concluded in ("NOASSERTION", "NONE", "")
                or declared != concluded,
        })
    metadata = {"index": index.get("annotations", {}).get(LICENSE_KEY)}
    for name, config in configs.items():
        metadata[name] = config.get("config", {}).get("Labels", {}).get(LICENSE_KEY)
    for name, value in metadata.items():
        if value != expected:
            errors.append(f"{name}: license value {value!r} differs from {expected!r}")
    return {
        "documentNamespace": sbom.get("documentNamespace"),
        "packages": sorted(inventory, key=lambda p: (p["name"], p["SPDXID"])),
        "hasExtractedLicensingInfos": sbom.get("hasExtractedLicensingInfos", []),
        "externalDocumentRefs": sbom.get("externalDocumentRefs", []),
        "metadata": metadata,
        "expectedLicense": expected,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sbom", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path,
                        help="raw OCI index JSON (skopeo inspect --raw)")
    parser.add_argument("--config", required=True, action="append", type=Path,
                        help="image config JSON (skopeo inspect --config); repeat for each platform")
    parser.add_argument("--expected-license", required=True,
                        help="reviewed expression; never inferred from incomplete package data")
    args = parser.parse_args()
    try:
        def read(path):
            return json.loads(path.read_text())
        report = audit(read(args.sbom), read(args.index),
                       {str(path): read(path) for path in args.config},
                       args.expected_license)
    except (OSError, ValueError, TypeError, AttributeError) as error:
        parser.exit(2, f"audit error: {error}\n")
    json.dump(report, sys.stdout, indent=2)
    print()
    return bool(report["errors"])


if __name__ == "__main__":
    sys.exit(main())
