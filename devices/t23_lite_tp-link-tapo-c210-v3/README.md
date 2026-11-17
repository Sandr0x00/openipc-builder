# TP-Link Tapo C210 v3 on OpenIPC

**Hardware:** Ingenic T23N · SmartSens SC3336 (3 MP, MIPI) · RTL8188FTV USB Wi-Fi (`0bda:f179`) ·
TMI8150 pan/tilt + IR-cut over SPI · 8 MB NOR XM25QH64C (JEDEC `20 40 17`, in both OpenIPC's
bootloader and kernel flash tables) · 64 MB RAM

Pins and calibration come from the camera's thingino build
(`thingino-c210-v3`, profile `tplink_tapo_c210_t23n_sc3336_rtl8188ftv`), where all of
them were verified on hardware. **Nothing in this profile has run on the camera yet.**

## What OpenIPC lacks for this camera, and where it comes from

| Gap | Fix in this repo |
|---|---|
| SC3336 is not in `ingenic-osdrv-t23` / openingenic | `package/sc3336-t23`: thingino's T23 driver source (includes adapted to openingenic's ISP headers) and its tuning file. The tuning file has the same format (`2.20`, 176288 bytes) as OpenIPC's own T23 files. OpenIPC's libimp is SDK 1.1.0, thingino's 1.3.0. |
| Sensor prober (`sinfo`) doesn't know the chip | `fw_setenv sensor sc3336` in the customizer; module options in `/etc/modprobe.d/sensor_sc3336_t23.conf` |
| Pan/tilt + IR-cut sit behind a TMI8150 on SPI0, which the T23 kernel config leaves off | `package/tmi8152-motor`: the driver thingino uses (same commit plus both C210 patches), enables `CONFIG_JZ_SPI0` (PB27-30), adds `tmi-ptz` |
| Majestic's day/night only drives GPIO IR-cuts | `/usr/sbin/daynight` (ported from thingino): IR-cut via `/dev/tmi8152_ir_cut`, IR LEDs on GPIO 49, black-and-white via Majestic `/night/on` and `/night/off` |
| No Wi-Fi profile for this board | `muxes.sh` raises the Wi-Fi power pin (GPIO 51) each boot, then `wlandev rtl8188fu-generic` |

## GPIO map

| GPIO | Use |
|---|---|
| 38 | TMI8150 H-bridge power (high = on), needed for motors and IR-cut |
| 49 | 850 nm IR LEDs, active-low |
| 50 | white LED, active-low (unused) |
| 51 | Wi-Fi power |
| 57 / 58 | SD card-detect / SD power (active-low) |
| 63 | speaker amplifier |
| 40 | reset button |
| 42 / 43 | status LED green / red |

## Boot sequence (overlay)

- `S30customizer` → `customizer.sh` (first boot only): sensor, osmem 44M / rmem 20M, Wi-Fi,
  PTZ backend, Majestic settings (mic on), then a reboot so the memory split applies.
  Wi-Fi credentials come from `wifi.env`, which the build script writes into the
  firmware tree only, never into git.
- `S30customizer` → `muxes.sh` (every boot): GPIO 38, 51, 58, 49.
- `S60ptz`: loads `extra/tmi8152_spi_dev.ko` + `extra/motor.ko` (pan 7850 steps, tilt 1850,
  speed 430), homes in the background and returns to the centre.
- `S95majestic`, then `S96daynight`.

## Resolution

Keep the main stream at **1920x1080, 25 fps** (set on first boot). The sensor always runs
its 2304x1296 mode and the ISP scales it down. Asking Majestic for the full 2304x1296 gives
no frames at all (`IMP_Encoder_PollingStream timeout`, 213-byte snapshots), tested
2026-11-17 at 30 and at 25 fps, and with `osmem 40M`/`rmem 24M` as well as 44M/20M, so it
is not a memory problem. Most likely a limit of OpenIPC's older Ingenic SDK (1.1.0).

## PTZ in the web UI

`ptz_control=motor`, `ptz=tmi8152`: the Live page's pad calls `/usr/bin/motor tmi8152 <h> <v>`
(h/v ≈ ±5 every 250 ms while held; centre button = h 0 v 0 = go to centre).
If an axis moves the wrong way: `fw_setenv ptz_flip x` (or `y`, `xy`).
From a shell: `tmi-ptz -j` (status), `-m X Y`, `-a X Y`, `-c`, `-r` (home), `-S`.

## Day/night

`daynight` is the thingino state machine: into IR when the ISP digital gain hits its
ceiling, back to colour on a learned analog-gain threshold, with debounce and a
10-minute minimum dwell. Override: `echo auto|day|night > /etc/daynight.force`.
Tuning: shell variables in `/etc/daynight.conf` (`DARK_DGAIN`, `ANALOG_INIT`, `MIN_DWELL`, …).

It logs `started src=proc` or `src=metrics` (`logread | grep daynight`). It waits for
Majestic and the ISP first, then reads `/proc/jz/isp/isp-m0` (`SENSOR analog gain`,
`ISP digital gain`) and falls back to Majestic's `isp_again`/`isp_dgain`. On this T23 both
use the same raw units (measured in daylight: analog 55, max 211; ISP digital 0, max 128),
so thingino's thresholds carry over.

## Build and flash

Build scripts (outside this repo):

```sh
/data/research/tapo/c210v3-build.sh          # fresh OpenIPC clone in /data/research/tapo/build/openipc-t23 + build
/data/research/tapo/c210v3-build.sh quick    # re-copy profile/packages, re-run make
/data/research/tapo/c210v3-mkfull.sh   # → /data/research/tapo/build/openipc-c210v3-full-8mb.bin
```

From thingino, over SSH (the full image includes the OpenIPC bootloader):

```sh
# 1. back up the whole chip first (thingino's mtd6 "all" is the full 8 MB)
ssh root@<cam> 'cat /dev/mtd6' > c210v3-thingino-full.bin   # expect 8388608 bytes
# 2. flash
cat openipc-c210v3-full-8mb.bin | ssh root@<cam> 'cat > /tmp/full.bin; md5sum /tmp/full.bin'
ssh root@<cam> 'sysupgrade -x /tmp/full.bin'      # never -r
```

Alternative without Linux: thingino's bootloader flashes `autoupdate-full.bin` from the SD
card at power-on (`autoupdate` in its env, writes the whole chip, leaves `autoupdate-full.done`).
Only usable while thingino's bootloader is still on the chip.

The camera then boots twice (the customizer reboots once) and joins the Wi-Fi from
`wifi.env`. If it doesn't show up, recover with UART or the CH341A and the backup.

## First-boot checklist

1. Wi-Fi up, SSH and web UI reachable.
2. `lsmod`: `tx_isp_t23`, `sensor_sc3336_t23`, `8188fu`, `tmi8152_spi_dev`, `motor`.
3. `logread | grep -i -E "sc3336|isp"`: chip found at 0x30, then a picture in the web UI.
4. Pan/tilt pad moves the head the way the arrows point (otherwise `ptz_flip`).
5. `echo night > /etc/daynight.force`: filter clicks, IR LEDs on, picture goes grey.
   Then `echo auto > /etc/daynight.force` and check `logread | grep daynight` for `src=`.
6. Microphone: audio in the RTSP stream.
