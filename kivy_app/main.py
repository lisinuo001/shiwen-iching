# -*- coding: utf-8 -*-
"""
筮问 · SHI WEN - Kivy Android 版  v2.4.0
交互：按住 CAST 按钮 3 秒 → 逐爻生成 0/1 → 六爻成卦
"""
import random, os, sys, math
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import (Color, Ellipse, Line, Rectangle,
                            RoundedRectangle, Mesh, InstructionGroup)
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp
from kivy.resources import resource_add_path, resource_find
from kivy.animation import Animation

# ══════════════════════════════════════════════
#  字体注册（Android 兼容）
# ══════════════════════════════════════════════
def _find_font():
    for p in [
        os.path.join(os.environ.get("ANDROID_APP_PATH", ""), "NotoSansCJK.otf"),
        os.path.join(os.getcwd(), "NotoSansCJK.otf"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK.otf"),
    ]:
        if p and os.path.exists(p):
            return p
    return resource_find("NotoSansCJK.otf")

_font_path = _find_font()
if _font_path:
    for n in ("NotoSansCJK", "Roboto", "RobotoMono"):
        LabelBase.register(name=n, fn_regular=_font_path)
    CN = "NotoSansCJK"
else:
    CN = "Roboto"

# ══════════════════════════════════════════════
#  颜色系统
# ══════════════════════════════════════════════
BG    = get_color_from_hex("#07080f")
INSET = get_color_from_hex("#0c1020")
CYAN  = get_color_from_hex("#00f5ff")
PINK  = get_color_from_hex("#ff2d9b")
GREEN = get_color_from_hex("#39ff14")
PURP  = get_color_from_hex("#b44fff")
YELL  = get_color_from_hex("#ffe600")
DIM   = get_color_from_hex("#2a3a50")
TEXT  = get_color_from_hex("#c8d8e8")
WHITE = get_color_from_hex("#ffffff")

Window.clearcolor = BG

# ══════════════════════════════════════════════
#  数据加载
# ══════════════════════════════════════════════
TRIGRAMS = {
    (1,1,1):("乾","☰","天"), (0,0,0):("坤","☷","地"),
    (1,0,0):("震","☳","雷"), (0,0,1):("艮","☶","山"),
    (0,1,1):("巽","☴","风"), (1,1,0):("兑","☱","泽"),
    (1,0,1):("坎","☵","水"), (0,1,0):("离","☲","火"),
}
TSYM = {k: v[1] for k, v in TRIGRAMS.items()}

def _load():
    for d in [os.getcwd(),
              os.path.dirname(os.path.abspath(__file__)),
              os.environ.get("ANDROID_APP_PATH", "")]:
        if d and d not in sys.path:
            sys.path.insert(0, d)
    try:
        from iching_data import HEXAGRAMS
        from yaoci_data import get_yaoci
        return HEXAGRAMS, get_yaoci
    except Exception as e:
        return {}, lambda k, i: ("爻辞待查", f"加载失败: {e}")

HEXAGRAMS, get_yaoci = _load()


# ══════════════════════════════════════════════
#  赛博风格按钮工厂
# ══════════════════════════════════════════════
def cyber_btn(text, bg, tc=None, fs=None, **kw):
    tc = tc or WHITE
    fs = fs or sp(14)
    b = Button(text=text, font_size=fs, bold=True, font_name=CN,
               background_normal="", background_color=bg, color=tc, **kw)
    def _dn(inst, *a): inst.background_color = [c*0.55 for c in bg[:3]] + [bg[3]]
    def _up(inst, *a): inst.background_color = bg
    b.bind(on_press=_dn, on_release=_up)
    return b


# ══════════════════════════════════════════════
#  六爻二进制卡片控件
# ══════════════════════════════════════════════
class HexBitCard(Widget):
    """显示单个爻的二进制卡片：待定 / 0(阴) / 1(阳)"""
    # state: 'idle' | 'pending' | 'yang'(1) | 'yin'(0)
    def __init__(self, idx, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.state = 'idle'
        self._glow = 0.0          # 光晕强度 0~1
        self._pulse_dir = 1
        self._pulse_ev = None
        self.size_hint = (None, None)
        self.size = (dp(46), dp(58))
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    # ── 绘制 ─────────────────────────────────
    def _draw(self, *a):
        self.canvas.clear()
        x, y = self.x, self.y
        w, h = self.width, self.height
        cx, cy = x + w/2, y + h/2
        r = dp(6)

        with self.canvas:
            if self.state == 'idle':
                # 暗色空卡
                Color(0.06, 0.08, 0.14, 1)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])
                Color(*DIM)
                Line(rounded_rectangle=(x+1, y+1, w-2, h-2, r), width=dp(1))
                # 中心"?"
                Color(*DIM)

            elif self.state == 'pending':
                # 脉冲蓝色卡
                g = self._glow
                Color(0.0, g*0.6, g*0.8, 1)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])
                Color(0, g, 1, 0.9)
                Line(rounded_rectangle=(x+1, y+1, w-2, h-2, r), width=dp(1.5))

            elif self.state == 'yang':
                # 阳爻：金色
                Color(0.15, 0.10, 0.0, 1)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])
                Color(*YELL)
                Line(rounded_rectangle=(x+1, y+1, w-2, h-2, r), width=dp(2))
                # 大字 "1"
                Color(*YELL)

            elif self.state == 'yin':
                # 阴爻：青色
                Color(0.0, 0.08, 0.15, 1)
                RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])
                Color(*CYAN)
                Line(rounded_rectangle=(x+1, y+1, w-2, h-2, r), width=dp(2))
                # 大字 "0"
                Color(*CYAN)

        # 用 Label 绘制中心文字（canvas 指令不能直接绘文字，改用子 Label）
        self._refresh_label()

    def _refresh_label(self):
        # 移除旧 label
        for c in list(self.children):
            self.remove_widget(c)

        lmap = {
            'idle':    ('?',   DIM,   sp(18)),
            'pending': ('~',   CYAN,  sp(20)),
            'yang':    ('1',   YELL,  sp(28)),
            'yin':     ('0',   CYAN,  sp(28)),
        }
        txt, col, fs = lmap.get(self.state, ('?', DIM, sp(18)))

        # 爻名
        names = ["初", "二", "三", "四", "五", "上"]
        name_lbl = Label(
            text=f"[color=#2a3a50]{names[self.idx]}[/color]",
            markup=True, font_name=CN, font_size=sp(9),
            size_hint=(1, None), height=dp(14),
            pos=(self.x, self.y + self.height - dp(15)),
            halign='center')
        name_lbl.text_size = (self.width, None)

        # 主数字
        main_lbl = Label(
            text=txt, font_name=CN, font_size=fs, bold=True,
            color=col,
            size_hint=(1, None), height=dp(36),
            pos=(self.x, self.y + dp(10)),
            halign='center')
        main_lbl.text_size = (self.width, None)

        # 阳/阴描述
        if self.state == 'yang':
            sub = '[color=#ffe600]阳[/color]'
        elif self.state == 'yin':
            sub = '[color=#00f5ff]阴[/color]'
        else:
            sub = ''
        sub_lbl = Label(
            text=sub, markup=True, font_name=CN, font_size=sp(10),
            size_hint=(1, None), height=dp(14),
            pos=(self.x, self.y + dp(2)),
            halign='center')
        sub_lbl.text_size = (self.width, None)

        self.add_widget(name_lbl)
        self.add_widget(main_lbl)
        self.add_widget(sub_lbl)

    # ── 状态切换 ────────────────────────────
    def set_pending(self):
        self.state = 'pending'
        self._glow = 0.3
        self._pulse_dir = 1
        if self._pulse_ev:
            self._pulse_ev.cancel()
        self._pulse_ev = Clock.schedule_interval(self._pulse, 0.04)
        self._draw()

    def _pulse(self, dt):
        self._glow += self._pulse_dir * 0.06
        if self._glow >= 1.0:
            self._glow = 1.0; self._pulse_dir = -1
        elif self._glow <= 0.2:
            self._glow = 0.2; self._pulse_dir = 1
        self._draw()

    def reveal(self, is_yang: bool):
        if self._pulse_ev:
            self._pulse_ev.cancel()
        self.state = 'yang' if is_yang else 'yin'
        self._draw()

    def reset(self):
        if self._pulse_ev:
            self._pulse_ev.cancel()
        self.state = 'idle'
        self._draw()


