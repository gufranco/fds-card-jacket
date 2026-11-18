import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

MM = 72 / 25.4
A4 = (210.0, 297.0)
A4_LANDSCAPE = (297.0, 210.0)
BLACK = (0, 0, 0, 1)
WHITE = (0, 0, 0, 0)
LINE_GRAY = (0, 0, 0, 0.38)
HOME_LINE_WIDTH = 0.3
HOME_HALO_WIDTH = 1.2
HOME_FOLD_DASHES = "[1.5 13.5] 0"
NOTCH_GUIDE_GRAY = (0, 0, 0, 0.2)
NOTCH_GUIDE_WIDTH = 0.2
NOTCH_GUIDE_MM = 1.0
CARD_THICKNESS_MM = 3.0
TOLERANCE_MM = 1.0
GUSSET = CARD_THICKNESS_MM + TOLERANCE_MM
SQUARE_RELIEF_MM = 2.0
SQUARE_JACKET_NOTCH_INSET_MM = 11.0
ENVELOPE_GLUE_MM = 25.0
ENVELOPE_FLAP_OFFSET_MM = 10.0
LOCK_FLAP_MM = 3.0
LOCK_TAB_HEIGHTS_MM = (20.0, 47.5, 75.0)
TAB_HEAD_MM = 10.0
TAB_NECK_MM = 6.0
TAB_NECK_LENGTH_MM = 2.0
TAB_HEAD_LENGTH_MM = 6.0
TAB_SLIT_MM = TAB_HEAD_MM - 2.0
ITEM_FOLDERS = {
    "Card-Jacket": "card-jacket",
    "Disk-Envelope": "envelope",
    "Disk-Cover": "cover",
}
WIDE_GLUE = {"jacket": 15.0}
STANDARD_GLUE = {"jacket": 11.5}
NEST_GAP_MM = 6.0
COVER_GAP_MM = (4.0, 0.0)
COLUMN_MM = 0.25
LATIN = "FB"
JAPANESE = "HM"
JAPANESE_FONT_FILE = "/System/Library/Fonts/ヒラギノ丸ゴ ProN W4.ttc"
RUBY_SCALE = 0.45
TEMPLATE_ORIGIN_MM = (6.195, 6.485)
TEMPLATE_CLIPS_MM = {
    "warning": (92.0, 23.8, 166.0, 71.0),
    "logo": (141.6, 63.3, 163.9, 68.8),
    "jacket_front": (13.5, 37.0, 81.5, 72.5),
}
CMYK_OPERATOR_PATTERN = rb"((?:[-\d.]+\s+){3}[-\d.]+)\s+(scn|SCN)\b"
FONTS = {
    LATIN: pymupdf.Font("figbo"),
    JAPANESE: pymupdf.Font(fontfile=JAPANESE_FONT_FILE),
}

Point = tuple[float, float]
Polygon = tuple[Point, ...]
Segment = tuple[str, str]


@dataclass(frozen=True)
class Block:
    lines: tuple[tuple[Segment, ...], ...]
    size: float
    boxed: bool = False
    center: bool = True


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point
    width: float = 0.4


@dataclass(frozen=True)
class Clip:
    source: str
    center: Point
    rotate: int = 0
    scale: float = 1.0


Element = Line | Clip


