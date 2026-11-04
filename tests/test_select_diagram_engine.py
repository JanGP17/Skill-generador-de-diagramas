import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "select_diagram_engine.py"
spec = importlib.util.spec_from_file_location("select_diagram_engine", SCRIPT)
router = importlib.util.module_from_spec(spec)
spec.loader.exec_module(router)


class EngineSelectionTests(unittest.TestCase):
    def test_uml_class_uses_plantuml(self):
        self.assertEqual(router.select("uml-class")["engine"], "plantuml")

    def test_flow_and_er_use_mermaid(self):
        for kind in ("flowchart", "er"):
            with self.subTest(kind=kind):
                self.assertEqual(router.select(kind)["engine"], "mermaid")

    def test_editable_er_uses_existing_visio_generator(self):
        result = router.select("er", editable_visio=True)
        self.assertEqual(result["generator"], "generate_visio_er_diagram.ps1")
        self.assertEqual(result["output_extension"], ".vsdx")

    def test_unsupported_visio_route_fails(self):
        with self.assertRaises(ValueError):
            router.select("uml-sequence", editable_visio=True)

    def test_every_routed_generator_exists(self):
        for generator in router.VISIO_SCRIPTS.values():
            with self.subTest(generator=generator):
                self.assertTrue((SCRIPT.parent / generator).is_file())


if __name__ == "__main__":
    unittest.main()