# ══════════════════════════════════════════════
#  按住施法按钮
# ══════════════════════════════════════════════
class HoldCastButton(Widget):
    """按住 3 秒起卦，带进度环"""
    HOLD_SECS = 3.0

    def __init__(self, on_complete=None, **kw):
        super().__init__(**kw)
        self._on_complete = on_complete
        self._holding = False
        self._progress = 0.0      # 0.0 ~ 1.0
        self._hold_ev = None
        self._disabled = False
        self.size_hint_y = None
        self.height = dp(72)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        x, y, w, h = self.x, self.y, self.width, self.height
        cx, cy = x + w/2, y + h/2
        r = dp(8)

        with self.canvas:
            # 背景
            if self._disabled:
                Color(0.1, 0.12, 0.1, 1)
            elif self._holding:
                Color(0.05, 0.15, 0.05, 1)
            else:
                Color(0.08, 0.04, 0.12, 1)
            RoundedRectangle(pos=(x, y), size=(w, h), radius=[r])

            # 边框
            if self._disabled:
                Color(*DIM)
            elif self._holding:
                Color(*GREEN)
            else:
                Color(*PURP)
            Line(rounded_rectangle=(x+1, y+1, w-2, h-2, r), width=dp(1.5))

            # 进度条（底部）
            if self._progress > 0:
                bar_w = (w - dp(24)) * self._progress
                Color(*GREEN)
                RoundedRectangle(
                    pos=(x + dp(12), y + dp(6)),
                    size=(bar_w, dp(4)),
                    radius=[dp(2)])

        # 文字 label
        for c in list(self.children):
            self.remove_widget(c)

        if self._disabled:
            txt = "✓  卦象已成"
            col = GREEN
        elif self._holding:
            pct = int(self._progress * 100)
            txt = f"施法中… {pct}%"
            col = GREEN
        else:
            txt = "◉  按住起卦  CAST"
            col = WHITE

        lbl = Label(text=txt, font_name=CN, font_size=sp(16), bold=True,
                    color=col,
                    size_hint=(1, None), height=h,
                    pos=(x, y + dp(10)),
                    halign='center')
        lbl.text_size = (w, None)
        self.add_widget(lbl)

    # ── 触摸事件 ─────────────────────────────
    def on_touch_down(self, touch):
        if self._disabled or not self.collide_point(*touch.pos):
            return False
        self._holding = True
        self._progress = 0.0
        if self._hold_ev:
            self._hold_ev.cancel()
        self._hold_ev = Clock.schedule_interval(self._tick, 0.033)
        self._draw()
        return True

    def on_touch_up(self, touch):
        if not self._holding:
            return False
        self._holding = False
        if self._hold_ev:
            self._hold_ev.cancel()
        if self._progress < 1.0:
            # 未完成，重置进度
            self._progress = 0.0
            self._draw()
        return True

    def _tick(self, dt):
        self._progress += dt / self.HOLD_SECS
        if self._progress >= 1.0:
            self._progress = 1.0
            self._hold_ev.cancel()
            self._holding = False
            self._disabled = True
            self._draw()
            if self._on_complete:
                self._on_complete()
        else:
            self._draw()

    def reset(self):
        self._disabled = False
        self._holding = False
        self._progress = 0.0
        if self._hold_ev:
            self._hold_ev.cancel()
        self._draw()


