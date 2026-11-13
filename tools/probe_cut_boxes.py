import sys

import pymupdf

mm = 25.4 / 72
page = pymupdf.open(sys.argv[1])[0]
cuts = sorted(
    (
        d["rect"]
        for d in page.get_drawings()
        if (d.get("dashes") or "").startswith("[ .57")
    ),
    key=lambda r: r.y0,
)
for r in cuts:
    print(
        f"cut {r.x0 * mm:.3f},{r.y0 * mm:.3f} - {r.x1 * mm:.3f},{r.y1 * mm:.3f}  {r.width * mm:.2f}x{r.height * mm:.2f}"
    )
print("page", page.rect.width * mm, page.rect.height * mm)
