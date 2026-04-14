# -*- coding: utf-8 -*-
"""
YiCORE v11.0 - Cyberpunk HUD Divination Console
Design Spec: DESIGN_SPEC.md v1.0 (frozen 2026-04-10)
"""
import random, os, sys, math, time
from kivy.app import App
# ScreenManager removed in v10.8 — direct BoxLayout page switching
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, Triangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.text import Label as CoreLabel
from kivy.metrics import dp, sp
from kivy.resources import resource_add_path, resource_find
# ==== DESIGN CONSTRAINTS (from DESIGN_SPEC.md) ====
# DO NOT use RoundedRectangle for any panel/card/button
# ALL containers must use 45-degree chamfered polygon
# Chamfer: large=dp(10), small=dp(8), button=dp(10)
# Border: glow(dp4,a0.20) + main(dp1.2) + corner_ticks(dp7,dp1.1)
# Scanlines: dp(4) spacing, white a0.010
# Top accent band: dp(2) height
# NO external image resources

# ---- Font ----
def _find_font():
    for p in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK.otf"),
        os.path.join(os.getcwd(), "NotoSansCJK.otf"),
    ]:
        if os.path.exists(p):
            return p
    return resource_find("NotoSansCJK.otf")

_fp = _find_font()
if _fp:
    for n in ("NotoSansCJK", "Roboto"):
        LabelBase.register(name=n, fn_regular=_fp)
    CN = "NotoSansCJK"
else:
    CN = "Roboto"

# ---- Palette (DESIGN_SPEC Section 3) ----
BG      = [0.06, 0.07, 0.11, 1]
CARD    = [0.11, 0.12, 0.18, 1]
CARD_HI = [0.15, 0.16, 0.24, 1]
CYAN    = [0.00, 0.87, 0.95, 1]
GOLD    = [1.00, 0.84, 0.20, 1]
PINK    = [0.96, 0.26, 0.58, 1]
GREEN   = [0.30, 0.92, 0.40, 1]
PURP    = [0.62, 0.40, 0.98, 1]
DIM     = [0.40, 0.44, 0.54, 1]
WHITE   = [0.94, 0.95, 0.97, 1]
SOFT    = [0.68, 0.72, 0.80, 1]

Window.clearcolor = BG

# ---- Data ----
TRIGRAMS = {
    (1,1,1): ("\u4e7e","\u2630","\u5929"), (0,0,0): ("\u5764","\u2637","\u5730"),
    (1,0,0): ("\u9707","\u2633","\u96f7"), (0,0,1): ("\u826e","\u2636","\u5c71"),
    (0,1,1): ("\u5dfd","\u2634","\u98ce"), (1,1,0): ("\u5151","\u2631","\u6cfd"),
    (1,0,1): ("\u574e","\u2635","\u6c34"), (0,1,0): ("\u79bb","\u2632","\u706b"),
}

def _load():
    d = os.path.dirname(os.path.abspath(__file__))
    for p in [d, os.path.dirname(d), os.getcwd()]:
        if p and p not in sys.path:
            sys.path.insert(0, p)
    try:
        from iching_data import HEXAGRAMS
        from yaoci_data import get_yaoci
        return HEXAGRAMS, get_yaoci
    except Exception:
        return {}, lambda k, i: ("\u723B\u8f9e\u5f85\u67e5", "\u6570\u636e\u52a0\u8f7d\u5931\u8d25")

HEXAGRAMS, get_yaoci = _load()
YN = ["\u521d\u723B","\u4e8c\u723B","\u4e09\u723B","\u56db\u723B","\u4e94\u723B","\u4e0a\u723B"]

# ---- Chamfered polygon (DESIGN_SPEC Section 2) ----
def _cpts(x, y, w, h, c):
    return [x+c,y+h, x+w,y+h, x+w,y+c, x+w-c,y, x,y, x,y+h-c]

def draw_chamfer_box(canvas, x, y, w, h, col_rgb, cut=None,
                     border_a=0.30, glow_a=0.20, scanlines=True, band=True,
                     fill_col=None):
    """Draw a chamfered panel per DESIGN_SPEC Section 2."""
    c = cut or dp(10)
    r, g, b = col_rgb[:3]
    pts = _cpts(x, y, w, h, c)
    cx, cy = x + w/2, y + h/2
    fc = fill_col or CARD[:3]
    with canvas:
        # fill
        Color(*fc, 1)
        for i in range(0, len(pts), 2):
            ni = (i+2) % len(pts)
            Triangle(points=[cx, cy, pts[i], pts[i+1], pts[ni], pts[ni+1]])
        # scanlines (Spec 2.4)
        if scanlines and h > dp(20):
            Color(1, 1, 1, 0.010)
            sy = y + dp(4)
            while sy < y + h - dp(4):
                Rectangle(pos=(x+dp(4), sy), size=(w-dp(8), dp(1)))
                sy += dp(4)
        # top accent band (Spec 2.3)
        if band:
            Color(r, g, b, border_a * 0.8)
            Rectangle(pos=(x, y+h-dp(2)), size=(w, dp(2)))
        # glow border (Spec 2.2 layer 1)
        bpts = pts + [pts[0], pts[1]]
        Color(r, g, b, glow_a)
        Line(points=bpts, width=dp(4), close=False)
        # main border (Spec 2.2 layer 2)
        Color(r, g, b, border_a)
        Line(points=bpts, width=dp(1.2), close=False)
        # corner ticks (Spec 2.2 layer 3)
        cs = dp(7)
        Color(r, g, b, min(border_a * 1.6, 0.85))
        Line(points=[x, y+cs, x, y, x+cs, y], width=dp(1.1))
        Line(points=[x+w-cs, y, x+w, y, x+w, y+cs], width=dp(1.1))
        Line(points=[x, y+h-cs, x, y+h, x+cs, y+h], width=dp(1.1))
        Line(points=[x+w-cs, y+h, x+w, y+h, x+w, y+h-cs], width=dp(1.1))

