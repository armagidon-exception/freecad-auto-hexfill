<!-- SPDX-License-Identifier: GPL-3.0-or-later -->

# auto-hexfill

Creates a read-only parametric sketch filled with a hexagonal grid from a boundary sketch.

## What

Select a sketch with a closed contour, then create a parametric hex-fill sketch. The generated sketch stays linked to the boundary and regenerates when the boundary changes.

Parameters such as cell diameter, gap, orientation, anchor, auto sizing, and boundary clipping are available in the Data tab.

## Why

This keeps a hex-fill pattern in sync with its design boundary without rebuilding it manually after every change.
