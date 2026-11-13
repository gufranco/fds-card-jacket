<div align="center">

<strong>Printable paper jackets, envelopes, cases, covers and labels for Famicom Disk System disk cards.</strong>

</div>

---

## What is in the kit

Every sheet is in [`pdf/`](pdf/), sized for A4.

| Item | Sheet | Holds |
|:-----|:------|:------|
| Card jacket | `FDS-Card-Jacket_A4_3up_*` | Three jackets that slide over a bare disk card |
| Envelope | `FDS-Disk-Envelope_A4_1up_*`, `FDS-Disk-Envelope_A4_2up_*` | A kraft-style pouch with a long tuck flap |
| Case | `FDS-Disk-Case_A4-landscape_1up_*` | A cardstock box with tuck ends |
| Cover | `FDS-Disk-Cover_A4-landscape_3up_*` | Three obi strips that wrap the case |
| Labels | `FDS-Disk-Label_A4_30up_*` | Thirty side A and side B labels |

## Which file to print

| Name contains | Use it when |
|:--------------|:------------|
| `HomePrint-Color` | You print at home in color |
| `HomePrint-Mono` | You print at home with black ink only |
| `CMYK-4x0_DieCut-Crease`, `CMYK-4x0_KissCut` | A print shop prints and die-cuts it; cut and crease lines are spot colors |
| `Square` | You cut with scissors and round the corners with a corner punch; every cut is horizontal or vertical |
| `StdGlue` | You prefer smaller glue flaps; the envelope then fits two per sheet |

Sheets without `Square` are drawn for a ruler and a craft knife.

## What you need

- An A4 printer and paper: 120 to 180 g/m2 for jackets, envelopes and covers, 250 to 300 g/m2 for the case, sticker paper for labels
- A craft knife and a metal ruler, or scissors and an R4 or R5 corner punch for the `Square` sheets
- A glue stick or 6 to 12 mm double-sided tape

## Print

1. Print at actual size, 100%. Turn off "fit to page" and any scaling.
2. Measure the ruler at the bottom of the sheet. It must be exactly 100 mm. If it is not, fix the print settings and print again.

## Assemble

| Mark | Meaning |
|:-----|:--------|
| Solid line | Cut |
| Dashed line | Fold; score it first with the back of the knife against the ruler |
| Gray tint, `のりしろ` | Glue |

1. Cut every piece out.
2. Score and fold every dashed line, and test the fit before any glue goes on.
3. Glue the tinted flaps and press until the glue sets.
4. On `Square` sheets, round the outer corners with the punch. Use R4 at most on the small case dust flaps.

The folds that wrap a disk leave 4 mm for its 3 mm thickness.

## Regenerate the sheets

The generator needs macOS, for the Hiragino Maru Gothic font, and [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
uv run python -I tools/fds_kit.py FDS-Card-Jacket_A4_3up_Color_v1.pdf pdf wide
uv run python -I tools/fds_kit.py FDS-Card-Jacket_A4_3up_Color_v1.pdf pdf standard
uv run python -I tools/fds_kit.py FDS-Card-Jacket_A4_3up_Color_v1.pdf pdf square
uv run python -I tools/fds_kit.py FDS-Card-Jacket_A4_3up_Color_v1.pdf pdf square-standard
```

The artwork comes from [`FDS-Card-Jacket_A4_3up_Color_v1.pdf`](FDS-Card-Jacket_A4_3up_Color_v1.pdf), the original jacket sheet, kept with its black-only twin [`FDS-Card-Jacket_A4_3up_Mono_v1.pdf`](FDS-Card-Jacket_A4_3up_Mono_v1.pdf).

## Trademarks

Nintendo and the Nintendo logo are trademarks of Nintendo. This project is not affiliated with or endorsed by Nintendo.
