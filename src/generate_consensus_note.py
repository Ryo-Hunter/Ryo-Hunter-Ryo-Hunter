#!/usr/bin/env python3
"""ldrit-memory-loop v0.7 parser.

Improvements over v0.6:
- Neutral review-tone rewriting for disagreement items.
- AgentLetters integration mode and input validation.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class Message:
    author: str
    timestamp: str
    body: str


@dataclass
class SentenceRecord:
    text: str
    author: str
    order: int


BLOCK_RE = re.compile(
    r"---\s*\nFrom:\s*(?P<author>.+?)\s*\n時間：(?P<ts>.+?)\s*\n---\s*\n(?P<body>.*?)(?=\n---\s*\nFrom:|\Z)",
    re.DOTALL,
)
SENTENCE_SPLIT_RE = re.compile(r"[\n。！？!?；;]+")
AGENTLETTERS_DISCUSSION_RE = re.compile(r"^\d{8}__ALL__.+__discussion\.md$")

NOISE_PREFIXES = (
    "from:",
    "時間：",
    "本段摘要",
    "摘要結束",
    "---",
    "##",
    "#",
)

AUTHOR_WEIGHT = {
    "yan": 5,
    "諺": 5,
    "hongye": 4,
    "紅葉": 4,
    "四葉": 4,
    "lin": 3,
    "凜": 3,
}

ACTION_HINTS = [
    "下一步",
    "建議",
    "提議",
    "請",
    "批准",
    "同意",
    "先",
    "建立",
    "聚焦",
    "執行",
    "整理",
    "抽出",
    "產出",
]

DECISION_BAD_HINTS = [
    "很高興",
    "感謝",
    "防禦塔",
    "我同意收尾",
    "這輪到此結束",
    "我的立場",
]


def parse_messages(text: str) -> list[Message]:
    messages: list[Message] = []
    for m in BLOCK_RE.finditer(text):
        body = m.group("body").strip()
        if not body:
            continue
        messages.append(
            Message(
                author=m.group("author").strip(),
                timestamp=m.group("ts").strip(),
                body=body,
            )
        )
    return messages


def validate_agentletters_input(in_path: Path, text: str, messages: list[Message]) -> None:
    """Validate minimum AgentLetters constraints for discussion summarization."""
    name = in_path.name
    if not AGENTLETTERS_DISCUSSION_RE.match(name):
        raise ValueError(
            "agentletters 模式要求輸入檔名符合：YYYYMMDD__ALL__主題名稱__discussion.md"
        )
    if "From:" not in text or "時間：" not in text:
        raise ValueError("agentletters 模式要求輸入含有 From 與時間欄位")
    if len({m.author for m in messages}) < 2:
        raise ValueError("agentletters 模式要求至少 2 位參與者發言")
    if "我目前最擔心的風險" not in text:
        raise ValueError("agentletters 模式要求討論內容至少包含一段風險揭露")


def unique_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in items:
        item = raw.strip()
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def clean_sentence(s: str) -> str:
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"\s+", " ", s.strip())
    s = re.sub(r"^\d+[\.)、]\s*", "", s)
    s = re.sub(r"^[-:：]+", "", s)
    return s.strip()


def is_noise_sentence(s: str) -> bool:
    t = s.strip()
    if len(t) < 10:
        return True
    low = t.lower()
    if any(low.startswith(p) for p in NOISE_PREFIXES):
        return True
    if t.endswith("："):
        return True
    if "我目前最擔心的風險" in t:
        return True
    if t in {"本次討論的共識", "本次討論未解決的問題", "本次分歧點的最終記錄"}:
        return True
    return False


def author_weight(author: str) -> int:
    a = author.strip()
    return AUTHOR_WEIGHT.get(a, AUTHOR_WEIGHT.get(a.lower(), 1))


def extract_sentence_records(messages: list[Message]) -> list[SentenceRecord]:
    records: list[SentenceRecord] = []
    order = 0
    for msg in messages:
        for p in SENTENCE_SPLIT_RE.split(msg.body):
            c = clean_sentence(p)
            if c and not is_noise_sentence(c):
                records.append(SentenceRecord(text=c, author=msg.author, order=order))
                order += 1
    deduped: list[SentenceRecord] = []
    seen: set[str] = set()
    for r in records:
        if r.text in seen:
            continue
        seen.add(r.text)
        deduped.append(r)
    return deduped


def select_by_keywords(records: list[SentenceRecord], keywords: list[str], limit: int = 5) -> list[str]:
    matched = [r for r in records if any(k in r.text for k in keywords)]
    matched.sort(key=lambda r: (-author_weight(r.author), r.order))
    out = [r.text for r in matched[:limit]]
    return unique_keep_order(out)


def extract_numbered_items(block_text: str, limit: int = 6) -> list[str]:
    items: list[str] = []
    for line in block_text.splitlines():
        m = re.match(r"\s*(\d+)[\.)、]\s*(.+)", line)
        if not m:
            continue
        item = clean_sentence(m.group(2))
        if item and not is_noise_sentence(item):
            items.append(item)
        if len(items) >= limit:
            break
    return unique_keep_order(items)


def extract_anchor_list(text: str, anchor: str, limit: int = 6) -> list[str]:
    i = text.find(anchor)
    if i == -1:
        return []
    tail = text[i + len(anchor) :]
    end = re.search(r"\n\s*---\s*\n", tail)
    block = tail[: end.start()] if end else tail
    return extract_numbered_items(block, limit=limit)


def extract_risks(messages: list[Message], limit: int = 4) -> list[str]:
    risks: list[str] = []
    marker = "我目前最擔心的風險"
    for msg in reversed(messages):
        if marker not in msg.body:
            continue
        tail = msg.body.split(marker, 1)[1]
        lines = [clean_sentence(x) for x in tail.splitlines()]
        for line in lines:
            if not line or is_noise_sentence(line):
                continue
            risks.append(line)
            break
        if len(risks) >= limit:
            break
    return unique_keep_order(risks)


def score_decision_sentence(text: str) -> int:
    score = 0
    if any(k in text for k in ACTION_HINTS):
        score += 3
    if "策略性迎合" in text or "A/B/C" in text or "實驗" in text:
        score += 2
    if "主控" in text or "諺" in text:
        score += 1
    if any(b in text for b in DECISION_BAD_HINTS):
        score -= 3
    return score


def extract_decisions(records: list[SentenceRecord], full_text: str, limit: int = 4) -> list[str]:
    anchored = extract_anchor_list(full_text, "建議主控決策", limit=limit)
    if anchored:
        return anchored

    candidates: list[tuple[int, int, str]] = []
    for r in records:
        s = score_decision_sentence(r.text)
        if s <= 0:
            continue
        candidates.append((s + author_weight(r.author), r.order, r.text))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    selected = [c[2] for c in candidates[:limit]]
    concrete = [s for s in selected if any(k in s for k in ["下一步", "建議", "先", "執行", "建立", "聚焦"])]
    if concrete:
        return unique_keep_order(concrete)[:limit]
    return unique_keep_order(selected)[:limit]


def infer_topic(text: str, fallback: str = "未命名主題") -> str:
    m = re.search(r"^#\s*討論主題[:：]\s*(.+)$", text, re.MULTILINE)
    return m.group(1).strip() if m else fallback


def token_set(text: str) -> set[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text)
    return set(tokens)


def semantic_dedupe(items: list[str], overlap_threshold: float = 0.72) -> list[str]:
    kept: list[str] = []
    kept_tokens: list[set[str]] = []
    for item in items:
        t = token_set(item)
        if not t:
            continue
        duplicated = False
        for kt in kept_tokens:
            inter = len(t & kt)
            ratio = inter / max(1, min(len(t), len(kt)))
            if ratio >= overlap_threshold:
                duplicated = True
                break
        if not duplicated:
            kept.append(item)
            kept_tokens.append(t)
    return kept


def trim_text(text: str, max_len: int = 90) -> str:
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def normalize_disagreement_tone(text: str) -> str:
    t = text.strip()
    rules = [
        (r"^但我對(.+?)有異議$", r"對\1仍存在異議"),
        (r"^但我不同意(.+)$", r"對\1存在不同意見"),
        (r"^四葉、凜，我接你們兩位最新回覆，先把分歧收斂成可執行版本$", "分歧已進入可執行收斂階段"),
        (r"^凜最終接受切換模式作為落地方案，但保留「硬終止是理論極限」的立場$", "凜接受切換模式落地，但保留硬終止為理論極限"),
    ]
    for pat, rep in rules:
        if re.match(pat, t):
            return re.sub(pat, rep, t)
    return t


def post_process_section(items: list[str], max_items: int = 4, trim_len: int = 90, neutralize: bool = False) -> list[str]:
    items = unique_keep_order(items)
    items = semantic_dedupe(items)
    if neutralize:
        items = [normalize_disagreement_tone(i) for i in items]
    items = [trim_text(i, trim_len) for i in items]
    return items[:max_items]


def render_section(title: str, items: list[str]) -> str:
    if not items:
        items = ["（待補）"]
    lines = [f"## {title}"]
    for i, item in enumerate(items, start=1):
        lines.append(f"{i}. {item}")
    return "\n".join(lines)


def build_note(topic: str, source_name: str, messages: list[Message], mode: str = "generic") -> str:
    if len({m.author for m in messages}) < 2:
        raise ValueError("輸入不符合最低結構：至少需要 2 位參與者發言")

    full_text = "\n\n".join(m.body for m in messages)
    records = extract_sentence_records(messages)

    consensus = extract_anchor_list(full_text, "本次討論的共識", 6)
    if not consensus:
        consensus = select_by_keywords(records, ["同意", "接受", "共識", "收斂", "可行", "成立", "附議"], 5)

    disagreements = extract_anchor_list(full_text, "本次分歧點的最終記錄", 4)
    if not disagreements:
        disagreements = extract_anchor_list(full_text, "本次討論未解決的問題", 4)
    if not disagreements:
        disagreements = select_by_keywords(records, ["異議", "不同意", "分歧", "保留", "反對", "爭議"], 4)

    hypotheses = extract_anchor_list(full_text, "本次討論未解決的問題", 5)
    if not hypotheses:
        hypotheses = select_by_keywords(records, ["待驗證", "假設", "尚未", "需要", "可測試", "閾值", "操作定義", "未解"], 5)

    experiments = select_by_keywords(records, ["實驗", "A/B/C", "比較", "指標", "控制條件", "觀察"], 4)
    risks = extract_risks(messages, 4)
    decisions = extract_decisions(records, full_text, 4)

    consensus = post_process_section(consensus, max_items=5, trim_len=88)
    disagreements = post_process_section(disagreements, max_items=4, trim_len=82, neutralize=True)
    hypotheses = post_process_section(hypotheses, max_items=5, trim_len=86)
    experiments = post_process_section(experiments, max_items=4, trim_len=82)
    risks = post_process_section(risks, max_items=4, trim_len=92)
    decisions = post_process_section(decisions, max_items=4, trim_len=86)

    sections = [
        "# Consensus Note",
        f"## 主題：{topic}",
        "",
        f"- 來源：`{source_name}`",
        "- 產出方式：ldrit-memory-loop v0.7",
        f"- 模式：{mode}",
        "",
        render_section("已收斂共識", consensus),
        "",
        render_section("保留分歧", disagreements),
        "",
        render_section("待驗證命題", hypotheses),
        "",
        render_section("最小可執行實驗", experiments),
        "",
        render_section("目前最大風險", risks),
        "",
        render_section("建議主控決策", decisions),
        "",
    ]
    return "\n".join(sections)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate consensus note from discussion markdown")
    p.add_argument("--input", required=True, help="Path to discussion markdown")
    p.add_argument("--output", required=True, help="Path to write consensus note")
    p.add_argument("--topic", default="", help="Optional topic override")
    p.add_argument(
        "--mode",
        default="generic",
        choices=["generic", "agentletters"],
        help="Input mode. Use agentletters for AgentLetters discussion files.",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)

    text = in_path.read_text(encoding="utf-8")
    messages = parse_messages(text)
    topic = args.topic.strip() or infer_topic(text)

    if args.mode == "agentletters":
        validate_agentletters_input(in_path, text, messages)

    note = build_note(topic=topic, source_name=in_path.name, messages=messages, mode=args.mode)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(note, encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
