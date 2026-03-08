# ldrit-memory-loop v0.1.0

## Overview
First public release of **ldrit-memory-loop**, an LDRIT-inspired tool that converts long multi-agent discussion logs into a structured, review-ready consensus note.

## What it does
- Parses discussion markdown files
- Produces a fixed review structure:
  - 已收斂共識
  - 保留分歧
  - 待驗證命題
  - 最小可執行實驗
  - 目前最大風險
  - 建議主控決策

## Included in v0.1.0
- CLI parser: `src/generate_consensus_note.py`
- Consensus template: `templates/consensus-note.template.md`
- Input sample: `examples/discussion.sample.md`
- Basic tests: `tests/test_generate_consensus_note.py`
- Initial spec and roadmap docs

## Notes
- This is a practical v0.x baseline focused on deterministic structure and usable decision handoff.
- Further semantic accuracy improvements are planned for future versions.

## License
MIT
