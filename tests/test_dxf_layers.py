"""Riktade DXF-lagertester – inga GUI-dialoger."""
import unittest

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from cadist_2d import Canvas, Layer, Line, parse_dxf, parse_dxf_layers


class DxfLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_layer_roundtrip_color_visibility_lock(self):
        canvas = Canvas()
        canvas.layers = [
            Layer("0", None, True),
            Layer("EL", "#ff0000", True, True),
            Layer("DOLD", "#0000ff", False, False),
        ]
        a = Line(QPointF(0, 0), QPointF(8, 0))
        a.layer = "EL"
        b = Line(QPointF(0, 2), QPointF(8, 2))
        b.layer = "DOLD"
        canvas.entities = [a, b]
        data = canvas.to_dxf()
        entities = parse_dxf(data, [])
        layers = parse_dxf_layers(data, entities)
        by_name = {layer.name: layer for layer in layers}
        self.assertEqual(set(by_name), {"0", "EL", "DOLD"})
        self.assertEqual((by_name["EL"].color, by_name["EL"].visible,
                          by_name["EL"].locked), ("#ff0000", True, True))
        self.assertEqual((by_name["DOLD"].color, by_name["DOLD"].visible,
                          by_name["DOLD"].locked), ("#0000ff", False, False))
        self.assertEqual([e.layer for e in entities], ["EL", "DOLD"])

    def test_unlisted_entity_layer_is_created(self):
        text = "\n".join([
            "0", "SECTION", "2", "ENTITIES",
            "0", "LINE", "8", "EXTERNT",
            "10", "0", "20", "0", "11", "5", "21", "5",
            "0", "ENDSEC", "0", "EOF", ""
        ])
        entities = parse_dxf(text, [])
        layers = parse_dxf_layers(text, entities)
        self.assertEqual([layer.name for layer in layers], ["0", "EXTERNT"])

    def test_frozen_and_negative_color_are_hidden(self):
        text = "\n".join([
            "0", "SECTION", "2", "TABLES",
            "0", "TABLE", "2", "LAYER",
            "0", "LAYER", "2", "FROST", "70", "1", "62", "3",
            "0", "LAYER", "2", "AV", "70", "0", "62", "-1",
            "0", "ENDTAB", "0", "ENDSEC", "0", "EOF", ""
        ])
        layers = {layer.name: layer for layer in parse_dxf_layers(text)}
        self.assertFalse(layers["FROST"].visible)
        self.assertFalse(layers["AV"].visible)

    def test_layer_names_from_blocks_do_not_become_model_layers(self):
        text = "\n".join([
            "0", "SECTION", "2", "BLOCKS",
            "0", "BLOCK", "2", "TEST", "10", "0", "20", "0",
            "0", "LINE", "8", "BARA_BLOCK",
            "10", "0", "20", "0", "11", "1", "21", "1",
            "0", "ENDBLK", "0", "ENDSEC",
            "0", "SECTION", "2", "ENTITIES",
            "0", "ENDSEC", "0", "EOF", ""
        ])
        self.assertEqual([l.name for l in parse_dxf_layers(text)], ["0"])


if __name__ == "__main__":
    unittest.main()
