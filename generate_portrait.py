#!/usr/bin/env python3
"""
Generate a halftone-dot SVG portrait from a (background-removed) photo.

Usage:
    python3 generate_portrait.py assets/surya-1.png assets/surya.svg

It samples the image on a hex grid and draws one circle per cell, sized by
darkness — so light areas fade to nothing and the subject emerges as dots.
Transparent / white pixels are treated as background and left empty.

Requires: pillow, numpy   ->   pip install pillow numpy
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets/surya-1.png"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/surya.svg"

# --- tunables ---
UPSCALE = 2.6      # sample a finer grid for crisper detail
SPACING = 9.0      # distance between dots (smaller = more detail)
MAX_R   = 5.2      # largest dot radius
GAMMA   = 1.25     # darkness response curve
FLOOR   = 0.14     # skip cells lighter than this

im = Image.open(SRC)
W, H = int(im.size[0] * UPSCALE), int(im.size[1] * UPSCALE)
im = im.resize((W, H), Image.LANCZOS)

# foreground mask: alpha channel if present, else "not near-white"
if im.mode in ("RGBA", "LA") or "transparency" in im.info:
    rgba = im.convert("RGBA")
    alpha = np.asarray(rgba.split()[-1], float) / 255.0
    rgb = rgba.convert("RGB")
else:
    rgb = im.convert("RGB")
    whiteness = np.asarray(rgb, float).min(axis=2) / 255.0
    alpha = np.clip((0.93 - whiteness) / 0.06, 0, 1)

mask_img = Image.fromarray((alpha * 255).astype(np.uint8))
mask_img = mask_img.filter(ImageFilter.MinFilter(7))     # erode white halo
mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
mask = np.asarray(mask_img, float) / 255.0

# tones: boost local contrast for features, keep skin light
gray = ImageOps.grayscale(rgb)
tone = gray.filter(ImageFilter.UnsharpMask(radius=10, percent=150, threshold=2))
tone = ImageOps.autocontrast(tone, cutoff=1)
lum = np.asarray(tone, float) / 255.0
lum = np.clip(lum ** 0.80, 0, 1)
darkness = np.clip((1.0 - lum) ** 1.15, 0, 1)
eff = darkness * mask

# hex-grid sampling -> circles
dots, row, y = [], 0, SPACING * 0.5
while y < H:
    x = SPACING * 0.5 + (SPACING * 0.5 if row % 2 else 0)
    while x < W:
        v = eff[int(y), int(x)]
        if v > FLOOR:
            r = MAX_R * (v ** GAMMA)
            if r > 0.4:
                dots.append((x, y, r))
        x += SPACING
    y += SPACING * 0.866
    row += 1

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
       f'width="{W}" height="{H}" fill="currentColor" role="img" '
       f'aria-label="Halftone portrait">'
       + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}"/>' for x, y, r in dots)
       + '</svg>')
open(OUT, "w").write(svg)
print(f"{len(dots)} dots -> {OUT} ({len(svg)//1024} KB)")