# ══════════════════════════════════════════════
#  主界面
# ══════════════════════════════════════════════
class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._bits = []          # list of bool, len 0~6
        self._casting = False
        self._cast_evs = []
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         spacing=dp(8),
                         padding=[dp(12), dp(10), dp(12), dp(10)])
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w,*a: setattr(self._bg,'pos',w.pos),
                  size=lambda w,*a: setattr(self._bg,'size',w.size))

        # ── 标题 ─────────────────────────────
        title = Label(
            text="[color=#00f5ff]▓  筮 问 · SHI WEN  ▓[/color]",
            markup=True, font_name=CN, font_size=sp(20), bold=True,
            size_hint_y=None, height=dp(48))
        root.add_widget(title)
        root.add_widget(self._hline(CYAN))

        # ── 六爻卡片区 ────────────────────────
        cards_title = Label(
            text="[color=#b44fff]── 六 爻 ──[/color]",
            markup=True, font_name=CN, font_size=sp(12),
            size_hint_y=None, height=dp(24))
        root.add_widget(cards_title)

        # 卡片行：上卦 + 下卦各3枚，用两行布局
        self._cards = []        # index 0=初爻 … 5=上爻

        for row_idx in range(2):
            row = BoxLayout(size_hint_y=None, height=dp(62),
                            spacing=dp(8))
            row.add_widget(Widget())  # 左弹性
            for bit_i in range(3):
                global_i = row_idx * 3 + bit_i   # 0-2 下卦, 3-5 上卦
                card = HexBitCard(global_i)
                self._cards.append(card)
                row.add_widget(card)
            row.add_widget(Widget())  # 右弹性
            root.add_widget(row)

        # 下卦/上卦标注
        label_row = BoxLayout(size_hint_y=None, height=dp(18))
        label_row.add_widget(Label(
            text="[color=#445566]← 下 卦 →[/color]",
            markup=True, font_name=CN, font_size=sp(10),
            halign='center'))
        label_row.add_widget(Label(
            text="[color=#445566]← 上 卦 →[/color]",
            markup=True, font_name=CN, font_size=sp(10),
            halign='center'))
        root.add_widget(label_row)

        # ── 进度提示 ─────────────────────────
        self._prog_lbl = Label(
            text="[color=#2a3a50]等待起卦…[/color]",
            markup=True, font_name=CN, font_size=sp(13),
            size_hint_y=None, height=dp(28))
        root.add_widget(self._prog_lbl)

        root.add_widget(self._hline(PURP))

        # ── 按住起卦按钮 ─────────────────────
        self._hold_btn = HoldCastButton(on_complete=self._on_hold_complete)
        root.add_widget(self._hold_btn)

        # ── 重新起卦（小按钮）─────────────────
        reset_btn = cyber_btn(
            "↺  重新起卦",
            bg=INSET, tc=DIM, fs=sp(13),
            size_hint_y=None, height=dp(40))
        reset_btn.bind(on_press=lambda *a: self._reset())
        root.add_widget(reset_btn)

        root.add_widget(self._hline(DIM))

        # ── 版权水印 ─────────────────────────
        root.add_widget(Label(
            text="[color=#1a2535]WADJY · 筮问 SHI WEN  v2.4[/color]",
            markup=True, font_name=CN, font_size=sp(9),
            size_hint_y=None, height=dp(16)))

        self.add_widget(root)

    # ── 工具 ─────────────────────────────────
    def _hline(self, color):
        w = Widget(size_hint_y=None, height=dp(1))
        with w.canvas:
            Color(*color)
            r = Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda ww,*a: setattr(r,'pos',ww.pos),
               size=lambda ww,*a: setattr(r,'size',ww.size))
        return w

    # ── 起卦逻辑 ──────────────────────────────
    def _on_hold_complete(self):
        """按钮按满3秒，开始逐爻生成"""
        if self._casting:
            return
        self._casting = True
        self._bits = []
        results = [random.choice([True, False]) for _ in range(6)]
        self._prog_lbl.text = "[color=#39ff14]施法中… 感应天机[/color]"

        # 逐爻依次亮起，间隔 0.45s
        for i, is_yang in enumerate(results):
            delay = i * 0.45
            # 先亮 pending
            Clock.schedule_once(
                lambda dt, idx=i: self._cards[idx].set_pending(), delay)
            # 再 reveal
            Clock.schedule_once(
                lambda dt, idx=i, v=is_yang: self._reveal_bit(idx, v),
                delay + 0.30)

        # 全部完成后跳转
        Clock.schedule_once(lambda dt: self._go_result(results),
                            6 * 0.45 + 0.5)

    def _reveal_bit(self, idx: int, is_yang: bool):
        self._cards[idx].reveal(is_yang)
        self._bits.append(is_yang)
        names = ["初爻","二爻","三爻","四爻","五爻","上爻"]
        sym = "阳 ━━━" if is_yang else "阴 ━ ━"
        col = "#ffe600" if is_yang else "#00f5ff"
        self._prog_lbl.text = (
            f"[color={col}]{names[idx]} → {sym}[/color]")

    def _go_result(self, results):
        self._casting = False
        self._prog_lbl.text = "[color=#b44fff]六爻已成 → 解析中…[/color]"
        sm = self.manager
        rs = sm.get_screen("result")
        rs.show_hexagram(results)
        sm.transition = SlideTransition(direction="left")
        sm.current = "result"

    def _reset(self):
        self._bits = []
        self._casting = False
        for c in self._cards:
            c.reset()
        self._hold_btn.reset()
        self._prog_lbl.text = "[color=#2a3a50]等待起卦…[/color]"


