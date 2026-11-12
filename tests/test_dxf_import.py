"""Riktade regressionstester för DXF-import och roundtrip (ingen GUI-interaktion)."""
import unittest

from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

from cadist_2d import BlockDef, Canvas, Insert, Line, Polyline, builtin_blocks, parse_dxf


class DxfImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_line_roundtrip_uses_endpoint_codes(self):
        canvas = Canvas()
        canvas.entities = [Line(QPointF(2, 3), QPointF(17, 29))]
        result = parse_dxf(canvas.to_dxf(), builtin_blocks())
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Line)
        self.assertEqual((result[0].a.x(), result[0].a.y()), (2, 3))
        self.assertEqual((result[0].b.x(), result[0].b.y()), (17, 29))

    def test_block_definition_does_not_become_model_entity(self):
        canvas = Canvas()
        block = BlockDef("MITT_BLOCK", [Line(QPointF(0, 0), QPointF(12, 7))])
        canvas.entities = [Insert(block, QPointF(100, 200))]
        blocks = builtin_blocks()
        entities = parse_dxf(canvas.to_dxf(), blocks)
        self.assertEqual(len(entities), 1)
        self.assertIsInstance(entities[0], Insert)
        self.assertEqual(entities[0].definition.name, "MITT_BLOCK")
        self.assertEqual(len(entities[0].definition.entities), 1)
        self.assertEqual((entities[0].definition.entities[0].b.x(),
                          entities[0].definition.entities[0].b.y()), (12, 7))
        self.assertIn("MITT_BLOCK", [b.name for b in blocks])

    def test_nonrectangular_closed_polyline_is_not_rectangle(self):
        canvas = Canvas()
        canvas.entities = [Polyline([QPointF(0, 0), QPointF(8, 1),
                                     QPointF(9, 5), QPointF(1, 7)], closed=True)]
        result = parse_dxf(canvas.to_dxf(), builtin_blocks())
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Polyline)
        self.assertTrue(result[0].closed)

    def test_block_base_point_is_applied(self):
        records = [
            (0, "SECTION"), (2, "BLOCKS"),
            (0, "BLOCK"), (2, "B1"), (10, 10), (20, 20),
            (0, "LINE"), (10, 10), (20, 20), (11, 15), (21, 20),
            (0, "ENDBLK"), (0, "ENDSEC"),
            (0, "SECTION"), (2, "ENTITIES"),
            (0, "INSERT"), (2, "B1"), (10, 100), (20, 100),
            (0, "ENDSEC"), (0, "EOF"),
        ]
        data = "\n".join(str(v) for pair in records for v in pair) + "\n"
        entities = parse_dxf(data, builtin_blocks())
        self.assertEqual(len(entities), 1)
        self.assertIsInstance(entities[0], Insert)
        self.assertEqual(entities[0].definition.entities[0].a.x(), 0)
        self.assertEqual(entities[0].definition.entities[0].a.y(), 0)
        self.assertEqual(entities[0].definition.entities[0].b.x(), 5)


if __name__ == "__main__":
    unittest.main()
