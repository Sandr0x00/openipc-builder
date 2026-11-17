#!/bin/sh
#
# Runs on every boot from S30customizer, before kernel modules (S35) and
# networking (S40).
#
# 38 = PB6: TMI8150 H-bridge power enable (pan/tilt motors and IR-cut filter)
# 51:       RTL8188FTV Wi-Fi power
# 58:       SD card power, active-low
# 49:       850 nm IR LEDs, active-low: start off (high); daynight drives it
gpio set 38
gpio set 51
gpio clear 58
gpio set 49
