Run the device-selection regression against a freshly built application with
its Gutenprint PPD generator installed and `PAPPL_MAX_VENDOR >= 256`:

```sh
python3 tests/device-selection.py /path/to/gutenprint-printer-app
```

For an OCI image built from the current checkout, pass the container command:

```sh
python3 tests/device-selection.py -- podman run --rm \
  --entrypoint /usr/bin/gutenprint-printer-app IMAGE
```

The test calls the real `drivers -o device-id=...` auto-add path. Unknown PCL
IDs must return no driver, while Epson Stylus Photo R300 and Canon PIXMA iP4000
must select their registered Gutenprint model drivers, including when their IDs
advertise PCL. It requires no hardware or generic PCL payload. It fails on an
empty inventory, missing models, explicitly simplified drivers, or application errors.
PAPPL-retrofit strips the Gutenprint suffix from display names; therefore this
test alone cannot prove expert PPD provenance. Run it on the expert-only build
and retain the expert-option validation from #9.

This verifies driver selection only. It does not replace the full OCI
print-to-socket-sink verification of filter output required by the issue, or
physical paper testing. The expert-option and OCI integration work is tracked
in #9 and #4 respectively.
