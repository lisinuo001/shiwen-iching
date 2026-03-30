
# -*- coding: utf-8 -*-
"""
易经算卦 - Kivy Android 版
"""
import random
import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
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

# ── 注册中文字体并设为全局默认 ──────────────────
_font_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK.otf")
if os.path.exists(_font_path):
    # 注册为 NotoSansCJK
    LabelBase.register(name="NotoSansCJK", fn_regular=_font_path)
    # 覆盖 Roboto（Kivy默认字体），使所有 Label/Button 自动使用中文字体
    LabelBase.register(name="Roboto",      fn_regular=_font_path)
    _CN_FONT = "NotoSansCJK"
else:
    _CN_FONT = "Roboto"

# ── 赛博朋克颜色 ──────────────────────────────
C_BG       = get_color_from_hex("#0a0a0f")
C_PANEL    = get_color_from_hex("#0d1117")
C_CARD     = get_color_from_hex("#111520")
C_INSET    = get_color_from_hex("#0c1020")
C_CYAN     = get_color_from_hex("#00f5ff")
C_PINK     = get_color_from_hex("#ff2d9b")
C_GREEN    = get_color_from_hex("#39ff14")
C_PURP     = get_color_from_hex("#b44fff")
C_YELL     = get_color_from_hex("#ffe600")
C_DIM      = get_color_from_hex("#445566")
C_TEXT     = get_color_from_hex("#c8d8e8")

Window.clearcolor = C_BG

# ── 64卦数据（精简版，完整版从模块导入）────────
TRIGRAMS = {
    (1,1,1):("乾","☰","天"), (0,0,0):("坤","☷","地"),
    (1,0,0):("震","☳","雷"), (0,0,1):("艮","☶","山"),
    (0,1,1):("巽","☴","风"), (1,1,0):("兑","☱","泽"),
    (1,0,1):("坎","☵","水"), (0,1,0):("离","☲","火"),
}

# 从主数据文件导入（打包时同目录）
try:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from iching_data import HEXAGRAMS
    from yaoci_data import get_yaoci
except Exception:
    HEXAGRAMS = {}
    def get_yaoci(k, i): return ("此爻待查", "请参考完整版")

TRIGRAM_SYMBOLS = {
    (1,1,1):"☰",(0,0,0):"☷",(1,0,0):"☳",
    (0,0,1):"☶",(0,1,1):"☴",(1,1,0):"☱",
    (1,0,1):"☵",(0,1,0):"☲",
}


