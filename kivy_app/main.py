# -*- coding: utf-8 -*-
"""
天机 · TIANJI - Kivy Android v2.5.0
按住1.5秒起卦 · 六爻赛博灯管 · 烟雾特效
"""
import random, os, sys, math
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import (Color, Ellipse, Line, Rectangle,
                            RoundedRectangle, Triangle)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp
from kivy.resources import resource_add_path, resource_find

# ══════════════════════════════════════════════
#  字体注册
# ══════════════════════════════════════════════
def _find_font():
    for p in [
        os.path.join(os.environ.get("ANDROID_APP_PATH",""), "NotoSansCJK.otf"),
        os.path.join(os.getcwd(), "NotoSansCJK.otf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK.otf"),
    ]:
        if p and os.path.exists(p): return p
    return resource_find("NotoSansCJK.otf")

_fp = _find_font()
if _fp:
    for n in ("NotoSansCJK","Roboto","RobotoMono"):
        LabelBase.register(name=n, fn_regular=_fp)
    CN = "NotoSansCJK"
else:
    CN = "Roboto"

# ══════════════════════════════════════════════
#  颜色
# ══════════════════════════════════════════════
BG    = get_color_from_hex("#060810")
INSET = get_color_from_hex("#0c1428")
CYAN  = get_color_from_hex("#00f5ff")
PINK  = get_color_from_hex("#ff2d9b")
GREEN = get_color_from_hex("#39ff14")
PURP  = get_color_from_hex("#b44fff")
YELL  = get_color_from_hex("#ffe600")
DIM   = get_color_from_hex("#1e2d45")
DDIM  = get_color_from_hex("#0e1828")
TEXT  = get_color_from_hex("#c8d8e8")
WHITE = get_color_from_hex("#ffffff")

Window.clearcolor = BG

# ══════════════════════════════════════════════
#  数据
# ══════════════════════════════════════════════
TRIGRAMS = {
    (1,1,1):("乾","☰","天"),(0,0,0):("坤","☷","地"),
    (1,0,0):("震","☳","雷"),(0,0,1):("艮","☶","山"),
    (0,1,1):("巽","☴","风"),(1,1,0):("兑","☱","泽"),
    (1,0,1):("坎","☵","水"),(0,1,0):("离","☲","火"),
}
TSYM = {k:v[1] for k,v in TRIGRAMS.items()}

def _load():
    for d in [os.getcwd(), os.path.dirname(os.path.abspath(__file__)),
              os.environ.get("ANDROID_APP_PATH","")]:
        if d and d not in sys.path: sys.path.insert(0,d)
    try:
        from iching_data import HEXAGRAMS
        from yaoci_data import get_yaoci
        return HEXAGRAMS, get_yaoci
    except Exception as e:
        return {}, lambda k,i: ("爻辞待查", f"数据加载失败:{e}")
HEXAGRAMS, get_yaoci = _load()


# ══════════════════════════════════════════════
#  工具：绘制霓虹光晕线条
# ══════════════════════════════════════════════
def neon_line(canvas, pts, col_rgb, bright=1.0):
    """在 canvas 上绘制带光晕的霓虹线条"""
    r,g,b = col_rgb
    # 外发光层
    with canvas:
        Color(r,g,b,0.08*bright); Line(points=pts, width=dp(9))
        Color(r,g,b,0.18*bright); Line(points=pts, width=dp(5))
        Color(r,g,b,0.45*bright); Line(points=pts, width=dp(2.5))
        Color(r,g,b,1.0*bright);  Line(points=pts, width=dp(1.0))

def neon_circle(canvas, cx,cy,r, col_rgb, bright=1.0):
    rr,g,b = col_rgb
    with canvas:
        Color(rr,g,b,0.08*bright); Line(circle=(cx,cy,r+dp(4)), width=dp(8))
        Color(rr,g,b,0.18*bright); Line(circle=(cx,cy,r+dp(2)), width=dp(4))
        Color(rr,g,b,0.45*bright); Line(circle=(cx,cy,r),       width=dp(2))
        Color(rr,g,b,1.0*bright);  Line(circle=(cx,cy,r),       width=dp(1))


