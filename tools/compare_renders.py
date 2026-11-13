import hashlib
import sys
from pathlib import Path

import pymupdf

new_dir, old_dir = Path(sys.argv[1]), Path(sys.argv[2])
bad = 0
for new in sorted(new_dir.glob("*.pdf")):
    digests = []
    for path in (new, old_dir / new.name):
        pix = pymupdf.open(path)[0].get_pixmap(dpi=100)
        digests.append(hashlib.sha256(pix.samples).hexdigest())
    same = digests[0] == digests[1]
    bad += not same
    print("same" if same else "DIFF", new.name)
sys.exit(1 if bad else 0)
