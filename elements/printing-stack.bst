kind: junction
# Canonical CUPS patches and the matching FSDK line are reviewed together here.
sources:
  - kind: git_repo
    url: github:projectbluefin/ghostscript-printer-app.git
    track: main
    ref: f36174f27f5bb08421712bd77680cbddfc71862e
config:
  overrides:
    plugins/buildstream-plugins-community.bst: plugins/buildstream-plugins-community.bst
  options:
    arch: "%{arch}"
