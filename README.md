<div align="center">

<strong>Printable paper jackets, envelopes and covers for Famicom Disk System disk cards.</strong>

</div>

---

## What is in the kit

Every sheet is an A4 PDF in [`sheets/`](sheets/), one folder per item, printed with black ink only.

| Item | Folder | Holds |
|:-----|:-------|:------|
| Card jacket | [`sheets/card-jacket/`](sheets/card-jacket/) | Three jackets per sheet that slide over a bare disk card |
| Envelope | [`sheets/envelope/`](sheets/envelope/) | One kraft-style pouch per sheet with a tuck flap and 25 mm glue flaps; every cut is horizontal or vertical |
| Cover | [`sheets/cover/`](sheets/cover/) | Three folded obi strips per sheet |

## Which file to print

| Name contains | Use it when |
|:--------------|:------------|
| `Square` | You cut with scissors and round the corners with a corner punch; every cut is horizontal or vertical |
| `StdGlue` | You prefer smaller glue flaps on the card jacket |

Sheets without `Square` are drawn for a ruler and a craft knife.

## What you need

- An A4 printer and 120 to 180 g/m2 paper
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

1. Cut every piece out.
2. Score and fold every dashed line, and test the fit before any glue goes on.
3. Glue the side and top flaps of each card jacket and the two side flaps of the envelope, and press until the glue sets.
4. On `Square` sheets, round the outer corners with the punch.

The folds that wrap a disk leave 4 mm for its 3 mm thickness.

## Regenerate the sheets

The generator needs macOS, for the Hiragino Maru Gothic font, and [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets wide
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets standard
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets square
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets square-standard
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets envelope
```

Each command writes into the item folders under [`sheets/`](sheets/).

The artwork comes from [`artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf`](artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf), the original jacket sheet, kept with its black-only twin [`artwork/FDS-Card-Jacket_A4_3up_Mono_v1.pdf`](artwork/FDS-Card-Jacket_A4_3up_Mono_v1.pdf). Both still print on their own.

## Trademarks

Nintendo and the Nintendo logo are trademarks of Nintendo. This project is not affiliated with or endorsed by Nintendo.
