# SPDX-License-Identifier: GPL-3.0-or-later

"""View provider for the generated hex-fill sketch."""

from __future__ import annotations

from typing import Any

from .resources import Resources


class HexFillViewProvider:
    """Read-only view provider for a parametric hex-fill sketch."""

    def __init__(self, vobj: Any) -> None:
        vobj.Proxy = self

    def getIcon(self) -> str:
        return Resources.icon("auto_hexfill.svg")

    def setEdit(self, vobj: Any, mode: int) -> bool:
        return False

    def doubleClicked(self, vobj: Any) -> bool:
        return True

    def attach(self, vobj: Any) -> None:
        self.Object = vobj.Object

    def dumps(self) -> dict[str, Any]:
        return {}

    def loads(self, state: dict[str, Any]) -> None:
        return None

    def __getstate__(self) -> dict[str, Any]:
        return self.dumps()

    def __setstate__(self, state: dict[str, Any]) -> None:
        return None
