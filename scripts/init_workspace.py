#!/usr/bin/env python3
"""Create a technical modeling workspace without replacing existing files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


STARTER = {
    "schema_version": 1,
    "project_name": "",
    "institution": "Universidad Nacional de Trujillo",
    "program": "Ingeniería Informática",
    "source_revision": "",
    "diagrams": [],
    "screenshots": [],
    "database": {"model_type": "unconfirmed", "entities": [], "relationships": []},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", help="New directory for technical model artifacts")
    args = parser.parse_args()
    root = Path(args.directory).resolve()
    if root.exists():
        parser.error("directory already exists; choose a new workspace")
    root.mkdir(parents=True)
    for sub in ("evidence", "diagrams", "figures", "checks"):
        (root / sub).mkdir()
    (root / "project.json").write_text(json.dumps(STARTER, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (root / "claims.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        csv.writer(stream).writerow(["element_id", "claim", "evidence_ids", "source_path", "location", "verification", "status"])
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