# ══════════════════════════════════════════════
#  赛博霓虹按钮
# ══════════════════════════════════════════════
def neon_btn(text, col, fs=None, **kw):
    """带霓虹边框的赛博按钮"""
    fs = fs or sp(15)
    r,g,b,a = col
    b_widget = Button(
        text=text, font_name=CN, font_size=fs, bold=True,
        background_normal="", background_color=(r*0.15,g*0.15,b*0.15,1),
        color=col, **kw)
    # 添加霓虹边框
    def _redraw_border(inst, *args):
        inst.canvas.after.clear()
        x,y,w,h = inst.x,inst.y,inst.width,inst.height
        with inst.canvas.after:
            Color(r,g,b,0.15); Line(rounded_rectangle=(x,y,w,h,dp(6)), width=dp(5))
            Color(r,g,b,0.40); Line(rounded_rectangle=(x,y,w,h,dp(6)), width=dp(2.5))
            Color(r,g,b,0.90); Line(rounded_rectangle=(x,y,w,h,dp(6)), width=dp(1))
    b_widget.bind(pos=_redraw_border, size=_redraw_border)
    # 按压效果
    def _dn(inst,*a):
        inst.background_color=(r*0.3,g*0.3,b*0.3,1)
    def _up(inst,*a):
        inst.background_color=(r*0.15,g*0.15,b*0.15,1)
    b_widget.bind(on_press=_dn, on_release=_up)
    return b_widget


# ══════════════════════════════════════════════
#  烟雾粒子系统
# ══════════════════════════════════════════════
class SmokeParticle:
    def __init__(self, cx, cy, col):
        self.x = cx + random.uniform(-dp(12), dp(12))
        self.y = cy + random.uniform(-dp(8),  dp(8))
        self.r = random.uniform(dp(1.5), dp(4))
        self.vx = random.uniform(-dp(0.4), dp(0.4))
        self.vy = random.uniform(dp(0.3), dp(1.2))
        self.alpha = random.uniform(0.5, 0.9)
        self.decay = random.uniform(0.025, 0.05)
        self.col = col
    @property
    def alive(self): return self.alpha > 0.02

class SmokeOverlay(Widget):
    """悬浮在卡片上方的烟雾层"""
    def __init__(self,**kw):
        super().__init__(**kw)
        self._particles = []
        self._ev = None
        self.size_hint = (1,1)
        self.bind(pos=self._redraw, size=self._redraw)

    def burst(self, wx, wy, col):
        """在世界坐标 wx,wy 喷射烟雾"""
        for _ in range(12):
            self._particles.append(SmokeParticle(wx, wy, col))
        if self._ev is None:
            self._ev = Clock.schedule_interval(self._step, 0.033)

    def _step(self, dt):
        for p in self._particles:
            p.x += p.vx; p.y += p.vy
            p.r  += dp(0.15)
            p.alpha -= p.decay
        self._particles = [p for p in self._particles if p.alive]
        if not self._particles:
            if self._ev: self._ev.cancel(); self._ev = None
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        with self.canvas:
            for p in self._particles:
                r,g,b = p.col
                Color(r,g,b, p.alpha * 0.6)
                Ellipse(pos=(p.x - p.r, p.y - p.r), size=(p.r*2, p.r*2))


