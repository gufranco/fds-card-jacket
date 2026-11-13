import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

MM = 72 / 25.4
A4 = (210.0, 297.0)
A4_LANDSCAPE = (297.0, 210.0)
BLACK = (0, 0, 0, 1)
RED = (0, 1, 1, 0)
WHITE = (0, 0, 0, 0)
LINE_GRAY = (0, 0, 0, 0.38)
CUT_PROXY = (0, 1, 0, 0)
CREASE_PROXY = (1, 0, 0, 0)
HOME_LINE_WIDTH = 0.3
HOME_HALO_WIDTH = 1.2
HOME_FOLD_DASHES = "[1.5 13.5] 0"
SHOP_LINE_WIDTH = 0.25
SHOP_CREASE_DASHES = "[4 2] 0"
SHOP_BLEED_MM = 3.0
CARD_THICKNESS_MM = 3.0
TOLERANCE_MM = 1.0
GUSSET = CARD_THICKNESS_MM + TOLERANCE_MM
RELIEF_MM = 1.0
TUCK_CLEARANCE_MM = 1.0
GLUE_TINT = (0, 0, 0, 0.08)
ZONE_MARGIN_MM = 1.0
SQUARE_RELIEF_MM = 2.0
SQUARE_DUST_FLAP_MM = 8.0
SQUARE_THUMB_MM = (14.0, 4.0)
SQUARE_ENVELOPE_NOTCH_MM = (16.0, 6.0)
SQUARE_JACKET_NOTCH_INSET_MM = 11.0
ITEM_FOLDERS = {
    "Card-Jacket": "card-jacket",
    "Disk-Envelope": "envelope",
    "Disk-Case": "case",
    "Disk-Cover": "cover",
    "Disk-Label": "labels",
}
WIDE_GLUE = {"jacket": 15.0, "envelope": 15.0, "case": 18.0}
STANDARD_GLUE = {"jacket": 11.5, "envelope": 6.5, "case": 12.0}
ENVELOPE_NEST_GAP_MM = 4.0
NEST_GAP_MM = 6.0
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
CUT_CS = "[/Separation /CutContour /DeviceCMYK << /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [0 1 0 0] /N 1 >>]"
CREASE_CS = "[/Separation /Crease /DeviceCMYK << /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [1 0 0 0] /N 1 >>]"
OVERPRINT_GS = "<< /Type /ExtGState /OP true /op true /OPM 1 >>"
FONTS = {
    LATIN: pymupdf.Font("figbo"),
    JAPANESE: pymupdf.Font(fontfile=JAPANESE_FONT_FILE),
}

Point = tuple[float, float]
Polygon = tuple[Point, ...]
Segment = tuple[str, str, bool]


@dataclass(frozen=True)
class Block:
    lines: tuple[tuple[Segment, ...], ...]
    size: float
    boxed: bool = False
    center: bool = True


@dataclass(frozen=True)
class Text:
    center: Point
    value: str
    size: float
    color: tuple[float, ...] = BLACK


@dataclass(frozen=True)
class Line:
    start: Point
    end: Point
    width: float = 0.4


@dataclass(frozen=True)
class Box:
    origin: Point
    size: Point
    fill: tuple[float, ...]


@dataclass(frozen=True)
class Clip:
    source: str
    center: Point
    rotate: int = 0
    scale: float = 1.0


Element = Text | Line | Box | Clip


@dataclass(frozen=True)
class Item:
    outline: Polygon
    creases: tuple[tuple[Point, Point], ...]
    art: tuple[Element, ...]
    glue: tuple[Point, ...] = field(default_factory=tuple)
    zones: tuple[Polygon, ...] = field(default_factory=tuple)
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
    home: bool
    mono: bool


def seg(text: str, ruby: str = "", red: bool = False) -> Segment:
    return text, ruby, red


