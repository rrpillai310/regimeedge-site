#!/usr/bin/env python3
"""
Generate the 1200x630 OG / Twitter share-card PNG for regimeedge.io.

Run from the repo root:
    python3 scripts/generate_og_image.py

Output:
    og-image.png  (1200x630, ~50 KB)

Matches the site's brand: dark navy background, green accent, JetBrains Mono
font. No external fonts required — falls back to a built-in mono if JetBrains
Mono isn't installed locally.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ── Brand tokens (mirror :root in index.html) ─────────────────────────────────
BG          = (6, 10, 18)           # var(--bg)
BG_CARD     = (11, 17, 32)          # var(--bg-card)
GREEN       = (0, 232, 122)         # var(--green)
GREEN_DIM   = (0, 168, 87)          # var(--green-dim)
TEXT        = (232, 240, 248)       # #e8f0f8 (h1 color in site)
MUTED       = (106, 117, 135)       # var(--muted)
BORDER      = (24, 36, 56)          # ~var(--green-border)

W, H = 1200, 630


def _load_font(size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    """
    Try in this order: JetBrains Mono (matches site), SF Mono on macOS,
    DejaVu Sans Mono (commonly bundled with Pillow), then PIL default.
    """
    candidates = [
        # macOS user-installed JetBrains Mono (after `brew install --cask font-jetbrains-mono`)
        f"/Library/Fonts/JetBrainsMono-{weight}.ttf",
        f"{Path.home()}/Library/Fonts/JetBrainsMono-{weight}.ttf",
        # macOS built-in mono fallbacks
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        # Linux fallbacks (so this works on any deploy host)
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except (OSError, IOError):
            continue
    # PIL's bitmap default — readable but not pretty
    return ImageFont.load_default()


def _draw_grid(d: ImageDraw.ImageDraw):
    """Subtle dot/grid background to match the site's grid pattern."""
    grid_color = (10, 16, 28)
    step = 60
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=grid_color, width=1)


def _draw_orb(img: Image.Image, cx: int, cy: int, radius: int, color: tuple[int, int, int], alpha: int):
    """Soft glow orb (Photoshop-style)."""
    orb = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(orb)
    for i in range(radius, 0, -2):
        a = int(alpha * (i / radius) ** 2)
        d.ellipse([(radius - i, radius - i), (radius + i, radius + i)], fill=(*color, a))
    img.paste(orb, (cx - radius, cy - radius), orb)


def _measure(d: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    """Pillow ≥10 uses textbbox; fall back to textsize on older versions."""
    if hasattr(d, "textbbox"):
        l, t, r, b = d.textbbox((0, 0), text, font=font)
        return r - l, b - t
    return d.textsize(text, font=font)


def generate(out_path: Path):
    img = Image.new("RGB", (W, H), BG)

    # Glow orbs (very subtle so foreground stays readable)
    _draw_orb(img, 1050, 100, 380, GREEN, alpha=24)
    _draw_orb(img, 120, 580, 320, (26, 63, 255), alpha=18)

    d = ImageDraw.Draw(img)
    _draw_grid(d)

    # Top accent border (matches the green border under the nav)
    d.line([(0, 0), (W, 0)], fill=GREEN, width=4)

    # Logo — top-left
    logo_font = _load_font(36, weight="Bold")
    d.text((60, 50), "[", font=logo_font, fill=GREEN_DIM)
    bw, bh = _measure(d, "[", logo_font)
    d.text((60 + bw + 6, 50), "REGIMEEDGE", font=logo_font, fill=GREEN)
    rw, _ = _measure(d, "REGIMEEDGE", logo_font)
    d.text((60 + bw + 6 + rw + 6, 50), "]", font=logo_font, fill=GREEN_DIM)

    # Tag line (uppercase mono, muted)
    tag_font = _load_font(20, weight="Medium")
    tag = "BUILT IN PUBLIC · LIVE API · NO BULLSHIT"
    d.text((60, 130), tag, font=tag_font, fill=GREEN_DIM)

    # Headline (white, large)
    h1_font = _load_font(78, weight="Bold")
    h1_line1 = "Sit out bad markets."
    h1_line2 = "Automatically."
    d.text((60, 175), h1_line1, font=h1_font, fill=TEXT)
    # "Automatically." in green (italic-feel via the green color, like the site's h1 em)
    _, line1_h = _measure(d, h1_line1, h1_font)
    d.text((60, 175 + line1_h + 6), h1_line2, font=h1_font, fill=GREEN)

    # Subhead — wraps neatly. Hand-tune line breaks because PIL has no native wrap.
    sub_font = _load_font(24, weight="Regular")
    sub_lines = [
        "A crypto signal bot that labels every market regime —",
        "TREND, RANGE, or STRESS — and refuses to trade in STRESS.",
        "Live API, public track record, methodology in the open.",
    ]
    y = 410
    for line in sub_lines:
        d.text((60, y), line, font=sub_font, fill=MUTED)
        y += 36

    # Bottom bar with URL on left, regime cards on right
    bar_y = 555
    d.line([(60, bar_y - 14), (W - 60, bar_y - 14)], fill=BORDER, width=1)

    url_font = _load_font(22, weight="Bold")
    d.text((60, bar_y), "regimeedge.io", font=url_font, fill=GREEN)

    # Mini regime pills on the bottom-right (TREND / RANGE / STRESS)
    pill_font = _load_font(15, weight="Bold")
    pills = [
        ("TREND",  (0, 232, 122), (10, 26, 18)),
        ("RANGE",  (227, 179, 65), (32, 25, 10)),
        ("STRESS", (248, 81, 73), (36, 14, 14)),
    ]
    pill_x = W - 60
    for label, fg, bg in reversed(pills):
        tw, th = _measure(d, label, pill_font)
        pw, ph = tw + 24, th + 14
        pill_x -= pw + 10
        d.rounded_rectangle(
            [(pill_x, bar_y - 3), (pill_x + pw, bar_y - 3 + ph)],
            radius=4, fill=bg, outline=fg, width=1,
        )
        d.text((pill_x + 12, bar_y + 1), label, font=pill_font, fill=fg)

    img.save(out_path, "PNG", optimize=True)
    print(f"  ✓ wrote {out_path}  ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "og-image.png"
    generate(out)
    print(f"\nNext: in index.html, the meta tags already point at og-image.png.")
    print(f"Verify the share preview after the next deploy at: https://www.opengraph.xyz/url/https%3A%2F%2Fregimeedge.io")
