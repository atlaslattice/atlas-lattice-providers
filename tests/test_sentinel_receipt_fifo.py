"""Regression: receipt custody must not block on attacker-supplied FIFO sinks.

No host rights or external actions are exercised. POSIX-only offline fixture.
"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ReceiptSinkSafety(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix" and hasattr(os, "mkfifo"), "requires POSIX FIFO")
    def test_unread_fifo_is_rejected_without_hanging_or_writing(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "unread-receipt.fifo"
            os.mkfifo(target, 0o600)
            probe = """
import sys
from core.sentinel_agent import SentinelReview, append_receipt
candidate = SentinelReview(
    "REVIEWABLE_LOCAL_ONLY", (), "0" * 64, 1, "WORK", {}, (), False
)
try:
    append_receipt(sys.argv[1], candidate)
except (OSError, ValueError):
    pass
else:
    raise SystemExit("UNSAFE_FIFO_ACCEPTED")
"""
            # The unfixed os.open(O_WRONLY) can wait forever for a FIFO reader.
            # A child/timeout makes that failure bounded and reproducible.
            proc = subprocess.run(
                [sys.executable, "-c", probe, str(target)],
                cwd=str(Path(__file__).resolve().parents[1]),
                capture_output=True, text=True, timeout=3,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(target.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
