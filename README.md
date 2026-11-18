<div align="center">

<strong>Printable paper jackets, envelopes and covers for Famicom Disk System disk cards.</strong>

</div>

---

## What is in the kit

Every sheet is an A4 PDF in [`sheets/`](sheets/), one folder per item, printed with black ink only.

| Item | Folder | Holds |
|:-----|:-------|:------|
| Card jacket | [`sheets/card-jacket/`](sheets/card-jacket/) | Three jackets per sheet that slide over a bare disk card; every cut is horizontal or vertical |
| Envelope | [`sheets/envelope/`](sheets/envelope/) | One kraft-style pouch per sheet with a tuck flap; every cut is horizontal or vertical. `TabLock` closes with two tabs and slits, the other with 25 mm glue flaps |
| Cover | [`sheets/cover/`](sheets/cover/) | Three folded obi strips per sheet |

## Which file to print

| Name contains | Use it when |
|:--------------|:------------|
| `Square` | You want the card jacket with large glue flaps |
| `Square_StdGlue` | You prefer smaller glue flaps on the card jacket |
| `TabLock` | You want the envelope to close without glue or tape |

## What you need

- An A4 printer and 120 to 180 g/m2 paper
- Scissors, or a craft knife and a metal ruler
- A glue stick or 6 to 12 mm double-sided tape, for the card jackets and the glued envelope
- Optional: a corner and notch punch, such as Toke e Crie reference 17671, to round corners and notch fold ends

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
3. Glue the side and top flaps of each card jacket and the two side flaps of the glued envelope, and press until the glue sets.
4. On the `TabLock` envelope, cut the two short slits in the back panel. Fold each side flap inside against the back panel, then push its tab out through the slit until the narrow neck sits in it.
5. Optional: round every outer corner with a corner punch, and notch each fold end that has a faint tick at the cut edge. Leave the square shoulders of the tabs as they are.

The folds that wrap a disk leave 4 mm for its 3 mm thickness.

## Regenerate the sheets

The generator needs macOS, for the Hiragino Maru Gothic font, and [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets cover
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets square
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets square-standard
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets envelope
uv run python -I tools/fds_kit.py artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf sheets envelope-lock
```

Each command writes into the item folders under [`sheets/`](sheets/).

The artwork comes from [`artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf`](artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf), the original jacket sheet, kept with its black-only twin [`artwork/FDS-Card-Jacket_A4_3up_Mono_v1.pdf`](artwork/FDS-Card-Jacket_A4_3up_Mono_v1.pdf). Both still print on their own.

## Trademarks

Nintendo and the Nintendo logo are trademarks of Nintendo. This project is not affiliated with or endorsed by Nintendo.
