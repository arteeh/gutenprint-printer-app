kind: autotools
description: Gutenprint library, XML resources, CUPS filters and dynamic PPD generator.

sources:
  - kind: git_repo
    url: salsa:printing-team/gutenprint.git
    track: debian/5.3.*
    ref: 5302dac58533a298f6890b2767492128910ea77b

build-depends:
  - freedesktop-sdk.bst:public-stacks/buildsystem-autotools.bst
  - freedesktop-sdk.bst:components/flex.bst
  - freedesktop-sdk.bst:components/bison.bst
  - freedesktop-sdk.bst:components/gettext.bst

depends:
  - freedesktop-sdk.bst:components/cups.bst
  - freedesktop-sdk.bst:components/libusb.bst
  - freedesktop-sdk.bst:bootstrap/readline.bst

variables:
  conf-local: >-
    --enable-shared
    --disable-static
    --disable-rpath
    --with-modules=static
    --without-gimp2
    --disable-libgutenprintui2
    --with-cups
    --enable-cups-level3-ppds
    --enable-translated-cups-ppds
    --enable-simplified-cups-ppds
    --enable-cups-1_2-enhancements
    --disable-cups-ppds
    --enable-escputil
    --disable-samples
    --disable-test
    --disable-testpattern
    --enable-nls
    --without-doc

config:
  install-commands:
    (>):
      - mkdir -p "%{install-root}/usr/share/ppd"
      - mv "%{install-root}/usr/lib/cups/driver/gutenprint.5.3" "%{install-root}/usr/share/ppd/gutenprint.5.3"
