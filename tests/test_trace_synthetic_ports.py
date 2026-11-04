import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "diagram_quality.py"
spec = importlib.util.spec_from_file_location("diagram_quality", SCRIPT)
quality = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = quality
spec.loader.exec_module(quality)


class SyntheticPortTraceTests(unittest.TestCase):
    def test_traced_continuity_port_is_not_outside_view(self):
        source = [{"path": "source.py", "start_line": 1, "end_line": 1}]
        manifest = {
            "project_revision": "test", "scope": "test", "omissions": [],
            "elements": [
                {"id": "node", "name": "Node", "type": "process", "status": "implementado", "sources": source},
                {"id": "port", "name": "C01", "type": "continuity_ref", "status": "documentado", "sources": source},
            ],
            "relations": [
                {"id": "edge", "name": "node → port", "type": "flow", "status": "implementado",
                 "from": "node", "to": "port", "label": "", "sources": source},
            ],
        }
        model = {"nodes": [{"id": "node"}, {"id": "port", "synthetic": True}],
                 "edges": [{"from": "node", "to": "port", "label": ""}]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = quality.validate_trace(path, None, model)
        codes = {item["code"] for item in result["issues"]}
        self.assertNotIn("trace_elements_not_in_model", codes)
        self.assertNotIn("relation_endpoint_missing", codes)


if __name__ == "__main__":
    unittest.main()
