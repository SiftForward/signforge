"""Example: rebuild the cyberpunk self-efficacy sign from this design session."""
from signforge import Sign, render

sign = Sign(
    width=28, height=10,
    style="cyberpunk", emblem="circuit",
    header="SELF-EFFICACY",
    lines=["EVERY FIX MAKES YOU", "HARDER TO BREAK."],
    sub="// BUILT BY EXPERIENCE //",
)

render(
    sign,
    svg_path="out/self_efficacy_cyberpunk.svg",
    dxf_path="out/self_efficacy_cyberpunk.dxf",
    png_preview="out/self_efficacy_cyberpunk.png",
)
print("Done.")