# ---- Canvas text helper ----
def draw_text(canvas, text, x, y, font_size, color, center_x=None):
    cl = CoreLabel(text=text, font_name=CN, font_size=font_size, color=(1,1,1,1))
    cl.refresh()
    tex = cl.texture
    if not tex: return 0, 0
    tw, th = tex.size
    if center_x is not None:
        x = center_x - tw/2
    r, g, b = color[:3]
    a = color[3] if len(color) > 3 else 1.0
    with canvas:
        Color(r, g, b, a)
        Rectangle(pos=(x, y), size=(tw, th), texture=tex)
    return tw, th

# ---- Smoke particles ----
class _P:
    __slots__ = ('x','y','r','vx','vy','a','da','col')
    def __init__(self, cx, cy, col):
        self.x = cx + random.uniform(-dp(14), dp(14))
        self.y = cy + random.uniform(-dp(8), dp(8))
        self.r = random.uniform(dp(2), dp(5))
        self.vx = random.uniform(-dp(0.5), dp(0.5))
        self.vy = random.uniform(dp(0.6), dp(1.5))
        self.a = random.uniform(0.55, 0.90)
        self.da = random.uniform(0.018, 0.035)
        self.col = col

class SmokeLayer(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._ps = []; self._ev = None
        self.size_hint = (None, None); self.size = (1, 1)
    def burst(self, cx, cy, col):
        for _ in range(16):
            self._ps.append(_P(cx, cy, col))
        if not self._ev:
            self._ev = Clock.schedule_interval(self._tick, 0.025)
    def _tick(self, dt):
        for p in self._ps:
            p.x += p.vx; p.y += p.vy; p.r += dp(0.18); p.a -= p.da
        self._ps = [p for p in self._ps if p.a > 0.02]
        if not self._ps and self._ev:
            self._ev.cancel(); self._ev = None
        self._draw()
    def _draw(self):
        self.canvas.clear()
        with self.canvas:
            for p in self._ps:
                Color(*p.col, p.a * 0.5)
                Ellipse(pos=(p.x-p.r, p.y-p.r), size=(p.r*2, p.r*2))

# ---- Draw yao line helper ----
def draw_yao_line(canvas, x, cy, w, is_yang, col, lw=None):
    lw = lw or dp(3)
    r, g, b = col[:3]
    gap = w * 0.18
    with canvas:
        Color(r, g, b, 0.15)
        if is_yang:
            Line(points=[x, cy, x+w, cy], width=lw*2)
        else:
            Line(points=[x, cy, x+w/2-gap/2, cy], width=lw*2)
            Line(points=[x+w/2+gap/2, cy, x+w, cy], width=lw*2)
        Color(r, g, b, 0.92)
        if is_yang:
            Line(points=[x, cy, x+w, cy], width=lw)
        else:
            Line(points=[x, cy, x+w/2-gap/2, cy], width=lw)
            Line(points=[x+w/2+gap/2, cy, x+w, cy], width=lw)

# ---- 7-segment LED digit helper ----
# Segments: a(top), b(top-right), c(bot-right), d(bot), e(bot-left), f(top-left), g(mid)
_SEG_MAP = {
    '0': (1,1,1,1,1,1,0),
    '1': (0,1,1,0,0,0,0),
}

def draw_led_digit(canvas, digit, cx, cy, dw, dh, col, lw=None):
    """Draw a 7-segment style digit centered at (cx, cy)."""
    lw = lw or dp(2.5)
    segs = _SEG_MAP.get(digit, (0,0,0,0,0,0,0))
    r, g, b = col[:3]
    hw, hh = dw/2, dh/2
    gap = dp(1.5)  # gap between segments
    x0, x1 = cx - hw, cx + hw
    y0, y1, ym = cy - hh, cy + hh, cy
    # segment definitions: (x_start, y_start, x_end, y_end)
    seg_pts = [
        (x0+gap, y1, x1-gap, y1),           # a - top horizontal
        (x1, y1-gap, x1, ym+gap),            # b - top right vertical
        (x1, ym-gap, x1, y0+gap),            # c - bot right vertical
        (x0+gap, y0, x1-gap, y0),            # d - bot horizontal
        (x0, ym-gap, x0, y0+gap),            # e - bot left vertical
        (x0, y1-gap, x0, ym+gap),            # f - top left vertical
        (x0+gap, ym, x1-gap, ym),            # g - mid horizontal
    ]
    with canvas:
        for i, on in enumerate(segs):
            if on:
                Color(r, g, b, 0.92)
                Line(points=[seg_pts[i][0], seg_pts[i][1], seg_pts[i][2], seg_pts[i][3]], width=lw, cap='square')
                # glow
                Color(r, g, b, 0.15)
                Line(points=[seg_pts[i][0], seg_pts[i][1], seg_pts[i][2], seg_pts[i][3]], width=lw*2.5, cap='square')
            else:
                Color(r, g, b, 0.06)
                Line(points=[seg_pts[i][0], seg_pts[i][1], seg_pts[i][2], seg_pts[i][3]], width=lw*0.6, cap='square')

# ---- YaoSlot: one row showing 0/1 + yao line (Widget + child Labels) ----
class YaoSlot(Widget):
    """A single yao display row. Widget base with manually positioned child Labels."""
    def __init__(self, idx, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.state = 'empty'
        self._val = None
        # child labels
        self._lbl_name = Label(text=YN[idx], font_name=CN, font_size=sp(12),
            color=(*DIM[:3], 0.30), halign='center', valign='middle')
        self._lbl_name.bind(size=lambda w, s: setattr(w, 'text_size', s))
        self.add_widget(self._lbl_name)
        self._lbl_digit = Label(text="-", font_name=CN, font_size=sp(26),
            color=(*DIM[:3], 0.15), bold=True, halign='center', valign='middle')
        self._lbl_digit.bind(size=lambda w, s: setattr(w, 'text_size', s))
        self.add_widget(self._lbl_digit)
        self._lbl_type = Label(text="", font_name=CN, font_size=sp(11),
            color=(*DIM[:3], 0.30), halign='center', valign='middle')
        self._lbl_type.bind(size=lambda w, s: setattr(w, 'text_size', s))
        self.add_widget(self._lbl_type)
        self.bind(pos=self._layout, size=self._layout)
        Clock.schedule_once(lambda dt: self._layout(), 0)

    def _layout(self, *_):
        x, y, w, h = self.x, self.y, self.width, self.height
        # name: left 10%
        nw = dp(36)
        self._lbl_name.pos = (x, y)
        self._lbl_name.size = (nw, h)
        # digit: next 15%
        dw = dp(44)
        self._lbl_digit.pos = (x + nw, y)
        self._lbl_digit.size = (dw, h)
        # type: right 12%
        tw = dp(40)
        self._lbl_type.pos = (x + w - tw, y)
        self._lbl_type.size = (tw, h)
        self._draw()

    def reveal(self, is_yang):
        self._val = is_yang
        self.state = 'revealed'
        col = GOLD if is_yang else CYAN
        self._lbl_name.color = (*col[:3], 0.70)
        self._lbl_digit.text = "1" if is_yang else "0"
        self._lbl_digit.color = col
        self._lbl_digit.font_size = sp(28)
        typ = "\u9633" if is_yang else "\u9634"
        self._lbl_type.text = typ + "\u723B"
        self._lbl_type.color = (*col[:3], 0.55)
        self._draw()

    def reset(self):
        self.state = 'empty'
        self._val = None
        self._lbl_name.color = (*DIM[:3], 0.30)
        self._lbl_digit.text = "-"
        self._lbl_digit.color = (*DIM[:3], 0.15)
        self._lbl_digit.font_size = sp(26)
        self._lbl_type.text = ""
        self._draw()

    def _draw(self, *_):
        self.canvas.before.clear()
        self.canvas.after.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 4 or h < 4:
            return
        with self.canvas.before:
            if self.state == 'empty':
                Color(*DIM[:3], 0.08)
                Rectangle(pos=(x, y + h/2 - dp(0.5)), size=(w, dp(1)))
            else:
                bg_c = [0.14, 0.12, 0.04] if self._val else [0.04, 0.10, 0.14]
                Color(*bg_c, 0.5)
                Rectangle(pos=(x, y + dp(1)), size=(w, h - dp(2)))
        # draw yao line in canvas.after (on top of labels)
        if self.state == 'revealed' and self._val is not None:
            nw = dp(36)
            dw = dp(44)
            tw = dp(40)
            lx = x + nw + dw + dp(4)
            lw = w - nw - dw - tw - dp(8)
            if lw > dp(10):
                col = GOLD[:3] if self._val else CYAN[:3]
                draw_yao_line(self.canvas.after, lx, y + h/2, lw, self._val, col, dp(2.5))

# ---- HoldButton with idle glow effect (#5) ----
class HoldButton(Widget):
    HOLD = 1.5
    def __init__(self, on_complete=None, **kw):
        super().__init__(**kw)
        self._cb = on_complete
        self._hold = False; self._prog = 0; self._done = False; self._ev = None
        self._phase = 0
        self.size_hint_y = None; self.height = dp(72)
        # Overlaid native labels for text
        self._lbl_cn = Label(text="\u6309\u4f4f \u00b7 \u542f\u52a8CORE", font_name=CN,
            font_size=sp(20), color=WHITE, bold=True, halign='center', valign='bottom',
            markup=True)
        self._lbl_cn.bind(size=lambda w,s: setattr(w,'text_size',s))
        self._lbl_en = Label(text="HOLD 1.5s", font_name=CN,
            font_size=sp(11), color=(*PINK[:3], 0.45), halign='center', valign='top',
            markup=True)
        self._lbl_en.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._lbl_cn)
        self.add_widget(self._lbl_en)
        self._idle_ev = Clock.schedule_interval(self._idle_tick, 0.030)
        self.bind(pos=self._layout, size=self._layout)
        Clock.schedule_once(lambda dt: self._layout(), 0)

    def _layout(self, *_):
        """Position child labels to match this widget's pos/size."""
        x, y, w, h = self.x, self.y, self.width, self.height
        mid = y + h / 2
        self._lbl_cn.pos = (x, mid)
        self._lbl_cn.size = (w, h / 2)
        self._lbl_en.pos = (x, y)
        self._lbl_en.size = (w, h / 2)
        self._draw_bg()

    def _idle_tick(self, dt):
        if not self._hold and not self._done:
            self._phase += dt
            self._draw_bg()

    def _update_labels(self):
        if self._done:
            self._lbl_cn.text = "CORE \u5df2\u542f\u52a8"
            self._lbl_cn.color = GREEN
            self._lbl_en.text = "DIVINATION COMPLETE"
            self._lbl_en.color = (*GREEN[:3], 0.45)
        elif self._hold:
            pct = int(self._prog * 100)
            self._lbl_cn.text = f"\u542f\u52a8CORE {pct}%"
            self._lbl_cn.color = GREEN
            self._lbl_en.text = "CHANNELING"
            self._lbl_en.color = (*GREEN[:3], 0.45)
        else:
            self._lbl_cn.text = "\u6309\u4f4f \u00b7 \u542f\u52a8CORE"
            self._lbl_cn.color = WHITE
            self._lbl_en.text = "HOLD 1.5s"
            self._lbl_en.color = (*PINK[:3], 0.45)

    def _draw_bg(self, *_):
        self.canvas.before.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        p = self._prog
        if self._done: mc = GREEN[:3]
        elif self._hold: mc = GREEN[:3]
        else: mc = PINK[:3]

        idle_glow = 0
        if not self._hold and not self._done:
            idle_glow = 0.5 + 0.5 * math.sin(self._phase * 2 * math.pi / 1.5)

        ba = 0.50 if self._hold else (0.25 + 0.15 * idle_glow)
        ga = 0.18 if self._hold else (0.08 + 0.12 * idle_glow)

        draw_chamfer_box(self.canvas.before, x, y, w, h, mc,
                         border_a=ba, glow_a=ga)
        if p > 0:
            pw = max(dp(4), (w - dp(6)) * p)
            with self.canvas.before:
                Color(*GREEN[:3], 0.18)
                Rectangle(pos=(x+dp(3), y+dp(3)), size=(pw, h-dp(6)))

        if not self._hold and not self._done:
            with self.canvas.before:
                Color(*mc, 0.06 * idle_glow)
                pts = _cpts(x-dp(3), y-dp(3), w+dp(6), h+dp(6), dp(12))
                bpts = pts + [pts[0], pts[1]]
                Line(points=bpts, width=dp(2), close=False)

    def on_touch_down(self, t):
        if self._done or not self.collide_point(*t.pos): return False
        self._hold = True; self._prog = 0
        if self._ev: self._ev.cancel()
        self._ev = Clock.schedule_interval(self._tick, 0.025)
        self._update_labels(); self._draw_bg(); return True
    def on_touch_up(self, t):
        if not self._hold: return False
        self._hold = False
        if self._ev: self._ev.cancel()
        if self._prog < 1.0: self._prog = 0
        self._update_labels(); self._draw_bg()
        return True
    def _tick(self, dt):
        self._prog += dt / self.HOLD
        if self._prog >= 1.0:
            self._prog = 1.0; self._done = True; self._ev.cancel(); self._hold = False
            self._update_labels(); self._draw_bg()
            if self._cb: self._cb()
        else:
            self._update_labels(); self._draw_bg()
    def reset(self):
        if self._ev: self._ev.cancel()
        self._prog = 0; self._hold = False; self._done = False
        self._update_labels(); self._draw_bg()

# ---- TapButton: Chinese big English small (#6) ----
class TapButton(Widget):
    def __init__(self, text_cn, text_en="", col=None, on_press=None, **kw):
        h = kw.pop('height', dp(44))
        super().__init__(**kw)
        self._col = col or CYAN; self._on_press = on_press; self._pressed = False
        self._has_en = bool(text_en)
        self.size_hint_y = None; self.height = h
        self._lbl_cn = Label(text=text_cn, font_name=CN, font_size=sp(16),
            color=(*self._col[:3], 0.90), bold=True, halign='center',
            valign='bottom' if text_en else 'middle')
        self._lbl_cn.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._lbl_cn)
        self._lbl_en = None
        if text_en:
            self._lbl_en = Label(text=text_en, font_name=CN, font_size=sp(11),
                color=(*self._col[:3], 0.40), halign='center', valign='top')
            self._lbl_en.bind(size=lambda w,s: setattr(w,'text_size',s))
            self.add_widget(self._lbl_en)
        self.bind(pos=self._layout, size=self._layout)
        Clock.schedule_once(lambda dt: self._layout(), 0)

    def _layout(self, *_):
        x, y, w, h = self.x, self.y, self.width, self.height
        if self._has_en and self._lbl_en:
            mid = y + h / 2
            self._lbl_cn.pos = (x, mid)
            self._lbl_cn.size = (w, h / 2)
            self._lbl_en.pos = (x, y)
            self._lbl_en.size = (w, h / 2)
        else:
            self._lbl_cn.pos = (x, y)
            self._lbl_cn.size = (w, h)
        self._redraw()

    def _redraw(self, *_):
        self.canvas.before.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        draw_chamfer_box(self.canvas.before, x, y, w, h, self._col[:3],
                         cut=dp(10), border_a=0.35 if self._pressed else 0.22,
                         glow_a=0.10 if self._pressed else 0.05, scanlines=False, band=False)
    def on_touch_down(self, t):
        if not self.collide_point(*t.pos): return False
        self._pressed = True; self._redraw(); return True
    def on_touch_up(self, t):
        if not self._pressed: return False
        self._pressed = False; self._redraw()
        if self.collide_point(*t.pos) and self._on_press: self._on_press()
        return True

