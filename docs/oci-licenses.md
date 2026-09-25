# OCI license evidence

The root `LICENSE` and `NOTICE` describe the application source. They do not
inventory the software in a composed printer image. In particular, issue #22
records GPL-2.0-or-later Gutenprint driver sources; an Apache-2.0-only image
label is not an aggregate inventory. Neither is the two-license candidate
`Apache-2.0 AND GPL-2.0-or-later` evidence of the entire runtime's licensing.

The [OCI annotation specification](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
defines `org.opencontainers.image.licenses` for contained software using an
SPDX expression. Before publishing an aggregate expression, review the full
staged runtime and record the evidence below. Do not construct an expression
by concatenating scanner findings: alternatives, exceptions, unknowns and
source files excluded from the image need review. If choosing source-scoped
metadata instead, explicitly document that scope on the image and index and
link the full artifact inventory; do not silently present it as an aggregate.

## Evidence to collect

For each architecture, retain the immutable source revision, image digest,
complete SPDX JSON, and a manifest of staged license/notice files. Review:

| Component | Source evidence to retain and inspect |
| --- | --- |
| Application | This revision's `LICENSE`, `NOTICE`, and source headers |
| Gutenprint | Pinned source `COPYING`, `debian/copyright`, and headers for installed drivers, filters, libraries, utilities and data |
| PAPPL | Pinned source `LICENSE`, `NOTICE` where present, and headers, including local patches |
| CUPS | Pinned source license/notice files and headers for installed libraries and backends, including local patches |
| FSDK and other runtime dependencies | Every staged component's pinned source notices and SPDX package records, including libcupsfilters, libppd, pappl-retrofit and any interpreter/runtime libraries |

The Gutenprint finding in [issue #22](https://github.com/projectbluefin/gutenprint-printer-app/issues/22)
uses `debian/copyright` at commit `5131fd401a6f4221a623125dd8b710b365ad83d3`.
Recheck the actual build pin; this finding is not a substitute for auditing
another revision. FSDK is a collection of components, not one license.

Keep all third-party notices, extracted `LicenseRef` texts, and unresolved
license findings. Repair missing source metadata or staging rules instead of
removing packages, license files or SPDX records to make a check pass.
Resolve referenced external SPDX documents before calling an inventory complete.
Distinguish build-only dependencies from the contents of the final layer.

## Capture and compare

At the time this procedure was added, the FSDK graph and `just sbom` command
were proposed in [PR #27](https://github.com/projectbluefin/gutenprint-printer-app/pull/27),
not present on `testing`. After integration, generate the complete SPDX from
the same pinned graph used to build each architecture (the proposal uses
`buildstream-sbom --deps all`). Archive the original outputs. A filesystem
scanner alone can miss source-built software without package-manager records.
Check that Gutenprint, PAPPL, CUPS, the app and the full runtime closure appear;
compare their records with the source notices and actual staged files above.

Capture the published index by immutable digest, then capture each platform's
config by its child manifest digest, not by a mutable tag:

```sh
skopeo inspect --raw "docker://${IMAGE}@${INDEX_DIGEST}" > index.json
skopeo inspect --config "docker://${IMAGE}@${AMD64_MANIFEST_DIGEST}" > amd64-config.json
skopeo inspect --config "docker://${IMAGE}@${ARM64_MANIFEST_DIGEST}" > arm64-config.json
python3 scripts/audit-oci-licenses.py \
  --sbom gutenprint-printer-app.spdx.json \
  --index index.json \
  --config amd64-config.json --config arm64-config.json \
  --expected-license "$REVIEWED_LICENSE_EXPRESSION" > license-audit.json
```

Take child digests from `index.json`'s `manifests`, checking their platforms.
Repeat with each architecture's SBOM when they differ. Also perform this
comparison on the local candidate index/configs **before** registry writes.
Retrieve the attached SPDX artifact, verify its signature and subject digest,
and compare it with the archived build output; matching labels alone does not
bind an SBOM to an image. Record those digest/signature results with the report.

The read-only script reports every package, both declared and concluded license
values, review flags, extracted texts and external document references. Missing
license values remain `NOASSERTION`, consistent with
[SPDX package information](https://spdx.github.io/spdx-spec/v2.3/package-information/).
It exits 1 for missing or different OCI license values and 2 for unreadable or
unsupported inputs. Equality is exact, so use one reviewed expression in both
the image builder and index publisher.

Exit 0 proves only that the supplied metadata matches the supplied expression.
It does not validate SPDX syntax, source notice retention, package coverage,
license compatibility, architecture coverage, signatures or digest binding.
`reviewRequired` findings still require inspection even on exit 0. The report
is not a replacement for the original SBOM (including its file records).

## Remaining release evidence

Issue #22 stays open until a full image has been built and inspected, the
source/notice inventory reviewed, a scoped or aggregate metadata policy applied
to the publisher, and the published index and attached SBOM verified. This
procedure and its tool do not claim that an image has been built or published,
or that OCI printing or physical paper output has been verified.

Run the audit tool's regression tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_license_audit.py'
```
