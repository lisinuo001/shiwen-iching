# -*- coding: utf-8 -*-
"""
筮问 · SHI WEN - Kivy Android 版  v2.3.0
"""
import random
import os
import sys
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp
from kivy.resources import resource_add_path, resource_find

# ── 注册中文字体（Android 兼容路径查找） ────────────
def _find_font():
    """多路径查找字体，兼容开发环境和 Android 打包环境"""
    candidates = [
        # Android APK 解压路径
        os.path.join(os.environ.get("ANDROID_APP_PATH", ""), "NotoSansCJK.otf"),
        # 相对当前工作目录
        os.path.join(os.getcwd(), "NotoSansCJK.otf"),
        # 相对脚本文件
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK.otf"),
        # Kivy resource_find
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    # 最后用 resource_find
    found = resource_find("NotoSansCJK.otf")
    return found if found else None

_font_path = _find_font()
if _font_path:
    LabelBase.register(name="NotoSansCJK", fn_regular=_font_path)
    LabelBase.register(name="Roboto",      fn_regular=_font_path)
    LabelBase.register(name="RobotoMono",  fn_regular=_font_path)
    _CN_FONT = "NotoSansCJK"
else:
    _CN_FONT = "Roboto"

# ── 赛博朋克颜色 ──────────────────────────────
C_BG    = get_color_from_hex("#0a0a0f")
C_PANEL = get_color_from_hex("#0d1117")
C_CARD  = get_color_from_hex("#111520")
C_INSET = get_color_from_hex("#0c1020")
C_CYAN  = get_color_from_hex("#00f5ff")
C_PINK  = get_color_from_hex("#ff2d9b")
C_GREEN = get_color_from_hex("#39ff14")
C_PURP  = get_color_from_hex("#b44fff")
C_YELL  = get_color_from_hex("#ffe600")
C_DIM   = get_color_from_hex("#445566")
C_TEXT  = get_color_from_hex("#c8d8e8")
C_WHITE = get_color_from_hex("#ffffff")

Window.clearcolor = C_BG

# ── 八卦基础数据 ─────────────────────────────
TRIGRAMS = {
    (1,1,1):("乾","☰","天"), (0,0,0):("坤","☷","地"),
    (1,0,0):("震","☳","雷"), (0,0,1):("艮","☶","山"),
    (0,1,1):("巽","☴","风"), (1,1,0):("兑","☱","泽"),
    (1,0,1):("坎","☵","水"), (0,1,0):("离","☲","火"),
}
TRIGRAM_SYMBOLS = {k: v[1] for k, v in TRIGRAMS.items()}

# ── 从数据文件导入（打包时放同目录）───────────
def _load_data():
    # Android 打包后 .py 文件在 app 目录下
    for search_dir in [
        os.getcwd(),
        os.path.dirname(os.path.abspath(__file__)),
        os.environ.get("ANDROID_APP_PATH", ""),
    ]:
        if search_dir and search_dir not in sys.path:
            sys.path.insert(0, search_dir)
    try:
        from iching_data import HEXAGRAMS
        from yaoci_data import get_yaoci
        return HEXAGRAMS, get_yaoci
    except Exception as e:
        return {}, lambda k, i: ("此爻待查", f"数据加载失败: {e}")

HEXAGRAMS, get_yaoci = _load_data()


# ══════════════════════════════════════════════
#  铜钱控件
# ══════════════════════════════════════════════
class CoinWidget(Widget):
    def __init__(self, idx, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.state = "idle"
        self._anim_angle = 0
        self._anim_event = None
        self.size_hint = (None, None)
        self.size = (dp(64), dp(64))
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        import math
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        r = min(self.width, self.height) / 2 - dp(3)
        with self.canvas:
            if self.state == "idle":
                Color(*C_DIM)
                Line(circle=(cx, cy, r), width=dp(1.5))
            elif self.state == "spinning":
                ry = abs(r * abs(math.cos(self._anim_angle * math.pi * 3)))
                Color(*C_YELL)
                Ellipse(pos=(cx - r, cy - ry), size=(r*2, max(ry*2, 2)))
            elif self.state == "yang":
                Color(0.1, 0.06, 0, 1)
                Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
                Color(*C_YELL)
                Line(circle=(cx, cy, r), width=dp(2))
                # 绘制阳面符号
                Color(*C_YELL)
                Line(points=[cx-r*0.4, cy, cx+r*0.4, cy], width=dp(2))
            elif self.state == "yin":
                Color(0.04, 0.04, 0.1, 1)
                Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
                Color(*C_CYAN)
                Line(circle=(cx, cy, r), width=dp(2))
                # 绘制阴面符号
                Color(*C_CYAN)
                Line(points=[cx-r*0.4, cy, cx-r*0.05, cy], width=dp(2))
                Line(points=[cx+r*0.05, cy, cx+r*0.4, cy], width=dp(2))

    def spin(self, result_yang: bool, callback=None):
        self.state = "spinning"
        self._result = result_yang
        self._anim_angle = 0
        self._max_ticks = 20 + random.randint(0, 8)
        self._tick = 0
        self._cb = callback
        if self._anim_event:
            self._anim_event.cancel()
        self._anim_event = Clock.schedule_interval(self._spin_step, 0.045)

    def _spin_step(self, dt):
        self._tick += 1
        self._anim_angle = self._tick / self._max_ticks
        self._redraw()
        if self._tick >= self._max_ticks:
            self._anim_event.cancel()
            self.state = "yang" if self._result else "yin"
            self._redraw()
            if self._cb:
                self._cb()

    def reset(self):
        self.state = "idle"
        if self._anim_event:
            try: self._anim_event.cancel()
            except: pass
        self._redraw()


# ══════════════════════════════════════════════
#  爻线控件（自适应宽度）
# ══════════════════════════════════════════════
class YaoLineWidget(Widget):
    def __init__(self, idx, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.is_yang = None
        self.size_hint_y = None
        self.height = dp(30)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        # 根据控件实际宽度自适应，留出边距
        half = self.width * 0.42
        gap = dp(10)
        names = ["初", "二", "三", "四", "五", "上"]
        with self.canvas:
            if self.is_yang is None:
                Color(*C_DIM)
                Line(points=[cx - half, cy, cx + half, cy],
                     width=dp(1), dash_offset=4, dash_length=6)
            elif self.is_yang:
                # 阳爻：整根线
                Color(*C_YELL)
                Line(points=[cx - half, cy, cx + half, cy], width=dp(5))
            else:
                # 阴爻：两段，中间有空隙
                Color(*C_CYAN)
                Line(points=[cx - half, cy, cx - gap, cy], width=dp(5))
                Line(points=[cx + gap, cy, cx + half, cy], width=dp(5))

    def set_yao(self, is_yang: bool):
        self.is_yang = is_yang
        self._draw()

    def reset(self):
        self.is_yang = None
        self._draw()


# ══════════════════════════════════════════════
#  通用赛博风格按钮工厂
# ══════════════════════════════════════════════
def cyber_btn(text, bg_color, text_color=None, font_size=None, **kw):
    tc = text_color or (0, 0, 0, 1)
    fs = font_size or sp(14)
    btn = Button(
        text=text,
        font_size=fs,
        bold=True,
        background_normal="",
        background_color=bg_color,
        color=tc,
        **kw
    )
    # 按压效果
    def on_press(instance):
        r, g, b, a = bg_color
        instance.background_color = (r*0.6, g*0.6, b*0.6, a)
    def on_release(instance):
        instance.background_color = bg_color
    btn.bind(on_press=on_press, on_release=on_release)
    return btn


# ══════════════════════════════════════════════
#  主起卦界面
# ══════════════════════════════════════════════
class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._lines = []
        self._throw_count = 0
        self._casting = False
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         spacing=dp(4), padding=[dp(10), dp(6), dp(10), dp(6)])
        with root.canvas.before:
            Color(*C_BG)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        # ── 标题栏 ──────────────────────────
        title = Label(
            text="[color=#00f5ff]▓▓  筮 问 · SHI WEN  ▓▓[/color]",
            markup=True, font_size=sp(18), bold=True,
            font_name=_CN_FONT,
            size_hint_y=None, height=dp(46))
        root.add_widget(title)

        root.add_widget(self._hline(C_CYAN))

        # ── 问题输入 ─────────────────────────
        q_box = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        q_lbl = Label(
            text="[color=#39ff14]问：[/color]",
            markup=True, size_hint_x=None, width=dp(38),
            font_name=_CN_FONT, font_size=sp(15))
        q_box.add_widget(q_lbl)
        self._q_input = TextInput(
            hint_text="请输入所问之事…",
            multiline=False, font_size=sp(13),
            font_name=_CN_FONT,
            background_color=C_INSET,
            foreground_color=C_GREEN,
            hint_text_color=C_DIM,
            cursor_color=C_CYAN)
        q_box.add_widget(self._q_input)
        root.add_widget(q_box)

        # ── 轮次提示 ─────────────────────────
        self._round_lbl = Label(
            text="[color=#ff2d9b]◈  第 0 / 2 轮  ·  点击 CAST 开始[/color]",
            markup=True, font_size=sp(13), font_name=_CN_FONT,
            size_hint_y=None, height=dp(28))
        root.add_widget(self._round_lbl)

        # ── 3 枚铜钱 ─────────────────────────
        coin_row = BoxLayout(size_hint_y=None, height=dp(80),
                             spacing=dp(16))
        coin_row.add_widget(Widget())  # 左弹性空间
        self._coins = []
        for i in range(3):
            c = CoinWidget(i)
            coin_row.add_widget(c)
            self._coins.append(c)
        coin_row.add_widget(Widget())  # 右弹性空间
        root.add_widget(coin_row)

        # ── 提示文字 ─────────────────────────
        self._info_lbl = Label(
            text="[color=#445566]第1投 → 下卦(初二三爻)  第2投 → 上卦(四五上爻)[/color]",
            markup=True, font_size=sp(11), font_name=_CN_FONT,
            size_hint_y=None, height=dp(24))
        root.add_widget(self._info_lbl)

        root.add_widget(self._hline(C_PURP))

        # ── 六爻显示区 ────────────────────────
        # 标题行
        yao_header = Label(
            text="[color=#b44fff]── 六 爻 ──[/color]",
            markup=True, font_size=sp(12), font_name=_CN_FONT,
            size_hint_y=None, height=dp(22))
        root.add_widget(yao_header)

        self._yao_widgets = []
        # 爻从上到下显示：上爻(5)→初爻(0)，符合传统卦象布局
        for i in range(5, -1, -1):
            row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(4))
            # 爻名标签
            yao_names = ["初", "二", "三", "四", "五", "上"]
            name_lbl = Label(
                text=f"[color=#445566]{yao_names[i]}爻[/color]",
                markup=True, font_size=sp(10), font_name=_CN_FONT,
                size_hint_x=None, width=dp(36), halign="right")
            row.add_widget(name_lbl)
            # 爻线
            yw = YaoLineWidget(i)
            self._yao_widgets.append(yw)
            row.add_widget(yw)
            root.add_widget(row)

        # 恢复正确顺序（索引0=初爻）
        self._yao_widgets.reverse()

        root.add_widget(self._hline(C_DIM))

        # ── 按钮区 ───────────────────────────
        btn_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))

        self._cast_btn = cyber_btn(
            text="▶  CAST  投掷铜钱",
            bg_color=C_PINK, text_color=C_WHITE,
            font_size=sp(15))
        self._cast_btn.bind(on_press=lambda *a: self._cast_throw())
        btn_row.add_widget(self._cast_btn)

        auto_btn = cyber_btn(
            text="⚡ AUTO",
            bg_color=C_PURP, text_color=C_WHITE,
            font_size=sp(13), size_hint_x=0.38)
        auto_btn.bind(on_press=lambda *a: self._auto_cast())
        btn_row.add_widget(auto_btn)

        reset_btn = cyber_btn(
            text="RESET",
            bg_color=C_INSET, text_color=C_DIM,
            font_size=sp(13), size_hint_x=0.38)
        reset_btn.bind(on_press=lambda *a: self._reset())
        btn_row.add_widget(reset_btn)

        root.add_widget(btn_row)

        # ── 状态栏 ───────────────────────────
        self._status_lbl = Label(
            text="[color=#39ff14]READY  //  等待起卦[/color]",
            markup=True, font_size=sp(10), font_name=_CN_FONT,
            size_hint_y=None, height=dp(22))
        root.add_widget(self._status_lbl)

        # ── 版权水印 ─────────────────────────
        watermark = Label(
            text="[color=#2a3a4a]WADJY · 筮问 SHI WEN  v2.3[/color]",
            markup=True, font_size=sp(9), font_name=_CN_FONT,
            size_hint_y=None, height=dp(18))
        root.add_widget(watermark)

        self.add_widget(root)

    def _hline(self, color):
        w = Widget(size_hint_y=None, height=dp(1))
        with w.canvas:
            Color(*color)
            rect = Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda ww, *a: setattr(rect, 'pos', ww.pos),
               size=lambda ww, *a: setattr(rect, 'size', ww.size))
        return w

    def _update_bg(self, instance, *a):
        self._bg_rect.pos = instance.pos
        self._bg_rect.size = instance.size

    # ── 起卦逻辑 ──────────────────────────────
    def _cast_throw(self):
        if self._casting or self._throw_count >= 2:
            return
        self._casting = True
        self._cast_btn.disabled = True

        results = [random.choice([True, False]) for _ in range(3)]
        for c in self._coins:
            c.reset()

        done = [0]
        def on_done():
            done[0] += 1
            if done[0] == 3:
                self._on_throw_done(results)

        for i, coin in enumerate(self._coins):
            Clock.schedule_once(
                lambda dt, c=coin, r=results[i]: c.spin(r, on_done),
                i * 0.12)

    def _on_throw_done(self, results):
        offset = self._throw_count * 3
        for i, is_yang in enumerate(results):
            yao_idx = offset + i
            self._lines.append(is_yang)
            self._yao_widgets[yao_idx].set_yao(is_yang)

        self._throw_count += 1
        self._casting = False

        if self._throw_count == 1:
            self._round_lbl.text = "[color=#39ff14]◈  第 1 / 2 轮  ·  下卦完成！[/color]"
            self._info_lbl.text = "[color=#39ff14]下卦 ✓  请再次点击 CAST 投掷上卦[/color]"
            self._cast_btn.text = "▶  CAST  投掷第 2 次"
            self._cast_btn.disabled = False
            self._status_lbl.text = "[color=#39ff14]下卦已生成 → 继续投上卦[/color]"
        else:
            self._round_lbl.text = "[color=#ff2d9b]◈  第 2 / 2 轮  ·  卦象已成！[/color]"
            self._cast_btn.text = "COMPLETE  ✓"
            self._info_lbl.text = "[color=#00f5ff]六爻已全部生成，正在解析…[/color]"
            self._status_lbl.text = "[color=#00f5ff]解析卦象中…[/color]"
            Clock.schedule_once(lambda dt: self._go_result(), 0.5)

    def _auto_cast(self):
        if self._casting:
            return
        self._reset_silent()
        self._casting = True

        r1 = [random.choice([True, False]) for _ in range(3)]
        done1 = [0]

        def do_second(dt=None):
            r2 = [random.choice([True, False]) for _ in range(3)]
            for c in self._coins:
                c.reset()
            done2 = [0]
            def fin():
                done2[0] += 1
                if done2[0] == 3:
                    self._on_throw_done(r2)
            for i, c in enumerate(self._coins):
                Clock.schedule_once(
                    lambda dt, cc=c, rr=r2[i]: cc.spin(rr, fin),
                    i * 0.1)

        def first_done():
            done1[0] += 1
            if done1[0] == 3:
                self._on_throw_done(r1)
                Clock.schedule_once(do_second, 0.6)

        for i, c in enumerate(self._coins):
            Clock.schedule_once(
                lambda dt, cc=c, rr=r1[i]: cc.spin(rr, first_done),
                i * 0.1)

    def _go_result(self):
        sm = self.manager
        rs = sm.get_screen("result")
        rs.show_hexagram(self._lines, self._q_input.text.strip())
        sm.transition = SlideTransition(direction="left")
        sm.current = "result"

    def _reset_silent(self):
        self._lines = []
        self._throw_count = 0
        self._casting = False
        for c in self._coins:
            c.reset()
        for yw in self._yao_widgets:
            yw.reset()
        self._round_lbl.text = "[color=#ff2d9b]◈  第 0 / 2 轮  ·  点击 CAST 开始[/color]"
        self._info_lbl.text = "[color=#445566]第1投 → 下卦(初二三爻)  第2投 → 上卦(四五上爻)[/color]"
        self._cast_btn.text = "▶  CAST  投掷铜钱"
        self._cast_btn.disabled = False

    def _reset(self):
        self._reset_silent()
        self._status_lbl.text = "[color=#445566]RESET  //  等待起卦[/color]"


