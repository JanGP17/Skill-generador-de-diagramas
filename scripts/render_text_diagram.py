"""Render a reviewed PlantUML or Mermaid source as SVG without overwriting files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from diagram_quality import inspect, load_config


UML_TYPES = {"uml-class", "uml-use-case", "uml-component", "uml-deployment", "uml-activity", "uml-sequence"}
MERMAID_TYPES = {"flowchart", "er", "sequence", "gantt"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Reviewed .puml or .mmd source")
    parser.add_argument("--type", choices=sorted(UML_TYPES | MERMAID_TYPES), required=True)
    parser.add_argument("--out", type=Path, required=True, help="New .svg output path")
    parser.add_argument("--png-out", type=Path, help="Optional new .png output path")
    parser.add_argument("--plantuml-jar", type=Path, help="Override PLANTUML_JAR")
    parser.add_argument("--quality-config", type=Path, help="JSON quality thresholds and switches")
    parser.add_argument("--quality-disable", default="", help="Comma-separated quality checks to disable")
    parser.add_argument("--no-quality", action="store_true", help="Skip quality reports")
    parser.add_argument("--trace", type=Path, help="Element-to-source trace manifest")
    parser.add_argument("--project-root", type=Path, help="Root used to verify trace sources")
    parser.add_argument("--quality-out", type=Path, help="New postflight JSON path")
    args = parser.parse_args()

    source = args.source.resolve()
    out = args.out.resolve()
    png_out = args.png_out.resolve() if args.png_out else None
    engine = "plantuml" if args.type in UML_TYPES else "mermaid"
    suffix = ".puml" if engine == "plantuml" else ".mmd"
    if not source.is_file() or source.suffix.lower() != suffix:
        parser.error(f"{args.type} requires an existing {suffix} source")
    if out.suffix.lower() != ".svg":
        parser.error("output must have .svg extension")
    if out.exists():
        parser.error(f"output already exists: {out}")
    if not out.parent.is_dir():
        parser.error(f"output directory does not exist: {out.parent}")
    if png_out and (png_out.suffix.lower() != ".png" or png_out.exists() or not png_out.parent.is_dir()):
        parser.error("--png-out must be a new .png path in an existing directory")
    quality_out = args.quality_out.resolve() if args.quality_out else out.with_suffix(".quality.json")
    preflight_out = out.with_suffix(".preflight.json")
    if not args.no_quality and (quality_out.exists() or preflight_out.exists()):
        parser.error("quality report path already exists")
    config = None
    if not args.no_quality:
        config = load_config(args.quality_config, args.quality_disable)
        preflight = inspect(source_path=source, trace_path=args.trace,
                            project_root=args.project_root, config=config, stage="pre")
        preflight_out.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")

    if engine == "plantuml":
        jar = args.plantuml_jar or Path(os.environ.get("PLANTUML_JAR", str(Path.home() / "tools" / "plantuml" / "plantuml.jar")))
        if not jar.is_file():
            parser.error(f"PlantUML JAR not found: {jar}; set PLANTUML_JAR or --plantuml-jar")
        java = shutil.which("java")
        if not java:
            parser.error("java not found on PATH")
        result = subprocess.run(
            [java, "-jar", str(jar), "-tsvg", "-pipe"],
            input=source.read_bytes(), capture_output=True, check=False,
        )
        if result.returncode != 0 or b"<svg" not in result.stdout:
            sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
            parser.error("PlantUML did not produce a valid SVG")
        out.write_bytes(result.stdout)
        if png_out:
            png_result = subprocess.run(
                [java, "-jar", str(jar), "-tpng", "-pipe"],
                input=source.read_bytes(), capture_output=True, check=False,
            )
            if png_result.returncode != 0 or not png_result.stdout.startswith(b"\x89PNG"):
                sys.stderr.write(png_result.stderr.decode("utf-8", errors="replace"))
                parser.error("PlantUML did not produce a valid PNG")
            png_out.write_bytes(png_result.stdout)
    else:
        mmdc = shutil.which("mmdc.cmd" if os.name == "nt" else "mmdc")
        if not mmdc:
            parser.error("Mermaid CLI (mmdc) not found on PATH")
        result = subprocess.run(
            [mmdc, "-i", str(source), "-o", str(out), "-b", "transparent"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        if result.returncode != 0:
            out.unlink(missing_ok=True)
            sys.stderr.write(result.stderr)
            parser.error("Mermaid CLI failed")
        if not out.is_file() or b"<svg" not in out.read_bytes():
            out.unlink(missing_ok=True)
            parser.error("Mermaid CLI did not produce a valid SVG")
        if png_out:
            png_result = subprocess.run(
                [mmdc, "-i", str(source), "-o", str(png_out), "-b", "white"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            if png_result.returncode != 0 or not png_out.is_file() or not png_out.read_bytes().startswith(b"\x89PNG"):
                png_out.unlink(missing_ok=True)
                sys.stderr.write(png_result.stderr)
                parser.error("Mermaid CLI did not produce a valid PNG")

    if not args.no_quality:
        postflight = inspect(source_path=source, svg_path=out, png_path=png_out,
                             trace_path=args.trace, project_root=args.project_root,
                             config=config, stage="post")
        quality_out.write_text(json.dumps(postflight, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        print(f"quality: {postflight['status']} -> {quality_out}")

    print(f"{engine}: {source} -> {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
