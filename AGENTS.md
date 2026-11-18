# AGENTS.md

Rules for any agent working in this repository. The [README](README.md) owns what the kit is, which file to print, assembly and how to regenerate the sheets. The generator is [`tools/fds_kit.py`](tools/fds_kit.py).

## Finishing punch

Every piece is finished with one hand punch: the Toke e Crie Furador Cantoneira Arredondada e Entalhe, reference 17671, model FCAE01. One side rounds a corner. The other side cuts a notch where crease lines meet an edge, so flaps tuck in cleanly.

| Fact | Value | Source |
|:-----|:------|:-------|
| Opening | 1.5 mm | Product description, [Mercado Livre listing MLB24311450](https://www.mercadolivre.com.br/furador-cantoneira-arredondada-e-entalhe-toke-crie-cor-rosa-chiclete/p/MLB24311450) |
| Paper weight | 90 to 220 g/m2 | Same description |
| Corner radius | Unknown | Not published by the maker |
| Notch width and depth | Unknown | Not published by the maker |

## Hard rules

### Cutting and folding

- Every outer corner of every piece is rounded with the finishing punch.
- Every place where a fold line meets a cut edge gets a notch made with the finishing punch.
- The corner radius and notch size are unknown. Measure a punched sample and record both in the table above before a sheet depends on either value.
- Cut and fold lines are straight: no curves. [`tools/check_curves.py`](tools/check_curves.py) checks it.
- Cut lines are as faint as fold lines, and fold dashes stay sparse.
- A fold that wraps a disk leaves 4 mm: the 3 mm Quick Disk plus 1 mm tolerance.
- `Square` sheets cut only horizontal and vertical lines. [`tools/check_square_layout.py`](tools/check_square_layout.py) checks it.

### Artwork and text

- Artwork follows Nintendo's originals, and Japanese text is written the way Nintendo wrote the original jacket.
- All artwork is clipped from [`artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf`](artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf). Never delete or modify it; the generator converts it to black ink.

### Sheets

- Every sheet is `HomePrint-Mono`: black ink only, no color sheets and nothing for a print shop.
- Paper only: no manual, booklet or 3D-printed parts.
- Sheets are A4 and print at 100 percent.
- Glue flaps are large by default. `StdGlue` sheets use the smaller widths, and the envelope ships only as the 2-up `StdGlue` and `Square_StdGlue` sheets.
- The three covers on the cover sheet sit 4 mm apart, so each has its own cut outline.
- A new variant is a new file. An existing sheet changes only when the owner names it.
- Regenerating every mode stays pixel-identical to the committed sheets. Run [`tools/compare_renders.py`](tools/compare_renders.py) in both directions, because it reports only sheets missing from its second argument.

### Repository

- The remote uses SSH, never HTTPS.
- The README is English only, with no translated copies.