# ---- HexagramDisplay (result page, 6 yao lines) ----
class HexagramDisplay(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._bits = None
        self.bind(pos=self._draw, size=self._draw)
    def set_bits(self, bits):
        self._bits = bits; self._draw()
    def _draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        if not self._bits or w < 4 or h < 4: return
        draw_chamfer_box(self.canvas, x, y, w, h, CYAN[:3],
                         border_a=0.22, glow_a=0.10)
        pad = dp(10)
        ix, iy, iw, ih = x+pad, y+pad, w-2*pad, h-2*pad
        gap_y = ih / 5 if len(self._bits) > 1 else 0
        lw = max(dp(3), min(ih * 0.07, dp(5)))
        for i, bit in enumerate(self._bits):
            cy2 = iy + i * gap_y
            col = GOLD[:3] if bit else CYAN[:3]
            draw_yao_line(self.canvas, ix, cy2, iw, bit, col, lw)

# ========== MAIN PAGE (v10.8 - no Screen/ScreenManager) ==========
class MainPage(BoxLayout):
    """Main divination page. Direct BoxLayout — no Screen/RelativeLayout."""
    def __init__(self, app_ref, **kw):
        super().__init__(orientation='vertical', **kw)
        self._app = app_ref
        self._bits = []; self._casting = False
        self._smoke = SmokeLayer()
        self._build()

    def _build(self):
        PAD = dp(16)
        GAP = dp(8)
        self.spacing = GAP
        self.padding = [PAD, PAD, PAD, PAD]

        # ---- Debug banner (hidden by default, tap title 5x to show) ----
        self._dbg = Label(
            text="", markup=True, font_name=CN, font_size=sp(9),
            size_hint=(1, None), height=dp(0), halign='left', valign='middle',
            color=[0.4, 0.4, 0.5, 0.6], opacity=0)
        self._dbg.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._dbg)
        self._dbg_visible = False
        self._dbg_tap_count = 0
        self._dbg_tap_time = 0

        # ---- Top bar: compact header row ----
        top_bar = BoxLayout(size_hint=(1, None), height=dp(36), spacing=dp(6))
        t1 = Label(text="[b]\u6613CORE[/b]", markup=True, font_name=CN,
            font_size=sp(24), color=WHITE, halign='left', valign='middle')
        t1.bind(size=lambda w,s: setattr(w,'text_size',s))
        t1.bind(on_touch_down=self._on_title_tap)
        top_bar.add_widget(t1)
        self._title_lbl = t1
        t2 = Label(text="[color=#66708a]YiCORE CONSOLE[/color]", markup=True,
            font_name=CN, font_size=sp(10), halign='left', valign='middle',
            size_hint_x=None, width=dp(100))
        t2.bind(size=lambda w,s: setattr(w,'text_size',s))
        top_bar.add_widget(t2)
        self._status = Label(
            text="[color=#4deb66]\u25cf[/color] [color=#66708a]READY[/color]",
            markup=True, font_name=CN, font_size=sp(11),
            size_hint_x=None, width=dp(60), halign='right', valign='middle')
        self._status.bind(size=lambda w,s: setattr(w,'text_size',s))
        top_bar.add_widget(self._status)
        self.add_widget(top_bar)

        # ---- Log line ----
        self._log = Label(
            text=f"[color=#00def2]YiCORE_LINK {time.strftime('%H:%M')}[/color]  [color=#66708a]\u7b49\u5f85\u8d77\u5366\u6307\u4ee4...[/color]",
            markup=True, font_name=CN, font_size=sp(11),
            size_hint=(1, None), height=dp(18), halign='left', valign='middle')
        self._log.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._log)

        # ---- 6 yao slots ----
        slot_box = BoxLayout(orientation='vertical', spacing=dp(6),
                             size_hint=(1, 1))
        self._slots = [None]*6
        for i in range(5, -1, -1):
            s = YaoSlot(i)
            s.size_hint = (1, 1)
            self._slots[i] = s
            slot_box.add_widget(s)
        self.add_widget(slot_box)

        # ---- Buttons ----
        self.add_widget(Widget(size_hint_y=None, height=dp(10)))
        self._hold_btn = HoldButton(on_complete=self._on_done)
        self._hold_btn.size_hint_x = 1
        self.add_widget(self._hold_btn)
        self.add_widget(Widget(size_hint_y=None, height=dp(10)))
        rst = TapButton("\u91cd\u7f6e", "RESET", col=DIM, height=dp(40), on_press=self._reset)
        rst.size_hint_x = 1
        self.add_widget(rst)

    def _on_title_tap(self, widget, touch):
        if not widget.collide_point(*touch.pos):
            return False
        now = time.time()
        if now - self._dbg_tap_time > 2.0:
            self._dbg_tap_count = 0
        self._dbg_tap_time = now
        self._dbg_tap_count += 1
        if self._dbg_tap_count >= 5:
            self._dbg_visible = not self._dbg_visible
            self._dbg_tap_count = 0
            if self._dbg_visible:
                self._dbg.height = dp(14)
                self._dbg.opacity = 1
                self._update_dbg()
            else:
                self._dbg.height = dp(0)
                self._dbg.opacity = 0
        return False

    def _update_dbg(self, *_):
        ww, wh = Window.width, Window.height
        from kivy.metrics import Metrics
        d = Metrics.density
        sw, sh = self.width, self.height
        self._dbg.text = f"v11.0 | Win {ww}x{wh} | self {sw:.0f}x{sh:.0f} | d={d:.1f}"

    def _on_done(self):
        if self._casting: return
        self._casting = True
        self._bits = [random.choice([True, False]) for _ in range(6)]
        for i in range(6):
            Clock.schedule_once(lambda dt, ii=i: self._reveal_one(ii), i * 0.28)
        Clock.schedule_once(lambda dt: self._go_result(), 6*0.28 + 0.6)

    def _reveal_one(self, idx):
        is_yang = self._bits[idx]
        self._slots[idx].reveal(is_yang)
        val = "1" if is_yang else "0"
        col = "#ffd633" if is_yang else "#00def2"
        typ = "\u9633\u723B" if is_yang else "\u9634\u723B"
        self._status.text = f"[color={col}]\u25cf[/color] [color=#66708a]{idx+1}/6[/color]"
        self._log.text = f"[color=#00def2]YiCORE_LINK[/color]  [color={col}]{YN[idx]} = {val} ({typ})[/color]"
        self._smoke.burst(self._slots[idx].center_x, self._slots[idx].center_y,
                          GOLD[:3] if is_yang else CYAN[:3])

    def _go_result(self):
        self._casting = False
        self._app.show_result(self._bits)

    def _reset(self):
        self._bits = []; self._casting = False
        self._hold_btn.reset()
        for s in self._slots:
            if s: s.reset()
        self._status.text = "[color=#4deb66]\u25cf[/color] [color=#66708a]READY[/color]"
        self._log.text = f"[color=#00def2]YiCORE_LINK {time.strftime('%H:%M')}[/color]  [color=#66708a]\u7b49\u5f85\u8d77\u5366\u6307\u4ee4...[/color]"

