import sys

import pymupdf

page = pymupdf.open(sys.argv[1])[0]
curves = sum(
    1
    for d in page.get_drawings()
    if d.get("width") and abs(d["width"] - 0.3) < 0.01
    for it in d["items"]
    if it[0] == "c"
)
print(sys.argv[1].rsplit("/", 1)[-1], "curve segments in cut and fold lines:", curves)
