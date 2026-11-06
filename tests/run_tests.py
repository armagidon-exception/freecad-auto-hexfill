# SPDX-License-Identifier: GPL-3.0-or-later

"""Headless tests for the parametric hex-fill sketch."""

from __future__ import annotations

import importlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_freecad = importlib.import_module("freecad")
ADDON_PACKAGE = ROOT / "freecad"
if str(ADDON_PACKAGE) not in _freecad.__path__:
    _freecad.__path__.append(str(ADDON_PACKAGE))

App = importlib.import_module("FreeCAD")
Part = importlib.import_module("Part")
Sketcher = importlib.import_module("Sketcher")
ParametricHexFillProxy = importlib.import_module(
    "freecad.auto_hexfill.parametric_hexfill"
).ParametricHexFillProxy
HexFillViewProvider = importlib.import_module(
    "freecad.auto_hexfill.parametric_hexfill_vp"
).HexFillViewProvider


class ParametricHexFillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = App.newDocument("AutoHexFillTest")
        self.boundary = self._make_boundary(self.doc, 20.0)
        self.generated = self._make_generated(self.doc, self.boundary)

    def tearDown(self) -> None:
        try:
            App.closeDocument(self.doc.Name)
        except Exception:
            pass

    @staticmethod
    def _make_boundary(doc: App.Document, radius: float) -> App.DocumentObject:
        sketch = doc.addObject("Sketcher::SketchObject", "Boundary")
        sketch.addGeometry(
            Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), radius),
            False,
        )
        sketch.addConstraint(Sketcher.Constraint("Radius", 0, radius))
        return sketch

    @staticmethod
    def _make_generated(
        doc: App.Document,
        boundary: App.DocumentObject,
    ) -> App.DocumentObject:
        obj = doc.addObject("Sketcher::SketchObjectPython", "HexFill")
        proxy = ParametricHexFillProxy(obj)
        obj.Boundary = boundary
        obj.Auto = False
        obj.Diameter = 5.0
        obj.Gap = 1.0
        proxy.sync_attachment(obj)
        doc.recompute()
        return obj

    def test_generates_geometry(self) -> None:
        self.assertGreater(self.generated.GeometryCount, 0)
        self.assertGreater(len(self.generated.Shape.Edges), 0)

    def test_generated_properties_are_read_only(self) -> None:
        self.assertEqual(self.generated.getEditorMode("Geometry"), ["ReadOnly"])
        self.assertEqual(self.generated.getEditorMode("Constraints"), ["ReadOnly"])

    def test_regenerates_when_boundary_changes(self) -> None:
        before = self.generated.GeometryCount
        self.boundary.setDatum(0, App.Units.Quantity("40 mm"))
        self.doc.recompute()
        self.assertNotEqual(self.generated.GeometryCount, before)
        self.assertGreater(self.generated.GeometryCount, 0)

    def test_regenerates_when_diameter_changes(self) -> None:
        before = self.generated.GeometryCount
        self.generated.Diameter = 8.0
        self.doc.recompute()
        self.assertNotEqual(self.generated.GeometryCount, before)
        self.assertGreater(self.generated.GeometryCount, 0)

    def test_auto_mode_generates_geometry(self) -> None:
        self.generated.Auto = True
        self.doc.recompute()
        self.assertGreater(self.generated.GeometryCount, 0)

    def test_missing_boundary_clears_geometry(self) -> None:
        self.generated.Boundary = None
        self.doc.recompute()
        self.assertEqual(self.generated.GeometryCount, 0)

    def test_view_provider_blocks_editing(self) -> None:
        view_object = type(
            "ViewObject",
            (),
            {"Proxy": None, "Object": self.generated},
        )()
        provider = HexFillViewProvider(view_object)
        self.assertIs(view_object.Proxy, provider)
        self.assertFalse(provider.setEdit(view_object, 0))
        self.assertTrue(provider.doubleClicked(view_object))

    def test_save_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auto_hexfill.FCStd"
            before = self.generated.GeometryCount
            self.doc.saveAs(str(path))
            App.closeDocument(self.doc.Name)
            self.doc = App.openDocument(str(path))
            self.generated = self.doc.getObject("HexFill")
            self.assertIsNotNone(self.generated)
            self.assertIsNotNone(self.generated.Proxy)
            self.assertEqual(self.generated.GeometryCount, before)
            self.doc.recompute()
            self.assertGreater(self.generated.GeometryCount, 0)

    def test_generated_sketch_can_be_padded(self) -> None:
        doc = App.newDocument("AutoHexFillPadTest")
        try:
            body = doc.addObject("PartDesign::Body", "Body")
            boundary = self._make_boundary(doc, 20.0)
            body.addObject(boundary)

            obj = doc.addObject("Sketcher::SketchObjectPython", "HexFill")
            proxy = ParametricHexFillProxy(obj)
            obj.Boundary = boundary
            obj.Auto = False
            obj.Diameter = 8.0
            obj.Gap = 1.5
            proxy.sync_attachment(obj)
            body.addObject(obj)

            pad = body.newObject("PartDesign::Pad", "Pad")
            pad.Profile = obj
            pad.Length = 5.0
            doc.recompute()

            self.assertGreater(len(obj.Shape.Edges), 0)
            self.assertGreater(len(pad.Shape.Solids), 0)
        finally:
            App.closeDocument(doc.Name)


def _run() -> None:
    suite = unittest.TestLoader().loadTestsFromTestCase(ParametricHexFillTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


_run()
