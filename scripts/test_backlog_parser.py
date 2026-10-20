import tempfile
import unittest
from pathlib import Path

from sync_github_issues import BACKLOG, parse_backlog


class BacklogParserTests(unittest.TestCase):
    def test_all_candidate_rows_must_be_valid(self):
        source = BACKLOG.read_text()
        self.assertEqual(len(parse_backlog(BACKLOG)), 96)
        row = next(line for line in source.splitlines() if line.startswith("| IC-096"))
        malformed = [row.replace("P1", "P3", 1), row.replace("feature", "unknown", 1),
                     row.replace("| P1", "P1", 1), row.rstrip("|"), row.lstrip("|")]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backlog.md"
            for candidate in malformed:
                with self.subTest(row=candidate):
                    path.write_text(source.replace(row, candidate))
                    with self.assertRaises(ValueError):
                        parse_backlog(path)


if __name__ == "__main__":
    unittest.main()
