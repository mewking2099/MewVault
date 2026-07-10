#!/usr/bin/env python3
"""srs.py — deterministic SM-2 spaced-repetition scheduler for learn-lab decks.

The scheduler stays OUT of the LLM: Claude grades answers conversationally,
this script decides when cards come back. deck.jsonl is the contract
(one card per line) shared with any future UI (MewLearn PRD).

Usage:
  srs.py due <deck.jsonl> [--limit 20] [--count]     # emit due/new cards as JSON lines
  srs.py grade <deck.jsonl> <card_id> <again|hard|good|easy>
  srs.py add <deck.jsonl> '<card json>'              # append one card (id required)
  srs.py stats <deck.jsonl>
  srs.py export <deck.jsonl> [out.tsv]               # Anki-importable TSV (front, back, tags)

Card shape:
  {"id":"n5-0042","front":"食べる","reading":"たべる","back":"to eat","tags":["verb"],
   "srs":{"ease":2.5,"interval":0,"due":"2026-07-10","reps":0,"lapses":0}}
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

GRADES = {"again": 0, "hard": 3, "good": 4, "easy": 5}
NEW_PER_SESSION = 8   # new cards mixed into a due batch


def load(deck_path: Path) -> list[dict]:
    cards = []
    if deck_path.exists():
        for line in deck_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                cards.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return cards


def save(deck_path: Path, cards: list[dict]) -> None:
    tmp = deck_path.with_suffix(".tmp")
    tmp.write_text("\n".join(json.dumps(c, ensure_ascii=False) for c in cards) + "\n",
                   encoding="utf-8")
    tmp.replace(deck_path)


def is_new(c: dict) -> bool:
    return c.get("srs", {}).get("reps", 0) == 0 and c.get("srs", {}).get("lapses", 0) == 0


def cmd_due(deck_path: Path, limit: int, count_only: bool) -> None:
    today = date.today().isoformat()
    cards = load(deck_path)
    due = [c for c in cards if not is_new(c) and c["srs"]["due"] <= today]
    new = [c for c in cards if is_new(c)]
    batch = due[:limit] + new[:min(NEW_PER_SESSION, max(0, limit - len(due)))]
    if count_only:
        print(json.dumps({"due": len(due), "new": len(new), "total": len(cards)}))
        return
    for c in batch:
        print(json.dumps(c, ensure_ascii=False))


def cmd_grade(deck_path: Path, card_id: str, grade_word: str) -> None:
    if grade_word not in GRADES:
        sys.exit(f"grade must be one of {list(GRADES)}")
    q = GRADES[grade_word]
    cards = load(deck_path)
    for c in cards:
        if c["id"] != card_id:
            continue
        s = c.setdefault("srs", {"ease": 2.5, "interval": 0, "due": date.today().isoformat(),
                                 "reps": 0, "lapses": 0})
        if q < 3:  # again → lapse, relearn tomorrow
            s["reps"] = 0
            s["lapses"] = s.get("lapses", 0) + 1
            s["interval"] = 1
        else:
            if s["reps"] == 0:
                s["interval"] = 1
            elif s["reps"] == 1:
                s["interval"] = 6
            else:
                s["interval"] = max(1, round(s["interval"] * s["ease"]))
            if grade_word == "hard":
                s["interval"] = max(1, round(s["interval"] * 0.7))
            elif grade_word == "easy":
                s["interval"] = round(s["interval"] * 1.3)
            s["reps"] += 1
        s["ease"] = max(1.3, s["ease"] + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        s["due"] = (date.today() + timedelta(days=s["interval"])).isoformat()
        save(deck_path, cards)
        print(json.dumps({"id": card_id, "next_due": s["due"], "interval": s["interval"],
                          "ease": round(s["ease"], 2)}))
        return
    sys.exit(f"card not found: {card_id}")


def cmd_add(deck_path: Path, card_json: str) -> None:
    card = json.loads(card_json)
    if "id" not in card or "front" not in card or "back" not in card:
        sys.exit("card needs id, front, back")
    cards = load(deck_path)
    if any(c["id"] == card["id"] for c in cards):
        sys.exit(f"duplicate id: {card['id']}")
    card.setdefault("srs", {"ease": 2.5, "interval": 0, "due": date.today().isoformat(),
                            "reps": 0, "lapses": 0})
    deck_path.parent.mkdir(parents=True, exist_ok=True)
    with open(deck_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(card, ensure_ascii=False) + "\n")
    print(f"added {card['id']} ({len(cards) + 1} cards)")


def cmd_stats(deck_path: Path) -> None:
    today = date.today().isoformat()
    cards = load(deck_path)
    due = sum(1 for c in cards if not is_new(c) and c["srs"]["due"] <= today)
    new = sum(1 for c in cards if is_new(c))
    leeches = [c["id"] for c in cards if c.get("srs", {}).get("lapses", 0) >= 4]
    mature = sum(1 for c in cards if c.get("srs", {}).get("interval", 0) >= 21)
    print(json.dumps({"total": len(cards), "due": due, "new": new, "mature": mature,
                      "leeches": leeches[:10]}, ensure_ascii=False))


def cmd_export(deck_path: Path, out: Path) -> None:
    cards = load(deck_path)
    lines = []
    for c in cards:
        front = c["front"] + (f" [{c['reading']}]" if c.get("reading") else "")
        lines.append(f"{front}\t{c['back']}\t{' '.join(c.get('tags', []))}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"exported {len(cards)} cards → {out} (Anki: File → Import, tab-separated)")


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, deck = sys.argv[1], Path(sys.argv[2])
    if cmd == "due":
        limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 20
        cmd_due(deck, limit, "--count" in sys.argv)
    elif cmd == "grade":
        cmd_grade(deck, sys.argv[3], sys.argv[4])
    elif cmd == "add":
        cmd_add(deck, sys.argv[3])
    elif cmd == "stats":
        cmd_stats(deck)
    elif cmd == "export":
        out = Path(sys.argv[3]) if len(sys.argv) > 3 else deck.with_suffix(".tsv")
        cmd_export(deck, out)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
