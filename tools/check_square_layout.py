import itertools
import sys

sys.path.insert(0, sys.argv[1])

import fds_kit as k
from shapely.geometry import LineString, Polygon

MIN_MARGIN_MM = 5.0
failures = 0
for which in ("square", "square-standard"):
    home, _, _ = k.sheet_sets(which)
    for key, (sheet, page) in home.items():
        placed = [Polygon([p.apply(pt) for pt in item.outline]) for item, p in sheet]
        diagonal = sum(
            1
            for item, _ in sheet
            for a, b in k.edges(item.outline)
            if a[0] != b[0] and a[1] != b[1]
        )
        overlap = max(
            (a.intersection(b).area for a, b in itertools.combinations(placed, 2)),
            default=0.0,
        )
        gap = min(
            (a.distance(b) for a, b in itertools.combinations(placed, 2)),
            default=float("inf"),
        )
        x0 = min(poly.bounds[0] for poly in placed)
        y0 = min(poly.bounds[1] for poly in placed)
        x1 = max(poly.bounds[2] for poly in placed)
        y1 = max(poly.bounds[3] for poly in placed)
        margin = min(x0, y0, page[0] - x1, page[1] - 10 - y1)
        valid = all(poly.is_valid for poly in placed)
        stray = sum(
            1
            for item, _ in sheet
            for a, b in item.creases
            if not Polygon(item.outline).buffer(0.01).contains(LineString([a, b]))
        )
        ok = (
            diagonal == 0
            and overlap == 0
            and margin >= MIN_MARGIN_MM
            and valid
            and stray == 0
        )
        failures += not ok
        print(
            f"{'ok  ' if ok else 'FAIL'} {key}: diagonal edges {diagonal}, overlap {overlap:.2f} mm2, "
            f"min gap {gap:.1f} mm, page margin {margin:.1f} mm, valid {valid}, creases outside {stray}"
        )
sys.exit(1 if failures else 0)
