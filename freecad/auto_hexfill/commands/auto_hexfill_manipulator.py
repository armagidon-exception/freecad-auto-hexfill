# SPDX-License-Identifier: GPL-3.0-or-later

"""Sketcher workbench integration for the parametric hex-fill command."""

from __future__ import annotations

from contextlib import suppress
from typing import ClassVar

import FreeCAD as App
import FreeCADGui as Gui

from .parametric_hexfill_command import ParametricHexFillCommand


class WorkbenchManipulator:
    """Add the parametric hex-fill command to the Sketcher workbench."""

    TARGET_WB_ALIASES: ClassVar[tuple[str, ...]] = (
        "SketcherWorkbench",
        "Sketcher",
    )
    _instance: ClassVar[WorkbenchManipulator | None] = None

    def _wanted(self) -> bool:
        try:
            active = Gui.activeWorkbench()
            for name, workbench in Gui.listWorkbenches().items():
                if workbench is active:
                    return name in self.TARGET_WB_ALIASES
        except Exception:
            pass
        return False

    def modifyToolBars(self) -> list[dict[str, str]]:
        if not self._wanted():
            return []
        return [{"append": ParametricHexFillCommand.Name, "toolBar": "Sketcher"}]

    def modifyMenuBar(self) -> list[dict[str, str]]:
        if not self._wanted():
            return []
        return [
            {
                "insert": ParametricHexFillCommand.Name,
                "menuItem": "Sketcher_MirrorSketch",
                "after": "1",
            }
        ]

    @classmethod
    def install(cls) -> None:
        if App.GuiUp and cls._instance is None:
            cls._instance = cls()
            Gui.addWorkbenchManipulator(cls._instance)
            with suppress(Exception):
                Gui.activeWorkbench().reloadActive()

    @classmethod
    def uninstall(cls) -> None:
        if App.GuiUp and cls._instance is not None:
            Gui.removeWorkbenchManipulator(cls._instance)
            cls._instance = None
            with suppress(Exception):
                Gui.activeWorkbench().reloadActive()
