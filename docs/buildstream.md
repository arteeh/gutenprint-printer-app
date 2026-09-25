# Source-pinned printing runtime

The BuildStream entry point is `printer-app/core-runtime.bst`. It composes the
repository's Gutenprint application, the Gutenprint driver and the shell-enabled
FSDK runtime. Rockcraft and distribution packages are not inputs to this graph.
`rockcraft.yaml` remains the legacy packaging recipe.

## Ownership and source updates

`elements/printing-stack.bst` pins projectbluefin/ghostscript-printer-app at
`f36174f27f5bb08421712bd77680cbddfc71862e`. That published commit is the shared
printing seam: its FSDK junction pins 26.08rc.1 at
`e076d4978ee6945763486f6ebd755d189460e4e7` and applies its canonical CUPS,
libcupsfilters and cups-filters patches. The link elements resolve into this
same project; there is no local CUPS source, patch copy or libcups provider.
Both FSDK consumers and PAPPL/retrofit use that one patched FSDK CUPS base.
The only junction override unifies the identical community plugin pin, avoiding
duplicate plugin project contexts. It does not override any FSDK component.

PAPPL and retrofit are reused from the shared project. Only Gutenprint's driver
and this repository's application are built locally. Gutenprint is pinned to
`5302dac58533a298f6890b2767492128910ea77b` (Debian's
`debian/5.3.4.20220624T01008808d602-4`), matching the existing packaging source.
`VERSION` is the application version input. BuildStream hashes the explicitly
listed local application files into the artifact key.

Update the shared junction as a unit and review its FSDK ref and patch changes.
Do not copy its patches or introduce a second CUPS build. Rerun the source
checkout probe after any pin update: `bst show` alone cannot prove patches apply.
The legacy `patches/cups-dnssd-backend-socket-only.patch` remains a Rockcraft/Snap
input only and is not imported by BuildStream.

## Native validation

Use BuildStream 2.5+, its host source tools (`git`, `patch`, `lzip`) and the pinned
FSDK builder image in `.github/workflows/printing-graph.yml`. Run on each native
architecture (`x86_64` and `aarch64`):

```sh
export ARCH="$(uname -m)"
tests/printing-graph.sh --sources
bst --no-interactive -o arch "$ARCH" source fetch --deps all printer-app/core-runtime.bst
bst --no-interactive -o arch "$ARCH" build printer-app/core-runtime.bst
bst --no-interactive -o arch "$ARCH" artifact checkout --directory .build-out printer-app/core-runtime.bst
tests/runtime-closure.sh .build-out
```

The graph probe checks one CUPS base owner, preserved library/license splits,
and absence of compiler/package-manager elements from the runtime closure.
`--sources` checks out CUPS and Gutenprint at their immutable refs and verifies
the DNS-SD socket-only and USB quirk-directory patches in the staged CUPS source.
CI starts without a persistent source cache and also fetches the complete graph.
The artifact probe checks real binaries, the dynamic PPD generator, application
backend symlink, a shell, and one libcups implementation, with no compiler or
package-manager executables. Development, documentation, debug, test and static
split domains are excluded from composition.

The driver installs in `/usr/lib/cups`, the application exposes that directory
through `/usr/lib/gutenprint-printer-app`, and the dynamic Gutenprint PPD generator
is installed in `/usr/share/ppd`. Libraries use FSDK's multiarch libdir. Build
systems are build-only dependencies; the composed runtime includes GNU shell
utilities but no SDK.

These probes establish graph/source and staged-file contracts. They do not prove
an OCI service can print. The OCI packaging work must run the real application
through IPP to a socket sink and inspect the resulting printer data. Physical
paper output remains unverified without hardware.