# ══════════════════════════════════════════════
#  六爻赛博灯管卡片
# ══════════════════════════════════════════════
class NeonBitCard(FloatLayout):
    """显示单爻的霓虹灯管卡片  state: idle/pending/yang/yin"""

    YAO_NAMES = ["初","二","三","四","五","上"]

    def __init__(self, idx, smoke_layer=None, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.state = 'idle'
        self._glow = 0.3
        self._gdir = 1
        self._pulse_ev = None
        self._smoke = smoke_layer
        self.size_hint = (None, None)
        self.size = (dp(52), dp(72))

        # 爻名 label（顶部）
        self._name_lbl = Label(
            text=self.YAO_NAMES[idx],
            font_name=CN, font_size=sp(9), bold=False,
            color=DIM,
            size_hint=(1, None), height=dp(16),
            pos_hint={'x':0, 'top':1},
            halign='center', valign='middle')
        self._name_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._name_lbl)

        # 主数字 label（中央）
        self._main_lbl = Label(
            text="", font_name=CN, font_size=sp(30), bold=True,
            color=DIM,
            size_hint=(1, None), height=dp(40),
            pos_hint={'x':0, 'center_y':0.52},
            halign='center', valign='middle')
        self._main_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._main_lbl)

        # 类型 label（底部）
        self._type_lbl = Label(
            text="", font_name=CN, font_size=sp(9),
            color=DIM,
            size_hint=(1, None), height=dp(14),
            pos_hint={'x':0, 'y':0},
            halign='center', valign='middle')
        self._type_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._type_lbl)

        self.bind(pos=self._draw_bg, size=self._draw_bg)
        self._draw_bg()

    # ── 背景框绘制 ────────────────────────────
    def _draw_bg(self, *a):
        self.canvas.before.clear()
        x,y,w,h = self.x, self.y, self.width, self.height
        g = self._glow
        with self.canvas.before:
            if self.state == 'idle':
                Color(0.04,0.06,0.12,1)
                RoundedRectangle(pos=(x,y),size=(w,h),radius=[dp(8)])
                Color(*DIM)
                Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)), width=dp(1))
            elif self.state == 'pending':
                # 脉冲发光边框
                Color(0.0, g*0.08, g*0.18, 1)
                RoundedRectangle(pos=(x,y),size=(w,h),radius=[dp(8)])
                r2,g2,b2 = 0,g,1
                Color(r2,g2,b2, 0.1*g)
                RoundedRectangle(pos=(x-dp(3),y-dp(3)),size=(w+dp(6),h+dp(6)),radius=[dp(10)])
                Color(r2,g2,b2,0.2*g);  Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(4))
                Color(r2,g2,b2,0.6*g);  Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(2))
                Color(r2,g2,b2,1.0);    Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(1))
            elif self.state == 'yang':
                # 金色深底
                Color(0.10,0.07,0.0,1)
                RoundedRectangle(pos=(x,y),size=(w,h),radius=[dp(8)])
                # 金色外发光
                ry,gy,by = YELL[:3]
                Color(ry,gy,by,0.12); RoundedRectangle(pos=(x-dp(3),y-dp(3)),size=(w+dp(6),h+dp(6)),radius=[dp(10)])
                Color(ry,gy,by,0.25); Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(5))
                Color(ry,gy,by,0.55); Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(2.5))
                Color(ry,gy,by,1.0);  Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(1))
            elif self.state == 'yin':
                # 青色深底
                Color(0.0,0.07,0.12,1)
                RoundedRectangle(pos=(x,y),size=(w,h),radius=[dp(8)])
                rc,gc,bc = CYAN[:3]
                Color(rc,gc,bc,0.12); RoundedRectangle(pos=(x-dp(3),y-dp(3)),size=(w+dp(6),h+dp(6)),radius=[dp(10)])
                Color(rc,gc,bc,0.25); Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(5))
                Color(rc,gc,bc,0.55); Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(2.5))
                Color(rc,gc,bc,1.0);  Line(rounded_rectangle=(x+1,y+1,w-2,h-2,dp(7)),width=dp(1))

        # 绘制中央霓虹数字（canvas.after 以免被背景遮住）
        self.canvas.after.clear()
        self._draw_digit()

    def _draw_digit(self):
        x,y,w,h = self.x, self.y, self.width, self.height
        cx = x + w/2
        # 数字绘制区域：卡片中央
        mid_y = y + h*0.50
        with self.canvas.after:
            if self.state == 'yang':
                # 霓虹 "1" —— 竖线 + 顶部小斜线
                col = YELL[:3]
                top = mid_y + dp(16)
                bot = mid_y - dp(16)
                neon_line(self.canvas.after, [cx, bot, cx, top], col)
                neon_line(self.canvas.after, [cx-dp(5), top-dp(5), cx, top], col, 0.7)
            elif self.state == 'yin':
                # 霓虹 "0" —— 圆圈
                col = CYAN[:3]
                neon_circle(self.canvas.after, cx, mid_y, dp(14), col)
            elif self.state == 'pending':
                # 扫描线动画 "~"
                g = self._glow
                col = (0, g*0.8, 1.0)
                neon_line(self.canvas.after,
                          [cx-dp(12), mid_y, cx+dp(12), mid_y], col, g)

    # ── 状态切换 ────────────────────────────
    def set_pending(self):
        self.state = 'pending'
        self._glow = 0.3; self._gdir = 1
        if self._pulse_ev: self._pulse_ev.cancel()
        self._pulse_ev = Clock.schedule_interval(self._pulse, 0.04)
        self._update_labels()
        self._draw_bg()

    def _pulse(self, dt):
        self._glow += self._gdir * 0.07
        if self._glow >= 1.0: self._glow=1.0; self._gdir=-1
        elif self._glow <= 0.15: self._glow=0.15; self._gdir=1
        self._draw_bg()

    def reveal(self, is_yang: bool):
        if self._pulse_ev: self._pulse_ev.cancel()
        self.state = 'yang' if is_yang else 'yin'
        self._update_labels()
        self._draw_bg()
        # 烟雾爆发
        if self._smoke:
            cx = self.x + self.width/2
            cy = self.y + self.height/2
            col = YELL[:3] if is_yang else CYAN[:3]
            self._smoke.burst(cx, cy, col)

    def reset(self):
        if self._pulse_ev: self._pulse_ev.cancel()
        self.state = 'idle'
        self._update_labels()
        self._draw_bg()

    def _update_labels(self):
        if self.state == 'idle':
            self._name_lbl.color = DIM
            self._main_lbl.text  = "·"
            self._main_lbl.color = DIM
            self._type_lbl.text  = ""
        elif self.state == 'pending':
            self._name_lbl.color = CYAN
            self._main_lbl.text  = ""
            self._type_lbl.text  = ""
        elif self.state == 'yang':
            self._name_lbl.color = YELL
            self._main_lbl.text  = ""   # 数字由 canvas 绘制
            self._type_lbl.text  = "阳"
            self._type_lbl.color = YELL
        elif self.state == 'yin':
            self._name_lbl.color = CYAN
            self._main_lbl.text  = ""
            self._type_lbl.text  = "阴"
            self._type_lbl.color = CYAN


