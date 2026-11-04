#!/usr/bin/env python3
"""Read-only, bounded source inventory for thesis evidence. Never executes project code."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    "target", ".next", ".nuxt", "coverage", "__pycache__", ".venv",
    "venv", ".idea", ".vscode", "out", "tmp", "temp",
}
SKIP_NAMES = {
    ".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
    "secrets.json", "credentials.json", "service-account.json", "package-lock.json",
    "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock",
}
SKIP_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".keystore", ".jks", ".sqlite", ".db"}
SOURCE_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs",
    ".php", ".vue", ".sql", ".prisma", ".dart", ".cs", ".kt",
    ".json", ".yaml", ".yml", ".toml", ".xml", ".gradle",
}
MARKER_NAMES = {"Dockerfile", "Makefile", "requirements.txt", "pom.xml", "go.mod", "Cargo.toml", "composer.json"}
MAX_FILES = 5000
MAX_FILE_BYTES = 512 * 1024
MAX_HITS = 1000

PATTERNS = {
    "route_candidate": re.compile(
        r"(?:@(?:app|router)\.(?:get|post|put|patch|delete|route)|"
        r"\b(?:app|router)\.(?:get|post|put|patch|delete)\s*\(|"
        r"@(?:Get|Post|Put|Patch|Delete|Request)Mapping\s*\(|"
        r"\b(?:Route|path)\s*\()", re.I
    ),
    "schema_candidate": re.compile(
        r"\b(?:CREATE\s+TABLE|ALTER\s+TABLE|model\s+\w+\s*\{|"
        r"class\s+\w+\s*\([^)]*(?:Model|Entity)|@Entity\b|"
        r"Schema\s*\(|Table\s*\()", re.I
    ),
    "test_candidate": re.compile(
        r"\b(?:def\s+test_\w+|it\s*\(|describe\s*\(|test\s*\(|"
        r"@Test\b|pytest\.mark|assert[A-Z]\w*\s*\()", re.I
    ),
    "auth_candidate": re.compile(
        r"\b(?:authorize|permission|middleware|authentication|jwt|oauth|"
        r"login|register|roles?)\b", re.I
    ),
}
SENSITIVE = re.compile(
    r"(?:password|passwd|secret|api[_-]?key|access[_-]?token|private[_-]?key|"
    r"authorization\s*:|BEGIN [A-Z ]*PRIVATE KEY|\bAKIA[0-9A-Z]{16}\b)", re.I
)


def walk_files(root: Path):
    count = 0
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(current) / d).is_symlink())
        for name in sorted(files):
            path = Path(current) / name
            if path.is_symlink() or name in SKIP_NAMES or name.startswith(".env") or path.suffix.lower() in SKIP_SUFFIXES:
                continue
            if path.suffix.lower() not in SOURCE_SUFFIXES and name not in MARKER_NAMES:
                continue
            count += 1
            if count > MAX_FILES:
                raise ValueError(f"El proyecto excede el límite de {MAX_FILES} archivos elegibles")
            yield path


def scan_file(path: Path, root: Path, report: dict) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            report["skipped"].append({"path": rel, "reason": "too_large"})
            return
        raw = path.read_bytes()
        if b"\x00" in raw:
            report["skipped"].append({"path": rel, "reason": "binary"})
            return
        decoded = raw.decode("utf-8", errors="replace")
    except (OSError, UnicodeError) as exc:
        report["skipped"].append({"path": rel, "reason": type(exc).__name__})
        return
    digest = hashlib.sha256(raw).hexdigest()
    report["files"].append({"path": rel, "bytes": size, "sha256": digest})
    for number, line in enumerate(decoded.splitlines(), 1):
        if len(report["evidence"]) >= MAX_HITS:
            report["truncated"] = True
            return
        kinds = [kind for kind, pattern in PATTERNS.items() if pattern.search(line)]
        if not kinds:
            continue
        snippet = "[línea omitida: posible secreto]" if SENSITIVE.search(line) else " ".join(line.strip().split())[:180]
        for kind in kinds:
            if len(report["evidence"]) >= MAX_HITS:
                report["truncated"] = True
                return
            report["evidence"].append({
                "id": f"E-{len(report['evidence']) + 1:04d}",
                "kind": kind,
                "path": rel,
                "line": number,
                "sha256": digest,
                "snippet": snippet,
                "status": "candidate_unverified",
            })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", help="Directorio del proyecto, solo lectura")
    parser.add_argument("--out", required=True, help="Directorio nuevo para el informe")
    args = parser.parse_args()
    root = Path(args.project).resolve(strict=True)
    out = Path(args.out).resolve()
    if not root.is_dir():
        parser.error("project debe ser un directorio")
    if out.exists():
        parser.error("la salida ya existe; usa un directorio nuevo")
    if out == root or root in out.parents:
        parser.error("la salida debe estar fuera del proyecto analizado")
    report = {
        "schema_version": 1,
        "project": str(root),
        "limits": {"max_files": MAX_FILES, "max_file_bytes": MAX_FILE_BYTES, "max_hits": MAX_HITS},
        "files": [], "evidence": [], "skipped": [], "truncated": False,
        "caution": "Coincidencias estáticas; verificar antes de convertirlas en afirmaciones técnicas.",
    }
    try:
        for path in walk_files(root):
            scan_file(path, root, report)
    except ValueError as exc:
        parser.error(str(exc))
    out.mkdir(parents=True)
    (out / "evidence.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (out / "traceability.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["evidence_id", "type", "relative_path", "line", "sha256", "candidate_excerpt", "thesis_claim", "chapter", "verification", "status"])
        for hit in report["evidence"]:
            writer.writerow([hit["id"], hit["kind"], hit["path"], hit["line"], hit["sha256"], hit["snippet"], "", "", "", "pending_review"])
    print(f"Archivos: {len(report['files'])}; candidatos: {len(report['evidence'])}; omitidos: {len(report['skipped'])}")
    print(f"Informe: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
