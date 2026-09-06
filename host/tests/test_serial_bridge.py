import unittest
from unittest import mock

from ragnar_link.serial_bridge import write_all


class WriteAllTests(unittest.TestCase):
    def test_write_all_retries_after_blocking_write(self):
        writes = [BlockingIOError(), 2, 3]

        def fake_write(_fd, data):
            result = writes.pop(0)
            if isinstance(result, Exception):
                raise result
            return result

        with (
            mock.patch("ragnar_link.serial_bridge.os.write", side_effect=fake_write) as write,
            mock.patch("ragnar_link.serial_bridge.select.select", return_value=([], [42], [])),
        ):
            write_all(42, b"hello", 1.0)

        self.assertEqual(write.call_count, 3)


if __name__ == "__main__":
    unittest.main()
