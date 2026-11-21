"""Redaction and truncation tests. Fake tokens are built at runtime so this file never trips the content scanner."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sdlc_guard import redact  # noqa: E402

AWS = "AKIA" + "IOSFODNN7EXAMPLE"
GH = "ghp_" + "a1B2c3D4" * 5
GH_PAT = "github_pat_" + "A1b2C3d4E5" * 6
ANTHROPIC = "sk-ant-" + "api03-" + "Zz9" * 12
OPENAI = "sk-" + "Proj" + "1234567890abcdefghij"
SLACK = "xox" + "b-1234567890-abcdefghijkl"
GOOGLE = "AIza" + "Sy" + "A" * 33
JWT = "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJ" + "zdWIiOiIxMjM0NTY3ODkwIn0" + "." + "abcDEF123456_-xyz"
PEM = "-----BEGIN " + "RSA PRIVATE KEY-----"


class TestFindSecrets(unittest.TestCase):
    def test_high_confidence_tokens(self) -> None:
        for name, token in {
            "aws_access_key": AWS,
            "github_token": GH,
            "github_pat": GH_PAT,
            "anthropic_key": ANTHROPIC,
            "openai_key": OPENAI,
            "slack_token": SLACK,
            "google_api_key": GOOGLE,
            "jwt": JWT,
            "private_key": PEM,
        }.items():
            with self.subTest(name=name):
                self.assertIn(name, redact.find_secrets(f"value is {token} here"))

    def test_plain_text_is_clean(self) -> None:
        text = "git status && echo token budget 5 ghp_short sk-short password policy docs"
        self.assertEqual(redact.find_secrets(text), [])

    def test_key_value_pairs_are_not_content_scan_hits(self) -> None:
        self.assertEqual(redact.find_secrets("password = 'hunter2hunter2'"), [])


class TestRedact(unittest.TestCase):
    def test_tokens_replaced(self) -> None:
        out = redact.redact(f"curl -H 'x: {GH}' --aws {AWS} {JWT}")
        for secret in (GH, AWS, JWT):
            self.assertNotIn(secret, out)
        self.assertIn("[REDACTED:github_token]", out)

    def test_key_value_values_replaced_keys_kept(self) -> None:
        out = redact.redact("db password=hunter2hunter2 and API_KEY: 'abc123456789' ok")
        self.assertNotIn("hunter2hunter2", out)
        self.assertNotIn("abc123456789", out)
        self.assertIn("password=", out)

    def test_bearer_and_url_credentials(self) -> None:
        out = redact.redact("Authorization: Bearer abcdef123456 and postgres://user:s3cr3tpass@db.example.invalid:5432/app")
        self.assertNotIn("abcdef123456", out)
        self.assertNotIn("s3cr3tpass", out)
        self.assertIn("postgres://user:", out)
        self.assertIn("@db.example.invalid", out)

    def test_private_key_block_removed(self) -> None:
        body = "MIIEowIBAAKCAQEA" + "x" * 40
        out = redact.redact(f"{PEM}\n{body}\n-----END RSA PRIVATE KEY-----")
        self.assertNotIn(body, out)

    def test_env_secret_values_replaced(self) -> None:
        env = {"MY_SERVICE_TOKEN": "supersecretvalue99", "PATH": "/usr/bin", "SHORT_KEY": "abc"}
        out = redact.redact("run with supersecretvalue99 in /usr/bin abc", env)
        self.assertNotIn("supersecretvalue99", out)
        self.assertIn("/usr/bin", out)
        self.assertIn("abc", out)  # too short to treat as a secret value

    def test_redact_is_idempotent_and_handles_empty(self) -> None:
        once = redact.redact(f"x {GH}")
        self.assertEqual(redact.redact(once), once)
        self.assertEqual(redact.redact(""), "")


class TestTruncate(unittest.TestCase):
    def test_no_truncation(self) -> None:
        self.assertEqual(redact.truncate("hello", 10), ("hello", False, 5))

    def test_truncation_reports_original_bytes(self) -> None:
        text, truncated, size = redact.truncate("x" * 100, 10)
        self.assertTrue(truncated)
        self.assertEqual(size, 100)
        self.assertTrue(text.startswith("x" * 10))
        self.assertIn("truncated", text)

    def test_multibyte_not_split(self) -> None:
        text, truncated, _ = redact.truncate("ทดสอบ" * 50, 10)
        self.assertTrue(truncated)
        text.encode("utf-8")  # must be valid UTF-8


if __name__ == "__main__":
    unittest.main()