# ══════════════════════════════════════════════
#  结果界面
# ══════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=[dp(12), dp(8), dp(12), dp(8)],
                         spacing=dp(6))
        with root.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w,*a: setattr(self._bg,'pos',w.pos),
                  size=lambda w,*a: setattr(self._bg,'size',w.size))

        # ── 顶栏 ─────────────────────────────
        top = BoxLayout(size_hint_y=None, height=dp(46))
        back = cyber_btn("◀ 返回", INSET, tc=CYAN, fs=sp(13),
                         size_hint_x=None, width=dp(90))
        back.bind(on_press=self._go_back)
        top.add_widget(back)
        self._title_lbl = Label(
            text="[color=#00f5ff]卦象解读[/color]",
            markup=True, font_name=CN, font_size=sp(16), bold=True)
        top.add_widget(self._title_lbl)
        root.add_widget(top)

        root.add_widget(self._hline(CYAN))

        # ── 卦象信息卡 ───────────────────────
        kua_box = BoxLayout(size_hint_y=None, height=dp(100), spacing=dp(10))
        self._sym_lbl = Label(text="", font_size=sp(60), font_name=CN,
                              color=CYAN, size_hint_x=None, width=dp(90))
        kua_box.add_widget(self._sym_lbl)

        info = BoxLayout(orientation="vertical", spacing=dp(2))
        self._name_lbl = Label(text="", font_size=sp(22), font_name=CN,
                               markup=True, halign="left", valign="middle")
        self._name_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self._pos_lbl  = Label(text="", font_size=sp(11), font_name=CN,
                               color=DIM,  markup=True, halign="left", valign="middle")
        self._pos_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        self._gushi_lbl= Label(text="", font_size=sp(12), font_name=CN,
                               color=YELL, markup=True, halign="left", valign="middle")
        self._gushi_lbl.bind(size=lambda w,s: setattr(w,'text_size',s))
        info.add_widget(self._name_lbl)
        info.add_widget(self._pos_lbl)
        info.add_widget(self._gushi_lbl)
        kua_box.add_widget(info)
        root.add_widget(kua_box)

        root.add_widget(self._hline(PURP))

        # ── 六爻缩略行 ───────────────────────
        self._yao_row = BoxLayout(size_hint_y=None, height=dp(36),
                                  spacing=dp(4))
        root.add_widget(self._yao_row)

        root.add_widget(self._hline(DIM))

        # ── 可滚动详情 ────────────────────────
        sv = ScrollView(do_scroll_x=False)
        self._detail = Label(
            text="", markup=True, font_name=CN, font_size=sp(12.5),
            color=TEXT, size_hint_y=None,
            halign="left", valign="top")
        sv.bind(width=lambda sv, w: setattr(
            self._detail, 'text_size', (w - dp(10), None)))
        self._detail.bind(texture_size=self._detail.setter('size'))
        sv.add_widget(self._detail)
        root.add_widget(sv)

        # ── 底部按钮 ─────────────────────────
        again = cyber_btn("◀  重新起卦", PINK, tc=WHITE, fs=sp(14),
                          size_hint_y=None, height=dp(52))
        again.bind(on_press=self._go_back)
        root.add_widget(again)

        self.add_widget(root)

    def _hline(self, color):
        w = Widget(size_hint_y=None, height=dp(1))
        with w.canvas:
            Color(*color)
            r = Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda ww,*a: setattr(r,'pos',ww.pos),
               size=lambda ww,*a: setattr(r,'size',ww.size))
        return w

    def _go_back(self, *a):
        sm = self.manager
        # 重置主界面
        ms = sm.get_screen("main")
        ms._reset()
        sm.transition = SlideTransition(direction="right")
        sm.current = "main"

    def show_hexagram(self, lines: list):
        int_lines = tuple(1 if v else 0 for v in lines)
        data = HEXAGRAMS.get(int_lines)
        if data is None:
            self._detail.text = (
                f"[color=#ff2d9b]ERROR: 卦象未找到\n键: {int_lines}[/color]")
            return

        seq, name, position, gushi, desc, baihua = data
        lower, upper = int_lines[:3], int_lines[3:]
        lt = TRIGRAMS.get(lower, ("?","?","?"))
        ut = TRIGRAMS.get(upper, ("?","?","?"))
        sym = TSYM.get(upper,"?") + TSYM.get(lower,"?")

        self._title_lbl.text = (
            f"[color=#00f5ff]第 {seq:02d} 卦  ·  {name} 卦[/color]")
        self._sym_lbl.text = sym
        self._name_lbl.text = f"[color=#00f5ff]{name} 卦[/color]"
        self._pos_lbl.text  = (
            f"[color=#2a3a50]{ut[2]}上{lt[2]}下  ·  {position}[/color]")
        self._gushi_lbl.text= f"[color=#ffe600]{gushi}[/color]"

        # 六爻缩略
        self._yao_row.clear_widgets()
        yao_names = ["初","二","三","四","五","上"]
        for i in range(6):
            col = "#ffe600" if int_lines[i]==1 else "#00f5ff"
            sym_s = "1" if int_lines[i]==1 else "0"
            lbl = Label(
                text=f"[color={col}]{sym_s}\n[color=#2a3a50]{yao_names[i]}[/color][/color]",
                markup=True, font_name=CN, font_size=sp(13), bold=True,
                halign='center')
            self._yao_row.add_widget(lbl)

        # 爻辞详解
        yao_full = ["初爻","二爻","三爻","四爻","五爻","上爻"]
        yao_txt = ""
        for i in range(6):
            yc, yb = get_yaoci(int_lines, i)
            sym_line = "━━━━━" if int_lines[i]==1 else "━━ ━━"
            col = "#ffe600" if int_lines[i]==1 else "#00f5ff"
            typ = "阳爻" if int_lines[i]==1 else "阴爻"
            yao_txt += (
                f"\n[color=#b44fff]▌ {yao_full[i]}[/color]  "
                f"[color={col}]{sym_line}  {typ}[/color]\n"
                f"[color=#ffe600]{yc}[/color]\n"
                f"[color=#c8d8e8]{yb}[/color]\n")

        self._detail.text = (
            f"[color=#00f5ff]◆ 卦义[/color]\n"
            f"[color=#c8d8e8]{desc}[/color]\n\n"
            f"[color=#00f5ff]◆ 白话解析[/color]\n"
            f"[color=#39ff14]{baihua}[/color]\n\n"
            f"[color=#b44fff]━━━ 爻辞详解 ━━━[/color]"
            + yao_txt
            + "\n[color=#2a3a50]— 易以道阴阳，仅供参考 —[/color]"
        )


# ══════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════
class ShiWenApp(App):
    def build(self):
        # 注册字体资源路径
        for d in [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
            if d: resource_add_path(d)
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(ResultScreen(name="result"))
        return sm

    def get_application_name(self):
        return "筮问"


if __name__ == "__main__":
    # 本地预览：模拟手机屏幕尺寸
    Window.size = (390, 844)
    ShiWenApp().run()