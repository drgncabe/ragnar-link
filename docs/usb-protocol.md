# Ragnar Host To ESP32 Gateway USB Protocol

The Ragnar host service talks to the ESP32-S3 gateway over USB CDC serial at 115200 baud.

Each frame is one UTF-8 JSON object followed by `\n`. Frames use protocol version `v: 1`.

## Host To Gateway

### `hello`

```json
{"v":1,"type":"hello","seq":1,"node":"ragnar","host_time_ms":1798992000000,"channel":6}
```

### `command`

Set ESP-NOW channel:

```json
{"v":1,"type":"command","seq":2,"command":"set_channel","channel":6}
```

### `status`

```json
{
  "v": 1,
  "type": "status",
  "seq": 3,
  "ragnar": "active",
  "camera_count": 3,
  "wifi_count": 47,
  "ble_count": 22,
  "gps": "fix",
  "capture": "running",
  "uptime_s": 1234,
  "message": "wardrive active"
}
```

Allowed values:

| Field | Values |
| --- | --- |
| `ragnar` | `unknown`, `idle`, `active`, `error` |
| `gps` | `unknown`, `no_fix`, `fix` |
| `capture` | `idle`, `running`, `paused`, `error` |

Counts are unsigned 16-bit integers. `uptime_s` is an unsigned 32-bit integer. `message` is optional and clipped by the host to 80 characters.

## Gateway To Host

### `hello`

```json
{"v":1,"type":"hello","seq":1,"status":"ready","message":"ragnar-espnow-gateway"}
```

### `ack`

```json
{"v":1,"type":"ack","seq":3,"status":"sent"}
```

Known statuses: `ready`, `sent`, `send_failed`, `bad_json`, `bad_version`, `line_too_long`, `channel_set`, `unknown_command`, `unknown_type`.

