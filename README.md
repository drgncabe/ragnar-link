# Ragnar Link

Ragnar Link is the Ragnar-side add-in for a USB-connected Waveshare ESP32-S3-LCD-1.47 gateway. The Raspberry Pi runs a small host service, talks JSON-over-USB to the ESP32-S3, and the ESP32-S3 owns all ESP-NOW traffic to IRIS/M5Stack stopwatch devices.

The repo intentionally keeps the bridge outside Ragnar core code:

- `host/` contains the Python daemon, serial protocol code, and tests.
- `installer/` contains the Ragnar installer script.
- `systemd/` contains the Linux service unit.
- `firmware/ragnar_espnow_gateway/` contains the ESP32-S3 PlatformIO firmware.
- `docs/` contains the USB protocol, ESP-NOW protocol, hardware notes, and the IRIS implementation contract.

## First Install On Ragnar

```sh
git clone https://github.com/drgncabe/ragnar-link.git
cd ragnar-link
sudo installer/install-ragnar-link.sh
```

Then plug in the Waveshare gateway and check:

```sh
sudo systemctl status ragnar-link
journalctl -u ragnar-link -f
```

## Development

Host tests:

```sh
cd host
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests
```

Firmware build:

```sh
cd firmware/ragnar_espnow_gateway
pio run
```

Firmware upload:

```sh
pio run -t upload
```

## Current Integration Shape

The host daemon can publish state from a JSON file or a command without requiring Ragnar code changes. That keeps the first integration low-risk:

- Ragnar, or a thin Ragnar-side adapter, writes `/run/ragnar-link/state.json`.
- `ragnar-linkd` watches that file and sends state changes to the USB gateway.
- The gateway re-broadcasts compact ESP-NOW frames to paired IRIS devices.

See [docs/iris-interface.md](docs/iris-interface.md) for exactly what the separate IRIS project must implement.
