import json
import unittest

from app.audit import safe_log_value


class AuditTests(unittest.TestCase):

    def test_newline_is_escaped(self):
        value = "alice\nADMIN login success"

        result = safe_log_value(value)

        self.assertNotIn("\n", result)
        self.assertIn("\\n", result)

    def test_carriage_return_is_escaped(self):
        value = "alice\radmin"

        result = safe_log_value(value)

        self.assertNotIn("\r", result)
        self.assertIn("\\r", result)

    def test_length_is_limited(self):
        value = "A" * 500

        result = safe_log_value(value, 128)

        self.assertEqual(len(result), 128)

    def test_json_keeps_single_record(self):
        event = {
            "username": safe_log_value(
                "alice\nfake event"
            )
        }

        serialized = json.dumps(event)

        self.assertEqual(
            len(serialized.splitlines()),
            1
        )


if __name__ == "__main__":
    unittest.main()