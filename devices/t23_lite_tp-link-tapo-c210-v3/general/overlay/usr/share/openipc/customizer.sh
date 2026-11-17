#!/bin/sh
bauer#
# First-boot settings for the TP-Link Tapo C210 v3
# (Ingenic T23N, SmartSens SC3336, RTL8188FTV Wi-Fi, TMI8150 pan/tilt + IR-cut).
# Pins come from thingino's tplink_tapo_c210_t23n_sc3336_rtl8188ftv profile.
#
# Sensor: Ingenic's prober (sinfo) does not know the SC3336, so name it here
# for load_ingenic. Its driver and tuning file come from package/sc3336-t23.
fw_setenv sensor sc3336
#
# Memory split proven on this camera under thingino: Linux 44 MB, ISP 20 MB.
# If Majestic logs ISP/rmem allocation errors, try osmem 42M / rmem 22M@0x2A00000.
fw_setenv osmem 44M@0x0
fw_setenv rmem 20M@0x2C00000
#
# SD card: card-detect GPIO 57 (power GPIO 58 is raised in muxes.sh)
fw_setenv gpio_mmc 57
#
# Wi-Fi: RTL8188FTV on USB. Its power pin (GPIO 51) is raised in muxes.sh, so
# the generic profile (just "modprobe 8188fu") is enough.
fw_setenv wlandev rtl8188fu-generic
# Wi-Fi credentials are not kept in git: build-c210v3.sh writes them to
# wifi.env next to this script from a local file.
if [ -f /usr/share/openipc/wifi.env ]; then
	. /usr/share/openipc/wifi.env
	[ -n "$WLANSSID" ] && fw_setenv wlanssid "$WLANSSID"
	[ -n "$WLANPASS" ] && fw_setenv wlanpass "$WLANPASS"
fi
#
# Pan/tilt: /usr/bin/motor drives the TMI8150 through /dev/motor (S60ptz).
# ptz_control=motor shows the web UI pad; it calls "motor <ptz> <h> <v>".
fw_setenv ptz_control motor
fw_setenv ptz tmi8152
fw_setenv ptz_caps 'pan tilt'
#
# Majestic
cli -s .video0.codec h264
cli -s .video0.size 1920x1080
cli -s .video0.fps 25
# Microphone on, speaker off by default (Majestic ships with audio off).
# The speaker amp stays wired to GPIO 63, so it can be switched on in the web UI.
cli -s .audio.enabled true
cli -s .audio.codec aac
cli -s .audio.outputEnabled false
# No on-screen text (date/time, name) in the picture by default
cli -s .osd.enabled false
cli -s .audio.speakerPin 63
# Day/night is done by /usr/sbin/daynight (S96daynight): the IR-cut filter
# sits behind the TMI8150, not on a GPIO, so Majestic's irCutPin/lightMonitor
# cannot drive it. Majestic only does the black-and-white switch, via
# /night/on and /night/off from that daemon.
cli -s .nightMode.colorToGray true
cli -s .nightMode.lightMonitor false
#
# Local name (mDNS) off; anonymous telemetry off
cli -s .mdns.enabled false
cli -s .system.telemetry false

# osmem/rmem only take effect after a reboot
(sleep 3; reboot -f) &

exit 0
