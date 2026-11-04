import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "layout_flowchart_diagram.py"
spec = importlib.util.spec_from_file_location("layout_flowchart_diagram", SCRIPT)
layout = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = layout
spec.loader.exec_module(layout)


class LabelPlacementTests(unittest.TestCase):
    def test_routed_label_avoids_nodes(self):
        diagram = {
            "diagramType": "flowchart",
            "nodes": [
                {"id": "start", "type": "decision", "text": "¿Válido?"},
                {"id": "yes", "type": "process", "text": "Registrar"},
                {"id": "end", "type": "end", "text": "Terminar"},
            ],
            "edges": [
                {"from": "start", "to": "yes", "label": "Sí"},
                {"from": "yes", "to": "end", "label": "Registro completo"},
            ],
        }
        layout.layout_flowchart(diagram)
        nodes = layout.build_boxes(diagram["nodes"])
        for edge in diagram["edges"]:
            with self.subTest(edge=edge["label"]):
                pos = edge["labelPosition"]
                label = layout.Box("label", pos["x"], pos["y"], pos["width"], pos["height"])
                self.assertFalse(any(layout.boxes_overlap(label, box) for box in nodes.values()))


if __name__ == "__main__":
    unittest.main()