# ========== CARD WIDGET (v11.0 - chamfered card wrapper) ==========
class CardBox(BoxLayout):
    """A chamfered card container that draws its own background."""
    def __init__(self, accent_col=None, **kw):
        super().__init__(orientation='vertical', **kw)
        self._accent = accent_col or CYAN[:3]
        self.padding = [dp(12), dp(8), dp(12), dp(10)]
        self.spacing = dp(4)
        self.size_hint_y = None
        self.bind(pos=self._draw_bg, size=self._draw_bg)
        self.bind(minimum_height=self.setter('height'))

    def _draw_bg(self, *_):
        self.canvas.before.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 4 or h < 4:
            return
        draw_chamfer_box(self.canvas.before, x, y, w, h, self._accent,
                         cut=dp(8), border_a=0.18, glow_a=0.06,
                         scanlines=False, band=True)

# ========== COLLAPSIBLE SECTION (v11.0 - tap header to expand/collapse) ==========
class CollapsibleSection(BoxLayout):
    """A section with a tappable header that shows/hides its content."""
    def __init__(self, title, accent_col=None, default_open=False, **kw):
        super().__init__(orientation='vertical', **kw)
        self.size_hint_y = None
        self._accent = accent_col or PURP[:3]
        self._open = default_open
        self._title_text = title

        # Header (always visible, tappable)
        self._hdr = Widget(size_hint_y=None, height=dp(36))
        self._hdr.bind(pos=self._draw_hdr, size=self._draw_hdr)
        self._hdr.bind(on_touch_down=self._on_tap)
        self.add_widget(self._hdr)

        # Content container
        self._content = BoxLayout(orientation='vertical', size_hint_y=None,
                                  spacing=dp(4))
        self._content.bind(minimum_height=self._content.setter('height'))
        if default_open:
            self.add_widget(self._content)

        self.bind(minimum_height=self.setter('height'))

    def add_content(self, widget):
        self._content.add_widget(widget)

    def _draw_hdr(self, *_):
        w = self._hdr
        w.canvas.clear()
        x, y, ww, hh = w.x, w.y, w.width, w.height
        r, g, b = self._accent[:3]
        arrow = "\u25bc" if self._open else "\u25b6"
        with w.canvas:
            Color(r, g, b, 0.12)
            Rectangle(pos=(x, y), size=(ww, hh))
            Color(r, g, b, 0.60)
            Rectangle(pos=(x, y), size=(dp(3), hh))
            Color(r, g, b, 0.20)
            Rectangle(pos=(x, y), size=(ww, dp(1)))
            Rectangle(pos=(x, y + hh - dp(1)), size=(ww, dp(1)))
        draw_text(w.canvas, f"{arrow} {self._title_text}", x + dp(12), y + dp(8),
                  sp(15), [r, g, b, 0.90])

    def _on_tap(self, widget, touch):
        if not widget.collide_point(*touch.pos):
            return False
        self._open = not self._open
        if self._open:
            self.add_widget(self._content)
        else:
            self.remove_widget(self._content)
        self._draw_hdr()
        return True

