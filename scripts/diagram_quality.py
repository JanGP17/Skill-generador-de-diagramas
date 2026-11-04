#!/usr/bin/env python3
"""Measure diagram readability, validate evidence, and split reviewed flow models.

This module reports risks. It never certifies visual quality or institutional compliance.
Only standard-library modules are used.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile


DEFAULT_CONFIG: dict[str, Any] = {
    "box_mm": {"width": 160.0, "height": 240.0},
    "font_pt": {"block_below": 5.0, "warn_below": 7.0, "visio_default": 9.0},
    "limits": {
        "nodes": 18, "edges": 24, "decisions": 6,
        "aspect_ratio": 3.0, "connector_diagonals": 12.0,
    },
    "checks": {
        "readability": True, "density": True, "traceability": True,
        "decomposition": True,
    },
}
SVG_NS = "{http://www.w3.org/2000/svg}"
FONT_PATTERN = re.compile(
    r"font-size\s*[:=]\s*['\"]?([0-9]+(?:\.[0-9]+)?)(px|pt|mm|cm|in)?",
    re.IGNORECASE,
)
LENGTH_PATTERN = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)(px|pt|mm|cm|in)?\s*$", re.I)
ALLOWED_STATES = {"implementado", "documentado", "propuesto"}


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: Path | None, disabled: str = "") -> dict[str, Any]:
    config = copy.deepcopy(DEFAULT_CONFIG)
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("quality configuration must be a JSON object")
        config = deep_merge(config, data)
    for key in filter(None, (part.strip() for part in disabled.split(","))):
        if key not in config["checks"]:
            raise ValueError(f"unknown check: {key}")
        config["checks"][key] = False
    width = float(config["box_mm"]["width"])
    height = float(config["box_mm"]["height"])
    block = float(config["font_pt"]["block_below"])
    warn = float(config["font_pt"]["warn_below"])
    if min(width, height, block, warn) <= 0 or block >= warn:
        raise ValueError("box and font thresholds must be positive; block_below < warn_below")
    for name, value in config["limits"].items():
        if float(value) <= 0:
            raise ValueError(f"limit {name} must be positive")
    return config


def metric(value: Any, kind: str, basis: str) -> dict[str, Any]:
    return {"value": value, "kind": kind, "basis": basis}


def finding(code: str, severity: str, message: str, evidence: Any = None) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "severity": severity, "message": message}
    if evidence is not None:
        item["evidence"] = evidence
    return item


def length_to_px(raw: str | None) -> float | None:
    if not raw:
        return None
    match = LENGTH_PATTERN.match(raw)
    if not match:
        return None
    value = float(match.group(1))
    factor = {"px": 1.0, "pt": 96 / 72, "mm": 96 / 25.4,
              "cm": 96 / 2.54, "in": 96}.get((match.group(2) or "px").lower())
    return value * factor


def font_to_pt(value: str, unit: str | None) -> float:
    return float(value) * {"px": 0.75, "pt": 1.0, "mm": 72 / 25.4,
                           "cm": 72 / 2.54, "in": 72}.get((unit or "px").lower(), 0.75)


def read_svg(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    if root.tag != SVG_NS + "svg":
        raise ValueError("root element is not SVG")
    view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
    if len(view_box) == 4:
        width_px, height_px = float(view_box[2]), float(view_box[3])
        basis = "SVG viewBox"
    else:
        width_px = length_to_px(root.attrib.get("width"))
        height_px = length_to_px(root.attrib.get("height"))
        basis = "SVG width/height"
    if not width_px or not height_px or not math.isfinite(width_px * height_px) or min(width_px, height_px) <= 0:
        raise ValueError("SVG has no valid positive dimensions")
    data = path.read_text(encoding="utf-8", errors="replace")
    font_sizes = [font_to_pt(number, unit) for number, unit in FONT_PATTERN.findall(data)]
    return {
        "width_px": width_px, "height_px": height_px, "basis": basis,
        "font_pt": min(font_sizes) if font_sizes else None,
        "font_count": len(font_sizes),
        "text_elements": sum(1 for element in root.iter() if element.tag in {SVG_NS + "text", SVG_NS + "foreignObject"}),
    }


def read_png(path: Path) -> dict[str, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("PNG signature or IHDR is invalid")
    width, height = struct.unpack(">II", header[16:24])
    if min(width, height) <= 0:
        raise ValueError("PNG dimensions are invalid")
    return {"width_px": width, "height_px": height}


def read_vsdx(path: Path) -> dict[str, Any]:
    try:
        with ZipFile(path) as archive:
            bad_member = archive.testzip()
            if bad_member:
                raise ValueError(f"VSDX corrupt member: {bad_member}")
            pages = [name for name in archive.namelist() if re.fullmatch(r"visio/pages/page\d+\.xml", name)]
            if not pages:
                raise ValueError("VSDX contains no page XML")
            fonts: list[dict[str, Any]] = []
            missing_fonts = 0
            for name in pages:
                root = ET.fromstring(archive.read(name))
                for shape in root.iter():
                    if shape.tag.rsplit("}", 1)[-1] != "Shape":
                        continue
                    has_text = any(text.tag.rsplit("}", 1)[-1] == "Text" and
                                   "".join(text.itertext()).strip() for text in shape.iter())
                    if not has_text:
                        continue
                    values = []
                    for cell in shape.iter():
                        if cell.tag.rsplit("}", 1)[-1] == "Cell" and cell.get("N") == "Size":
                            try:
                                size = float(cell.get("V", "")) * 72.0
                                if math.isfinite(size) and size > 0:
                                    values.append(size)
                            except ValueError:
                                pass
                    if values:
                        fonts.append({"page": name, "shape_id": shape.get("ID"),
                                      "font_pt": round(min(values), 3)})
                    else:
                        missing_fonts += 1
    except BadZipFile as exc:
        raise ValueError("VSDX is not a valid ZIP package") from exc
    return {"pages": len(pages), "text_shapes_measured": len(fonts),
            "text_shapes_unmeasured": missing_fonts,
            "min_font_pt": min((item["font_pt"] for item in fonts), default=None),
            "shape_fonts": fonts}


def load_model(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    model = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(model, dict):
        raise ValueError("diagram model must be an object")
    kind = str(model.get("diagramType", "unknown")).lower()
    nodes = model.get("nodes")
    edges = model.get("edges")
    if isinstance(nodes, list):
        node_count = len(nodes)
        decision_count = sum(str(item.get("type", "")).lower() == "decision" for item in nodes if isinstance(item, dict))
    elif kind in {"use_case", "usecase", "uml_use_case"}:
        actors = model.get("actors") or []
        cases = model.get("useCases") or []
        node_count = len(actors) + len(cases)
        decision_count = 0
    elif kind in {"single", "single_entity", "entity"}:
        node_count, decision_count = 1, 0
    elif kind in {"overview", "general", "chen"}:
        node_count, decision_count = len(model.get("entities") or []), 0
    else:
        node_count, decision_count = None, None
    if isinstance(edges, list):
        edge_count = len(edges)
    elif kind in {"use_case", "usecase", "uml_use_case"}:
        edge_count = len(model.get("associations") or []) + len(model.get("dependencies") or [])
    elif kind in {"overview", "general", "chen"}:
        edge_count = len(model.get("relationships") or [])
    else:
        edge_count = None
    layout = model.get("layout") or {}
    width_in = float(layout["pageWidth"]) if layout.get("pageWidth") is not None else None
    height_in = float(layout["pageHeight"]) if layout.get("pageHeight") is not None else None
    if width_in is not None and (not math.isfinite(width_in) or width_in <= 0):
        raise ValueError("model pageWidth must be positive")
    if height_in is not None and (not math.isfinite(height_in) or height_in <= 0):
        raise ValueError("model pageHeight must be positive")
    segment_lengths = []
    for edge in edges if isinstance(edges, list) else []:
        points = edge.get("points") if isinstance(edge, dict) else None
        if isinstance(points, list) and len(points) >= 2:
            pairs = [(float(point["x"]), float(point["y"])) if isinstance(point, dict)
                     else (float(point[0]), float(point[1])) for point in points]
            segment_lengths.append(sum(math.dist(a, b) for a, b in zip(pairs, pairs[1:])))
    for segment in model.get("segments") or []:
        if isinstance(segment, dict) and all(key in segment for key in ("x1", "y1", "x2", "y2")):
            segment_lengths.append(math.dist((float(segment["x1"]), float(segment["y1"])),
                                                 (float(segment["x2"]), float(segment["y2"]))))
    return model, {
        "type": kind, "nodes": node_count, "edges": edge_count,
        "decisions": decision_count, "width_in": width_in, "height_in": height_in,
        "connector_length_in": sum(segment_lengths) if segment_lengths else None,
        "measured_connectors": len(segment_lengths),
    }


def read_source(path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".mmd":
        edges = len(re.findall(r"(?:-->|---|-.->|==>)", source))
        decisions = source.count("{") if re.search(r"\bflowchart\b", source) else None
        nodes = len(set(re.findall(r"(?m)^\s*([A-Za-z][\w-]*)\s*(?:\[|\(|\{)", source))) or None
    elif path.suffix.lower() == ".puml":
        nodes = len(re.findall(r"(?m)^\s*(?:class|interface|entity|component|actor)\s+", source))
        if nodes == 0:
            nodes = len(re.findall(r"(?m)^\s*:[^;]+;", source)) or None
        edges = len(re.findall(r"(?m)^\s*\S+\s+(?:-->|<--|\*--|o--|--|\.\.>)\s+\S+", source)) or None
        decisions = len(re.findall(r"(?m)^\s*(?:if\s*\(|switch\s*\()", source)) or None
    else:
        raise ValueError("source must be .puml or .mmd")
    return {"nodes": nodes, "edges": edges, "decisions": decisions}


def current_revision(root: Path) -> str | None:
    result = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def validate_model_graph(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Check only relationships that the structured model explicitly declares."""
    nodes = model.get("nodes")
    edges = model.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return []
    issues: list[dict[str, Any]] = []
    ids: set[str] = set()
    for node in nodes:
        identifier = str(node.get("id") or "") if isinstance(node, dict) else ""
        if not identifier:
            issues.append(finding("model_id_missing", "blocking", "Model node has no ID"))
        elif identifier in ids:
            issues.append(finding("model_id_duplicate", "blocking", f"Duplicate model node ID: {identifier}"))
        ids.add(identifier)
    for index, edge in enumerate(edges, 1):
        if not isinstance(edge, dict) or str(edge.get("from") or "") not in ids or str(edge.get("to") or "") not in ids:
            issues.append(finding("model_relation_invalid", "blocking", f"Model edge {index} has an unknown endpoint"))
    return issues