# ══════════════════════════════════════════════
#  按住起卦按钮（1.5 秒）
# ══════════════════════════════════════════════
class HoldButton(FloatLayout):
    HOLD_SECS = 1.5

    def __init__(self, on_complete=None, **kw):
        super().__init__(**kw)
        self._cb       = on_complete
        self._holding  = False
        self._prog     = 0.0
        self._done     = False
        self._ev       = None
        self.size_hint_y = None
        self.height    = dp(64)

        # 主 Label
        self._lbl = Label(
            text="◉  按住起卦  CAST",
            font_name=CN, font_size=sp(17), bold=True,
            color=WHITE,
            size_hint=(1,1),
            pos_hint={'x':0,'y':0},
            halign='center', valign='middle')
        self._lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self.add_widget(self._lbl)

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.before.clear()
        x,y,w,h = self.x, self.y, self.width, self.height
        p = self._prog

        with self.canvas.before:
            # 背景
            if self._done:
                Color(0.0, 0.15, 0.0, 1)
            elif self._holding:
                Color(0.02, 0.10, 0.02, 1)
            else:
                Color(0.04, 0.02, 0.10, 1)
            RoundedRectangle(pos=(x,y), size=(w,h), radius=[dp(10)])

            # 进度填充（左到右亮色）
            if p > 0:
                pw = (w-dp(4)) * p
                Color(*GREEN[:3], 0.25)
                RoundedRectangle(pos=(x+dp(2),y+dp(2)), size=(pw, h-dp(4)), radius=[dp(8)])

            # 外边框霓虹
            if self._done:
                rc,gc,bc = GREEN[:3]
            elif self._holding:
                rc,gc,bc = GREEN[:3]
            else:
                rc,gc,bc = PURP[:3]

            Color(rc,gc,bc,0.12); Line(rounded_rectangle=(x,y,w,h,dp(10)), width=dp(8))
            Color(rc,gc,bc,0.35); Line(rounded_rectangle=(x,y,w,h,dp(10)), width=dp(3.5))
            Color(rc,gc,bc,0.90); Line(rounded_rectangle=(x,y,w,h,dp(10)), width=dp(1.2))

        # 更新文字
        if self._done:
            self._lbl.text  = "✦  天机已成  ✦"
            self._lbl.color = GREEN
        elif self._holding:
            pct = int(p * 100)
            self._lbl.text  = f"[  {pct}%  ]  感应中…"
            self._lbl.color = GREEN
        else:
            self._lbl.text  = "◉  按住起卦  CAST"
            self._lbl.color = WHITE

    def on_touch_down(self, touch):
        if self._done or not self.collide_point(*touch.pos): return False
        self._holding = True; self._prog = 0.0
        if self._ev: self._ev.cancel()
        self._ev = Clock.schedule_interval(self._tick, 0.025)
        self._redraw(); return True

    def on_touch_up(self, touch):
        if not self._holding: return False
        self._holding = False
        if self._ev: self._ev.cancel()
        if self._prog < 1.0:
            self._prog = 0.0
            self._redraw()
        return True

    def _tick(self, dt):
        self._prog += dt / self.HOLD_SECS
        if self._prog >= 1.0:
            self._prog = 1.0; self._done = True
            self._ev.cancel(); self._holding = False
            self._redraw()
            if self._cb: self._cb()
        else:
            self._redraw()

    def reset(self):
        if self._ev: self._ev.cancel()
        self._prog=0.0; self._holding=False; self._done=False
        self._redraw()


