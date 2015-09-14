# enocean-ui

EnOcean (ESP3 protocol) - web bridge, running on Raspberry Pi.

How to use:

 * Disable serial console in rpi-setup (port is used by EnOcean module).
 * Install `python-twisted`.
 * Run `python -m enocean` in this directory.
 * Use http://raspberrypi:8080/radio/list to see last packets and retransmit them.

