# Persistent state and printer ownership

The current Rockcraft image runs as UID/GID 584792. Its startup script keeps
state, PPDs, spool files, TLS material, temporary files, SNMP configuration and
USB quirks under `/var/lib/gutenprint-printer-app`. It seeds missing backend
configuration only; restarts and upgrades preserve edited or empty files.
Logs go to the container log. Back up the entire volume with the app stopped.
Never mount one state directory into two running applications.

## Rootless LAN instance

Build the image from this revision using the README's Rockcraft procedure and
load it into Podman. Substitute that local image reference below. These are
current Rockcraft UID settings; the numeric user for the future BuildStream
runtime tracked in #3 may differ.

```sh
mkdir -p "$HOME/.local/share/gutenprint-printer-app"
podman run -d --name gutenprint-printer-app \
  --userns=keep-id:uid=584792,gid=584792 --user 584792:584792 \
  --network host \
  -e PORT=18080 \
  -e SYSTEM_NAME='Gutenprint studio' \
  -v "$HOME/.local/share/gutenprint-printer-app:/var/lib/gutenprint-printer-app:Z" \
  localhost/gutenprint-printer-app:test
```

This maps the invoking user's ownership to the container service user. Check
volume writability under that mapping before starting the service. Do not use
world-writable permissions to work around an incorrect user mapping.

`PORT` defaults to 8000 and must be 1024–65535. Set a distinct port for every
application using the host network (for example, 18080 and 18081). An explicit
port avoids automatic port selection. Host networking makes the web/IPP service
reachable on the host's LAN interfaces; use host firewall rules to restrict it
to the intended network. Do not expose the admin interface to the Internet.

`SYSTEM_NAME` sets the initial PAPPL system/DNS-SD name, defaulting to
`Gutenprint Printer Application (PORT)`. A saved system name takes precedence;
change an existing name through the web interface. Give each configured printer
a unique DNS-SD name as well, such as `Gutenprint studio Epson` and
`Ghostscript office laser`. System names alone do not isolate printer queues.

Discovery can show the same physical printer in multiple apps. Assign one app
as the owner of each physical device and create its queue only in that app.
Do not auto-add all discovered devices in overlapping driver families. Remove
old queues/advertisements before transferring ownership. Unique ports and names
do not prevent two backends from writing to the same device.

Edit `cups/snmp.conf` in the persistent directory to scope SNMP discovery to
intended printer addresses. This does not scope DNS-SD browsing or enforce a
network access control policy. Do not mount the host D-Bus socket or share Avahi
runtime directories: the image uses its own D-Bus and Avahi processes.

## Rootless USB instance

Keep USB absent for LAN-only instances. For USB, add only the assigned device
node, for example `--device /dev/bus/usb/001/004 --group-add keep-groups`, to the
command above. Use a runtime supporting supplementary group preservation
(such as crun). The host user must already have read/write access to that node
through an appropriate host udev rule or device group. Container permissions
cannot grant access the host user lacks. SELinux device policy may also need
host administrator configuration.

Do not pass all of `/dev/bus/usb`, use `--privileged`, or give multiple printer
apps the same node. Stop conflicting host CUPS queues or other device owners
before assigning the printer. An IPP-over-USB printer should normally be owned
by `ipp-usb`, with clients using its IPP service instead of claiming USB again.
USB bus/device numbers can change on reconnect: resolve the assigned printer's
serial to its current node and recreate the container. This procedure does not
implement automatic hotplug assignment or cross-application ownership locks.

## Validation and evidence

Local initializer regression checks:

```sh
python3 -m unittest discover -s tests -v
shellcheck scripts/prepare-state.sh scripts/start-server.sh
```

These checks do not prove OCI printing or LAN advertisements. Before declaring
issue #5 fully validated, run this acceptance procedure against the real image:

1. Start two instances with separate persistent directories, ports 18080/18081,
   and distinct system names. Do not attach USB. Create a different synthetic
   printer in each web interface with a real Gutenprint driver and a
   `socket://` destination pointing at a separate TCP capture sink.
2. Submit a supported document through IPP to each queue. Wait for completed
   job state and verify each sink received nonempty driver-generated output
   appropriate to the chosen driver. A mock application or echoed input is not
   shipping evidence. Record driver, device URI, job IDs and captured artifacts.
3. From another LAN machine, browse `_ipp._tcp` and `_ipps._tcp` with
   `avahi-browse -rt`. Confirm distinct printer service names, matching ports
   and `rp` paths, and that each queue appears once. Check the host for any
   other service advertising the same physical device.
4. Change a printer's media/default settings and system name through the UI;
   edit `cups/snmp.conf` and a USB quirk file. Stop and remove the containers,
   then recreate them with the same volumes. Confirm saved printers, names,
   settings and edits remain, and repeat the IPP print-to-sink check.
5. Upgrade the image with the same volumes and repeat step 4. Record image
   digest, commit, architecture, runtime version and results for both instances.

OCI print-to-sink and LAN coexistence are **unverified** by the initializer
unit tests. Real USB access, physical LAN discovery, and paper output remain
**unverified until hardware is available**. Follow the
[Ghostscript physical validation procedure](https://github.com/projectbluefin/ghostscript-printer-app/blob/main/docs/oci-physical-validation.md)
with this app's paths, UID and assigned device node; record printer model,
serial, driver, options, restart result, and observed paper output separately.