# ══════════════════════════════════════════════
#  分隔线工具
# ══════════════════════════════════════════════
def hline(color, h=dp(1)):
    w = Widget(size_hint_y=None, height=h)
    with w.canvas:
        Color(*color)
        rc = Rectangle(pos=w.pos, size=w.size)
    w.bind(pos=lambda ww,*a: setattr(rc,'pos',ww.pos),
           size=lambda ww,*a: setattr(rc,'size',ww.size))
    return w


# ══════════════════════════════════════════════
#  主界面
# ══════════════════════════════════════════════
class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._bits    = []
        self._casting = False
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         spacing=dp(6),
                         padding=[dp(12), dp(8), dp(12), dp(8)])
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w,*a: setattr(self._bg,'pos',w.pos),
                  size=lambda w,*a: setattr(self._bg,'size',w.size))

        # ── 标题 ─────────────────────────────
        title_box = BoxLayout(size_hint_y=None, height=dp(52))
        with title_box.canvas.before:
            Color(0.0, 0.035, 0.08, 1)
            self._tb_rect = RoundedRectangle(pos=title_box.pos, size=title_box.size, radius=[dp(10)])
        title_box.bind(pos=lambda w,*a: setattr(self._tb_rect,'pos',w.pos),
                       size=lambda w,*a: setattr(self._tb_rect,'size',w.size))

        title = Label(
            text="[color=#00f5ff]天[/color][color=#b44fff]机[/color]"
                 "[color=#445566] · [/color][color=#39ff14]TIANJI[/color]",
            markup=True, font_name=CN, font_size=sp(22), bold=True)
        title_box.add_widget(title)
        root.add_widget(title_box)

        root.add_widget(hline(CYAN))

        # ── 六爻卡片区（弹性填充）────────────
        cards_wrap = BoxLayout(orientation="vertical", spacing=dp(4))

        row_label = BoxLayout(size_hint_y=None, height=dp(18))
        row_label.add_widget(Label(
            text="[color=#1e2d45]─── 六 爻 ───[/color]",
            markup=True, font_name=CN, font_size=sp(10), halign='center'))
        cards_wrap.add_widget(row_label)

        # 烟雾层（跨两行卡片）
        self._smoke = SmokeOverlay()

        # 卡片容器（用 FloatLayout 叠加烟雾层）
        cards_float = FloatLayout()
        cards_v = BoxLayout(orientation="vertical", spacing=dp(8),
                            size_hint=(1,1))

        self._cards = []
        for row_i in range(2):
            row = BoxLayout(spacing=dp(8))
            row.add_widget(Widget())
            for ci in range(3):
                idx = row_i * 3 + ci
                card = NeonBitCard(idx, smoke_layer=self._smoke)
                self._cards.append(card)
                row.add_widget(card)
            row.add_widget(Widget())
            cards_v.add_widget(row)

        cards_float.add_widget(cards_v)
        cards_float.add_widget(self._smoke)
        cards_wrap.add_widget(cards_float)

        # 下卦/上卦标注
        lab_row = BoxLayout(size_hint_y=None, height=dp(16))
        for txt in ["← 下 卦 →", "← 上 卦 →"]:
            lab_row.add_widget(Label(
                text=f"[color=#1e2d45]{txt}[/color]",
                markup=True, font_name=CN, font_size=sp(9), halign='center'))
        cards_wrap.add_widget(lab_row)

        root.add_widget(cards_wrap)

        # ── 进度提示 ─────────────────────────
        self._prog_lbl = Label(
            text="[color=#1e2d45]— 等待感应 —[/color]",
            markup=True, font_name=CN, font_size=sp(13),
            size_hint_y=None, height=dp(30))
        root.add_widget(self._prog_lbl)

        root.add_widget(hline(PURP))

        # ── 按住起卦 ─────────────────────────
        self._hold_btn = HoldButton(on_complete=self._on_hold_done)
        root.add_widget(self._hold_btn)

        # ── 重新起卦 ─────────────────────────
        rst = neon_btn("↺  重新", DIM, fs=sp(12),
                       size_hint_y=None, height=dp(36))
        rst.bind(on_press=lambda *a: self._reset())
        root.add_widget(rst)

        root.add_widget(hline(DIM))

        # ── 水印 ─────────────────────────────
        root.add_widget(Label(
            text="[color=#0e1828]WADJY  ·  天机 TIANJI  v2.5[/color]",
            markup=True, font_name=CN, font_size=sp(8),
            size_hint_y=None, height=dp(14)))

        self.add_widget(root)

    # ── 逻辑 ─────────────────────────────────
    def _on_hold_done(self):
        if self._casting: return
        self._casting = True
        self._bits = []
        results = [random.choice([True,False]) for _ in range(6)]

        for i, is_yang in enumerate(results):
            d = i * 0.38
            Clock.schedule_once(lambda dt,ii=i: self._cards[ii].set_pending(), d)
            Clock.schedule_once(lambda dt,ii=i,v=is_yang: self._reveal(ii,v), d+0.22)

        Clock.schedule_once(lambda dt: self._go_result(results), 6*0.38+0.6)

    def _reveal(self, idx, is_yang):
        self._cards[idx].reveal(is_yang)
        self._bits.append(is_yang)
        names = ["初爻","二爻","三爻","四爻","五爻","上爻"]
        sym  = "━━━ 阳" if is_yang else "━ ━ 阴"
        col  = "#ffe600" if is_yang else "#00f5ff"
        self._prog_lbl.text = f"[color={col}]{names[idx]}  {sym}[/color]"

    def _go_result(self, results):
        self._casting = False
        rs = self.manager.get_screen("result")
        rs.show_hexagram(results)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "result"

    def _reset(self):
        self._bits = []; self._casting = False
        for c in self._cards: c.reset()
        self._hold_btn.reset()
        self._prog_lbl.text = "[color=#1e2d45]— 等待感应 —[/color]"


