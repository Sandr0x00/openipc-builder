#!/bin/sh
#
# Perform basic settings on the TP-Link Tapo C210 (SSC333, ATBM6012B Wi-Fi)
#
# Majestic settings (pins from the stock firmware's oem.config)
cli -s .nightMode.irCutPin1 78
cli -s .nightMode.backlightPin 14
cli -s .nightMode.colorToGray true
cli -s .audio.speakerPin 61
cli -s .video0.codec h264
#
# Local name (mDNS, answers to openipc.local): off
cli -s .mdns.enabled false
#
# Anonymous telemetry (Majestic's default is on): off
cli -s .system.telemetry false
#
# Pan/tilt: 24BYJ48 steppers driven directly by GPIO. gpio-motors reads horizontal x4, then
# vertical x4. Order chosen so the web UI arrows move the head the way they point (checked on
# hardware): pan pins 47 46 45 44, tilt pins 77 76 79 80.
# ptz_control=gpio makes the web UI show the pan/tilt pad on the Live page
fw_setenv ptz_control gpio
fw_setenv ptz_gpio '47 46 45 44 77 76 79 80'
#
# Wi-Fi driver profile. The image's /etc/wireless/usb only knows atbm6012b-ssc333-tapo-c110
# (same ATBM6012B module and GPIO 16 reset as the C210); an unknown name leaves the camera
# with no wlan0.
fw_setenv wlandev atbm6012b-ssc333-tapo-c110
#fw_setenv wlanssid Router
#fw_setenv wlanpass 12345678

exit 0
