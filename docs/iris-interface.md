# IRIS Project Interface Requirements

Prompt the IRIS project with this:

> Implement the IRIS/M5Stack receiver side of Ragnar Link v1. The Ragnar-side host repo is `https://github.com/drgncabe/ragnar-link.git` and the gateway firmware repo is `https://github.com/drgncabe/ragnar-link-gateway.git`; use `docs/espnow-protocol.md` as the source of truth. IRIS must receive ESP-NOW broadcast packets from the Ragnar Link Waveshare ESP32-S3 gateway, validate `RagnarStatusPacket` frames exactly, and update the stopwatch/remote UI with Ragnar status. The packet is 24 bytes, little-endian, magic `RL`, version `1`, type `0x01`, CRC-16/CCITT-FALSE over bytes 0-21, with counts for cameras, Wi-Fi, BLE, GPS state, capture state, and Ragnar state. IRIS must drop invalid packets, tolerate skipped sequence numbers, mark Ragnar stale after 15 seconds without a valid packet, and keep working when Ragnar is offline. Default ESP-NOW channel is 6, but the channel must be configurable because it must match the Ragnar gateway.

## IRIS Must Implement

- ESP-NOW receive callback for broadcast, unencrypted v1 packets.
- `RagnarStatusPacket` parser with exact 24-byte layout from `docs/espnow-protocol.md`.
- CRC-16/CCITT-FALSE validation.
- Stale timer: show disconnected/stale if no valid packet for 15 seconds.
- UI mapping:

| Field | UI behavior |
| --- | --- |
| `ragnar_state` | `unknown`, `idle`, `active`, `error` indicator |
| `camera_count` | camera count |
| `wifi_count` | Wi-Fi AP/client count |
| `ble_count` | BLE device count |
| `gps_state` | `unknown`, `no fix`, `fix` |
| `capture_state` | `idle`, `running`, `paused`, `error` |
| `sequence` | optional diagnostics only |

## IRIS Should Not Implement Yet

- Pairing UI
- Encryption
- Commands back to Ragnar
- Firmware updates

Those can be v2 features after the one-way status link is stable.