# ══════════════════════════════════════════════
#  结果界面
# ══════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=[dp(12),dp(8),dp(12),dp(8)],
                         spacing=dp(6))
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w,*a: setattr(self._bg,'pos',w.pos),
                  size=lambda w,*a: setattr(self._bg,'size',w.size))

        # ── 顶栏 ─────────────────────────────
        top = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        back = neon_btn("◀ 返回", CYAN, fs=sp(13), size_hint_x=None, width=dp(90))
        back.bind(on_press=self._go_back)
        top.add_widget(back)
        self._title_lbl = Label(
            text="[color=#00f5ff]卦象解读[/color]",
            markup=True, font_name=CN, font_size=sp(17), bold=True)
        top.add_widget(self._title_lbl)
        root.add_widget(top)
        root.add_widget(hline(CYAN))

        # ── 卦象信息 ─────────────────────────
        kua = BoxLayout(size_hint_y=None, height=dp(96), spacing=dp(10))
        self._sym_lbl = Label(text="", font_name=CN, font_size=sp(58),
                              color=CYAN, size_hint_x=None, width=dp(86))
        kua.add_widget(self._sym_lbl)
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        self._name_lbl = Label(text="", font_name=CN, font_size=sp(21),
                               markup=True, halign="left", valign="middle")
        self._name_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self._pos_lbl  = Label(text="", font_name=CN, font_size=sp(11),
                               color=DIM, markup=True, halign="left", valign="middle")
        self._pos_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self._gushi_lbl= Label(text="", font_name=CN, font_size=sp(12),
                               color=YELL, markup=True, halign="left", valign="middle")
        self._gushi_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        info.add_widget(self._name_lbl)
        info.add_widget(self._pos_lbl)
        info.add_widget(self._gushi_lbl)
        kua.add_widget(info)
        root.add_widget(kua)
        root.add_widget(hline(PURP))

        # ── 六爻缩略行 ───────────────────────
        self._yao_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))
        root.add_widget(self._yao_row)
        root.add_widget(hline(DIM))

        # ── 滚动详情 ─────────────────────────
        sv = ScrollView(do_scroll_x=False)
        self._detail = Label(
            text="", markup=True, font_name=CN, font_size=sp(12.5),
            color=TEXT, size_hint_y=None,
            halign="left", valign="top")
        sv.bind(width=lambda sv,w: setattr(self._detail,'text_size',(w-dp(8),None)))
        self._detail.bind(texture_size=self._detail.setter('size'))
        sv.add_widget(self._detail)
        root.add_widget(sv)

        # ── 底部按钮 ─────────────────────────
        again = neon_btn("◀  重新起卦", PINK, fs=sp(15),
                         size_hint_y=None, height=dp(52))
        again.bind(on_press=self._go_back)
        root.add_widget(again)
        self.add_widget(root)

    def _go_back(self, *a):
        self.manager.get_screen("main")._reset()
        self.manager.transition = SlideTransition(direction="right")
        self.manager.current = "main"

    def show_hexagram(self, lines: list):
        il = tuple(1 if v else 0 for v in lines)
        data = HEXAGRAMS.get(il)
        if data is None:
            self._detail.text = f"[color=#ff2d9b]卦象未找到  键:{il}[/color]"
            return

        seq, name, position, gushi, desc, baihua = data
        lo, up = il[:3], il[3:]
        lt = TRIGRAMS.get(lo, ("?","?","?"))
        ut = TRIGRAMS.get(up, ("?","?","?"))
        sym = TSYM.get(up,"?") + TSYM.get(lo,"?")

        self._title_lbl.text = f"[color=#00f5ff]第 {seq:02d} 卦  ·  {name} 卦[/color]"
        self._sym_lbl.text   = sym
        self._name_lbl.text  = f"[color=#00f5ff]{name} 卦[/color]"
        self._pos_lbl.text   = f"[color=#1e2d45]{ut[2]}上{lt[2]}下  ·  {position}[/color]"
        self._gushi_lbl.text = f"[color=#ffe600]{gushi}[/color]"

        # 六爻缩略
        self._yao_row.clear_widgets()
        yn = ["初","二","三","四","五","上"]
        for i in range(6):
            col = "#ffe600" if il[i]==1 else "#00f5ff"
            s   = "1" if il[i]==1 else "0"
            self._yao_row.add_widget(Label(
                text=f"[color={col}][b]{s}[/b]\n{yn[i]}[/color]",
                markup=True, font_name=CN, font_size=sp(12), halign='center'))

        # 爻辞
        yf = ["初爻","二爻","三爻","四爻","五爻","上爻"]
        yao_txt = ""
        for i in range(6):
            yc, yb = get_yaoci(il, i)
            col  = "#ffe600" if il[i]==1 else "#00f5ff"
            bar  = "━━━━━" if il[i]==1 else "━━ ━━"
            typ  = "阳" if il[i]==1 else "阴"
            yao_txt += (
                f"\n[color=#b44fff]▌ {yf[i]}[/color]  "
                f"[color={col}]{bar} {typ}爻[/color]\n"
                f"[color=#ffe600]{yc}[/color]\n"
                f"[color=#c8d8e8]{yb}[/color]\n")

        self._detail.text = (
            f"[color=#00f5ff]◆ 卦义[/color]\n"
            f"[color=#c8d8e8]{desc}[/color]\n\n"
            f"[color=#00f5ff]◆ 白话解析[/color]\n"
            f"[color=#39ff14]{baihua}[/color]\n\n"
            f"[color=#b44fff]━━━ 爻辞详解 ━━━[/color]"
            + yao_txt
            + "\n[color=#1e2d45]— 易以道阴阳，仅供参考 —[/color]")


# ══════════════════════════════════════════════
#  App 入口
# ══════════════════════════════════════════════
class TianJiApp(App):
    def build(self):
        for d in [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
            if d: resource_add_path(d)
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(ResultScreen(name="result"))
        return sm

    def get_application_name(self):
        return "天机"


if __name__ == "__main__":
    Window.size = (390, 844)
    TianJiApp().run()