BLOCKS: dict[str, Block] = {
    "envelope_title": Block(
        ((seg("カード"), seg("保管袋", "ほかんぶくろ")),), 14, boxed=True
    ),
    "envelope_notice": Block(
        (
            (
                seg("※", red=True),
                seg("使用後", "しようご", True),
                seg("は", red=True),
                seg("必", "かなら", True),
                seg("ずカードをこのふくろに", red=True),
            ),
            (seg("もどしてください。", red=True),),
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
    "case_title": Block(
        ((seg("ディスクカード"), seg("専用", "せんよう"), seg("ケース")),),
        13,
        boxed=True,
    ),
    "case_notice": Block(
        (
            (
                seg("※カードは", red=True),
                seg("必", "かなら", True),
                seg("ず", red=True),
                seg("保護", "ほご", True),
                seg("ジャケットに", red=True),
                seg("入", "い", True),
                seg("れてから", red=True),
            ),
            (seg("しまってください。", red=True),),
        ),
        8.6,
        center=False,
    ),
    "case_caution": Block(
        (
            (
                seg("※"),
                seg("直射日光", "ちょくしゃにっこう"),
                seg("の"),
                seg("当", "あ"),
                seg("たる"),
                seg("所", "ところ"),
                seg("、"),
                seg("高温", "こうおん"),
                seg("・"),
                seg("多湿", "たしつ"),
                seg("の"),
            ),
            (
                seg("所", "ところ"),
                seg("、"),
                seg("磁気", "じき"),
                seg("を"),
                seg("発生", "はっせい"),
                seg("する"),
                seg("物", "もの"),
                seg("の"),
                seg("近", "ちか"),
                seg("くには"),
                seg("置", "お"),
                seg("かないで"),
            ),
            (seg("ください。"),),
        ),
        7.2,
        center=False,
    ),
    "cover_title": Block(((seg("ディスクカード"),),), 15, boxed=True),
    "cover_name": Block(((seg("ソフト"), seg("名", "めい")),), 7.5, center=False),
    "label_side": Block(((seg("面"),),), 9.0),
    "glue": Block(((seg("のりしろ"),),), 5.0),
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


def row(points: Polygon, y: float) -> list[float]:
    return [
        a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
        for a, b in edges(points)
        if a[1] != b[1] and min(a[1], b[1]) <= y <= max(a[1], b[1])
    ]


def vertical(
    points: Polygon, x: float, top: float | None = None, bottom: float | None = None
) -> tuple[Point, Point]:
    ys = column(points, x)
    return (x, top if top is not None else min(ys)), (
        x,
        bottom if bottom is not None else max(ys),
    )


def horizontal(
    points: Polygon, y: float, left: float, right: float
) -> tuple[Point, Point]:
    xs = [x for x in row(points, y) if left - 0.01 <= x <= right + 0.01]
    return (max(min(xs), left), y), (min(max(xs), right), y)


def jacket(glue: float) -> Item:
    left, fold_a, fold_b, top, bottom = 6.195, 86.195, 168.195, 21.985, 100.985
    flap_top, notch_y, side_y = 6.485, 77.485, 89.485
    right = fold_b + GUSSET + glue
    r = RELIEF_MM
    outline: Polygon = (
        (left + 6, top),
        (fold_a, top),
        (fold_a + r, top),
        (fold_a + 9.3, flap_top),
        (fold_b - 9.3, flap_top),
        (fold_b - r, top),
        (fold_b, top),
        (fold_b, top + r),
        (right, top + r + 6),
        (right, bottom - 7),
        (fold_b + 6, bottom - 1),
        (fold_b, side_y),
        (fold_b - 22, notch_y),
        (fold_a + 22, notch_y),
        (fold_a, side_y),
        (fold_a - 9, bottom),
        (left + 6, bottom),
        (left, bottom - 6),
        (left, top + 6),
    )
    creases = (
        vertical(outline, fold_a, top, side_y),
        vertical(outline, fold_b, top + r, side_y),
        ((fold_a + r, top), (fold_b - r, top)),
        vertical(outline, fold_a - GUSSET),
        vertical(outline, fold_b + GUSSET),
        horizontal(outline, top - GUSSET, fold_a, fold_b),
    )
    m = ZONE_MARGIN_MM
    zones = (
        (
            (fold_b + GUSSET + m, top + r + 7),
            (right - m, top + r + 7),
            (right - m, bottom - 8),
            (fold_b + GUSSET + m, bottom - 8),
        ),
        (
            (fold_a + 10.5, flap_top + m),
            (fold_b - 10.5, flap_top + m),
            (fold_b - 10.5, top - GUSSET - m),
            (fold_a + 10.5, top - GUSSET - m),
        ),
    )
    art = (Clip("jacket_front", (47.5, 54.75)), Clip("warning", (129.0, 47.4)))
    glue_points = (
        (fold_b + GUSSET + glue / 2, (top + bottom) / 2),
        ((fold_a + fold_b) / 2, (flap_top + top - GUSSET) / 2),
    )
    return Item(outline, creases, art, glue_points, zones)


def envelope(glue: float) -> Item:
    w, h, tuck, notch = 80.0, 95.0, 35.0, 8.0
    flap = GUSSET + glue
    taper, inset, end, r = 6.5, 2.0, 8.0, RELIEF_MM
    f0 = tuck + h + GUSSET
    f1 = f0 + h
    outline: Polygon = (
        (0, tuck),
        (inset, tuck),
        (inset + taper, 0),
        (w - inset - taper, 0),
        (w - inset, tuck),
        (w, tuck),
        (w, f0),
        (w, f0 + r),
        (w + flap, f0 + r + end),
        (w + flap, f1 - r - end),
        (w, f1 - r),
        (w, f1),
        (w / 2 + notch, f1),
        (w / 2, f1 - 6),
        (w / 2 - notch, f1),
        (0, f1),
        (0, f1 - r),
        (-flap, f1 - r - end),
        (-flap, f0 + r + end),
        (0, f0 + r),
        (0, f0),
    )
    creases = (
        horizontal(outline, tuck, inset, w - inset),
        horizontal(outline, tuck - GUSSET, 0, w),
        ((0, tuck + h), (w, tuck + h)),
        ((0, f0), (w, f0)),
        ((0, f0 + r), (0, f1 - r)),
        ((w, f0 + r), (w, f1 - r)),
        vertical(outline, -GUSSET),
        vertical(outline, w + GUSSET),
    )
    m = ZONE_MARGIN_MM
    zone_top, zone_bottom = f0 + r + end + m, f1 - r - end - m
    zones = (
        (
            (-flap + m, zone_top),
            (-GUSSET - m, zone_top),
            (-GUSSET - m, zone_bottom),
            (-flap + m, zone_bottom),
        ),
        (
            (w + GUSSET + m, zone_top),
            (w + flap - m, zone_top),
            (w + flap - m, zone_bottom),
            (w + GUSSET + m, zone_bottom),
        ),
    )
    art = (
        Clip("envelope_title", (w / 2, f1 - 30), 180),
        Clip("envelope_notice", (w / 2, f1 - 52), 180),
        Clip("logo", (w / 2, f0 + 12), 180),
        Clip("warning", (w / 2, tuck + 30)),
        Clip("envelope_flap", (w / 2, tuck + 70)),
    )
    glue_x = GUSSET + glue / 2
    return Item(
        outline,
        creases,
        art,
        ((-glue_x, (f0 + f1) / 2), (w + glue_x, (f0 + f1) / 2)),
        zones,
    )


def case(glue_w: float) -> Item:
    w, d, h, tuck = 90.0, 10.0, 100.0, 15.0
    back, side1, front, side2 = glue_w, glue_w + w, glue_w + w + d, glue_w + 2 * w + d
    end = side2 + d
    r, c, mid = RELIEF_MM, TUCK_CLEARANCE_MM, glue_w + w / 2
    outline: Polygon = (
        (0, 6 + r),
        (back, r),
        (back, 0),
        (mid - 7, 0),
        (mid, 4),
        (mid + 7, 0),
        (side1, 0),
        (side1 + 0.5, -8),
        (front - 2.5, -8),
        (front, 0),
        (front, -d),
        (front + c, -d),
        (front + c + 3.5, -d - tuck),
        (side2 - c - 3.5, -d - tuck),
        (side2 - c, -d),
        (side2, -d),
        (side2, 0),
        (side2 + 2.5, -8),
        (end - 0.5, -8),
        (end, 0),
        (end, h),
        (end - 0.5, h + 8),
        (side2 + 2.5, h + 8),
        (side2, h),
        (front, h),
        (front - 2.5, h + 8),
        (side1 + 0.5, h + 8),
        (side1, h),
        (side1, h + d),
        (side1 - c, h + d),
        (side1 - c - 3.5, h + d + tuck),
        (back + c + 3.5, h + d + tuck),
        (back + c, h + d),
        (back, h + d),
        (back, h),
        (back, h - r),
        (0, h - 6 - r),
    )
    creases = (
        ((back, r), (back, h - r)),
        *(((x, 0.0), (x, h)) for x in (side1, front, side2)),
        ((front, 0), (side2, 0)),
        ((front + c, -d), (side2 - c, -d)),
        ((side1, 0), (front, 0)),
        ((side2, 0), (end, 0)),
        ((side1, h), (front, h)),
        ((side2, h), (end, h)),
        ((back, h), (side1, h)),
        ((back + c, h + d), (side1 - c, h + d)),
    )
    m = ZONE_MARGIN_MM
    zones = (((m, 8 + r), (back - m, 2 + r), (back - m, h - 2 - r), (m, h - 8 - r)),)
    art = (
        Clip("case_title", (front + w / 2, 24)),
        Clip("case_notice", (front + w / 2, 46)),
        Clip("logo", (front + w / 2, 88)),
        Clip("warning", (back + w / 2, 32)),
        Clip("case_caution", (back + w / 2, 78)),
        Clip("logo", (side1 + d / 2, h / 2), 90),
        Clip("logo", (side2 + d / 2, h / 2), 90),
    )
    return Item(outline, creases, art, ((glue_w / 2, h / 2),), zones)


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
    return Item(outline, creases, art)


def label(side: str, bleed: float) -> Item:
    w, h, block = 52.0, 22.0, 10.0
    outline: Polygon = ((0, 0), (w, 0), (w, h), (0, h))
    art = (
        Box((-bleed, -bleed), (block + bleed, h + 2 * bleed), fill=RED),
        Text((block / 2, h / 2 - 3.0), side, 13, color=WHITE),
        Clip("label_side_white", (block / 2, h / 2 + 4.5)),
        Clip("logo", (w - 12.5, 5.0), scale=0.75),
        Clip("cover_name", (block + 7.0, 10.5), scale=0.85),
        Line((block + 3, 15.0), (w - 3, 15.0), 0.35),
        Line((block + 3, 19.5), (w - 3, 19.5), 0.35),
    )
    return Item(outline, (), art)


def rectangle(x0: float, y0: float, x1: float, y1: float) -> Polygon:
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


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
    m = ZONE_MARGIN_MM
    zones = (
        rectangle(fold_b + GUSSET + m, top + r + m, right - m, side_y - m),
        rectangle(
            fold_a + inset + m, flap_top + m, fold_b - inset - m, top - GUSSET - m
        ),
    )
    art = (Clip("jacket_front", (47.5, 54.75)), Clip("warning", (129.0, 47.4)))
    glue_points = (
        (fold_b + GUSSET + glue / 2, (top + r + side_y) / 2),
        ((fold_a + fold_b) / 2, (flap_top + top - GUSSET) / 2),
    )
    return Item(outline, creases, art, glue_points, zones)


def envelope_square(glue: float) -> Item:
    w, h, tuck, inset = 80.0, 95.0, 35.0, 2.0
    notch_w, notch_d = SQUARE_ENVELOPE_NOTCH_MM
    flap, end = GUSSET + glue, GUSSET
    f0 = tuck + h + GUSSET
    f1 = f0 + h
    outline: Polygon = (
        (0, tuck),
        (inset, tuck),
        (inset, 0),
        (w - inset, 0),
        (w - inset, tuck),
        (w, tuck),
        (w, f0 + end),
        (w + flap, f0 + end),
        (w + flap, f1 - end),
        (w, f1 - end),
        (w, f1),
        ((w + notch_w) / 2, f1),
        ((w + notch_w) / 2, f1 - notch_d),
        ((w - notch_w) / 2, f1 - notch_d),
        ((w - notch_w) / 2, f1),
        (0, f1),
        (0, f1 - end),
        (-flap, f1 - end),
        (-flap, f0 + end),
        (0, f0 + end),
    )
    creases = (
        ((inset, tuck), (w - inset, tuck)),
        ((inset, tuck - GUSSET), (w - inset, tuck - GUSSET)),
        ((0, tuck + h), (w, tuck + h)),
        ((0, f0), (w, f0)),
        ((0, f0 + end), (0, f1 - end)),
        ((w, f0 + end), (w, f1 - end)),
        ((-GUSSET, f0 + end), (-GUSSET, f1 - end)),
        ((w + GUSSET, f0 + end), (w + GUSSET, f1 - end)),
    )
    m = ZONE_MARGIN_MM
    zones = (
        rectangle(-flap + m, f0 + end + m, -GUSSET - m, f1 - end - m),
        rectangle(w + GUSSET + m, f0 + end + m, w + flap - m, f1 - end - m),
    )
    art = (
        Clip("envelope_title", (w / 2, f1 - 30), 180),
        Clip("envelope_notice", (w / 2, f1 - 52), 180),
        Clip("logo", (w / 2, f0 + 12), 180),
        Clip("warning", (w / 2, tuck + 30)),
        Clip("envelope_flap", (w / 2, tuck + 70)),
    )
    glue_x = GUSSET + glue / 2
    return Item(
        outline,
        creases,
        art,
        ((-glue_x, (f0 + f1) / 2), (w + glue_x, (f0 + f1) / 2)),
        zones,
    )


def case_square(glue_w: float) -> Item:
    w, d, h, tuck, dust = 90.0, 10.0, 100.0, 15.0, SQUARE_DUST_FLAP_MM
    back, side1, front, side2 = glue_w, glue_w + w, glue_w + w + d, glue_w + 2 * w + d
    end = side2 + d
    r = c = SQUARE_RELIEF_MM
    mid = glue_w + w / 2
    thumb_w, thumb_d = SQUARE_THUMB_MM
    outline: Polygon = (
        (0, r),
        (back, r),
        (back, 0),
        (mid - thumb_w / 2, 0),
        (mid - thumb_w / 2, thumb_d),
        (mid + thumb_w / 2, thumb_d),
        (mid + thumb_w / 2, 0),
        (side1, 0),
        (side1, -dust),
        (front, -dust),
        (front, -d),
        (front + c, -d),
        (front + c, -d - tuck),
        (side2 - c, -d - tuck),
        (side2 - c, -d),
        (side2, -d),
        (side2, -dust),
        (end, -dust),
        (end, h + dust),
        (side2, h + dust),
        (side2, h),
        (front, h),
        (front, h + dust),
        (side1, h + dust),
        (side1, h + d),
        (side1 - c, h + d),
        (side1 - c, h + d + tuck),
        (back + c, h + d + tuck),
        (back + c, h + d),
        (back, h + d),
        (back, h - r),
        (0, h - r),
    )
    creases = (
        ((back, r), (back, h - r)),
        *(((x, 0.0), (x, h)) for x in (side1, front, side2)),
        ((front, 0), (side2, 0)),
        ((front + c, -d), (side2 - c, -d)),
        ((side1, 0), (front, 0)),
        ((side2, 0), (end, 0)),
        ((side1, h), (front, h)),
        ((side2, h), (end, h)),
        ((back, h), (side1, h)),
        ((back + c, h + d), (side1 - c, h + d)),
    )
    slits = (
        ((front, 0), (front, -dust)),
        ((side2, 0), (side2, -dust)),
        ((side1, h), (side1, h + dust)),
    )
    m = ZONE_MARGIN_MM
    zones = (rectangle(m, r + m, back - m, h - r - m),)
    art = (
        Clip("case_title", (front + w / 2, 24)),
        Clip("case_notice", (front + w / 2, 46)),
        Clip("logo", (front + w / 2, 88)),
        Clip("warning", (back + w / 2, 32)),
        Clip("case_caution", (back + w / 2, 78)),
        Clip("logo", (side1 + d / 2, h / 2), 90),
        Clip("logo", (side2 + d / 2, h / 2), 90),
    )
    return Item(outline, creases, art, ((glue_w / 2, h / 2),), zones, slits)


def resolve(color: tuple[float, ...], mono: bool) -> tuple[float, ...]:
    return BLACK if mono and color == RED else color


def line_width(line: tuple[Segment, ...], size: float) -> float:
    return sum(FONTS[JAPANESE].text_length(text, size) for text, _, _ in line)


def block_page(
    doc: pymupdf.Document,
    block: Block,
    mono: bool,
    ink: tuple[float, ...] | None = None,
) -> pymupdf.Rect:
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
        for text, reading, red in line:
            color = ink or resolve(RED if red else BLACK, mono)
            width = FONTS[JAPANESE].text_length(text, block.size)
            page.insert_text(
                (x, baseline), text, fontsize=block.size, fontname=JAPANESE, color=color
            )
            if reading:
                rx = x + (width - FONTS[JAPANESE].text_length(reading, ruby)) / 2
                page.insert_text(
                    (rx, baseline - block.size * 0.98),
                    reading,
                    fontsize=ruby,
                    fontname=JAPANESE,
                    color=color,
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


def plain_cmyk(doc: pymupdf.Document, mono: bool) -> None:
    drop_text(doc)
    for xref in range(1, doc.xref_length()):
        if doc.xref_is_stream(xref) and b"/CS9" in (
            stream := doc.xref_stream(xref) or b""
        ):
            stream = re.sub(rb"/CS9 (cs|CS)", rb"/DeviceCMYK \1", stream)
            doc.update_stream(
                xref,
                re.sub(CMYK_OPERATOR_PATTERN, to_black_ink, stream) if mono else stream,
            )
        if doc.xref_get_key(xref, "DefaultCMYK")[0] != "null":
            doc.xref_set_key(xref, "DefaultCMYK", "null")


def art_source(
    template: Path, mono: bool
) -> tuple[pymupdf.Document, dict[str, tuple[int, pymupdf.Rect]]]:
    doc = pymupdf.open(template)
    plain_cmyk(doc, mono)
    keep = doc.page_count
    dx, dy = _template_offset(doc[0])
    pages = {
        name: (
            0,
            pymupdf.Rect(*(
                (r[0] + dx) * MM,
                (r[1] + dy) * MM,
                (r[2] + dx) * MM,
                (r[3] + dy) * MM,
            )),
        )
        for name, r in TEMPLATE_CLIPS_MM.items()
    }
    for name, block in BLOCKS.items():
        pages[name] = (doc.page_count, block_page(doc, block, mono))
    pages["label_side_white"] = (
        doc.page_count,
        block_page(doc, BLOCKS["label_side"], mono, WHITE),
    )
    pages["glue_gray"] = (
        doc.page_count,
        block_page(doc, BLOCKS["glue"], mono, LINE_GRAY),
    )
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


def draw_slits(
    ctx: Context,
    item: Item,
    place: Placement,
    color: tuple[float, ...],
    width: float,
    layer: str,
) -> None:
    if not item.slits:
        return
    shape = ctx.page.new_shape()
    for a, b in item.slits:
        shape.draw_line(to_pt(place.apply(a)), to_pt(place.apply(b)))
    shape.finish(color=color, width=width, oc=ctx.layers[layer])
    shape.commit()


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


def draw_text(ctx: Context, text: Text, place: Placement) -> None:
    half = FONTS[LATIN].text_length(text.value, text.size) / 2 / MM
    cx, cy = place.apply(text.center)
    ctx.page.insert_text(
        to_pt((cx - half, cy + text.size * 0.35 / MM)),
        text.value,
        fontsize=text.size,
        fontname=LATIN,
        color=resolve(text.color, ctx.mono),
        oc=ctx.layers["art"],
    )


def draw_shape_element(ctx: Context, element: Line | Box, place: Placement) -> None:
    shape = ctx.page.new_shape()
    if isinstance(element, Line):
        shape.draw_line(
            to_pt(place.apply(element.start)), to_pt(place.apply(element.end))
        )
        shape.finish(color=BLACK, width=element.width, oc=ctx.layers["art"])
    else:
        a = place.apply(element.origin)
        b = place.apply((
            element.origin[0] + element.size[0],
            element.origin[1] + element.size[1],
        ))
        shape.draw_rect(pymupdf.Rect(to_pt(a), to_pt(b)).normalize())
        shape.finish(
            color=None,
            fill=resolve(element.fill, ctx.mono),
            width=0,
            oc=ctx.layers["art"],
        )
    shape.commit()


def draw_element(ctx: Context, element: Element, place: Placement) -> None:
    if isinstance(element, Clip):
        draw_clip(ctx, element, place)
    elif isinstance(element, Text):
        draw_text(ctx, element, place)
    else:
        draw_shape_element(ctx, element, place)


def draw_lines(ctx: Context, item: Item, place: Placement) -> None:
    crease = ctx.page.new_shape()
    for a, b in item.creases:
        crease.draw_line(to_pt(place.apply(a)), to_pt(place.apply(b)))
    if ctx.home:
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
        draw_slits(ctx, item, place, WHITE, HOME_HALO_WIDTH, "art")
    else:
        crease.finish(
            color=CREASE_PROXY,
            width=SHOP_LINE_WIDTH,
            dashes=SHOP_CREASE_DASHES,
            oc=ctx.layers["crease"],
        )
    crease.commit()
    cut = polygon_shape(ctx.page, item.outline, place)
    if ctx.home:
        cut.finish(
            color=LINE_GRAY, width=HOME_LINE_WIDTH, closePath=True, oc=ctx.layers["art"]
        )
    else:
        cut.finish(
            color=CUT_PROXY, width=SHOP_LINE_WIDTH, closePath=True, oc=ctx.layers["cut"]
        )
    cut.commit()
    if ctx.home:
        draw_slits(ctx, item, place, LINE_GRAY, HOME_LINE_WIDTH, "art")
    else:
        draw_slits(ctx, item, place, CUT_PROXY, SHOP_LINE_WIDTH, "cut")


def draw_zones(ctx: Context, item: Item, place: Placement) -> None:
    for zone in item.zones:
        shape = polygon_shape(ctx.page, zone, place)
        shape.finish(
            color=None, fill=GLUE_TINT, width=0, closePath=True, oc=ctx.layers["art"]
        )
        shape.commit()


def draw_item(ctx: Context, item: Item, place: Placement) -> None:
    if ctx.home:
        draw_zones(ctx, item, place)
    for element in item.art:
        draw_element(ctx, element, place)
    if ctx.home:
        for point in item.glue:
            draw_clip(ctx, Clip("glue_gray", point, 90), place)
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
        "100 mm at 100%   cut: solid   fold: dashed, score first   glue: tint",
        fontsize=7,
        fontname=LATIN,
        color=BLACK,
        oc=ctx.layers["art"],
    )


def follow(doc: pymupdf.Document, xref: int, path: str) -> tuple[int, str]:
    kind, value = doc.xref_get_key(xref, path)
    return (int(value.split()[0]), "") if kind == "xref" else (xref, f"{path}/")


def set_resource(
    doc: pymupdf.Document, page: pymupdf.Page, category: str, name: str, value: str
) -> None:
    res_xref, res_prefix = follow(doc, page.xref, "Resources")
    cat_xref, cat_prefix = follow(doc, res_xref, f"{res_prefix}{category}")
    doc.xref_set_key(cat_xref, f"{cat_prefix}{name}", value)


def bind_spots(doc: pymupdf.Document, page: pymupdf.Page) -> None:
    set_resource(doc, page, "ColorSpace", "CSCut", CUT_CS)
    set_resource(doc, page, "ColorSpace", "CSCrease", CREASE_CS)
    gs_xref = doc.get_new_xref()
    doc.update_object(gs_xref, OVERPRINT_GS)
    set_resource(doc, page, "ExtGState", "GSop", f"{gs_xref} 0 R")
    for xref in page.get_contents():
        stream = doc.xref_stream(xref)
        stream = stream.replace(b"0 1 0 0 K", b"/GSop gs /CSCut CS 1 SCN").replace(
            b"1 0 0 0 K", b"/GSop gs /CSCrease CS 1 SCN"
        )
        doc.update_stream(xref, stream)


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
    mode: str,
    template: Path,
    out: Path,
) -> None:
    home, mono = mode != "shop", mode == "mono"
    source, pages = art_source(template, mono)
    doc = pymupdf.open()
    page = doc.new_page(width=page_mm[0] * MM, height=page_mm[1] * MM)
    page.insert_font(fontname=LATIN, fontbuffer=FONTS[LATIN].buffer)
    names = ("Art", "CutContour - die cut, do not print", "Crease - fold, do not print")
    layers = dict(
        zip(
            ("art", "cut", "crease"),
            (doc.add_ocg(n, on=True) for n in names),
            strict=True,
        )
    )
    ctx = Context(page, source, pages, layers, home, mono)
    for item, place in sheet:
        draw_item(ctx, item, place)
    union = trim_union(sheet)
    if home:
        draw_ruler(ctx, (15, page_mm[1] - 12))
    else:
        bind_spots(doc, page)
        page.set_bleedbox(
            union
            + (
                -SHOP_BLEED_MM * MM,
                -SHOP_BLEED_MM * MM,
                SHOP_BLEED_MM * MM,
                SHOP_BLEED_MM * MM,
            )
        )
        page.set_trimbox(union)
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


def centered(box: tuple[float, float, float, float], page: Point) -> Point:
    return (page[0] - (box[2] - box[0])) / 2, (page[1] - (box[3] - box[1]) - 10) / 2


def envelope_two_up(env: Item) -> list[tuple[Item, Placement]]:
    box = polygon_bbox(env.outline)
    flap = -box[0]
    step = (box[2] - box[0]) - flap + ENVELOPE_NEST_GAP_MM
    rise = 35.0
    x0 = (A4[0] - (box[2] - box[0] + step)) / 2
    y0 = (A4[1] - (box[3] - box[1] + rise) - 10) / 2
    return [
        (env, Placement((x0, y0), False, box)),
        (env, Placement((x0 + step, y0 + rise), True, box)),
    ]


def standard_glue_sheets() -> dict[str, tuple[list[tuple[Item, Placement]], Point]]:
    jk, cs = jacket(STANDARD_GLUE["jacket"]), case(STANDARD_GLUE["case"])
    jk_box, cs_box = polygon_bbox(jk.outline), polygon_bbox(cs.outline)
    pitch = nesting_pitch(jk.outline)
    jk_x = (A4[0] - (jk_box[2] - jk_box[0])) / 2
    jk_y = (A4[1] - (2 * pitch + jk_box[3] - jk_box[1]) - 10) / 2
    return {
        "Card-Jacket_A4_3up_StdGlue": (
            [
                (jk, Placement((jk_x, jk_y + i * pitch), False, jk_box))
                for i in range(3)
            ],
            A4,
        ),
        "Disk-Envelope_A4_2up_StdGlue": (
            envelope_two_up(envelope(STANDARD_GLUE["envelope"])),
            A4,
        ),
        "Disk-Case_A4-landscape_1up_StdGlue": (
            [(cs, Placement(centered(cs_box, A4_LANDSCAPE), False, cs_box))],
            A4_LANDSCAPE,
        ),
    }


def sheets(gang: bool) -> dict[str, tuple[list[tuple[Item, Placement]], Point]]:
    jk, env, cs, cv = (
        jacket(WIDE_GLUE["jacket"]),
        envelope(WIDE_GLUE["envelope"]),
        case(WIDE_GLUE["case"]),
        cover(),
    )
    jk_box, env_box, cs_box, cv_box = (
        polygon_bbox(i.outline) for i in (jk, env, cs, cv)
    )
    pitch = nesting_pitch(jk.outline)
    jk_height = 2 * pitch + jk_box[3] - jk_box[1]
    jk_x = (A4[0] - (jk_box[2] - jk_box[0])) / 2
    jk_y = (A4[1] - jk_height - 10) / 2
    labels = (label("A", 0.0 if gang else 1.0), label("B", 0.0 if gang else 1.0))
    label_box = polygon_bbox(labels[0].outline)
    cover_gap, label_gap = (
        ((0.0, 0.0), (0.0, 0.0)) if gang else ((8.0, 0.0), (6.0, 4.0))
    )
    return {
        "Card-Jacket_A4_3up": (
            [
                (jk, Placement((jk_x, jk_y + i * pitch), False, jk_box))
                for i in range(3)
            ],
            A4,
        ),
        "Disk-Envelope_A4_1up": (
            [(env, Placement(centered(env_box, A4), False, env_box))],
            A4,
        ),
        "Disk-Case_A4-landscape_1up": (
            [(cs, Placement(centered(cs_box, A4_LANDSCAPE), False, cs_box))],
            A4_LANDSCAPE,
        ),
        "Disk-Cover_A4-landscape_3up": (
            [
                (cv, Placement(p, False, cv_box))
                for p in grid((80, 144), A4_LANDSCAPE, 3, 1, cover_gap)
            ],
            A4_LANDSCAPE,
        ),
        "Disk-Label_A4_30up": (
            [
                (labels[i // 3 % 2], Placement(p, False, label_box))
                for i, p in enumerate(grid((52, 22), A4, 3, 10, label_gap))
            ],
            A4,
        ),
    }


def square_sheets(
    glue: dict[str, float], two_up_envelope: bool
) -> dict[str, tuple[list[tuple[Item, Placement]], Point]]:
    tag = "Square_StdGlue" if two_up_envelope else "Square"
    jk, env, cs = (
        jacket_square(glue["jacket"]),
        envelope_square(glue["envelope"]),
        case_square(glue["case"]),
    )
    jk_box, env_box, cs_box = (polygon_bbox(i.outline) for i in (jk, env, cs))
    pitch = nesting_pitch(jk.outline)
    jk_x = (A4[0] - (jk_box[2] - jk_box[0])) / 2
    jk_y = (A4[1] - (2 * pitch + jk_box[3] - jk_box[1]) - 10) / 2
    envelopes = (
        envelope_two_up(env)
        if two_up_envelope
        else [(env, Placement(centered(env_box, A4), False, env_box))]
    )
    return {
        f"Card-Jacket_A4_3up_{tag}": (
            [
                (jk, Placement((jk_x, jk_y + i * pitch), False, jk_box))
                for i in range(3)
            ],
            A4,
        ),
        f"Disk-Envelope_A4_{2 if two_up_envelope else 1}up_{tag}": (envelopes, A4),
        f"Disk-Case_A4-landscape_1up_{tag}": (
            [(cs, Placement(centered(cs_box, A4_LANDSCAPE), False, cs_box))],
            A4_LANDSCAPE,
        ),
    }


SheetSet = dict[str, tuple[list[tuple[Item, Placement]], Point]]


def sheet_sets(which: str) -> tuple[SheetSet, SheetSet, str]:
    if which == "standard":
        return standard_glue_sheets(), standard_glue_sheets(), "v4"
    if which in ("square", "square-standard"):
        glue = STANDARD_GLUE if which == "square-standard" else WIDE_GLUE
        squares = square_sheets(glue, which == "square-standard")
        return squares, squares, "v5"
    return sheets(gang=True), sheets(gang=False), "v4"


def item_folder(out_dir: str, key: str) -> Path:
    prefix = next(p for p in ITEM_FOLDERS if key.startswith(f"{p}_"))
    folder = Path(out_dir) / ITEM_FOLDERS[prefix]
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def main(template: str, out_dir: str, which: str) -> None:
    home_sheets, shop_sheets, version = sheet_sets(which)
    for key, (sheet, page_mm) in home_sheets.items():
        folder = item_folder(out_dir, key)
        cut = "KissCut" if "Label" in key else "DieCut-Crease"
        shop_sheet, shop_page = shop_sheets[key]
        render(
            sheet,
            page_mm,
            "home",
            Path(template),
            folder / f"FDS-{key}_HomePrint-Color_{version}.pdf",
        )
        render(
            sheet,
            page_mm,
            "mono",
            Path(template),
            folder / f"FDS-{key}_HomePrint-Mono_{version}.pdf",
        )
        render(
            shop_sheet,
            shop_page,
            "shop",
            Path(template),
            folder / f"FDS-{key}_CMYK-4x0_{cut}_{version}.pdf",
        )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "wide")
