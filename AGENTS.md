# AGENTS.md

Rules for any agent working in this repository. The [README](README.md) owns what the kit is, which file to print, assembly and how to regenerate the sheets. The generator is [`tools/fds_kit.py`](tools/fds_kit.py).

## Finishing punch

The kit is for anyone, so every sheet works with scissors or a craft knife alone. A corner and notch punch is optional finishing, and no dimension in any sheet depends on one. The owner's punch is the Toke e Crie Furador Cantoneira Arredondada e Entalhe, reference 17671, model FCAE01. One side rounds a corner. The other side cuts a notch where crease lines meet an edge, so flaps tuck in cleanly.

| Fact | Value | Source |
|:-----|:------|:-------|
| Opening | 1.5 mm | Product description, [Mercado Livre listing MLB24311450](https://www.mercadolivre.com.br/furador-cantoneira-arredondada-e-entalhe-toke-crie-cor-rosa-chiclete/p/MLB24311450) |
| Paper weight | 90 to 220 g/m2 | Same description |
| Corner radius | Unknown | Not published by the maker |
| Notch width and depth | Unknown | Not published by the maker |
| Corner shape | A quarter round that replaces a square corner | Product image on the same listing |
| Notch shape | A smooth concave scallop with curved shoulders, cut into a straight edge | Same image |

The maker's image shows three uses: rounded corners on cards, a notch that shapes the shoulders of a planner tab, and a notch at each point where an envelope's flap folds meet its edge.

### Where each sheet is punched

| Sheet | Rounded corners | Notches |
|:------|:----------------|:--------|
| Cover | All four corners of each cover | Both side edges at the spine, one notch spanning its two fold lines |
| Envelope, `TabLock` | The two tuck flap corners, the two flap corners at the opening and the two outer corners of each tab head | Same as the glued envelope |
| Envelope | The two tuck flap corners and the four glue flap corners | Both side edges at the top fold and at the bottom fold, and the opening edge at each side wall; each notch spans its two fold lines |

## Hard rules

### Cutting and folding

- Every piece cuts, folds and closes with scissors or a craft knife alone. Nothing may require the finishing punch, and no lock, slit or tab dimension may depend on the punch's size.
- New designs close without glue or tape, with a straight-cut tab and slit lock. The glued card jackets and the glued v6 envelope remain until a glue-free version replaces them.
- With the optional punch, every outer corner of a piece is rounded and every place where a fold line meets a cut edge is notched.
- The square shoulders of a lock tab stay square: they are what catches in the slit.
- A fold that ends at an inside corner gets no notch and no guide: the punch cannot seat there, and the cut already frees the fold.
- Every notch site carries a guide mark centered on the notch, for lining up the punch. The mark is very subtle and hard to see, so it never shows on the finished piece: a 1 mm tick at 20 percent black and 0.2 pt, lighter and thinner than the fold lines, running from the cut edge into the area the notch removes. The values are `NOTCH_GUIDE_MM`, `NOTCH_GUIDE_GRAY` and `NOTCH_GUIDE_WIDTH` in the generator. On the cover it sits at the middle of the spine on each side edge.
- The corner radius and notch size are unknown and stay irrelevant to every dimension, because the punch is optional.
- Cut and fold lines are straight: no curves. [`tools/check_curves.py`](tools/check_curves.py) checks it. The only curves on a finished piece come from the finishing punch.
- Cut lines are as faint as fold lines, and fold dashes stay sparse.
- A fold that wraps a disk leaves 4 mm: the 3 mm Quick Disk plus 1 mm tolerance.
- Every sheet cuts only horizontal and vertical lines; the card jackets ship only as `Square` sheets. [`tools/check_square_layout.py`](tools/check_square_layout.py) checks the jackets and the envelope.

### Artwork and text

- Artwork follows Nintendo's originals, and Japanese text is written the way Nintendo wrote the original jacket.
- All artwork is clipped from [`artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf`](artwork/FDS-Card-Jacket_A4_3up_Color_v1.pdf). Never delete or modify it; the generator converts it to black ink.

### Sheets

- Every sheet is `HomePrint-Mono`: black ink only, no color sheets and nothing for a print shop.
- Paper only: no manual, booklet or 3D-printed parts.
- Sheets are A4 and print at 100 percent.
- Glue flaps are large by default, and `StdGlue` card jackets use the smaller widths.
- Glue areas are blank: no gray tint and no `のりしろ` label on any sheet, and the ruler legend names only cut and fold lines.
- The envelope is a 1-up sheet: only right angles, a full-width tuck flap, and side flaps that start 10 mm below the bottom fold, so a punch has room to notch that fold, and end flush with the opening, so the opening is one straight cut. The glued v6 has 25 mm glue flaps and no steps.
- The `TabLock` envelope, v7, needs no glue: each 15 mm side flap folds inside against the back panel and carries a T-tab, a 10 mm head on a 6 mm neck 2 mm long, that pushes out through an 8 mm slit in the back panel. The slit is 2 mm shorter than the head, so the head squeezes through and its square shoulders catch. The tabs sit at the bottom of the back panel, the only band there free of artwork. The values are `LOCK_FLAP_MM` and the `TAB_*` constants in the generator.
- The three covers on the cover sheet sit 4 mm apart, so each has its own cut outline.
- A new variant is a new file. An existing sheet changes only when the owner names it.
- Regenerating every mode stays pixel-identical to the committed sheets. Run [`tools/compare_renders.py`](tools/compare_renders.py) in both directions, because it reports only sheets missing from its second argument.

### Repository

- The remote uses SSH, never HTTPS.
- The README is English only, with no translated copies.
