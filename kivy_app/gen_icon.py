# -*- coding: utf-8 -*-
"""
YiCORE Icon & Splash Generator v2.0
- Icon: Clean taiji, no scanlines, high contrast, 512x512
- Splash: Full-screen cyberpunk splash, 1080x1920
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os

HERE = os.path.dirname(os.path.abspath(__file__))

def _rounded_rect_mask(size, radius):
    """Create a rounded rectangle alpha mask."""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([(0, 0), (size - 1, size - 1)], radius=radius, fill=255)
    return mask


def gen_icon(size=512):
    """Generate a cyberpunk rounded-square icon with taiji + HUD elements."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    corner_r = size // 5  # rounded corner radius

    # --- Rounded square background: deep blue-purple gradient ---
    for py in range(size):
        for px in range(size):
            d = math.sqrt((px - cx)**2 + (py - cy)**2) / (size * 0.7)
            d = min(d, 1.0)
            r = int(14 + 12 * (1 - d))   # subtle purple tint
            g = int(8 + 6 * (1 - d))
            b = int(28 + 18 * (1 - d))   # blue-purple base
            img.putpixel((px, py), (r, g, b, 255))

    # --- Taiji circle ---
    R = int(size * 0.30)   # taiji radius (smaller, leaves room for HUD)
    hr = R // 2
    taiji_cy = cy - size // 20  # slightly above center

    for px in range(cx - R - 1, cx + R + 2):
        for py in range(taiji_cy - R - 1, taiji_cy + R + 2):
            if px < 0 or px >= size or py < 0 or py >= size:
                continue
            dx, dy = px - cx, py - taiji_cy
            dist_sq = dx * dx + dy * dy
            if dist_sq > R * R:
                continue

            d_up = math.sqrt(dx * dx + (dy + hr) ** 2)
            d_lo = math.sqrt(dx * dx + (dy - hr) ** 2)

            # S-curve logic
            if dy <= 0:
                is_yang = False if d_up <= hr else (dx < 0)
            else:
                is_yang = True if d_lo <= hr else (dx < 0)

            dist = math.sqrt(dist_sq)
            edge_fade = min(1.0, (R - dist) / max(1, R * 0.04))

            if is_yang:
                # Neon CYAN-BLUE half (yang) — bright electric blue
                t = 1 - dist / R
                br = 0.60 + 0.40 * t
                img.putpixel((px, py), (
                    int(20 * br * edge_fade),
                    int(200 * br * edge_fade),
                    int(255 * br * edge_fade), 255))
            else:
                # MAGENTA-PURPLE half (yin) — neon pink/purple glow
                t = 1 - dist / R
                br = 0.55 + 0.45 * t
                img.putpixel((px, py), (
                    int(200 * br * edge_fade),
                    int(40 * br * edge_fade),
                    int(220 * br * edge_fade), 255))

    # --- Fish eyes (SWAPPED: each eye is the OPPOSITE color of its half) ---
    # S-curve logic: upper-left = yang(cyan), upper semicircle lobe = yin(purple)
    # So the center (cx, taiji_cy - hr) is IN the yin lobe (purple area)
    # And the center (cx, taiji_cy + hr) is IN the yang lobe (cyan area)
    eye_r = int(R * 0.14)

    # Upper dot at (cx, taiji_cy - hr) is in PURPLE(yin) half → draw CYAN dot
    ey_up_cx, ey_up_cy = cx, taiji_cy - hr
    for px in range(ey_up_cx - eye_r - 1, ey_up_cx + eye_r + 2):
        for py in range(ey_up_cy - eye_r - 1, ey_up_cy + eye_r + 2):
            if px < 0 or px >= size or py < 0 or py >= size:
                continue
            dx, dy = px - ey_up_cx, py - ey_up_cy
            d = math.sqrt(dx*dx + dy*dy)
            if d <= eye_r:
                fade = 1 - d / eye_r
                # Bright CYAN dot (yang-color in yin-half)
                r_val = int(10 + 10 * fade)
                g_val = int(190 + 40 * fade)
                b_val = int(245 + 10 * fade)
                img.putpixel((px, py), (r_val, g_val, b_val, 255))

    # Lower dot at (cx, taiji_cy + hr) is in CYAN(yang) half → draw PURPLE dot
    ey_lo_cx, ey_lo_cy = cx, taiji_cy + hr
    for px in range(ey_lo_cx - eye_r - 1, ey_lo_cx + eye_r + 2):
        for py in range(ey_lo_cy - eye_r - 1, ey_lo_cy + eye_r + 2):
            if px < 0 or px >= size or py < 0 or py >= size:
                continue
            dx, dy = px - ey_lo_cx, py - ey_lo_cy
            d = math.sqrt(dx*dx + dy*dy)
            if d <= eye_r:
                fade = 1 - d / eye_r
                # Bright PURPLE dot (yin-color in yang-half)
                r_val = int(190 + 50 * fade)
                g_val = int(30 + 20 * fade)
                b_val = int(200 + 40 * fade)
                img.putpixel((px, py), (r_val, g_val, b_val, 255))

    # --- Taiji border (neon glow) ---
    for ring_r in range(R + 8, R + 2, -1):
        alpha = int(40 * (1 - (ring_r - R - 2) / 6))
        draw.ellipse([cx - ring_r, taiji_cy - ring_r,
                       cx + ring_r, taiji_cy + ring_r],
                     outline=(0, 222, 242, max(0, alpha)), width=2)
    draw.ellipse([cx - R - 1, taiji_cy - R - 1, cx + R + 1, taiji_cy + R + 1],
                 outline=(0, 222, 242, 200), width=2)

    # --- HUD corner brackets (cyberpunk signature) ---
    m = size // 6
    mw = 3
    mc = (0, 222, 242, 180)
    p = size // 16
    draw.line([(p, p + m), (p, p), (p + m, p)], fill=mc, width=mw)
    draw.line([(size - p - m, p), (size - p, p), (size - p, p + m)], fill=mc, width=mw)
    draw.line([(p, size - p - m), (p, size - p), (p + m, size - p)], fill=mc, width=mw)
    draw.line([(size - p - m, size - p), (size - p, size - p), (size - p, size - p - m)], fill=mc, width=mw)

    # (No scan lines — removed per design spec, affects clarity)

    # --- "YiCORE" text at bottom ---
    try:
        font_path = os.path.join(HERE, "NotoSansCJK.otf")
        font_label = ImageFont.truetype(font_path, size // 14)
    except Exception:
        font_label = ImageFont.load_default()

    def _tw_icon(text, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0]
        except AttributeError:
            w, h = draw.textsize(text, font=font)
            return w

    txt = "\u6613CORE"
    tw = _tw_icon(txt, font_label)
    text_y = taiji_cy + R + size // 16
    # Text glow
    draw.text((cx - tw // 2, text_y), txt,
              fill=(0, 222, 242, 200), font=font_label)

    # --- Tiny decorative dots ---
    dot_c = (0, 222, 242, 100)
    dot_r = 2
    for dx_off in [-R - 15, R + 15]:
        draw.ellipse([cx + dx_off - dot_r, taiji_cy - dot_r,
                       cx + dx_off + dot_r, taiji_cy + dot_r], fill=dot_c)

    # --- Apply rounded rectangle mask ---
    try:
        mask = _rounded_rect_mask(size, corner_r)
        # Compose: rounded icon over transparent
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        return result.convert("RGB")
    except Exception:
        # Fallback if rounded_rectangle not available (older Pillow)
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