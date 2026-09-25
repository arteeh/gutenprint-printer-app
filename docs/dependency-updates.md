# Dependency proposal ownership

The organization Renovate runner reads `renovate.json`; do not add a second
repository-local Renovate schedule. Proposals target `testing`. Promotion to
`stable` is a separate operation. All Renovate updates require review, including
pin and digest updates enabled by inherited organization configuration. Proposals
are opened immediately so failed compatibility checks remain visible.

## Current ownership

| Inputs | Proposal owner | Renovate policy |
| --- | --- | --- |
| `.github/workflows/*.yml` action references | Organization Renovate runner | GitHub Actions manager enabled |
| `rockcraft.yaml`, `snap/**` source/version fields | Existing `auto-update.yml` desktop-snaps workflow | Excluded from extraction |
| Application C sources in this checkout | Contributors | No dependency manager |
| Future BuildStream application/driver sources | Assign when #2 lands | No source manager enabled yet |

The manager allowlist prevents inherited custom managers from silently taking
ownership of new source manifests. The legacy file exclusions also preserve the
existing updater boundary if more managers are enabled later. Neither Renovate
nor a new source tracker should update a pin already owned by desktop-snaps or
another source updater.

## Enabling application and driver proposals

Issue [#8](https://github.com/projectbluefin/gutenprint-printer-app/issues/8)
is not complete with this configuration. Its source graph prerequisite is
[#2](https://github.com/projectbluefin/gutenprint-printer-app/issues/2).
Once that graph exists, the change enabling source proposals must:

1. List each concrete source field and its single updater owner. Where a dedicated
   FSDK source tracker owns a ref, exclude it from Renovate. Transfer ownership by
   removing the previous updater's scope in the same change.
2. Add narrowly scoped managers for unowned application/driver stable releases;
   exclude development, beta and release-candidate refs. Exercise extraction and
   replacement with a newer eligible release and an ineligible prerelease.
3. Update immutable commits or archive integrity hashes together with version
   metadata and OCI labels in one proposal. Do not introduce tag-only updates or
   an unused lock file disconnected from the actual build graph.
4. Verify that a repeat runner invocation updates the existing proposal rather
   than creating a competing PR. Keep automerge disabled and failed checks visible.
5. Require full native OCI builds and real print-to-socket-sink verification on
   both x86_64 and aarch64 before release. Promotion must consume that verified
   image, not rebuild an untested image. An echo fixture or manifest-only check
   does not prove printing behavior; physical output requires printer hardware.

The Ghostscript [source updater precedent](https://github.com/projectbluefin/ghostscript-printer-app/blob/main/.github/workflows/update-fsdk-sources.yml)
shows atomic source and metadata updates, but must not be copied as a second
owner of Renovate-managed refs. The current Rockcraft/Snapcraft build workflows
are not evidence that the future OCI print gate has passed.

Validate repository configuration with `renovate-config-validator --strict
renovate.json` using the Renovate version deployed by the organization runner.
