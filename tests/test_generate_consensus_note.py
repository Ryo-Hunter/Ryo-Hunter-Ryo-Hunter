import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generate_consensus_note import build_note, infer_topic, parse_messages


class ConsensusParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample = (ROOT / "examples" / "discussion.sample.md").read_text(encoding="utf-8")

    def test_parse_messages(self) -> None:
        msgs = parse_messages(self.sample)
        self.assertGreaterEqual(len(msgs), 3)
        self.assertIn("A", {m.author for m in msgs})
        self.assertIn("B", {m.author for m in msgs})

    def test_build_note_has_required_sections(self) -> None:
        msgs = parse_messages(self.sample)
        note = build_note(topic=infer_topic(self.sample), source_name="sample.md", messages=msgs)
        for heading in [
            "## 已收斂共識",
            "## 保留分歧",
            "## 待驗證命題",
            "## 最小可執行實驗",
            "## 目前最大風險",
            "## 建議主控決策",
        ]:
            self.assertIn(heading, note)


if __name__ == "__main__":
    unittest.main()
