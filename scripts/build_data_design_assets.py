#!/usr/bin/env python3
"""Build editable ER inputs and data-dictionary drafts from recorded entities."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def safe_name(raw: object, fallback: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(raw or "").lower()).strip("-")
    return value or fallback


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_json")
    parser.add_argument("--out", required=True, help="New output directory")
    args = parser.parse_args()
    source = Path(args.project_json).resolve(strict=True)
    out = Path(args.out).resolve()
    if out.exists():
        parser.error("output directory already exists")
    project = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(project, dict) or not isinstance(project.get("database"), dict):
        parser.error("project JSON needs a database object")
    database = project["database"]
    model_type = database.get("model_type", "unconfirmed")
    if model_type not in {"physical_database", "conceptual", "data_objects", "unconfirmed"}:
        parser.error("invalid database.model_type")
    entities = database.get("entities") or []
    relationships = database.get("relationships") or []
    if not isinstance(entities, list) or not isinstance(relationships, list):
        parser.error("entities and relationships must be lists")
    ids = set()
    overview_entities = []
    output_files: dict[str, str] = {}
    pending = []
    for index, item in enumerate(entities, 1):
        if not isinstance(item, dict):
            parser.error(f"entity {index} must be an object")
        eid = str(item.get("id") or "").strip()
        name = str(item.get("name") or "").strip()
        if not eid or not name or eid in ids:
            parser.error(f"entity {index} needs a unique id and name")
        ids.add(eid)
        fields = item.get("fields") or []
        if not isinstance(fields, list):
            parser.error(f"fields for {eid} must be a list")
        if not item.get("evidence_ids"):
            pending.append(f"Entity {eid}: no evidence IDs")
        attrs = []
        for field in fields:
            if not isinstance(field, dict) or not field.get("name"):
                parser.error(f"fields for {eid} need name objects")
            if not field.get("evidence_ids"):
                pending.append(f"Field {eid}.{field['name']}: no evidence IDs")
            attrs.append({"name": str(field["name"]), "key": bool(field.get("key", False))})
        overview_entities.append({"id": eid, "name": name, "attributes": []})
        filename = f"er-{safe_name(eid, f'entity-{index}')}.json"
        if filename in output_files:
            parser.error(f"entity IDs produce duplicate filename: {filename}")
        output_files[filename] = json.dumps({"diagramType": "single_entity", "title": name, "entity": {"name": name, "attributes": attrs}}, ensure_ascii=False, indent=2) + "\n"
    overview_relations = []
    for index, rel in enumerate(relationships, 1):
        if not isinstance(rel, dict) or rel.get("from") not in ids or rel.get("to") not in ids:
            parser.error(f"relationship {index} must link existing entity IDs")
        if not rel.get("evidence_ids"):
            pending.append(f"Relationship {index}: no evidence IDs")
        overview_relations.append({
            "name": str(rel.get("name") or f"Relación {index}"),
            "from": rel["from"], "to": rel["to"],
            "fromCardinality": str(rel.get("fromCardinality") or ""),
            "toCardinality": str(rel.get("toCardinality") or ""),
        })
    output_files["er-overview.json"] = json.dumps({"diagramType": "overview", "title": "Modelo de datos", "entities": overview_entities, "relationships": overview_relations}, ensure_ascii=False, indent=2) + "\n"
    lines = ["# Diccionario de datos (borrador)", "", f"Tipo de modelo declarado: **{model_type}**.", "", "Los campos y relaciones requieren cotejo con su evidencia. Este archivo no certifica tablas físicas ni migraciones.", ""]
    for item in entities:
        lines.extend([f"## {item['name']}", "", f"Evidencia de entidad: {', '.join(map(str, item.get('evidence_ids') or [])) or 'PENDIENTE'}", "", "| Campo | Tipo declarado | Clave | Descripción | Evidencia |", "|---|---|---|---|---|"])
        for field in item.get("fields") or []:
            cells = [field.get("name", ""), field.get("type", ""), "sí" if field.get("key") else "no", field.get("description", ""), ", ".join(map(str, field.get("evidence_ids") or [])) or "PENDIENTE"]
            lines.append("| " + " | ".join(str(v).replace("|", "\\|").replace("\n", " ") for v in cells) + " |")
        lines.append("")
    lines.extend(["## Pendientes", ""])
    lines.extend(f"- {x}" for x in pending) if pending else lines.append("- Ninguno en el modelo declarado; revisar validez de las fuentes.")
    out.mkdir(parents=True)
    for name, value in output_files.items():
        (out / name).write_text(value, encoding="utf-8")
    (out / "diccionario-datos.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Entities: {len(entities)}; relationships: {len(relationships)}; evidence gaps: {len(pending)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
