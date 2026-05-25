#!/usr/bin/env python3
"""Check a real consolidation candidate against required lean-memory cues."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from render_lean_memory import _infer_day, char_count_summary, render_lean_memory
except ModuleNotFoundError:
    from .render_lean_memory import _infer_day, char_count_summary, render_lean_memory

FILES = [
    "identity_constraints",
    "active_frontier",
    "settled_facts",
    "public_comms",
    "open_loops",
]


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_store(data_dir: Path) -> Dict[str, Dict[str, Any]]:
    store: Dict[str, Dict[str, Any]] = {}
    for name in FILES:
        store[name] = _load_json(data_dir / f"{name}.json")
    return store


def _required_anchor_cues(store: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    identity = store["identity_constraints"]
    frontier = store["active_frontier"]

    focus = frontier.get("focus", {})
    context = str(focus.get("context", "")).strip()
    goal = str(focus.get("goal", "")).strip()

    anchors = identity.get("anchors", {})
    room = str(anchors.get("room") or identity.get("identity", {}).get("room") or "").strip()
    email = str(
        anchors.get("contact_email") or identity.get("identity", {}).get("email") or ""
    ).strip()
    memory_kit_path = str(anchors.get("memory_kit_path", "")).strip()

    cues: List[Tuple[str, str]] = []
    day_line = _infer_day(context)
    if day_line:
        cues.append(("inferred day line", day_line))
    if goal:
        cues.append(("goal string", f"Goal: {goal}"))
    if room:
        cues.append(("room", f"Room: {room}"))
    if email:
        cues.append(("email", f"Email: {email}"))
    if memory_kit_path:
        cues.append(("memory_kit_path", f"Memory Kit Path: {memory_kit_path}"))

    return cues


def _required_do_not_repeat_topics(store: Dict[str, Dict[str, Any]]) -> List[str]:
    topics = []
    for entry in list(store["public_comms"].get("entries", [])):
        state = str(entry.get("announcement_state", "")).strip().lower()
        topic = str(entry.get("topic", "")).strip()
        if state == "do_not_repeat" and topic:
            topics.append(topic)
    return sorted(set(topics), key=lambda topic: topic.lower())


def _is_found(candidate_lower: str, expected: str) -> bool:
    return expected.strip().lower() in candidate_lower


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_path: Path
    candidate_total_chars: int | None
    candidate_embedded_chars: int | None
    rendered_total_chars: int | None
    rendered_embedded_chars: int | None
    required_cue_results: List[Tuple[str, str, bool]]
    required_topic_results: List[Tuple[str, bool]]
    hard_rules: List[str]
    all_found: bool
    read_error: str | None = None


def evaluate_memory_candidate(data_dir: Path, candidate_path: Path) -> CandidateEvaluation:
    try:
        candidate_text = candidate_path.read_text(encoding="utf-8")
    except OSError as exc:
        return CandidateEvaluation(
            candidate_path=candidate_path,
            candidate_total_chars=None,
            candidate_embedded_chars=None,
            rendered_total_chars=None,
            rendered_embedded_chars=None,
            required_cue_results=[],
            required_topic_results=[],
            hard_rules=[],
            all_found=False,
            read_error=str(exc),
        )

    store = _load_store(data_dir)
    rendered = render_lean_memory(data_dir)
    candidate_total_chars, candidate_embedded_chars = char_count_summary(candidate_text)
    rendered_total_chars, rendered_embedded_chars = char_count_summary(rendered)

    required_cues = _required_anchor_cues(store)
    required_topics = _required_do_not_repeat_topics(store)

    candidate_lower = candidate_text.lower()
    cue_results = [
        (label, snippet, _is_found(candidate_lower, snippet)) for label, snippet in required_cues
    ]
    topic_results = [(topic, _is_found(candidate_lower, topic)) for topic in required_topics]
    all_found = all(found for _, _, found in cue_results) and all(found for _, found in topic_results)
    hard_rules = list(store["identity_constraints"].get("hard_rules", []))

    return CandidateEvaluation(
        candidate_path=candidate_path,
        candidate_total_chars=candidate_total_chars,
        candidate_embedded_chars=candidate_embedded_chars,
        rendered_total_chars=rendered_total_chars,
        rendered_embedded_chars=rendered_embedded_chars,
        required_cue_results=cue_results,
        required_topic_results=topic_results,
        hard_rules=hard_rules,
        all_found=all_found,
    )


def check_memory_candidate(data_dir: Path, candidate_path: Path) -> int:
    evaluation = evaluate_memory_candidate(data_dir, candidate_path)
    if evaluation.read_error:
        print(f"ERROR: unable to read candidate file: {evaluation.read_error}")
        return 1

    print("MEMORY CANDIDATE CHECK")
    print(f"- Candidate: {evaluation.candidate_path}")
    print(f"- Candidate total chars: {evaluation.candidate_total_chars}")
    print(
        "- Candidate embedded CHAR_COUNT: "
        f"{evaluation.candidate_embedded_chars if evaluation.candidate_embedded_chars is not None else 'unknown'}"
    )
    print(f"- Rendered total chars: {evaluation.rendered_total_chars}")
    print(
        "- Rendered embedded CHAR_COUNT: "
        f"{evaluation.rendered_embedded_chars if evaluation.rendered_embedded_chars is not None else 'unknown'}"
    )

    print("- Required anchor cues:")
    for label, snippet, found in evaluation.required_cue_results:
        status = "FOUND" if found else "MISSING"
        print(f"  * {status} | {label} | {snippet}")

    print("- Required do_not_repeat topics:")
    for topic, found in evaluation.required_topic_results:
        status = "FOUND" if found else "MISSING"
        print(f"  * {status} | {topic}")

    print("- Reviewer reminders:")
    for rule in evaluation.hard_rules[:5]:
        print(f"  * {rule}")

    print("- STATUS: OK" if evaluation.all_found else "- STATUS: WARN")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare a memory candidate against required cues.")
    parser.add_argument(
        "data_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1] / "data"),
        help="Path to the data directory (defaults to repo data/).",
    )
    parser.add_argument("--candidate", required=True, help="Path to candidate text file.")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir).resolve()
    candidate_path = Path(args.candidate).resolve()
    return check_memory_candidate(data_dir, candidate_path)


if __name__ == "__main__":
    raise SystemExit(main())