# ══════════════════════════════════════════════
#  铜钱控件
# ══════════════════════════════════════════════
class CoinWidget(Widget):
    def __init__(self, idx, **kw):
        super().__init__(**kw)
        self.idx   = idx
        self.state = "idle"   # idle / spinning / yang / yin
        self._anim_angle = 0
        self._anim_event = None
        self.size_hint = (None, None)
        self.size = (dp(64), dp(64))
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        r = min(self.width, self.height) / 2 - dp(3)
        with self.canvas:
            if self.state == "idle":
                Color(*C_DIM)
                Line(circle=(cx, cy, r), width=dp(1.5))
                Color(*C_DIM)
                # 编号
            elif self.state == "spinning":
                ry = abs(r * abs(__import__('math').cos(self._anim_angle * 3.14 * 3)))
                Color(*C_YELL)
                Ellipse(pos=(cx - r, cy - ry), size=(r*2, ry*2 if ry > 1 else 2))
            elif self.state == "yang":
                Color(0.1, 0.06, 0, 1)
                Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
                Color(*C_YELL)
                Line(circle=(cx, cy, r), width=dp(2))
            elif self.state == "yin":
                Color(0.04, 0.04, 0.1, 1)
                Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
                Color(*C_CYAN)
                Line(circle=(cx, cy, r), width=dp(2))

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
#  爻线控件
# ══════════════════════════════════════════════
class YaoLineWidget(Widget):
    def __init__(self, idx, **kw):
        super().__init__(**kw)
        self.idx = idx
        self.is_yang = None
        self.size_hint_y = None
        self.height = dp(28)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _draw(self, *a):
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        w2 = self.width * 0.38
        names = ["初", "二", "三", "四", "五", "上"]
        with self.canvas:
            if self.is_yang is None:
                Color(*C_DIM)
                Line(points=[cx - dp(60), cy, cx + dp(60), cy],
                     width=dp(1), dash_offset=4, dash_length=4)
            elif self.is_yang:
                Color(*C_YELL)
                Line(points=[cx - dp(72), cy, cx + dp(72), cy], width=dp(5))
            else:
                Color(*C_CYAN)
                Line(points=[cx - dp(72), cy, cx - dp(8), cy], width=dp(5))
                Line(points=[cx + dp(8), cy, cx + dp(72), cy], width=dp(5))

    def set_yao(self, is_yang: bool):
        self.is_yang = is_yang
        self._draw()

    def reset(self):
        self.is_yang = None
        self._draw()


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
                         spacing=dp(6), padding=dp(8))
        with root.canvas.before:
            Color(*C_BG)
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=self._update_bg, size=self._update_bg)

        # 标题栏
        title = Label(
            text="[color=#00f5ff]▓▓ 易·经·算·卦  CYBER v2.0 ▓▓[/color]",
            markup=True, font_size=sp(17),
            size_hint_y=None, height=dp(44))
        root.add_widget(title)

        # 分割线
        root.add_widget(self._hline(C_CYAN))

        # 问题输入
        q_box = BoxLayout(size_hint_y=None, height=dp(44),
                          spacing=dp(6))
        q_box.add_widget(Label(text="[color=#39ff14]问:[/color]",
                               markup=True, size_hint_x=None,
                               width=dp(30), font_size=sp(14)))
        self._q_input = TextInput(
            hint_text="输入所问之事...",
            multiline=False, font_size=sp(13),
            background_color=C_INSET,
            foreground_color=C_GREEN,
            hint_text_color=C_DIM,
            cursor_color=C_CYAN)
        q_box.add_widget(self._q_input)
        root.add_widget(q_box)

        # 轮次提示
        self._round_lbl = Label(
            text="[color=#ff2d9b][ ROUND 0/2 ]  点击 CAST 开始[/color]",
            markup=True, font_size=sp(13),
            size_hint_y=None, height=dp(30))
        root.add_widget(self._round_lbl)

        # 3枚铜钱
        coin_row = BoxLayout(size_hint_y=None, height=dp(80),
                             spacing=dp(16))
        coin_row.add_widget(Widget())
        self._coins = []
        for i in range(3):
            c = CoinWidget(i)
            coin_row.add_widget(c)
            self._coins.append(c)
        coin_row.add_widget(Widget())
        root.add_widget(coin_row)

        # 提示文字
        self._info_lbl = Label(
            text="第1次 → 下卦(初/二/三爻)  第2次 → 上卦(四/五/上爻)",
            font_size=sp(11), color=C_DIM,
            size_hint_y=None, height=dp(28))
        root.add_widget(self._info_lbl)

        root.add_widget(self._hline(C_CYAN))

        # 六爻显示
        self._yao_widgets = []
        for i in range(6):
            yw = YaoLineWidget(i)
            root.add_widget(yw)
            self._yao_widgets.append(yw)

        root.add_widget(self._hline(C_DIM))

        # 按钮区
        btn_row = BoxLayout(size_hint_y=None, height=dp(52),
                            spacing=dp(8))
        self._cast_btn = Button(
            text="▶  CAST  投掷铜钱",
            font_size=sp(14), bold=True,
            background_color=C_PINK,
            color=(0, 0, 0, 1))
        self._cast_btn.bind(on_press=lambda *a: self._cast_throw())
        btn_row.add_widget(self._cast_btn)

        auto_btn = Button(
            text="⚡ AUTO",
            font_size=sp(13),
            background_color=C_PURP,
            color=(0, 0, 0, 1),
            size_hint_x=0.4)
        auto_btn.bind(on_press=lambda *a: self._auto_cast())
        btn_row.add_widget(auto_btn)

        reset_btn = Button(
            text="RESET",
            font_size=sp(13),
            background_color=C_INSET,
            color=C_DIM,
            size_hint_x=0.4)
        reset_btn.bind(on_press=lambda *a: self._reset())
        btn_row.add_widget(reset_btn)
        root.add_widget(btn_row)

        # 状态栏
        self._status_lbl = Label(
            text="[color=#39ff14]READY // 等待起卦[/color]",
            markup=True, font_size=sp(10),
            size_hint_y=None, height=dp(22))
        root.add_widget(self._status_lbl)

        self.add_widget(root)

    def _hline(self, color):
        w = Widget(size_hint_y=None, height=dp(1))
        with w.canvas:
            Color(*color)
            self._hl = Rectangle(pos=w.pos, size=w.size)
        w.bind(pos=lambda ww, *a: setattr(self._hl, 'pos', ww.pos),
               size=lambda ww, *a: setattr(self._hl, 'size', ww.size))
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
            Clock.schedule_once(lambda dt, c=coin, r=results[i]: c.spin(r, on_done),
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
            self._round_lbl.text = "[color=#39ff14][ ROUND 1/2 ]  下卦完成！[/color]"
            self._info_lbl.text = "下卦 ✓  请再次点击 CAST 投掷上卦"
            self._cast_btn.text = "▶  CAST  投掷第2次"
            self._cast_btn.disabled = False
            self._status_lbl.text = "[color=#39ff14]下卦已生成 → 继续投上卦[/color]"
        else:
            self._round_lbl.text = "[color=#ff2d9b][ ROUND 2/2 ]  卦成！[/color]"
            self._cast_btn.text = "COMPLETE ✓"
            self._info_lbl.text = "六爻已全部生成，正在解析..."
            self._status_var_set("正在解析卦象...")
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
            for c in self._coins: c.reset()
            done2 = [0]
            def fin():
                done2[0] += 1
                if done2[0] == 3:
                    self._on_throw_done(r2)
            for i, c in enumerate(self._coins):
                Clock.schedule_once(lambda dt, cc=c, rr=r2[i]: cc.spin(rr, fin),
                                     i * 0.1)

        def first_done():
            done1[0] += 1
            if done1[0] == 3:
                self._on_throw_done(r1)
                Clock.schedule_once(do_second, 0.6)

        for i, c in enumerate(self._coins):
            Clock.schedule_once(lambda dt, cc=c, rr=r1[i]: cc.spin(rr, first_done),
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
        for c in self._coins: c.reset()
        for yw in self._yao_widgets: yw.reset()
        self._round_lbl.text = "[color=#ff2d9b][ ROUND 0/2 ]  点击 CAST 开始[/color]"
        self._info_lbl.text = "第1次 → 下卦(初/二/三爻)  第2次 → 上卦(四/五/上爻)"
        self._cast_btn.text = "▶  CAST  投掷铜钱"
        self._cast_btn.disabled = False

    def _reset(self):
        self._reset_silent()
        self._status_var_set("RESET // 等待起卦")

    def _status_var_set(self, txt):
        self._status_lbl.text = f"[color=#39ff14]{txt}[/color]"


# ══════════════════════════════════════════════
#  结果展示界面
# ══════════════════════════════════════════════
class ResultScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build()

    def _build(self):
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(6))
        with root.canvas.before:
            Color(*C_BG)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda w, *a: setattr(self._bg,'pos',w.pos),
                  size=lambda w, *a: setattr(self._bg,'size',w.size))

        # 顶栏
        top = BoxLayout(size_hint_y=None, height=dp(42))
        back_btn = Button(
            text="◀ 返回",
            size_hint_x=None, width=dp(80),
            font_size=sp(13),
            background_color=C_INSET, color=C_CYAN)
        back_btn.bind(on_press=self._go_back)
        top.add_widget(back_btn)
        self._kua_title_lbl = Label(
            text="[color=#00f5ff]卦象解读[/color]",
            markup=True, font_size=sp(15))
        top.add_widget(self._kua_title_lbl)
        root.add_widget(top)

        # 卦象信息区
        kua_box = BoxLayout(size_hint_y=None, height=dp(90),
                            spacing=dp(10))
        self._sym_lbl = Label(text="", font_size=sp(52),
                              color=C_CYAN,
                              size_hint_x=None, width=dp(90))
        kua_box.add_widget(self._sym_lbl)
        info_col = BoxLayout(orientation="vertical")
        self._name_lbl  = Label(text="", font_size=sp(18),
                                color=C_CYAN, markup=True, halign="left")
        self._pos_lbl   = Label(text="", font_size=sp(11),
                                color=C_DIM,  markup=True, halign="left")
        self._gushi_lbl = Label(text="", font_size=sp(12),
                                color=C_YELL, markup=True, halign="left")
        info_col.add_widget(self._name_lbl)
        info_col.add_widget(self._pos_lbl)
        info_col.add_widget(self._gushi_lbl)
        kua_box.add_widget(info_col)
        root.add_widget(kua_box)

        # 滚动文本区
        sv = ScrollView()
        self._detail_lbl = Label(
            text="", markup=True,
            font_size=sp(11),
            color=C_TEXT,
            size_hint_y=None,
            text_size=(Window.width - dp(24), None),
            halign="left", valign="top")
        self._detail_lbl.bind(texture_size=self._detail_lbl.setter('size'))
        sv.add_widget(self._detail_lbl)
        root.add_widget(sv)

        self.add_widget(root)

    def _go_back(self, *a):
        sm = self.manager
        sm.transition = SlideTransition(direction="right")
        sm.current = "main"

    def show_hexagram(self, lines: list, question: str):
        int_lines = tuple(1 if v else 0 for v in lines)
        data = HEXAGRAMS.get(int_lines)
        if data is None:
            self._detail_lbl.text = "[color=#ff2d9b]ERROR: 卦象查找失败[/color]"
            return

        seq, name, position, gushi, desc, baihua = data
        lower = int_lines[:3]
        upper = int_lines[3:]
        lower_t = TRIGRAMS.get(lower, ("?","?","?"))
        upper_t = TRIGRAMS.get(upper, ("?","?","?"))
        sym = TRIGRAM_SYMBOLS.get(upper,"?") + TRIGRAM_SYMBOLS.get(lower,"?")

        self._kua_title_lbl.text = (
            f"[color=#00f5ff]第{seq:02d}卦  {name}卦[/color]")
        self._sym_lbl.text = sym
        self._name_lbl.text = f"[color=#00f5ff]{name} 卦[/color]"
        self._pos_lbl.text  = (
            f"[color=#445566]{upper_t[2]}上{lower_t[2]}下  |  {position}[/color]")
        self._gushi_lbl.text = f"[color=#ffe600]{gushi}[/color]"

        # 构建爻辞文本
        yao_names = ["初爻","二爻","三爻","四爻","五爻","上爻"]
        yao_txt = ""
        for i in range(6):
            yc, yb = get_yaoci(int_lines, i)
            sym_line = "─────" if int_lines[i]==1 else "── ──"
            col = "#ffe600" if int_lines[i]==1 else "#00f5ff"
            yao_txt += (f"\n[color=#b44fff][{yao_names[i]}] "
                        f"[color={col}]{sym_line}[/color][/color]\n"
                        f"[color=#ffe600]{yc}[/color]\n"
                        f"[color=#445566]→ {yb}[/color]\n")

        q_txt = (f"[color=#ff2d9b]>> 所问：{question}[/color]\n\n"
                 if question else "")

        self._detail_lbl.text = (
            q_txt +
            f"[color=#00f5ff]◆ 卦义[/color]\n"
            f"[color=#c8d8e8]{desc}[/color]\n\n"
            f"[color=#00f5ff]◆ 白话解析[/color]\n"
            f"[color=#39ff14]{baihua}[/color]\n\n"
            f"[color=#b44fff]━━━ 爻辞逐爻解读 ━━━[/color]"
            + yao_txt +
            "\n[color=#445566]>> 易以道阴阳，仅供参考。[/color]"
        )


# ══════════════════════════════════════════════
#  App 入口
# ══════════════════════════════════════════════
class IChing(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(ResultScreen(name="result"))
        return sm


if __name__ == "__main__":
    IChing().run()
