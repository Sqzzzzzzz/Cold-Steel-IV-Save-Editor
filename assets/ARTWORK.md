# Artwork

`cs4_cover.jpg` is the Cold Steel IV cover image supplied by the user as
`IMG_0440.jpeg` for this editor background. The asset is copied byte-for-byte;
Qt scales it proportionally and crops it to fill the window. Existing dark blue
and vignette overlays preserve readable text, while glass panels sample the
same image coordinates. No AI image generation or image retouching was used.
The artwork and logo belong to their respective rights holders.

The earlier academy images are retained only as historical project assets;
they are no longer loaded by the CS4 window.

`hud_arrow_up.svg`, `hud_arrow_down.svg`, and `hud_check.svg` are original
code-drawn control symbols. Navigation pictograms and glass frames are drawn
in `qt_hud_widgets.py`. Shared CS3 item imagery is documented in
`icons/original/sources.json`. All 31 master-quartz textures were extracted
from the owner's CS4 `assets.pka`, with each decoded member checked against
the archive SHA-256. The PNGs preserve decoded source pixels; Qt clips their
opaque UV corners into round UI icons. Other item families retain CS3 art.
Reproduction: `python tools/extract_cs4_master_icons.py <assets.pka>`.