# ========== WATERMARK LAYER (v11.0) ==========
class WatermarkLayer(Widget):
    """Draws a faint 'WADJY' watermark in the background."""
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        if w < 20 or h < 20:
            return
        # Draw WADJY text repeated diagonally
        fs = sp(28)
        step_x = dp(140)
        step_y = dp(100)
        col = [0.20, 0.22, 0.30, 0.08]
        row = 0
        py = y
        while py < y + h + step_y:
            px = x - step_x + (row % 2) * step_x * 0.5
            while px < x + w + step_x:
                draw_text(self.canvas, "WADJY", px, py, fs, col)
                px += step_x
            py += step_y
            row += 1

# ========== RESULT PAGE (v11.0 - card-based modular layout) ==========
class ResultPage(BoxLayout):
    """Result display page with card-based modular layout."""
    def __init__(self, app_ref, **kw):
        super().__init__(orientation='vertical', **kw)
        self._app = app_ref
        self.padding = [dp(14), dp(8), dp(14), dp(8)]
        self.spacing = dp(6)
        self._build()

    def _build(self):
        # ---- Watermark (bottom layer) ----
        self._watermark = WatermarkLayer()
        self._watermark.size_hint = (1, 1)

        # ---- Top bar with back arrow ----
        top_bar = BoxLayout(size_hint=(1, None), height=dp(32), spacing=dp(6))
        self._back_lbl = Label(
            text="[color=#66708a]\u25c0 \u8fd4\u56de[/color]", markup=True,
            font_name=CN, font_size=sp(13), halign='left', valign='middle',
            size_hint_x=None, width=dp(60))
        self._back_lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))
        self._back_lbl.bind(on_touch_down=self._on_back_tap)
        top_bar.add_widget(self._back_lbl)
        self._result_title = Label(
            text="[color=#66708a]DIVINATION RESULT[/color]", markup=True,
            font_name=CN, font_size=sp(11), halign='right', valign='middle')
        self._result_title.bind(size=lambda w, s: setattr(w, 'text_size', s))
        top_bar.add_widget(self._result_title)
        self.add_widget(top_bar)

        # ---- Scroll area for all cards ----
        sv = ScrollView(do_scroll_x=False, size_hint=(1, 1))
        self._scroll = sv

        outer = BoxLayout(orientation='vertical', size_hint_y=None,
                          spacing=dp(10), padding=[0, dp(4), 0, dp(4)])
        outer.bind(minimum_height=outer.setter('height'))
        self._outer = outer

        # == CARD 1: Hero (hexagram + name + gushi) ==
        hero_card = CardBox(accent_col=CYAN[:3])
        hero_inner = BoxLayout(size_hint_y=None, height=dp(140), spacing=dp(12))
        self._hex_w = HexagramDisplay()
        self._hex_w.size_hint = (None, 1)
        self._hex_w.width = dp(80)
        hero_inner.add_widget(self._hex_w)

        info = BoxLayout(orientation='vertical', spacing=dp(2), size_hint_y=None,
                         height=dp(140))
        self._name = Label(text="", font_name=CN, font_size=sp(34), markup=True,
            bold=True, halign='left', valign='middle', size_hint_y=0.32)
        self._name.bind(size=lambda w, s: setattr(w, 'text_size', s))
        info.add_widget(self._name)
        self._gushi = Label(text="", font_name=CN, font_size=sp(14), markup=True,
            halign='left', valign='top', size_hint_y=0.36)
        self._gushi.bind(size=lambda w, s: setattr(w, 'text_size', s))
        info.add_widget(self._gushi)
        self._seq = Label(text="", font_name=CN, font_size=sp(11), markup=True,
            halign='left', valign='middle', size_hint_y=0.16)
        self._seq.bind(size=lambda w, s: setattr(w, 'text_size', s))
        info.add_widget(self._seq)
        self._trig = Label(text="", font_name=CN, font_size=sp(11), markup=True,
            halign='left', valign='middle', size_hint_y=0.16)
        self._trig.bind(size=lambda w, s: setattr(w, 'text_size', s))
        info.add_widget(self._trig)
        hero_inner.add_widget(info)
        hero_card.add_widget(hero_inner)
        outer.add_widget(hero_card)

        # == CARD 2: Baihua (vernacular interpretation) - PRIORITY ==
        bh_card = CardBox(accent_col=GREEN[:3])
        bh_hdr = Label(
            text="[color=#4deb66]\u25cf[/color] [b][color=#4deb66]\u767d\u8bdd\u89e3\u8bfb[/color][/b]  [color=#66708a]INTERPRETATION[/color]",
            markup=True, font_name=CN, font_size=sp(14),
            size_hint_y=None, height=dp(26), halign='left', valign='middle')
        bh_hdr.bind(size=lambda w, s: setattr(w, 'text_size', s))
        bh_card.add_widget(bh_hdr)
        self._bh = self._clbl(sp(17))
        bh_card.add_widget(self._bh)
        outer.add_widget(bh_card)

        # == CARD 3: Guaxiang (hexagram meaning) ==
        desc_card = CardBox(accent_col=CYAN[:3])
        desc_hdr = Label(
            text="[color=#00def2]\u25cf[/color] [b][color=#00def2]\u5366\u8c61\u542b\u4e49[/color][/b]  [color=#66708a]HEXAGRAM MEANING[/color]",
            markup=True, font_name=CN, font_size=sp(14),
            size_hint_y=None, height=dp(26), halign='left', valign='middle')
        desc_hdr.bind(size=lambda w, s: setattr(w, 'text_size', s))
        desc_card.add_widget(desc_hdr)
        self._desc = self._clbl(sp(15))
        desc_card.add_widget(self._desc)
        outer.add_widget(desc_card)

        # == CARD 4: Yao details (collapsible) ==
        self._yao_section = CollapsibleSection(
            "\u516d\u723b\u8be6\u89e3  SIX LINES", accent_col=PURP[:3],
            default_open=False)
        self._yao = []
        for i in range(6):
            hdr = Label(text="", markup=True, font_name=CN, font_size=sp(12),
                bold=True, size_hint_y=None, height=dp(22), halign='left', valign='middle')
            hdr.bind(size=lambda w, s: setattr(w, 'text_size', s))
            body = self._clbl(sp(12))
            self._yao.append((hdr, body))
            self._yao_section.add_content(hdr)
            self._yao_section.add_content(body)
        outer.add_widget(self._yao_section)

        # == Footer ==
        outer.add_widget(Label(
            text="[color=#66708a]\u6613\u4ee5\u9053\u9634\u9633 \u00b7 \u5366\u8c61\u4ec5\u4f9b\u53c2\u8003[/color]  [color=#3a3e4a]WADJY[/color]",
            markup=True, font_name=CN, font_size=sp(10),
            size_hint_y=None, height=dp(24), halign='center', valign='middle'))

        sv.add_widget(outer)
        self.add_widget(sv)

        # ---- Bottom button ----
        btn = TapButton("\u91cd\u65b0\u8d77\u5366", "NEW DIVINATION", col=PINK, height=dp(46),
                        on_press=lambda: self._app.show_main())
        btn.size_hint_x = 1
        self.add_widget(btn)

    def _on_back_tap(self, widget, touch):
        if not widget.collide_point(*touch.pos):
            return False
        self._app.show_main()
        return True

    def _clbl(self, fs=None):
        lbl = Label(text="", markup=True, font_name=CN, font_size=fs or sp(15),
            color=SOFT, size_hint_y=None, halign='left', valign='top')
        lbl.bind(size=lambda w, s: setattr(w, 'text_size', (s[0], None)))
        lbl.bind(texture_size=lbl.setter('size'))
        return lbl

    def show(self, bits):
        il = tuple(1 if v else 0 for v in bits)
        data = HEXAGRAMS.get(il)
        if not data:
            self._desc.text = f"[color=#f24494]\u5366\u8c61\u672a\u627e\u5230: {il}[/color]"
            return
        seq, name, pos, gushi, desc, baihua = data
        lo, up = il[:3], il[3:]
        lt = TRIGRAMS.get(lo, ("?", "?", "?"))
        ut = TRIGRAMS.get(up, ("?", "?", "?"))

        # Reset scroll to top
        self._scroll.scroll_y = 1.0

        self._hex_w.set_bits(il)
        self._name.text = f"[color=#00def2]{name}[/color]"
        self._gushi.text = f"[color=#ffd633]{gushi}[/color]"
        self._seq.text = f"[color=#66708a]\u7b2c{seq:02d}\u5366  HEXAGRAM #{seq:02d}[/color]"
        self._trig.text = f"[color=#66708a]{ut[0]}{ut[2]}\u4e0a  {lt[0]}{lt[2]}\u4e0b  {pos}[/color]"

        self._desc.text = f"[color=#c8d4e0]{desc}[/color]"

        # Clean baihua
        bh_text = baihua
        for prefix in ["\u3010\u767d\u8bdd\u3011", "\u767d\u8bdd\uff1a"]:
            if bh_text.startswith(prefix):
                bh_text = bh_text[len(prefix):]
        bh_text = bh_text.strip()
        bh_text += "\n\n\u5efa\u8bae\uff1a\u5728\u5f53\u524d\u5f62\u52bf\u4e0b\uff0c\u5e94\u4fdd\u6301\u5185\u5fc3\u5e73\u9759\uff0c\u987a\u5e94\u81ea\u7136\u89c4\u5f8b\uff0c\u4e0d\u5b9c\u8fc7\u4e8e\u6025\u8e81\u3002\u8c28\u614e\u884c\u4e8b\uff0c\u6ce8\u610f\u89c2\u5bdf\u5468\u56f4\u73af\u5883\u7684\u53d8\u5316\uff0c\u628a\u63e1\u65f6\u673a\u65b9\u53ef\u6709\u6240\u4f5c\u4e3a\u3002"
        self._bh.text = f"[color=#4deb66]{bh_text}[/color]"

        for i in range(6):
            h, b = self._yao[i]
            yc, yb = get_yaoci(il, i)
            c = "#ffd633" if il[i] else "#00def2"
            t = "\u9633\u723B" if il[i] else "\u9634\u723B"
            v = "1" if il[i] else "0"
            h.text = f"[color=#9e66fa]{YN[i]}[/color]  [color={c}][{v}] {t}[/color]"
            b.text = f"[color=#ffd633]{yc}[/color]\n[color=#8a92a4]{yb}[/color]"

# ---- App (v11.0 - simplest possible root) ----
class TianJiApp(App):
    def build(self):
        for d in [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
            if d: resource_add_path(d)

        self._main_page = MainPage(app_ref=self)
        self._result_page = ResultPage(app_ref=self)

        # Return MainPage directly as root widget.
        # BoxLayout returned from build() auto-fills the Window.
        # No FloatLayout wrapper, no ScreenManager, nothing extra.
        self._current = 'main'
        return self._main_page

    def show_result(self, bits):
        self._result_page.show(bits)
        self.root_window.remove_widget(self.root)
        self.root = self._result_page
        self.root_window.add_widget(self._result_page)
        self._current = 'result'

    def show_main(self):
        self._main_page._reset()
        self.root_window.remove_widget(self.root)
        self.root = self._main_page
        self.root_window.add_widget(self._main_page)
        self._current = 'main'

    def get_application_name(self):
        return "\u5929\u673a"

if __name__ == "__main__":
    Window.size = (390, 844)
    TianJiApp().run()
