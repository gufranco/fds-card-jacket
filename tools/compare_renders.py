import hashlib
import sys
from pathlib import Path

import pymupdf


def pdfs(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*.pdf")}


def digest(path: Path) -> str:
    pix = pymupdf.open(path)[0].get_pixmap(dpi=100)
    return hashlib.sha256(pix.samples).hexdigest()


new_dir, old_dir = Path(sys.argv[1]), Path(sys.argv[2])
new_set, old_set = pdfs(new_dir), pdfs(old_dir)
bad = 0
for missing in sorted(new_set - old_set):
    bad += 1
    print("ONLY-NEW", missing)
for name in sorted(new_set & old_set):
    same = digest(new_dir / name) == digest(old_dir / name)
    bad += not same
    print("same" if same else "DIFF", name)
sys.exit(1 if bad else 0)
