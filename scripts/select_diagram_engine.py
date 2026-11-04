#!/usr/bin/env python3
"""Select a diagram engine from notation and requested editability."""

import argparse
import json

TEXT_TYPES = {
    "uml-class": ("plantuml", ".puml"),
    "uml-use-case": ("plantuml", ".puml"),
    "uml-component": ("plantuml", ".puml"),
    "uml-deployment": ("plantuml", ".puml"),
    "uml-activity": ("plantuml", ".puml"),
    "uml-sequence": ("plantuml", ".puml"),
    "flowchart": ("mermaid", ".mmd"),
    "er": ("mermaid", ".mmd"),
    "sequence": ("mermaid", ".mmd"),
    "gantt": ("mermaid", ".mmd"),
}

VISIO_SCRIPTS = {
    "uml-use-case": "generate_visio_use_case_diagram.ps1",
    "flowchart": "generate_visio_flowchart_diagram.ps1",
    "er": "generate_visio_er_diagram.ps1",
    "functional-architecture": "generate_visio_function_architecture_diagram.ps1",
}


def select(diagram_type: str, editable_visio: bool = False) -> dict:
    """Return an existing route; reject unsupported combinations explicitly."""
    if editable_visio:
        if diagram_type not in VISIO_SCRIPTS:
            raise ValueError(f"No existe ruta Visio para {diagram_type}")
        return {"engine": "visio", "source_extension": ".json",
                "output_extension": ".vsdx", "generator": VISIO_SCRIPTS[diagram_type],
                "diagram_type": diagram_type}
    if diagram_type not in TEXT_TYPES:
        raise ValueError(f"No existe ruta textual para {diagram_type}")
    engine, extension = TEXT_TYPES[diagram_type]
    return {"engine": engine, "source_extension": extension,
            "output_extension": ".svg", "render_type": diagram_type,
            "diagram_type": diagram_type}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagram_type", choices=sorted(set(TEXT_TYPES) | set(VISIO_SCRIPTS)))
    parser.add_argument("--editable-visio", action="store_true",
                        help="Preferir VSDX editable cuando existe un generador de ese tipo")
    args = parser.parse_args()
    try:
        result = select(args.diagram_type, args.editable_visio)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
