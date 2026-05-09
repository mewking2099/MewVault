"""mew instinct — manage the instinct pipeline."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

MEWVAULT_DIR = Path(__file__).parent.parent.parent.resolve()
PENDING_DIR = MEWVAULT_DIR / "instincts" / "pending"
PROMOTED_DIR = MEWVAULT_DIR / "instincts" / "promoted"
PROMOTE_THRESHOLD = 0.8


def run_instinct(args) -> None:
    action = getattr(args, "instinct_action", None) or "status"
    if action == "status":
        _status()
    elif action == "promote":
        _promote(args)
    elif action == "prune":
        _prune()
    elif action == "export":
        _export(args)
    elif action == "import":
        _import_instincts(args)
    else:
        _status()


def _status() -> None:
    print("\nInstinct Pipeline Status\n")

    pending = _load_all(PENDING_DIR)
    promoted = _load_all(PROMOTED_DIR)

    print(f"Pending ({len(pending)}):")
    if pending:
        for inst in sorted(pending, key=lambda x: -x.get("confidence", 0)):
            conf = inst.get("confidence", 0)
            mark = "→ promote?" if conf >= PROMOTE_THRESHOLD else "  "
            print(f"  {mark} [{conf:.2f}] {inst.get('id', '?')} — {inst.get('correct_behavior', '')[:60]}")
    else:
        print("  (none)")

    print(f"\nPromoted ({len(promoted)}):")
    if promoted:
        for inst in sorted(promoted, key=lambda x: -x.get("confidence", 0)):
            print(f"  [{inst.get('confidence', 0):.2f}] {inst.get('id', '?')} — {inst.get('correct_behavior', '')[:60]}")
    else:
        print("  (none)")
    print()


def _promote(args) -> None:
    inst_id = args.id
    confidence_override = getattr(args, "confidence", None)

    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)

    # Find in pending
    src_file = None
    for f in PENDING_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("id") == inst_id or f.stem == inst_id:
                src_file = f
                instinct = data
                break
        except (json.JSONDecodeError, OSError):
            continue

    if src_file is None:
        print(f"Instinct not found in pending: {inst_id}", file=sys.stderr)
        sys.exit(1)

    if confidence_override is not None:
        instinct["confidence"] = confidence_override

    instinct["status"] = "promoted"
    instinct["promoted_at"] = datetime.now(timezone.utc).isoformat()
    instinct["confirmed_sessions"] = instinct.get("confirmed_sessions", 1) + 1

    dst_file = PROMOTED_DIR / src_file.name
    dst_file.write_text(json.dumps(instinct, indent=2), encoding="utf-8")
    src_file.unlink()

    print(f"Promoted: {inst_id} (confidence: {instinct['confidence']:.2f})")
    print(f"  → {dst_file}")


def _prune() -> None:
    if not PENDING_DIR.exists():
        print("No pending instincts directory found.")
        return

    cutoff_days = 14
    now = datetime.now(timezone.utc)
    pruned = 0
    for f in list(PENDING_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            created_str = data.get("created", "")
            if created_str:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                age_days = (now - created).days
                if age_days > cutoff_days and data.get("confidence", 1.0) < PROMOTE_THRESHOLD:
                    f.unlink()
                    pruned += 1
                    print(f"  Pruned: {data.get('id', f.stem)} (age: {age_days}d, conf: {data.get('confidence', 0):.2f})")
        except (json.JSONDecodeError, OSError, ValueError):
            continue

    print(f"\nPruned {pruned} stale pending instincts (>{cutoff_days} days, conf < {PROMOTE_THRESHOLD}).")


def _export(args) -> None:
    out_path = Path(getattr(args, "out", None) or "instincts-export.json")
    promoted = _load_all(PROMOTED_DIR)
    out_path.write_text(json.dumps(promoted, indent=2), encoding="utf-8")
    print(f"Exported {len(promoted)} promoted instincts to: {out_path}")


def _import_instincts(args) -> None:
    src_path = Path(args.file)
    if not src_path.exists():
        print(f"File not found: {src_path}", file=sys.stderr)
        sys.exit(1)

    PROMOTED_DIR.mkdir(parents=True, exist_ok=True)
    instincts = json.loads(src_path.read_text(encoding="utf-8"))
    if not isinstance(instincts, list):
        instincts = [instincts]

    imported = 0
    for inst in instincts:
        inst_id = inst.get("id")
        if not inst_id:
            continue
        dst = PROMOTED_DIR / f"{inst_id}.json"
        if not dst.exists():
            dst.write_text(json.dumps(inst, indent=2), encoding="utf-8")
            imported += 1

    print(f"Imported {imported} instincts (skipped {len(instincts) - imported} already present).")


def _load_all(directory: Path) -> list:
    if not directory.exists():
        return []
    result = []
    for f in directory.glob("*.json"):
        try:
            result.append(json.loads(f.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return result
