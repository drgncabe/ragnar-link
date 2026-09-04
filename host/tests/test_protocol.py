import json
import unittest

from ragnar_link.protocol import hello_frame, normalize_state, parse_json_line, status_frame


class ProtocolTests(unittest.TestCase):
    def test_status_frame_is_compact_json_line(self):
        line = status_frame(
            7,
            {
                "ragnar": "ACTIVE",
                "camera_count": 3,
                "wifi_count": 47,
                "ble_count": 22,
                "gps": "FIX",
                "capture": "RUNNING",
                "extra": "ignored",
            },
        ).to_json_line()

        self.assertTrue(line.endswith(b"\n"))
        body = json.loads(line)
        self.assertEqual(
            body,
            {
                "ble_count": 22,
                "camera_count": 3,
                "capture": "running",
                "gps": "fix",
                "ragnar": "active",
                "seq": 7,
                "type": "status",
                "uptime_s": 0,
                "v": 1,
                "wifi_count": 47,
            },
        )

    def test_parse_rejects_wrong_version(self):
        with self.assertRaises(ValueError):
            parse_json_line(b'{"v":99,"type":"hello"}\n')

    def test_hello_frame_includes_channel(self):
        body = json.loads(hello_frame(1, "ragnar", 6).to_json_line())
        self.assertEqual(body["type"], "hello")
        self.assertEqual(body["channel"], 6)
        self.assertEqual(body["node"], "ragnar")

    def test_normalize_state_clamps_counts_and_message(self):
        state = normalize_state(
            {
                "camera_count": -10,
                "wifi_count": 70000,
                "ble_count": 1,
                "uptime_s": 2**40,
                "message": "x" * 100,
            }
        )
        self.assertEqual(state["camera_count"], 0)
        self.assertEqual(state["wifi_count"], 65535)
        self.assertEqual(state["uptime_s"], 4294967295)
        self.assertEqual(len(state["message"]), 80)


if __name__ == "__main__":
    unittest.main()
