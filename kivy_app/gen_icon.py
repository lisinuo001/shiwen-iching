# -*- coding: utf-8 -*-
"""
YiCORE Icon & Splash Generator v2.0
- Icon: Clean taiji, no scanlines, high contrast, 512x512
- Splash: Full-screen cyberpunk splash, 1080x1920
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))

def gen_icon(size=512):
    """Generate a clean, high-contrast cyberpunk taiji icon with proper S-curve."""
    img = Image.new("RGBA", (size, size), (15, 17, 25, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    R = int(size * 0.42)  # main circle radius (slightly larger)
    hr = R // 2            # half-radius for S-curve semicircles

    # Background: subtle radial gradient
    for i in range(size):
        for j in range(size):
            d = math.sqrt((i - cx)**2 + (j - cy)**2) / (size * 0.7)
            v = max(0, int(18 - d * 14))
            img.putpixel((i, j), (v + 8, v + 10, v + 18, 255))

    # --- Classic Taiji using polar angle method ---
    # The S-curve boundary is defined by:
    #   - In the top half (dy < 0): the boundary curves around a semicircle
    #     centered at (cx, cy - hr), radius hr
    #   - In the bottom half (dy >= 0): the boundary curves around a semicircle
    #     centered at (cx, cy + hr), radius hr
    # A point is "yang" (cyan) if it is on the LEFT side of the S-curve.

    for px in range(cx - R - 1, cx + R + 2):
        for py in range(cy - R - 1, cy + R + 2):
            dx, dy = px - cx, py - cy
            dist_sq = dx * dx + dy * dy
            if dist_sq > R * R:
                continue

            # Distance from upper and lower semicircle centers
            d_up = math.sqrt(dx * dx + (dy + hr) ** 2)
            d_lo = math.sqrt(dx * dx + (dy - hr) ** 2)

            # Classic taiji S-curve logic:
            #   Upper half: left is yang, except inside upper semicircle (yin lobe)
            #   Lower half: left is yin, except inside lower semicircle (yang lobe)
            if dy <= 0:
                if d_up <= hr:
                    is_yang = False  # yin lobe curving into upper half
                else:
                    is_yang = (dx < 0)  # left side = yang
            else:
                if d_lo <= hr:
                    is_yang = True   # yang lobe curving into lower half
                else:
                    is_yang = (dx < 0)  # left side = yang (continues from top)

            dist = math.sqrt(dist_sq)
            edge_fade = min(1.0, (R - dist) / max(1, R * 0.03))  # anti-alias edge

            if is_yang:
                # Cyan side with subtle gradient (brighter near center)
                t = 1 - dist / R
                br = 0.75 + 0.25 * t
                g_val = int(222 * br * edge_fade)
                b_val = int(242 * br * edge_fade)
                r_val = int(10 * br * edge_fade)
                img.putpixel((px, py), (r_val, g_val, b_val, 255))
            else:
                # Dark side
                t = 1 - dist / R
                br = 0.15 + 0.20 * t
                v = int(50 * br * edge_fade)
                img.putpixel((px, py), (v, v + 1, v + 5, 255))

    # --- Fish eyes ---
    eye_r = int(R * 0.11)  # ~11% of main radius

    # Yin eye (dark dot) in yang (cyan) half — upper-left area, at (cx, cy - hr)
    eye_cx_yin, eye_cy_yin = cx, cy - hr
    for px in range(eye_cx_yin - eye_r - 1, eye_cx_yin + eye_r + 2):
        for py in range(eye_cy_yin - eye_r - 1, eye_cy_yin + eye_r + 2):
            dx, dy = px - eye_cx_yin, py - eye_cy_yin
            d = math.sqrt(dx*dx + dy*dy)
            if d <= eye_r:
                fade = 1 - d / eye_r
                # Sphere-like shading (darker at edges, slightly lighter center)
                v = int(22 + 20 * fade)
                img.putpixel((px, py), (v, v + 1, v + 3, 255))

    # Yang eye (bright dot) in yin (dark) half — lower-right area, at (cx, cy + hr)
    eye_cx_yang, eye_cy_yang = cx, cy + hr
    for px in range(eye_cx_yang - eye_r - 1, eye_cx_yang + eye_r + 2):
        for py in range(eye_cy_yang - eye_r - 1, eye_cy_yang + eye_r + 2):
            dx, dy = px - eye_cx_yang, py - eye_cy_yang
            d = math.sqrt(dx*dx + dy*dy)
            if d <= eye_r:
                fade = 1 - d / eye_r
                g_val = int(160 + 62 * fade)
                b_val = int(180 + 62 * fade)
                img.putpixel((px, py), (0, g_val, b_val, 255))

    # --- Outer glow rings ---
    for ring_r in range(R + 18, R + 6, -1):
        alpha = int(18 * (1 - (ring_r - R - 6) / 12))
        draw.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
                     outline=(0, 222, 242, max(0, alpha)), width=2)

    # --- Clean main circle border ---
    draw.ellipse([cx - R - 1, cy - R - 1, cx + R + 1, cy + R + 1],
                 outline=(0, 222, 242, 230), width=3)

    # --- Corner chamfer brackets (cyberpunk) ---
    m = size // 7
    mw = 2
    mc = (0, 222, 242, 140)
    p = 6  # padding from edge
    draw.line([(p, p + m), (p, p), (p + m, p)], fill=mc, width=mw)
    draw.line([(size - p - m, p), (size - p, p), (size - p, p + m)], fill=mc, width=mw)
    draw.line([(p, size - p - m), (p, size - p), (p + m, size - p)], fill=mc, width=mw)
    draw.line([(size - p - m, size - p), (size - p, size - p), (size - p, size - p - m)], fill=mc, width=mw)

    # --- Subtle "YiCORE" text below circle ---
    try:
        font_path = os.path.join(HERE, "NotoSansCJK.otf")
        font_tiny = ImageFont.truetype(font_path, size // 20)
    except Exception:
        font_tiny = ImageFont.load_default()

    def _tw_icon(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]
        except AttributeError:
            w, h = draw.textsize(text, font=font)
            return w

    txt = "YiCORE"
    tw = _tw_icon(txt, font_tiny)
    draw.text((cx - tw // 2, cy + R + 16), txt,
              fill=(0, 222, 242, 80), font=font_tiny)

    return img.convert("RGB")


def gen_splash(width=1080, height=1920):
    """Generate a full-screen cyberpunk splash screen."""
    img = Image.new("RGBA", (width, height), (15, 17, 25, 255))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2

    # Background: radial gradient from center
    for y in range(height):
        for x in range(width):
            d = math.sqrt((x - cx)**2 + (y - cy)**2) / (max(width, height) * 0.6)
            d = min(d, 1.0)
            r = int(15 + 8 * (1 - d))
            g = int(17 + 10 * (1 - d))
            b = int(25 + 15 * (1 - d))
            img.putpixel((x, y), (r, g, b, 255))

    # Grid lines (very subtle)
    grid_c = (0, 222, 242, 12)
    for gx in range(0, width, 60):
        draw.line([(gx, 0), (gx, height)], fill=grid_c, width=1)
    for gy in range(0, height, 60):
        draw.line([(0, gy), (width, gy)], fill=grid_c, width=1)

    # Central taiji (drawn directly on splash, not pasted as opaque square)
    taiji_size = min(width, height) // 3
    taiji_img = gen_icon(taiji_size)
    taiji_rgba = taiji_img.convert("RGBA")
    tx = cx - taiji_size // 2
    ty = cy - taiji_size // 2 - height // 10  # slightly above center
    # Create a mask: pixels close to the BG color become transparent
    taiji_data = taiji_rgba.load()
    for yi in range(taiji_size):
        for xi in range(taiji_size):
            r_p, g_p, b_p, a_p = taiji_data[xi, yi]
            # Background color is approximately (8-18, 10-20, 18-30)
            # If pixel is very dark AND not part of the taiji circle, make transparent
            # Use distance from center to detect outside-circle pixels
            ddx = xi - taiji_size // 2
            ddy = yi - taiji_size // 2
            circle_r = int(taiji_size * 0.42) + 20  # slightly larger than icon circle
            if ddx * ddx + ddy * ddy > circle_r * circle_r:
                taiji_data[xi, yi] = (r_p, g_p, b_p, 0)
    img.paste(taiji_rgba, (tx, ty), taiji_rgba)

    # Horizontal accent lines
    line_y1 = ty - 30
    line_y2 = ty + taiji_size + 30
    draw.line([(width // 6, line_y1), (width * 5 // 6, line_y1)],
              fill=(0, 222, 242, 60), width=1)
    draw.line([(width // 6, line_y2), (width * 5 // 6, line_y2)],
              fill=(0, 222, 242, 60), width=1)

    # Title text "易CORE" - large
    title_y = line_y2 + 60
    try:
        font_path = os.path.join(HERE, "NotoSansCJK.otf")
        font_big = ImageFont.truetype(font_path, 96)
        font_sub = ImageFont.truetype(font_path, 28)
        font_tiny = ImageFont.truetype(font_path, 18)
    except Exception:
        font_big = ImageFont.load_default()
        font_sub = font_big
        font_tiny = font_big

    # Helper for text width (compat with old and new Pillow)
    def _tw(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]
        except AttributeError:
            w, h = draw.textsize(text, font=font)
            return w

    # "易CORE"
    tw = _tw("\u6613CORE", font_big)
    draw.text((cx - tw // 2, title_y), "\u6613CORE",
              fill=(0, 222, 242, 240), font=font_big)

    # "YiCORE DIVINATION SYSTEM"
    sub_text = "YiCORE DIVINATION SYSTEM"
    sw = _tw(sub_text, font_sub)
    draw.text((cx - sw // 2, title_y + 120), sub_text,
              fill=(102, 112, 138, 180), font=font_sub)

    # Version text at bottom
    ver_text = "v11.0  |  INITIALIZING..."
    vw = _tw(ver_text, font_tiny)
    draw.text((cx - vw // 2, height - 120), ver_text,
              fill=(102, 112, 138, 120), font=font_tiny)

    # Corner brackets
    blen = 80
    bc = (0, 222, 242, 100)
    bw = 2
    draw.line([(40, 40 + blen), (40, 40), (40 + blen, 40)], fill=bc, width=bw)
    draw.line([(width - 40 - blen, 40), (width - 40, 40), (width - 40, 40 + blen)], fill=bc, width=bw)
    draw.line([(40, height - 40 - blen), (40, height - 40), (40 + blen, height - 40)], fill=bc, width=bw)
    draw.line([(width - 40 - blen, height - 40), (width - 40, height - 40), (width - 40, height - 40 - blen)], fill=bc, width=bw)

    # Bottom bar
    bar_y = height - 60
    draw.rectangle([(0, bar_y), (width, bar_y + 2)], fill=(0, 222, 242, 40))

    return img.convert("RGB")


if __name__ == "__main__":
    print("Generating icon (512x512)...")
    icon = gen_icon(512)
    icon.save(os.path.join(HERE, "icon.png"))
    print("  -> icon.png saved")

    print("Generating splash (1080x1920)...")
    splash = gen_splash(1080, 1920)
    splash.save(os.path.join(HERE, "presplash.png"))
    print("  -> presplash.png saved")

    print("Done!")