# ══════════════════════════════════════════════
#  结果展示界面
# ══════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical",
                         padding=[dp(10), dp(6), dp(10), dp(6)],
                         spacing=dp(6))
        with root.canvas.before:
            Color(*C_BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w, *a: setattr(self._bg, 'pos', w.pos),
                  size=lambda w, *a: setattr(self._bg, 'size', w.size))

        # ── 顶栏 ─────────────────────────────
        top = BoxLayout(size_hint_y=None, height=dp(44))
        back_btn = cyber_btn(
            text="◀ 返回",
            bg_color=C_INSET, text_color=C_CYAN,
            font_size=sp(13), size_hint_x=None, width=dp(90))
        back_btn.bind(on_press=self._go_back)
        top.add_widget(back_btn)
        self._kua_title_lbl = Label(
            text="[color=#00f5ff]卦象解读[/color]",
            markup=True, font_size=sp(16),
            font_name=_CN_FONT, bold=True)
        top.add_widget(self._kua_title_lbl)
        root.add_widget(top)

        root.add_widget(self._hline(C_CYAN))

        # ── 卦象信息卡 ───────────────────────
        kua_box = BoxLayout(size_hint_y=None, height=dp(96), spacing=dp(12))

        self._sym_lbl = Label(
            text="", font_size=sp(56),
            font_name=_CN_FONT, color=C_CYAN,
            size_hint_x=None, width=dp(96))
        kua_box.add_widget(self._sym_lbl)

        info_col = BoxLayout(orientation="vertical", spacing=dp(2))
        self._name_lbl = Label(
            text="", font_size=sp(20),
            font_name=_CN_FONT, color=C_CYAN,
            markup=True, halign="left", valign="middle")
        self._name_lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))

        self._pos_lbl = Label(
            text="", font_size=sp(11),
            font_name=_CN_FONT, color=C_DIM,
            markup=True, halign="left", valign="middle")
        self._pos_lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))

        self._gushi_lbl = Label(
            text="", font_size=sp(12),
            font_name=_CN_FONT, color=C_YELL,
            markup=True, halign="left", valign="middle")
        self._gushi_lbl.bind(size=lambda w, s: setattr(w, 'text_size', s))

        info_col.add_widget(self._name_lbl)
        info_col.add_widget(self._pos_lbl)
        info_col.add_widget(self._gushi_lbl)
        kua_box.add_widget(info_col)
        root.add_widget(kua_box)

        root.add_widget(self._hline(C_PURP))

        # ── 可滚动详情区 ─────────────────────
        sv = ScrollView(do_scroll_x=False)
        self._detail_lbl = Label(
            text="", markup=True,
            font_size=sp(12),
            font_name=_CN_FONT,
            color=C_TEXT,
            size_hint_y=None,
            halign="left", valign="top")
        # 让 Label 宽度跟随 ScrollView 宽度
        sv.bind(width=lambda sv, w: setattr(
            self._detail_lbl, 'text_size', (w - dp(16), None)))
        self._detail_lbl.bind(
            texture_size=self._detail_lbl.setter('size'))
        sv.add_widget(self._detail_lbl)
        root.add_widget(sv)

        # ── 底部按钮 ─────────────────────────
        again_btn = cyber_btn(
            text="◀  重新起卦",
            bg_color=C_PINK, text_color=C_WHITE,
            font_size=sp(14),
            size_hint_y=None, height=dp(50))
        again_btn.bind(on_press=self._go_back)
        root.add_widget(again_btn)

        self.add_widget(root)

    def _hline(self, color):
        w = Widget(size_hint_y=None, height=dp(1))
        with w.canvas:
            Color(*color)
            rect = Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda ww, *a: setattr(rect, 'pos', ww.pos),
               size=lambda ww, *a: setattr(rect, 'size', ww.size))
        return w

    def _go_back(self, *a):
        sm = self.manager
        sm.transition = SlideTransition(direction="right")
        sm.current = "main"

    def show_hexagram(self, lines: list, question: str):
        int_lines = tuple(1 if v else 0 for v in lines)
        data = HEXAGRAMS.get(int_lines)
        if data is None:
            self._detail_lbl.text = (
                f"[color=#ff2d9b]ERROR: 卦象查找失败\n键值: {int_lines}[/color]")
            return

        seq, name, position, gushi, desc, baihua = data

        lower = int_lines[:3]
        upper = int_lines[3:]
        lower_t = TRIGRAMS.get(lower, ("?", "?", "?"))
        upper_t = TRIGRAMS.get(upper, ("?", "?", "?"))
        sym = TRIGRAM_SYMBOLS.get(upper, "?") + TRIGRAM_SYMBOLS.get(lower, "?")

        self._kua_title_lbl.text = (
            f"[color=#00f5ff]第 {seq:02d} 卦  ·  {name} 卦[/color]")
        self._sym_lbl.text = sym
        self._name_lbl.text = f"[color=#00f5ff]{name} 卦[/color]"
        self._pos_lbl.text = (
            f"[color=#445566]{upper_t[2]}上{lower_t[2]}下  |  {position}[/color]")
        self._gushi_lbl.text = f"[color=#ffe600]{gushi}[/color]"

        # ── 爻辞文本 ──────────────────────────
        yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
        yao_txt = ""
        for i in range(6):
            yc, yb = get_yaoci(int_lines, i)
            sym_line = "─────" if int_lines[i] == 1 else "── ──"
            col = "#ffe600" if int_lines[i] == 1 else "#00f5ff"
            yao_txt += (
                f"\n[color=#b44fff][{yao_names[i]}]  "
                f"[color={col}]{sym_line}[/color][/color]\n"
                f"[color=#ffe600]{yc}[/color]\n"
                f"[color=#c8d8e8]→ {yb}[/color]\n")

        q_txt = (f"[color=#ff2d9b]» 所问：{question}[/color]\n\n"
                 if question else "")

        self._detail_lbl.text = (
            q_txt
            + f"[color=#00f5ff]◆ 卦义[/color]\n"
            + f"[color=#c8d8e8]{desc}[/color]\n\n"
            + f"[color=#00f5ff]◆ 白话解析[/color]\n"
            + f"[color=#39ff14]{baihua}[/color]\n\n"
            + f"[color=#b44fff]━━━ 爻辞逐爻解读 ━━━[/color]"
            + yao_txt
            + "\n[color=#445566]— 易以道阴阳，仅供参考。—[/color]"
        )


# ══════════════════════════════════════════════
#  App 入口
# ══════════════════════════════════════════════
class IChing(App):
    def build(self):
        # 将字体目录加入 Kivy 资源搜索路径
        font_dir = os.path.dirname(os.path.abspath(__file__))
        resource_add_path(font_dir)
        resource_add_path(os.getcwd())

        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(ResultScreen(name="result"))
        return sm

    def get_application_name(self):
        return "筮问"


if __name__ == "__main__":
    IChing().run()