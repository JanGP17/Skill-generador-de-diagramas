#!/usr/bin/env python3
"""Make an evidence-aware figure registry from a UNT project manifest."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

KINDS = {"use_case", "function_architecture", "er", "flowchart", "screenshot", "other"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_json")
    parser.add_argument("--out", required=True, help="New output directory")
    args = parser.parse_args()
    source = Path(args.project_json).resolve(strict=True)
    out = Path(args.out).resolve()
    if out.exists():
        parser.error("output directory already exists")
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        parser.error("project JSON must contain an object")
    items = []
    for section, default_kind in (("diagrams", None), ("screenshots", "screenshot")):
        for index, entry in enumerate(data.get(section, []), 1):
            if not isinstance(entry, dict):
                parser.error(f"{section}[{index}] must be an object")
            kind = default_kind or entry.get("kind")
            if kind not in KINDS:
                parser.error(f"unsupported figure kind: {kind}")
            fid = str(entry.get("id") or f"{kind}-{index}")
            if any(existing["id"] == fid for existing in items):
                parser.error(f"duplicate figure id: {fid}")
            evidence = entry.get("evidence_ids") or []
            if not isinstance(evidence, list):
                parser.error(f"evidence_ids for {fid} must be a list")
            source_path = str(entry.get("source_path") or "")
            status = "ready_for_review" if evidence and source_path else "needs_evidence"
            if kind == "screenshot" and not source_path:
                status = "needs_user_screenshot"
            items.append({
                "id": fid, "kind": kind, "caption": str(entry.get("caption") or ""),
                "chapter": str(entry.get("chapter") or ""),
                "first_mention": str(entry.get("first_mention") or ""),
                "evidence_ids": evidence, "source_path": source_path,
                "editable_path": str(entry.get("editable_path") or ""),
                "preview_path": str(entry.get("preview_path") or ""),
                "status": status,
            })
    out.mkdir(parents=True)
    (out / "figure-registry.json").write_text(json.dumps({"schema_version": 1, "figures": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "figure-registry.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["id", "kind", "caption", "chapter", "first_mention", "evidence_ids", "source_path", "editable_path", "preview_path", "status"])
        for row in items:
            writer.writerow([row["id"], row["kind"], row["caption"], row["chapter"], row["first_mention"], ";".join(map(str, row["evidence_ids"])), row["source_path"], row["editable_path"], row["preview_path"], row["status"]])
    print(f"Figures: {len(items)}; pending: {sum(i['status'] != 'ready_for_review' for i in items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
