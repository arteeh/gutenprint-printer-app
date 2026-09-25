kind: manual
description: Build the Gutenprint Printer Application executable.

sources:
  - kind: local
    path: Makefile
  - kind: local
    path: gutenprint-printer-app.c
  - kind: local
    path: gutenprint-printer-app.1
  - kind: local
    path: gutenprint-printer-app.service
  - kind: local
    path: testpage.ps
  - kind: local
    path: VERSION

build-depends:
  # Makefile detects this directory to install the application backend symlink.
  - freedesktop-sdk.bst:components/cups-daemon-only.bst
  - freedesktop-sdk.bst:public-stacks/buildsystem-autotools.bst

depends:
  - printer-app/pappl-retrofit.bst
  - freedesktop-sdk.bst:components/ghostscript.bst

config:
  build-commands:
    - make clean
    - make -j2 VERSION="$(cat VERSION)" LDFLAGS="$LDFLAGS -ljpeg"
  install-commands:
    - make DESTDIR="%{install-root}" VERSION="$(cat VERSION)" LDFLAGS="$LDFLAGS -ljpeg" unitdir= install
    - install -m 0644 /usr/share/legacy-printer-app/testpage.pdf "%{install-root}/usr/share/gutenprint-printer-app/testpage.pdf"
