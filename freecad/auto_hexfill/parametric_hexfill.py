# SPDX-License-Identifier: GPL-3.0-or-later

"""Parametric hex-fill sketch bound to a boundary sketch."""

from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import TYPE_CHECKING, Any, Iterable

import FreeCAD as App
import Part

if TYPE_CHECKING:
    from FreeCAD import DocumentObject

PROPERTY_GROUP = "HexFill"
ORIENTATIONS = ["Flat top", "Point up"]
ANCHOR_HORIZONTAL = ["Left", "Center", "Right"]
ANCHOR_VERTICAL = ["Bottom", "Center", "Top"]
DEFAULT_DIAMETER = 5.0
DEFAULT_GAP = 1.0
AUTOFIT_SHRINK = 0.8
AUTOFIT_STEPS = 20
MIN_DIAMETER = 0.05

_HEXFILL_CORE: ModuleType | None = None


def hexfill_core() -> ModuleType:
    """Return the HexFillCore module, importing it on first use."""
    global _HEXFILL_CORE
    if _HEXFILL_CORE is None:
        _HEXFILL_CORE = import_module("freecad.hexfill.HexFillCore")
    return _HEXFILL_CORE


def _length_mm(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(getattr(value, "Value", 0.0))


def _orientation(obj: Any) -> str:
    value = str(getattr(obj, "Orientation", ORIENTATIONS[0])).strip().lower()
    return "point" if value.startswith("point") else "flat"


def _anchor(obj: Any) -> tuple[str, str]:
    horizontal = str(getattr(obj, "AnchorH", "Center")).strip().lower()
    vertical = str(getattr(obj, "AnchorV", "Center")).strip().lower()
    return horizontal, vertical


def _clear_geometry(obj: Any) -> None:
    try:
        if int(getattr(obj, "ConstraintCount", 0)):
            obj.Constraints = []
    except Exception:
        pass

    try:
        obj.Geometry = []
        return
    except Exception:
        pass

    try:
        for index in reversed(range(int(obj.GeometryCount))):
            obj.delGeometry(index)
    except Exception:
        pass


def _add_geometries(obj: Any, geometries: list[Any]) -> None:
    if not geometries:
        return

    try:
        obj.addGeometry(geometries, False)
        return
    except Exception:
        pass

    for geometry in geometries:
        try:
            obj.addGeometry(geometry, False)
        except Exception:
            continue


def _edge_to_geometry(edge: Any) -> list[Any]:
    curve = getattr(edge, "Curve", None)
    try:
        if isinstance(curve, Part.Line):
            return [Part.LineSegment(edge.Vertexes[0].Point, edge.Vertexes[-1].Point)]
        if isinstance(curve, Part.Circle):
            return [Part.ArcOfCircle(curve, edge.FirstParameter, edge.LastParameter)]
    except Exception:
        pass

    try:
        points = edge.discretize(8)
    except Exception:
        return []

    return [Part.LineSegment(points[index], points[index + 1]) for index in range(len(points) - 1)]


def _wires_to_geometries(wires: Iterable[Any]) -> list[Any]:
    geometries: list[Any] = []
    for wire in wires:
        try:
            edges = wire.Edges
        except Exception:
            continue
        for edge in edges:
            geometries.extend(_edge_to_geometry(edge))
    return geometries


def _ensure_properties(obj: Any) -> None:
    properties = obj.PropertiesList

    if "Boundary" not in properties:
        obj.addProperty(
            "App::PropertyLink",
            "Boundary",
            PROPERTY_GROUP,
            "Sketch whose closed contour defines the fill boundary",
        )

    if "Auto" not in properties:
        obj.addProperty(
            "App::PropertyBool",
            "Auto",
            PROPERTY_GROUP,
            "Choose cell diameter and gap automatically from the boundary size",
        )
        obj.Auto = True

    if "Diameter" not in properties:
        obj.addProperty(
            "App::PropertyLength",
            "Diameter",
            PROPERTY_GROUP,
            "Circumscribed-circle diameter of one cell",
        )
        obj.Diameter = DEFAULT_DIAMETER

    if "Gap" not in properties:
        obj.addProperty(
            "App::PropertyLength",
            "Gap",
            PROPERTY_GROUP,
            "Wall-to-wall distance between neighbouring cells",
        )
        obj.Gap = DEFAULT_GAP

    if "AutoFit" not in properties:
        obj.addProperty(
            "App::PropertyBool",
            "AutoFit",
            PROPERTY_GROUP,
            "Shrink the diameter until at least one cell fits",
        )
        obj.AutoFit = True

    if "Outfill" not in properties:
        obj.addProperty(
            "App::PropertyBool",
            "Outfill",
            PROPERTY_GROUP,
            "Clip border cells exactly at the boundary",
        )
        obj.Outfill = False

    if "Orientation" not in properties:
        obj.addProperty(
            "App::PropertyEnumeration",
            "Orientation",
            PROPERTY_GROUP,
            "Hexagon orientation",
        )
        obj.Orientation = ORIENTATIONS
        obj.Orientation = ORIENTATIONS[0]

    if "AnchorH" not in properties:
        obj.addProperty(
            "App::PropertyEnumeration",
            "AnchorH",
            PROPERTY_GROUP,
            "Horizontal anchor of the lattice",
        )
        obj.AnchorH = ANCHOR_HORIZONTAL
        obj.AnchorH = "Center"

    if "AnchorV" not in properties:
        obj.addProperty(
            "App::PropertyEnumeration",
            "AnchorV",
            PROPERTY_GROUP,
            "Vertical anchor of the lattice",
        )
        obj.AnchorV = ANCHOR_VERTICAL
        obj.AnchorV = "Center"


def _mark_generated_properties_read_only(obj: Any) -> None:
    for name in ("Geometry", "Constraints"):
        try:
            obj.setEditorMode(name, 1)
        except Exception:
            continue


class ParametricHexFillProxy:
    """Object proxy for a generated, read-only hex-fill sketch."""

    def __init__(self, obj: DocumentObject) -> None:
        obj.Proxy = self
        _ensure_properties(obj)
        _mark_generated_properties_read_only(obj)
        self.sync_attachment(obj)

    def dumps(self) -> dict[str, int]:
        return {"version": 1}

    def loads(self, state: dict[str, Any]) -> None:
        return None

    def __getstate__(self) -> dict[str, int]:
        return self.dumps()

    def __setstate__(self, state: dict[str, Any]) -> None:
        return None

    def onDocumentRestored(self, obj: DocumentObject) -> None:
        _ensure_properties(obj)
        _mark_generated_properties_read_only(obj)
        self.sync_attachment(obj)
        obj.touch()

    def onChanged(self, obj: DocumentObject, prop: str) -> None:
        if prop == "Boundary":
            self.sync_attachment(obj)

    def sync_attachment(self, obj: DocumentObject) -> None:
        boundary = getattr(obj, "Boundary", None)
        support = getattr(obj, "AttachmentSupport", None)

        try:
            current = support[0][0] if support else None
        except Exception:
            current = None

        if boundary is None:
            if support:
                try:
                    obj.AttachmentSupport = []
                    obj.MapMode = "Deactivated"
                except Exception:
                    pass
            return

        map_mode = str(getattr(obj, "MapMode", "Deactivated"))
        if current is boundary and map_mode == "ObjectXY":
            return

        try:
            obj.AttachmentSupport = [(boundary, "")]
            obj.MapMode = "ObjectXY"
        except Exception as exc:
            App.Console.PrintWarning(f"auto-hexfill: could not attach to boundary ({exc})\n")

    def execute(self, obj: DocumentObject) -> bool:
        self.sync_attachment(obj)

        try:
            obj.positionBySupport()
        except Exception:
            pass

        _clear_geometry(obj)

        try:
            core = hexfill_core()
        except Exception as exc:
            App.Console.PrintError(f"auto-hexfill: HexFill addon is not available ({exc})\n")
            return False

        boundary = getattr(obj, "Boundary", None)
        if boundary is None:
            return False

        try:
            if not boundary.isDerivedFrom("Sketcher::SketchObject"):
                App.Console.PrintWarning("auto-hexfill: Boundary must be a sketch.\n")
                return False
        except Exception:
            return False

        try:
            face = core.get_boundary_face(boundary)
            if face is None:
                return False

            placement = core.get_source_placement(boundary, face)
            diameter, gap = self._parameters(obj, face, placement, core)
            if diameter <= 0 or gap < 0:
                App.Console.PrintWarning(
                    "auto-hexfill: Diameter must be positive and Gap non-negative.\n"
                )
                return False

            orientation = _orientation(obj)
            anchor = _anchor(obj)
            outfill = bool(getattr(obj, "Outfill", False))

            try:
                estimated = int(
                    core.estimate_grid_positions(face, placement, diameter, gap, orientation)
                )
            except Exception:
                estimated = 0

            max_cells = int(getattr(core, "MAX_CELLS", 20000))
            if estimated > max_cells:
                App.Console.PrintWarning(
                    "auto-hexfill: the grid is too large for this Diameter/Gap; "
                    f"{estimated} positions exceed the limit of {max_cells}.\n"
                )
                return False

            wires = core.generate_hex_wires_local(
                face,
                placement,
                diameter,
                gap,
                outfill,
                anchor,
                orientation,
            )
            _add_geometries(obj, _wires_to_geometries(wires))
        except Exception as exc:
            App.Console.PrintError(f"auto-hexfill: regeneration failed ({exc})\n")

        return False

    def _parameters(
        self,
        obj: DocumentObject,
        face: Any,
        placement: Any,
        core: ModuleType,
    ) -> tuple[float, float]:
        if bool(getattr(obj, "Auto", True)):
            diameter, gap = core.auto_parameters(face, placement)
            return float(diameter), float(gap)

        diameter = _length_mm(getattr(obj, "Diameter", DEFAULT_DIAMETER))
        gap = _length_mm(getattr(obj, "Gap", DEFAULT_GAP))

        if bool(getattr(obj, "AutoFit", True)):
            diameter = self._fit_diameter(obj, face, placement, diameter, gap, core)

        return diameter, gap

    def _fit_diameter(
        self,
        obj: DocumentObject,
        face: Any,
        placement: Any,
        diameter: float,
        gap: float,
        core: ModuleType,
    ) -> float:
        orientation = _orientation(obj)
        anchor = _anchor(obj)
        outfill = bool(getattr(obj, "Outfill", False))

        try:
            cells = core.generate_hex_cells_local(
                face, placement, diameter, gap, outfill, anchor, orientation
            )
        except Exception:
            return diameter

        if cells:
            return diameter

        current = diameter
        for _ in range(AUTOFIT_STEPS):
            current *= AUTOFIT_SHRINK
            if current < MIN_DIAMETER:
                break
            try:
                cells = core.generate_hex_cells_local(
                    face, placement, current, gap, outfill, anchor, orientation
                )
            except Exception:
                continue
            if cells:
                return current

        return diameter