def validate_trace(path: Path, project_root: Path | None, model: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("trace manifest must be an object")
    elements = manifest.get("elements") or []
    relations = manifest.get("relations") or []
    issues: list[dict[str, Any]] = []
    ids: set[str] = set()
    model_ids = {str(item.get("id")) for item in (model or {}).get("nodes", [])
                 if isinstance(item, dict) and not item.get("synthetic")}
    synthetic_ids = {str(item.get("id")) for item in (model or {}).get("nodes", [])
                     if isinstance(item, dict) and item.get("synthetic")}
    root = project_root.resolve() if project_root else None
    revision = str(manifest.get("project_revision") or "")
    head = current_revision(root) if root else None
    source_cache: dict[Path, tuple[int, str]] = {}
    changed_sources: dict[str, set[str]] = {}
    if head and revision and not head.startswith(revision) and not revision.startswith(head):
        issues.append(finding("stale_revision", "warning", "Manifest revision differs from project HEAD",
                              {"manifest": revision, "head": head}))
    elif not revision:
        issues.append(finding("revision_missing", "warning", "Project revision is not recorded"))

    def check_source(owner: str, sources: Any, status: str, rationale: str) -> None:
        if not isinstance(sources, list) or not sources:
            severity = "warning" if status == "propuesto" and rationale else "blocking"
            issues.append(finding("source_missing", severity, f"{owner} has no source"))
            return
        for source in sources:
            if not isinstance(source, dict) or not source.get("path"):
                issues.append(finding("source_invalid", "blocking", f"{owner} has an invalid source"))
                continue
            if root is None:
                issues.append(finding("source_unverified", "warning", f"{owner} source cannot be checked without project root"))
                continue
            location = (root / str(source["path"])).resolve()
            if location != root and root not in location.parents:
                issues.append(finding("source_outside_root", "blocking", f"{owner} source escapes project root"))
                continue
            if not location.is_file():
                issues.append(finding("source_not_found", "blocking", f"{owner} source file is missing", str(location)))
                continue
            start = source.get("start_line")
            end = source.get("end_line", start)
            if location not in source_cache:
                data = location.read_bytes()
                source_cache[location] = (len(data.decode("utf-8", errors="replace").splitlines()),
                                          hashlib.sha256(data).hexdigest().lower())
            count, actual_hash = source_cache[location]
            if start is None:
                issues.append(finding("line_unverified", "warning", f"{owner} source has no line location"))
            else:
                if not (1 <= int(start) <= int(end) <= count):
                    issues.append(finding("line_invalid", "blocking", f"{owner} source line is invalid",
                                          {"path": str(location), "lines": count}))
            expected = source.get("sha256")
            if expected and actual_hash != str(expected).lower():
                changed_sources.setdefault(str(location), set()).add(owner)

    for kind, entries in (("element", elements), ("relation", relations)):
        if not isinstance(entries, list):
            issues.append(finding("entries_invalid", "blocking", f"{kind} list is invalid"))
            continue
        for item in entries:
            if not isinstance(item, dict) or not str(item.get("id") or "").strip():
                issues.append(finding("id_missing", "blocking", f"{kind} has no unique ID"))
                continue
            identifier = str(item["id"])
            if identifier in ids:
                issues.append(finding("id_duplicate", "blocking", f"duplicate ID: {identifier}"))
            ids.add(identifier)
            status = str(item.get("status") or "")
            if status not in ALLOWED_STATES:
                issues.append(finding("status_invalid", "blocking", f"{identifier} has invalid status: {status}"))
            if not item.get("name") or not item.get("type"):
                issues.append(finding("identity_incomplete", "blocking", f"{identifier} needs name and type"))
            check_source(identifier, item.get("sources"), status, str(item.get("rationale") or ""))
    for location, owners in changed_sources.items():
        issues.append(finding("source_changed", "warning", "Source hash changed; review affected model claims",
                              {"path": location, "owners": sorted(owners)}))
    element_ids = {str(item.get("id")) for item in elements if isinstance(item, dict)}
    for relation in relations if isinstance(relations, list) else []:
        if isinstance(relation, dict) and (str(relation.get("from")) not in element_ids or
                                           str(relation.get("to")) not in element_ids):
            issues.append(finding("relation_endpoint_missing", "blocking",
                                  f"{relation.get('id')} references an unknown element"))
    if model_ids:
        missing = sorted(model_ids - element_ids)
        extra = sorted(element_ids - model_ids - synthetic_ids)
        if missing:
            issues.append(finding("model_elements_untraced", "blocking", "Model nodes lack trace entries", missing))
        if extra:
            issues.append(finding("trace_elements_not_in_model", "warning", "Trace elements are outside this view", extra))
    if model and isinstance(model.get("edges"), list) and isinstance(relations, list):
        model_edges = Counter((str(edge.get("from")), str(edge.get("to")), str(edge.get("label") or ""))
                              for edge in model["edges"] if isinstance(edge, dict))
        traced_edges = Counter((str(edge.get("from")), str(edge.get("to")), str(edge.get("label") or ""))
                               for edge in relations if isinstance(edge, dict))
        absent = model_edges - traced_edges
        extra = traced_edges - model_edges
        if absent:
            issues.append(finding("model_relations_untraced", "blocking", "Model edges lack matching trace relations",
                                  [{"from": a, "to": b, "label": c, "count": n} for (a, b, c), n in absent.items()]))
        if extra:
            issues.append(finding("trace_relations_not_in_model", "warning", "Trace relations are outside this view or labels differ",
                                  [{"from": a, "to": b, "label": c, "count": n} for (a, b, c), n in extra.items()]))
    return {
        "manifest": str(path), "diagram_id": manifest.get("diagram_id"),
        "project_revision": revision or None, "current_revision": head,
        "scope": manifest.get("scope"), "omissions": manifest.get("omissions") or [],
        "elements": len(elements), "relations": len(relations), "issues": issues,
    }


def inspect(
    *, model_path: Path | None = None, source_path: Path | None = None,
    svg_path: Path | None = None, png_path: Path | None = None,
    vsdx_path: Path | None = None, trace_path: Path | None = None,
    project_root: Path | None = None, config: dict[str, Any] | None = None,
    stage: str = "post", font_pt: float | None = None,
) -> dict[str, Any]:
    config = config or copy.deepcopy(DEFAULT_CONFIG)
    findings: list[dict[str, Any]] = []
    measurements: dict[str, Any] = {}
    inputs = {key: str(path) for key, path in {
        "model": model_path, "source": source_path, "svg": svg_path,
        "png": png_path, "vsdx": vsdx_path, "trace": trace_path,
    }.items() if path}
    model = None
    details: dict[str, Any] = {}
    if model_path:
        model, details = load_model(model_path)
        findings.extend(validate_model_graph(model))
    if source_path:
        source_details = read_source(source_path)
        for key, value in source_details.items():
            if details.get(key) is None:
                details[key] = value
    for key in ("nodes", "edges", "decisions"):
        value = details.get(key)
        measurements[key] = metric(value, "exact" if model_path and value is not None else
                                   "estimated" if value is not None else "unavailable",
                                   "diagram model" if model_path and value is not None else
                                   "source syntax" if value is not None else "not provided")
    vsdx_info = read_vsdx(vsdx_path) if vsdx_path else None
    if svg_path:
        svg = read_svg(svg_path)
        width_px, height_px = svg["width_px"], svg["height_px"]
        width_mm, height_mm = width_px * 25.4 / 96, height_px * 25.4 / 96
        base_font = svg["font_pt"]
        font_basis = "smallest declared SVG font-size"
        dimension_basis = svg["basis"]
        measurements["svg_text_elements"] = metric(svg["text_elements"], "exact", "SVG XML elements")
    elif details.get("width_in") and details.get("height_in"):
        width_mm, height_mm = details["width_in"] * 25.4, details["height_in"] * 25.4
        base_font = (font_pt if font_pt is not None else
                     vsdx_info["min_font_pt"] if vsdx_info and vsdx_info["min_font_pt"] is not None else
                     float(config["font_pt"]["visio_default"]))
        font_basis = ("explicit --font-pt override" if font_pt is not None else
                      "smallest measured VSDX text-shape font" if vsdx_info and vsdx_info["min_font_pt"] is not None else
                      "estimated Visio default/edge font")
        dimension_basis = "positioned JSON page size"
    else:
        width_mm = height_mm = base_font = None
        font_basis = dimension_basis = "not available before layout/render"
    if svg_path and font_pt is not None:
        base_font, font_basis = font_pt, "explicit --font-pt override"
    if width_mm and height_mm:
        if not all(math.isfinite(v) and v > 0 for v in (width_mm, height_mm)):
            raise ValueError("diagram dimensions are invalid")
        factor = min(float(config["box_mm"]["width"]) / width_mm,
                     float(config["box_mm"]["height"]) / height_mm)
        aspect = max(width_mm / height_mm, height_mm / width_mm)
        measurements["dimensions_mm"] = metric({"width": round(width_mm, 3), "height": round(height_mm, 3)},
                                                "exact" if svg_path or model_path else "estimated", dimension_basis)
        measurements["aspect_ratio"] = metric(round(aspect, 3), "exact", dimension_basis)
        measurements["fit_scale"] = metric(round(factor, 4), "estimated",
                                           "uniform fit to configurable reference box")
        estimated_font = base_font * factor if base_font is not None else None
        measurements["font_pt_at_fit"] = metric(round(estimated_font, 3) if estimated_font is not None else None,
                                                "estimated" if estimated_font is not None else "unavailable",
                                                font_basis)
    else:
        aspect = estimated_font = None
        for key in ("dimensions_mm", "aspect_ratio", "fit_scale", "font_pt_at_fit"):
            measurements[key] = metric(None, "unavailable", dimension_basis)
    if png_path:
        measurements["png"] = metric(read_png(png_path), "exact", "PNG IHDR")
    if vsdx_path:
        measurements["vsdx"] = metric(vsdx_info, "exact", "VSDX package XML and ShapeSheet font cells")
        if vsdx_info["text_shapes_unmeasured"]:
            findings.append(finding("visio_font_incomplete", "warning",
                                    "Some VSDX text shapes have no explicit font-size cell",
                                    vsdx_info["text_shapes_unmeasured"]))
    if details.get("connector_length_in") is not None and details.get("width_in") and details.get("height_in"):
        diagonal = math.hypot(details["width_in"], details["height_in"])
        connector_diagonals = details["connector_length_in"] / diagonal
        measurements["connector_diagonals"] = metric(round(connector_diagonals, 3), "estimated",
                                                     f"{details['measured_connectors']} routed edges/segments")
    else:
        connector_diagonals = None
        measurements["connector_diagonals"] = metric(None, "unavailable", "no positioned connector points")

    if config["checks"]["readability"]:
        if estimated_font is None:
            findings.append(finding("font_unmeasured", "warning", "Font size at final scale cannot be estimated"))
        elif estimated_font < float(config["font_pt"]["block_below"]):
            findings.append(finding("font_too_small", "blocking", "Estimated font is below the automatic visual-approval threshold",
                                    round(estimated_font, 3)))
        elif estimated_font < float(config["font_pt"]["warn_below"]):
            findings.append(finding("font_small", "warning", "Estimated font needs visual review",
                                    round(estimated_font, 3)))
        if aspect is not None and aspect > float(config["limits"]["aspect_ratio"]):
            findings.append(finding("extreme_aspect", "warning", "Diagram is excessively wide or tall",
                                    round(aspect, 3)))
    if config["checks"]["density"]:
        for key, limit_key in (("nodes", "nodes"), ("edges", "edges"), ("decisions", "decisions")):
            value = details.get(key)
            if value is not None and value > int(config["limits"][limit_key]):
                findings.append(finding(f"{key}_dense", "warning", f"{key} exceeds the configured review threshold",
                                        {"count": value, "limit": config["limits"][limit_key]}))
        if connector_diagonals is not None and connector_diagonals > float(config["limits"]["connector_diagonals"]):
            findings.append(finding("long_connectors", "warning", "Total connector length is high",
                                    round(connector_diagonals, 3)))
    trace = None
    if config["checks"]["traceability"]:
        if trace_path:
            trace = validate_trace(trace_path, project_root, model)
            findings.extend(trace["issues"])
        else:
            findings.append(finding("trace_unavailable", "warning", "No element-to-source manifest was supplied"))
    split_recommended = any(item["code"] in {
        "font_too_small", "font_small", "extreme_aspect", "nodes_dense",
        "edges_dense", "decisions_dense", "long_connectors",
    } for item in findings)
    if config["checks"]["decomposition"] and split_recommended:
        findings.append(finding("decomposition_review", "warning",
                                "Review semantic groups before generating subdiagrams"))
    blocked = any(item["severity"] == "blocking" for item in findings)
    return {
        "schema_version": 1, "stage": stage, "inputs": inputs,
        "reference_box_mm": config["box_mm"],
        "measurements": measurements, "traceability": trace,
        "findings": findings, "split_recommended": split_recommended,
        "status": "blocked" if blocked else "needs_review" if findings else "ready_for_visual_review",
        "automatic_visual_approval": False,
        "limitations": [
            "Font and fit are estimates, not a rendered document or print test.",
            "SVG/XML and package validity do not establish visual or semantic correctness.",
        ],
    }


def split_flow(model_path: Path, groups_path: Path | None, out: Path) -> dict[str, Any]:
    model, details = load_model(model_path)
    if details["type"] not in {"flowchart", "workflow", "business_flow", "algorithm_flow"}:
        if groups_path is not None:
            raise ValueError("automatic split currently supports only flowchart JSON; review non-flow groups manually")
        if out.exists():
            raise ValueError("output directory already exists")
        out.mkdir(parents=True)
        report = {
            "status": "needs_review", "reason": "Semantic partition is not verified for this diagram type",
            "model": str(model_path), "diagramType": details["type"],
            "nodes": details.get("nodes"), "edges": details.get("edges"),
            "suggested_review": ["Identify responsibilities or subsystems from project sources",
                                 "Map each element and relation to a reviewed view",
                                 "Verify no relation, multiplicity, or constraint is lost"],
            "generated_subdiagrams": [], "visual_approval": False,
        }
        (out / "proposal.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report
    nodes = model.get("nodes") or []
    edges = model.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("flowchart needs nodes and edges")
    ids = [str(node.get("id") or "") for node in nodes]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError("flowchart nodes need unique IDs")
    node_by_id = {str(node["id"]): node for node in nodes}
    for index, edge in enumerate(edges, 1):
        if edge.get("from") not in node_by_id or edge.get("to") not in node_by_id:
            raise ValueError(f"edge {index} has an unknown endpoint")
    if out.exists():
        raise ValueError("output directory already exists")
    if groups_path is None:
        out.mkdir(parents=True)
        candidate_fields = ("module", "responsibility", "phase", "subprocess", "actor")
        candidates = {}
        for field in candidate_fields:
            values = {str(node.get(field)) for node in nodes if node.get(field)}
            if len(values) > 1 and all(node.get(field) for node in nodes):
                candidates[field] = sorted(values)
        report = {
            "status": "needs_review", "reason": "No reviewed semantic groups were provided",
            "model": str(model_path), "nodes": len(nodes), "edges": len(edges),
            "semantic_candidates": candidates,
            "required_input": "A groups JSON with id, title, basis, and nodeIds for each group",
            "omitted": [], "generated_subdiagrams": [],
        }
        (out / "proposal.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report
    plan = json.loads(groups_path.read_text(encoding="utf-8"))
    groups = plan.get("groups") if isinstance(plan, dict) else None
    if not isinstance(groups, list) or len(groups) < 2:
        raise ValueError("groups file needs at least two semantic groups")
    membership: dict[str, str] = {}
    group_by_id: dict[str, dict[str, Any]] = {}
    for group in groups:
        gid = str(group.get("id") or "")
        members = group.get("nodeIds")
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", gid) or gid in group_by_id:
            raise ValueError("group IDs must be unique lowercase slugs")
        if not group.get("title") or not group.get("basis") or not isinstance(members, list) or not members:
            raise ValueError(f"group {gid} needs title, semantic basis, and nodeIds")
        group_by_id[gid] = group
        for node_id in members:
            if node_id not in node_by_id or node_id in membership:
                raise ValueError(f"unknown or duplicate group membership: {node_id}")
            membership[node_id] = gid
    if set(membership) != set(node_by_id):
        raise ValueError(f"groups do not cover every node: {sorted(set(node_by_id) - set(membership))}")
    edge_records = []
    for index, edge in enumerate(edges, 1):
        eid = str(edge.get("id") or f"edge-{index:04d}")
        if eid in {record["id"] for record in edge_records}:
            raise ValueError(f"duplicate edge ID: {eid}")
        edge_records.append({"id": eid, "from": edge["from"], "to": edge["to"],
                             "label": edge.get("label", ""), "fromGroup": membership[edge["from"]],
                             "toGroup": membership[edge["to"]]})
    cross_records = [record for record in edge_records if record["fromGroup"] != record["toGroup"]]
    for index, record in enumerate(cross_records, 1):
        record["referenceCode"] = f"C{index:02d}"
    out.mkdir(parents=True)
    overview_nodes = [{"id": gid, "type": "process", "text": group["title"],
                       "semanticBasis": group["basis"]} for gid, group in group_by_id.items()]
    overview_bundles: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for record in cross_records:
        overview_bundles.setdefault((record["fromGroup"], record["toGroup"]), []).append(record)
    overview_edges = [{"id": f"overview-{source}-{target}", "from": source, "to": target,
                       "label": f"{len(bundle)} " + ("relación" if len(bundle) == 1 else "relaciones"),
                       "originalEdgeIds": [record["id"] for record in bundle],
                       "referenceCodes": [record["referenceCode"] for record in bundle],
                       "originalRelations": [{"id": record["id"], "from": record["from"],
                                              "to": record["to"], "label": record["label"]}
                                             for record in bundle]}
                      for (source, target), bundle in overview_bundles.items()]
    overview = {"diagramType": "flowchart", "title": f"Vista general: {model.get('title') or model_path.stem}",
                "nodes": overview_nodes, "edges": overview_edges,
                "quality": {"view": "semantic_overview", "aggregated_edges": True,
                            "original_relations_preserved_in_metadata": True}}
    (out / "overview.json").write_text(json.dumps(overview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    continuity = []
    inventory = []
    emitted_edge_ids: Counter[str] = Counter()
    for gid, group in group_by_id.items():
        member_ids = set(group["nodeIds"])
        subnodes = []
        for node in nodes:
            if node["id"] in member_ids:
                copied = copy.deepcopy(node)
                for key in ("x", "y", "rank", "column"):
                    copied.pop(key, None)
                copied["rank"] = len(subnodes)
                copied["column"] = 0
                subnodes.append(copied)
        local_rank = {node["id"]: node["rank"] for node in subnodes}
        used_port_rows: set[int] = set()
        subedges = []
        for record, edge in zip(edge_records, edges):
            source_here = record["from"] in member_ids
            target_here = record["to"] in member_ids
            if source_here and target_here:
                copied = copy.deepcopy(edge)
                copied["id"] = record["id"]
                copied.pop("points", None)
                subedges.append(copied)
            elif source_here or target_here:
                direction = "out" if source_here else "in"
                external_id = record["to"] if source_here else record["from"]
                other_gid = membership[external_id]
                reference_id = f"continuity_{direction}_{record['id']}"
                port = {
                    "id": reference_id, "type": "process",
                    "text": record["referenceCode"], "width": 0.85, "height": 0.36,
                    "synthetic": True, "kind": "continuity",
                    "originalNodeId": external_id, "originalEdgeId": record["id"],
                    "otherGroup": other_gid, "direction": direction,
                }
                local_id = record["from"] if source_here else record["to"]
                row = local_rank[local_id]
                while row in used_port_rows:
                    row += 1
                used_port_rows.add(row)
                port["rank"] = row
                port["column"] = 1
                subnodes.append(port)
                subedges.append({
                    "id": record["id"], "from": record["from"] if source_here else reference_id,
                    "to": reference_id if source_here else record["to"],
                    "label": record["label"], "originalFrom": record["from"],
                    "originalTo": record["to"], "continuity": True,
                })
                continuity.append({"edgeId": record["id"], "view": gid, "direction": direction,
                                   "referenceId": reference_id, "referenceCode": record["referenceCode"],
                                   "otherGroup": other_gid, "originalFrom": record["from"],
                                   "originalTo": record["to"], "label": record["label"]})
        sub = {"diagramType": "flowchart", "title": group["title"],
               "layout": {"direction": "TB", "rankGap": 0.48, "columnGap": 1.1},
               "nodes": subnodes, "edges": subedges,
               "quality": {"view": gid, "semanticBasis": group["basis"],
                           "continuityReferencesAreSynthetic": True}}
        emitted_edge_ids.update(str(edge["id"]) for edge in subedges)
        filename = f"sub-{gid}.json"
        (out / filename).write_text(json.dumps(sub, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        inventory.append({"group": gid, "file": filename,
                          "originalNodes": sorted(member_ids),
                          "originalEdges": [edge["id"] for edge in edge_records
                                            if edge["from"] in member_ids or edge["to"] in member_ids]})
    expected_occurrences = {
        edge["id"]: 1 if edge["fromGroup"] == edge["toGroup"] else 2
        for edge in edge_records
    }
    cross_ids = {edge["id"] for edge in edge_records if edge["fromGroup"] != edge["toGroup"]}
    overview_ids = [str(edge_id) for edge in overview_edges for edge_id in edge["originalEdgeIds"]]
    report = {
        "status": "generated_for_review", "model": str(model_path),
        "groups": [{"id": gid, "title": item["title"], "basis": item["basis"]}
                   for gid, item in group_by_id.items()],
        "original": {"nodes": len(nodes), "edges": len(edges)},
        "inventory": inventory, "continuity": continuity,
        "overview_bundles": [{"fromGroup": edge["from"], "toGroup": edge["to"],
                              "originalEdgeIds": edge["originalEdgeIds"],
                              "referenceCodes": edge["referenceCodes"]} for edge in overview_edges],
        "omitted_nodes": [], "omitted_edges": [],
        "semantic_verification": {
            "all_nodes_assigned_once": len(membership) == len(nodes),
            "all_edges_preserved": all(emitted_edge_ids[edge_id] == expected
                                       for edge_id, expected in expected_occurrences.items()),
            "cross_group_edges_referenced_in_both_views":
                all(sum(ref["edgeId"] == edge["id"] for ref in continuity) == 2
                    for edge in edge_records if edge["fromGroup"] != edge["toGroup"]),
            "overview_contains_every_cross_group_edge":
                len(overview_ids) == len(cross_ids) and set(overview_ids) == cross_ids,
        },
        "group_basis_verification": "reviewed input; technical truth requires source review",
        "visual_approval": False,
    }
    (out / "continuity-and-inventory.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("inspect", help="Preflight or postflight quality report")
    for option in ("model", "source", "svg", "png", "vsdx", "trace", "project-root", "config"):
        check.add_argument("--" + option, type=Path)
    check.add_argument("--stage", choices=["pre", "post"], default="post")
    check.add_argument("--font-pt", type=float)
    check.add_argument("--disable", default="", help="Comma-separated checks: readability,density,traceability,decomposition")
    check.add_argument("--out", type=Path, help="New JSON report path; stdout if omitted")
    split = commands.add_parser("split", help="Propose or generate reviewed flowchart subdiagrams")
    split.add_argument("--model", type=Path, required=True)
    split.add_argument("--groups", type=Path, help="Reviewed semantic groups JSON")
    split.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            config = load_config(args.config, args.disable)
            report = inspect(
                model_path=args.model, source_path=args.source, svg_path=args.svg,
                png_path=args.png, vsdx_path=args.vsdx, trace_path=args.trace,
                project_root=args.project_root, config=config, stage=args.stage,
                font_pt=args.font_pt,
            )
            data = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            if args.out:
                if args.out.exists():
                    raise ValueError("quality output already exists")
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(data, encoding="utf-8")
                print(json.dumps({"report": str(args.out), "status": report["status"],
                                  "findings": len(report["findings"])}, ensure_ascii=False))
            else:
                print(data, end="")
        else:
            report = split_flow(args.model, args.groups, args.out)
            print(json.dumps({"output": str(args.out), "status": report["status"],
                              "groups": len(report.get("groups", []))}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"diagram quality error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
