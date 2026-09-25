# Container service lifecycle

The current Rockcraft image runs `/usr/bin/python3 /scripts/supervise.py` as
its single Pebble service under `_daemon_` (numeric UID/GID 584792). Python
and D-Bus are already included in the image. The supervisor itself does not
depend on Rockcraft environment variables or its former startup scripts.
A future BuildStream image can install the same supervisor, with Python 3.8+
and a PID 1 reaper such as catatonit, alongside the real printer stack.

The supervisor starts D-Bus in the foreground, waits for a successful GetId
call, starts Avahi in the foreground, waits for its D-Bus API, then starts
`/usr/bin/gutenprint-printer-app ... server`. Each readiness wait is bounded
to 30 seconds and monitors previously started children. Avahi does not chroot,
change UID, or set resource limits; the image supplies its nonroot identity
and D-Bus policies. Each child inherits the container log streams.

Set `PORT` to an available port from 1024 through 65535; the default is 8632.
PAPPL serves HTTP and HTTPS on the same port. Keep the application's existing
state volume mounted at `/var/lib/gutenprint-printer-app` across restarts.
The supervisor never initializes or truncates saved application state. The
separate persistence work in #5 also covers spool and TLS storage.

Any required child exit, including status zero, makes the supervisor exit
with status 1 after cleaning up the remaining processes. Pebble's
`on-failure: shutdown` then stops the container. SIGTERM or SIGINT instead
requests an orderly stop: application first, then Avahi, then D-Bus. Each
process group receives SIGTERM and has up to five seconds before SIGKILL.
Set the outer container/unit stop timeout above 20 seconds to allow cleanup.
Do not share `/run/dbus` or `/run/avahi-daemon` with the host or other instances.

## Validation and remaining acceptance work

Run `python3 -m unittest discover -s tests -v` for lifecycle regression tests.
They launch real subprocesses to exercise exit detection, readiness timeout,
signal forwarding and forced termination. These tests do **not** prove IPP
readiness or successful printing.

Issue #3 remains open until the source-pinned BuildStream graph in #2 is
available and its actual OCI image passes all of the following:

1. Start with the image's default numeric UID/GID, a persistent state volume,
   and an explicitly selected free `PORT`. Verify both HTTP and HTTPS/IPP
   readiness (self-signed TLS is expected on first start).
2. Add a real Gutenprint queue using a `cups:socket://` device pointing at a
   TCP sink. Submit a supported document over IPP, wait for job completion,
   and inspect captured printer-language output. Echo programs are not a
   substitute for the Gutenprint filter pipeline.
3. Restart with the same volume and verify the queue and saved configuration
   remain, then submit another job.
4. Terminate each required child in separate runs and assert container
   failure. Stop the outer unit normally and verify no app, filter, backend,
   Avahi or D-Bus processes remain.

Full image, HTTP/HTTPS, and print-to-socket checks have not been run in the
contributor environment, which has no container engine or printing stack.
Physical paper output requires hardware validation.
