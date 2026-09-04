# Ragnar State Source

Ragnar Link is designed as an add-in. It does not require Ragnar core to import ESP-NOW libraries or know about the Waveshare board.

By default, the service reads:

```text
/run/ragnar-link/state.json
```

Example:

```json
{
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

If Ragnar can already emit JSON through a command, set `state_command` in `/etc/ragnar-link/config.yaml` instead:

```yaml
state_file:
state_command:
  - /usr/local/bin/ragnar-status-json
```

The command must print a JSON object to stdout and exit quickly.

