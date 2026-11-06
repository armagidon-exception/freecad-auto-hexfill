# SPDX-License-Identifier: GPL-3.0-or-later

"""Command that creates a parametric hex-fill sketch from a boundary sketch."""

from __future__ import annotations

from typing import Any, ClassVar

import FreeCAD as App
import FreeCADGui as Gui

from ..parametric_hexfill import ParametricHexFillProxy
from ..parametric_hexfill_vp import HexFillViewProvider
from ..resources import Resources

translate = App.Qt.translate


def _is_boundary_sketch(obj: Any) -> bool:
    if obj is None or not obj.isDerivedFrom("Sketcher::SketchObject"):
        return False
    if isinstance(getattr(obj, "Proxy", None), ParametricHexFillProxy):
        return False

    shape = getattr(obj, "Shape", None)
    if shape is None:
        return False

    try:
        return bool(shape.Faces) or any(wire.isClosed() for wire in shape.Wires)
    except Exception:
        return False


def _add_to_container(boundary: Any, obj: Any) -> None:
    try:
        container = boundary.getParentGeoFeatureGroup()
    except Exception:
        container = None

    if container is None:
        return

    try:
        container.addObject(obj)
    except Exception as exc:
        App.Console.PrintWarning(
            f"auto-hexfill: could not add the sketch to its container ({exc})\n"
        )


class ParametricHexFillCommand:
    """Create a read-only hex-fill sketch bound to the selected sketch."""

    Name: ClassVar[str] = "auto_hexfill_ParametricHexFill"

    def GetResources(self) -> dict[str, str]:
        return {
            "Pixmap": Resources.icon("command_hexfill.svg"),
            "MenuText": translate("auto_hexfill", "Create parametric HexFill"),
            "ToolTip": translate(
                "auto_hexfill",
                "Create a read-only hex-fill sketch bound to the selected sketch",
            ),
        }

    def IsActive(self) -> bool:
        if App.ActiveDocument is None:
            return False
        selection = Gui.Selection.getSelection()
        return len(selection) == 1 and _is_boundary_sketch(selection[0])

    def Activated(self) -> None:
        doc = App.ActiveDocument
        selection = Gui.Selection.getSelection()
        if doc is None or len(selection) != 1:
            return

        boundary = selection[0]
        if not _is_boundary_sketch(boundary):
            return

        doc.openTransaction("Create parametric HexFill")
        try:
            obj = doc.addObject("Sketcher::SketchObjectPython", "HexFill")
            obj.Label = f"HexFill {boundary.Label}"
            proxy = ParametricHexFillProxy(obj)
            obj.Boundary = boundary
            proxy.sync_attachment(obj)
            _add_to_container(boundary, obj)
            if App.GuiUp and getattr(obj, "ViewObject", None) is not None:
                HexFillViewProvider(obj.ViewObject)
            doc.commitTransaction()
        except Exception as exc:
            doc.abortTransaction()
            App.Console.PrintError(f"auto-hexfill: could not create the sketch ({exc})\n")
            return

        doc.recompute()

    @classmethod
    def Install(cls) -> None:
        if App.GuiUp:
            Gui.addCommand(cls.Name, cls())
