# auto-hexfill

Creates a read-only parametric sketch filled with a hexagonal grid from a boundary sketch.

The generated sketch keeps a live link to its boundary sketch. When the boundary changes and the document is recomputed, the grid is regenerated automatically.

## Requirements

- FreeCAD 1.1 or newer.
- The [HexFill](https://github.com/Clientik/FreeCAD-HexFill) addon.

## Usage

1. Draw a sketch containing at least one closed contour.
2. Select that sketch in the Sketcher workbench.
3. Run **Create parametric HexFill** from the default Sketcher toolbar or the **Sketch** menu.
4. Select the generated sketch and adjust `Auto`, `Diameter`, `Gap`, `Outfill`, `Orientation`, or the anchor in the Data tab.
5. Recompute the document after changing the boundary.

The generated sketch cannot be edited in Sketcher. Its geometry is always rebuilt from the boundary and the properties above.

## Maintainer

me
me@foobar.com
