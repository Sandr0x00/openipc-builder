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
# Pan/tilt: 24BYJ48 steppers driven directly by GPIO (stock: pan A..D = 47 46 45 44,
# tilt A..D = 80 79 76 77). gpio-motors reads: horizontal x4, then vertical x4.
fw_setenv ptz_gpio '44 45 46 47 80 79 76 77'
#
# Wi-Fi driver profile. The image's /etc/wireless/usb only knows atbm6012b-ssc333-tapo-c110
# (same ATBM6012B module and GPIO 16 reset as the C210); an unknown name leaves the camera
# with no wlan0.
fw_setenv wlandev atbm6012b-ssc333-tapo-c110
#fw_setenv wlanssid Router
#fw_setenv wlanpass 12345678

exit 0