@dataclass(frozen=True)
class Item:
    outline: Polygon
    creases: tuple[tuple[Point, Point], ...]
    art: tuple[Element, ...]
    notch_guides: tuple[tuple[Point, Point], ...] = field(default_factory=tuple)
    slits: tuple[tuple[Point, Point], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Placement:
    offset: Point
    flip: bool
    bbox: tuple[float, float, float, float]

    def apply(self, p: Point) -> Point:
        x0, y0, x1, y1 = self.bbox
        x, y = (x0 + x1 - p[0], y0 + y1 - p[1]) if self.flip else p
        return self.offset[0] + x - x0, self.offset[1] + y - y0


@dataclass(frozen=True)
class Context:
    page: pymupdf.Page
    source: pymupdf.Document
    pages: dict[str, tuple[int, pymupdf.Rect]]
    layers: dict[str, int]


def seg(text: str, ruby: str = "") -> Segment:
    return text, ruby


BLOCKS: dict[str, Block] = {
    "envelope_title": Block(
        ((seg("カード"), seg("保管袋", "ほかんぶくろ")),), 14, boxed=True
    ),
    "envelope_notice": Block(
        (
            (
                seg("※"),
                seg("使用後", "しようご"),
                seg("は"),
                seg("必", "かなら"),
                seg("ずカードをこのふくろに"),
            ),
            (seg("もどしてください。"),),
        ),
        8.6,
        center=False,
    ),
    "envelope_flap": Block(
        (
            (
                seg("※ふたはカードの"),
                seg("上", "うえ"),
                seg("から、ふくろの"),
                seg("内側", "うちがわ"),
                seg("に"),
            ),
            (seg("差", "さ"), seg("しこんでください。")),
        ),
        7.2,
        center=False,
    ),
    "cover_title": Block(((seg("ディスクカード"),),), 15, boxed=True),
    "cover_name": Block(((seg("ソフト"), seg("名", "めい")),), 7.5, center=False),
}


def polygon_bbox(points: Polygon) -> tuple[float, float, float, float]:
    return (
        min(p[0] for p in points),
        min(p[1] for p in points),
        max(p[0] for p in points),
        max(p[1] for p in points),
    )


def edges(points: Polygon) -> list[tuple[Point, Point]]:
    return list(zip(points, points[1:] + points[:1], strict=True))


def column(points: Polygon, x: float) -> list[float]:
    return [
        a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
        for a, b in edges(points)
        if a[0] != b[0] and min(a[0], b[0]) <= x <= max(a[0], b[0])
    ]


@dataclass(frozen=True)
class EnvelopeFrame:
    width: float
    tuck: float
    bottom: float
    opening: float
    shoulder: float
    flap: float


def envelope_frame(flap_width: float) -> EnvelopeFrame:
    w, h, tip = 80.0, 95.0, 31.0
    tuck = tip + GUSSET
    bottom = tuck + h + GUSSET
    return EnvelopeFrame(
        width=w,
        tuck=tuck,
        bottom=bottom,
        opening=bottom + h,
        shoulder=bottom + ENVELOPE_FLAP_OFFSET_MM,
        flap=GUSSET + flap_width,
    )


def envelope_outline(f: EnvelopeFrame) -> Polygon:
    return (
        (0, 0),
        (f.width, 0),
        (f.width, f.shoulder),
        (f.width + f.flap, f.shoulder),
        (f.width + f.flap, f.opening),
        (-f.flap, f.opening),
        (-f.flap, f.shoulder),
        (0, f.shoulder),
    )


def envelope_creases(f: EnvelopeFrame) -> tuple[tuple[Point, Point], ...]:
    rows = (f.tuck - GUSSET, f.tuck, f.bottom - GUSSET, f.bottom)
    columns = (-GUSSET, 0.0, f.width, f.width + GUSSET)
    return (
        *(((0.0, y), (f.width, y)) for y in rows),
        *(((x, f.shoulder), (x, f.opening)) for x in columns),
    )


def envelope_guides(f: EnvelopeFrame) -> tuple[tuple[Point, Point], ...]:
    side = tuple(
        guide
        for y in (f.tuck - GUSSET / 2, f.bottom - GUSSET / 2)
        for guide in (
            ((0.0, y), (NOTCH_GUIDE_MM, y)),
            ((f.width, y), (f.width - NOTCH_GUIDE_MM, y)),
        )
    )
    opening = tuple(
        ((x, f.opening), (x, f.opening - NOTCH_GUIDE_MM))
        for x in (-GUSSET / 2, f.width + GUSSET / 2)
    )
    return side + opening


def envelope_art(f: EnvelopeFrame) -> tuple[Element, ...]:
    w = f.width
    return (
        Clip("envelope_title", (w / 2, f.opening - 30), 180),
        Clip("envelope_notice", (w / 2, f.opening - 52), 180),
        Clip("logo", (w / 2, f.bottom + 12), 180),
        Clip("warning", (w / 2, f.tuck + 30)),
        Clip("envelope_flap", (w / 2, f.tuck + 70)),
    )


def envelope() -> Item:
    f = envelope_frame(ENVELOPE_GLUE_MM)
    return Item(
        envelope_outline(f),
        envelope_creases(f),
        envelope_art(f),
        envelope_guides(f),
    )


def lock_tab(edge_x: float, center: float, outward: float) -> tuple[Point, ...]:
    neck, head = TAB_NECK_MM / 2, TAB_HEAD_MM / 2
    base = edge_x + outward * TAB_NECK_LENGTH_MM
    tip = base + outward * TAB_HEAD_LENGTH_MM
    return (
        (edge_x, center - neck),
        (base, center - neck),
        (base, center - head),
        (tip, center - head),
        (tip, center + head),
        (base, center + head),
        (base, center + neck),
        (edge_x, center + neck),
    )


def envelope_lock_outline(f: EnvelopeFrame) -> Polygon:
    centers = sorted(f.bottom + h for h in LOCK_TAB_HEIGHTS_MM)
    right = tuple(p for c in centers for p in lock_tab(f.width + f.flap, c, 1.0))
    left = tuple(reversed([p for c in centers for p in lock_tab(-f.flap, c, -1.0)]))
    return (
        (0, 0),
        (f.width, 0),
        (f.width, f.shoulder),
        (f.width + f.flap, f.shoulder),
        *right,
        (f.width + f.flap, f.opening),
        (-f.flap, f.opening),
        *left,
        (-f.flap, f.shoulder),
        (0, f.shoulder),
    )


def envelope_slits(f: EnvelopeFrame) -> tuple[tuple[Point, Point], ...]:
    inset = f.flap - GUSSET + TAB_NECK_LENGTH_MM / 2
    half = TAB_SLIT_MM / 2
    return tuple(
        ((x, back_y - half), (x, back_y + half))
        for back_y in (f.bottom - GUSSET - h for h in LOCK_TAB_HEIGHTS_MM)
        for x in (inset, f.width - inset)
    )


def envelope_lock() -> Item:
    f = envelope_frame(LOCK_FLAP_MM)
    return Item(
        envelope_lock_outline(f),
        envelope_creases(f),
        envelope_art(f),
        envelope_guides(f),
        envelope_slits(f),
    )


def cover() -> Item:
    w, front, spine_h, back = 80.0, 81.0, 6.0, 57.0
    total = front + spine_h + back
    outline: Polygon = ((0, 0), (w, 0), (w, total), (0, total))
    creases = (((0, front), (w, front)), ((0, front + spine_h), (w, front + spine_h)))
    art = (
        Clip("cover_title", (w / 2, 20)),
        Clip("cover_name", (17, 44)),
        Line((27, 46.5), (w - 8, 46.5), 0.5),
        Clip("logo", (w / 2, 70)),
        Clip("warning", (w / 2, front + spine_h + back / 2), 180),
    )
    mid = front + spine_h / 2
    guides = (((0, mid), (NOTCH_GUIDE_MM, mid)), ((w, mid), (w - NOTCH_GUIDE_MM, mid)))
    return Item(outline, creases, art, notch_guides=guides)


def jacket_square(glue: float) -> Item:
    left, fold_a, fold_b, top, bottom = 6.195, 86.195, 168.195, 21.985, 100.985
    flap_top, notch_y, side_y = 6.485, 77.485, 89.485
    right = fold_b + GUSSET + glue
    r = SQUARE_RELIEF_MM
    inset = GUSSET + r
    notch_a = fold_a + SQUARE_JACKET_NOTCH_INSET_MM
    notch_b = fold_b - SQUARE_JACKET_NOTCH_INSET_MM
    outline: Polygon = (
        (left, top),
        (fold_a + inset, top),
        (fold_a + inset, flap_top),
        (fold_b - inset, flap_top),
        (fold_b - inset, top),
        (fold_b, top),
        (fold_b, top + r),
        (right, top + r),
        (right, side_y),
        (notch_b, side_y),
        (notch_b, notch_y),
        (notch_a, notch_y),
        (notch_a, side_y),
        (fold_a, side_y),
        (fold_a, bottom),
        (left, bottom),
    )
    creases = (
        ((fold_a, top), (fold_a, side_y)),
        ((fold_b, top + r), (fold_b, side_y)),
        ((fold_a + inset, top), (fold_b - inset, top)),
        ((fold_a - GUSSET, top), (fold_a - GUSSET, bottom)),
        ((fold_b + GUSSET, top + r), (fold_b + GUSSET, side_y)),
        ((fold_a + inset, top - GUSSET), (fold_b - inset, top - GUSSET)),
    )
    art = (Clip("jacket_front", (47.5, 54.75)), Clip("warning", (129.0, 47.4)))
    return Item(outline, creases, art)


def line_width(line: tuple[Segment, ...], size: float) -> float:
    return sum(FONTS[JAPANESE].text_length(text, size) for text, _ in line)


def block_page(doc: pymupdf.Document, block: Block) -> pymupdf.Rect:
    pad = 3 * MM if block.boxed else 0.6 * MM
    ruby = block.size * RUBY_SCALE
    pitch = block.size * 1.25 + ruby
    widest = max(line_width(line, block.size) for line in block.lines)
    page = doc.new_page(
        width=widest + 2 * pad,
        height=len(block.lines) * pitch + 2 * pad - block.size * 0.15,
    )
    page.insert_font(fontname=JAPANESE, fontbuffer=FONTS[JAPANESE].buffer)
    for index, line in enumerate(block.lines):
        x = pad + ((widest - line_width(line, block.size)) / 2 if block.center else 0)
        baseline = pad + index * pitch + ruby + block.size * 0.95
        for text, reading in line:
            width = FONTS[JAPANESE].text_length(text, block.size)
            page.insert_text(
                (x, baseline), text, fontsize=block.size, fontname=JAPANESE, color=BLACK
            )
            if reading:
                rx = x + (width - FONTS[JAPANESE].text_length(reading, ruby)) / 2
                page.insert_text(
                    (rx, baseline - block.size * 0.98),
                    reading,
                    fontsize=ruby,
                    fontname=JAPANESE,
                    color=BLACK,
                )
            x += width
    if block.boxed:
        page.draw_rect(page.rect + (0.5, 0.5, -0.5, -0.5), color=BLACK, width=1.6)
    return page.rect


def to_black_ink(match: re.Match[bytes]) -> bytes:
    ink = sum(float(v) for v in match.group(1).split())
    return (b"0 0 0 1 " if ink > 0 else b"0 0 0 0 ") + match.group(2)


def is_content(doc: pymupdf.Document, xref: int, page_contents: set[int]) -> bool:
    return xref in page_contents or doc.xref_get_key(xref, "Subtype") == (
        "name",
        "/Form",
    )


def drop_text(doc: pymupdf.Document) -> None:
    page_contents = set(doc[0].get_contents())
    for xref in range(1, doc.xref_length()):
        if doc.xref_is_stream(xref) and is_content(doc, xref, page_contents):
            doc.update_stream(
                xref,
                re.sub(
                    rb"\bBT\b.*?\bET\b", b"", doc.xref_stream(xref), flags=re.DOTALL
                ),
            )
        res_xref, prefix = follow(doc, xref, "Resources")
        if doc.xref_get_key(res_xref, f"{prefix}Font")[0] != "null":
            doc.xref_set_key(res_xref, f"{prefix}Font", "null")


def black_only(doc: pymupdf.Document) -> None:
    drop_text(doc)
    for xref in range(1, doc.xref_length()):
        if doc.xref_is_stream(xref) and b"/CS9" in (
            stream := doc.xref_stream(xref) or b""
        ):
            stream = re.sub(rb"/CS9 (cs|CS)", rb"/DeviceCMYK \1", stream)
            doc.update_stream(
                xref,
                re.sub(CMYK_OPERATOR_PATTERN, to_black_ink, stream),
            )
        if doc.xref_get_key(xref, "DefaultCMYK")[0] != "null":
            doc.xref_set_key(xref, "DefaultCMYK", "null")


def art_source(
    template: Path,
) -> tuple[pymupdf.Document, dict[str, tuple[int, pymupdf.Rect]]]:
    doc = pymupdf.open(template)
    black_only(doc)
    keep = doc.page_count
    dx, dy = _template_offset(doc[0])
    pages = {
        name: (
            0,
            pymupdf.Rect(
                *(
                    (r[0] + dx) * MM,
                    (r[1] + dy) * MM,
                    (r[2] + dx) * MM,
                    (r[3] + dy) * MM,
                )
            ),
        )
        for name, r in TEMPLATE_CLIPS_MM.items()
    }
    for name, block in BLOCKS.items():
        pages[name] = (doc.page_count, block_page(doc, block))
    if keep != 1:
        raise ValueError("the artwork source must be a one-page sheet")
    return pymupdf.open("pdf", doc.tobytes()), pages


def _template_offset(page: pymupdf.Page) -> Point:
    cuts = sorted(
        (
            d["rect"]
            for d in page.get_drawings()
            if (d.get("dashes") or "").startswith("[ .57")
        ),
        key=lambda r: r.y0,
    )
    if not cuts:
        raise ValueError(
            "the jacket sheet carries no template cut line to anchor the artwork"
        )
    return cuts[0].x0 / MM - TEMPLATE_ORIGIN_MM[0], cuts[
        0
    ].y0 / MM - TEMPLATE_ORIGIN_MM[1]


def to_pt(p: Point) -> pymupdf.Point:
    return pymupdf.Point(p[0] * MM, p[1] * MM)


def polygon_shape(
    page: pymupdf.Page, outline: Polygon, place: Placement
) -> pymupdf.Shape:
    shape = page.new_shape()
    shape.draw_polyline([to_pt(place.apply(p)) for p in (*outline, outline[0])])
    return shape


def draw_clip(ctx: Context, clip: Clip, place: Placement) -> None:
    index, rect = ctx.pages[clip.source]
    rotate = (clip.rotate + (180 if place.flip else 0)) % 360
    w, h = rect.width * clip.scale, rect.height * clip.scale
    w, h = (h, w) if rotate in (90, 270) else (w, h)
    cx, cy = to_pt(place.apply(clip.center))
    target = pymupdf.Rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    ctx.page.show_pdf_page(
        target, ctx.source, index, clip=rect, rotate=rotate, oc=ctx.layers["art"]
    )


def draw_line_element(ctx: Context, element: Line, place: Placement) -> None:
    shape = ctx.page.new_shape()
    shape.draw_line(to_pt(place.apply(element.start)), to_pt(place.apply(element.end)))
    shape.finish(color=BLACK, width=element.width, oc=ctx.layers["art"])
    shape.commit()


def draw_element(ctx: Context, element: Element, place: Placement) -> None:
    if isinstance(element, Clip):
        draw_clip(ctx, element, place)
    else:
        draw_line_element(ctx, element, place)


def draw_lines(ctx: Context, item: Item, place: Placement) -> None:
    crease = ctx.page.new_shape()
    for a, b in item.creases:
        crease.draw_line(to_pt(place.apply(a)), to_pt(place.apply(b)))
    crease.finish(
        color=LINE_GRAY,
        width=HOME_LINE_WIDTH,
        dashes=HOME_FOLD_DASHES,
        oc=ctx.layers["art"],
    )
    halo = polygon_shape(ctx.page, item.outline, place)
    halo.finish(
        color=WHITE, width=HOME_HALO_WIDTH, closePath=True, oc=ctx.layers["art"]
    )
    halo.commit()
    crease.commit()
    cut = polygon_shape(ctx.page, item.outline, place)
    cut.finish(
        color=LINE_GRAY, width=HOME_LINE_WIDTH, closePath=True, oc=ctx.layers["art"]
    )
    cut.commit()
    draw_segments(ctx, item.slits, place, LINE_GRAY, HOME_LINE_WIDTH)
    draw_segments(ctx, item.notch_guides, place, NOTCH_GUIDE_GRAY, NOTCH_GUIDE_WIDTH)


def draw_segments(
    ctx: Context,
    segments: tuple[tuple[Point, Point], ...],
    place: Placement,
    color: tuple[float, ...],
    width: float,
) -> None:
    if not segments:
        return
    shape = ctx.page.new_shape()
    for a, b in segments:
        shape.draw_line(to_pt(place.apply(a)), to_pt(place.apply(b)))
    shape.finish(color=color, width=width, oc=ctx.layers["art"])
    shape.commit()


def draw_item(ctx: Context, item: Item, place: Placement) -> None:
    for element in item.art:
        draw_element(ctx, element, place)
    draw_lines(ctx, item, place)


def draw_ruler(ctx: Context, origin: Point) -> None:
    shape = ctx.page.new_shape()
    x0, y0 = origin
    shape.draw_line(to_pt((x0, y0)), to_pt((x0 + 100, y0)))
    for tick in range(101):
        length = 4 if tick % 10 == 0 else (2.5 if tick % 5 == 0 else 1.5)
        shape.draw_line(to_pt((x0 + tick, y0)), to_pt((x0 + tick, y0 + length)))
    shape.finish(color=BLACK, width=0.4, oc=ctx.layers["art"])
    shape.commit()
    ctx.page.insert_text(
        to_pt((x0 + 103, y0 + 3.5)),
        "100 mm at 100%   cut: solid   fold: dashed, score first",
        fontsize=7,
        fontname=LATIN,
        color=BLACK,
        oc=ctx.layers["art"],
    )


def follow(doc: pymupdf.Document, xref: int, path: str) -> tuple[int, str]:
    kind, value = doc.xref_get_key(xref, path)
    return (int(value.split()[0]), "") if kind == "xref" else (xref, f"{path}/")


def trim_union(sheet: list[tuple[Item, Placement]]) -> pymupdf.Rect:
    rects = [
        pymupdf.Rect(
            to_pt(p.apply(polygon_bbox(i.outline)[:2])),
            to_pt(p.apply(polygon_bbox(i.outline)[2:])),
        ).normalize()
        for i, p in sheet
    ]
    union = rects[0]
    for rect in rects[1:]:
        union = union | rect
    return union


def render(
    sheet: list[tuple[Item, Placement]],
    page_mm: Point,
    template: Path,
    out: Path,
) -> None:
    source, pages = art_source(template)
    doc = pymupdf.open()
    page = doc.new_page(width=page_mm[0] * MM, height=page_mm[1] * MM)
    page.insert_font(fontname=LATIN, fontbuffer=FONTS[LATIN].buffer)
    layers = {"art": doc.add_ocg("Art", on=True)}
    ctx = Context(page, source, pages, layers)
    for item, place in sheet:
        draw_item(ctx, item, place)
    union = trim_union(sheet)
    draw_ruler(ctx, (15, page_mm[1] - 12))
    doc.set_metadata({"title": out.stem, "creator": "FDS paper kit"})
    doc.subset_fonts()
    doc.save(out, garbage=4, deflate=True)
    print(f"{out.name}: trim {union.width / MM:.1f} x {union.height / MM:.1f} mm")


def grid(size: Point, page: Point, columns: int, rows: int, gap: Point) -> list[Point]:
    width = columns * size[0] + (columns - 1) * gap[0]
    height = rows * size[1] + (rows - 1) * gap[1]
    x0, y0 = (page[0] - width) / 2, (page[1] - height - 10) / 2
    return [
        (x0 + c * (size[0] + gap[0]), y0 + r * (size[1] + gap[1]))
        for r in range(rows)
        for c in range(columns)
    ]


def nesting_pitch(outline: Polygon) -> float:
    x0, _, x1, _ = polygon_bbox(outline)
    columns = int((x1 - x0) / COLUMN_MM)
    spans = [
        max(ys) - min(ys)
        for ys in (column(outline, x0 + (i + 0.5) * COLUMN_MM) for i in range(columns))
        if ys
    ]
    return max(spans) + NEST_GAP_MM


def cover_sheets() -> dict[str, tuple[list[tuple[Item, Placement]], Point]]:
    cv = cover()
    cv_box = polygon_bbox(cv.outline)
    return {
        "Disk-Cover_A4-landscape_3up": (
            [
                (cv, Placement(p, False, cv_box))
                for p in grid((80, 144), A4_LANDSCAPE, 3, 1, COVER_GAP_MM)
            ],
            A4_LANDSCAPE,
        ),
    }


def square_sheets(
    glue: dict[str, float], standard_glue: bool
) -> dict[str, tuple[list[tuple[Item, Placement]], Point]]:
    tag = "Square_StdGlue" if standard_glue else "Square"
    jk = jacket_square(glue["jacket"])
    jk_box = polygon_bbox(jk.outline)
    pitch = nesting_pitch(jk.outline)
    jk_x = (A4[0] - (jk_box[2] - jk_box[0])) / 2
    jk_y = (A4[1] - (2 * pitch + jk_box[3] - jk_box[1]) - 10) / 2
    return {
        f"Card-Jacket_A4_3up_{tag}": (
            [
                (jk, Placement((jk_x, jk_y + i * pitch), False, jk_box))
                for i in range(3)
            ],
            A4,
        ),
    }


def single_sheet(
    key: str, item: Item
) -> dict[str, tuple[list[tuple[Item, Placement]], Point]]:
    box = polygon_bbox(item.outline)
    offset = (
        (A4[0] - (box[2] - box[0])) / 2,
        (A4[1] - (box[3] - box[1]) - 10) / 2,
    )
    return {key: ([(item, Placement(offset, False, box))], A4)}


SheetSet = dict[str, tuple[list[tuple[Item, Placement]], Point]]


def sheet_sets(which: str) -> tuple[SheetSet, str]:
    if which in ("square", "square-standard"):
        glue = STANDARD_GLUE if which == "square-standard" else WIDE_GLUE
        return square_sheets(glue, which == "square-standard"), "v5"
    if which == "envelope":
        return single_sheet("Disk-Envelope_A4_1up", envelope()), "v6"
    if which == "envelope-lock":
        return single_sheet("Disk-Envelope_A4_1up_TabLock", envelope_lock()), "v7"
    if which == "cover":
        return cover_sheets(), "v4"
    raise ValueError(
        f"unknown mode {which!r}: use cover, square, square-standard, envelope"
        " or envelope-lock"
    )


def item_folder(out_dir: str, key: str) -> Path:
    prefix = next(p for p in ITEM_FOLDERS if key.startswith(f"{p}_"))
    folder = Path(out_dir) / ITEM_FOLDERS[prefix]
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def main(template: str, out_dir: str, which: str) -> None:
    home_sheets, version = sheet_sets(which)
    for key, (sheet, page_mm) in home_sheets.items():
        folder = item_folder(out_dir, key)
        render(
            sheet,
            page_mm,
            Path(template),
            folder / f"FDS-{key}_HomePrint-Mono_{version}.pdf",
        )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "cover")
