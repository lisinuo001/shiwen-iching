# -*- coding: utf-8 -*-
"""
筮问 · SHI WEN  ——  赛博朋克易经占卜系统  v2.1
"""
import tkinter as tk
from tkinter import ttk
import random, math
from iching_data import get_hexagram, TRIGRAMS, HEXAGRAMS
from yaoci_data import get_yaoci

APP_NAME    = "筮问 · SHI WEN"
APP_VER     = "v2.1"
WIN_TITLE   = f"[ 筮·问 ]  CYBER I-CHING  {APP_VER}"
WATERMARK   = "WADJY"

# ══════════════════════════════════════════════
#  赛博朋克配色
# ══════════════════════════════════════════════
BG_VOID    = "#0a0a0f"
BG_PANEL   = "#0d1117"
BG_CARD    = "#111520"
BG_INSET   = "#0c1020"
NEON_CYAN  = "#00f5ff"
NEON_PINK  = "#ff2d9b"
NEON_GREEN = "#39ff14"
NEON_PURP  = "#b44fff"
NEON_YELL  = "#ffe600"
NEON_ORG   = "#ff6b00"
DIM_CYAN   = "#004d55"
DIM_PINK   = "#55003a"
GRID_LINE  = "#1a2030"
NEON_CYAN_DIM = "#003d44"
NEON_PURP_DIM = "#2a1040"
TEXT_MAIN  = "#c8d8e8"
TEXT_DIM   = "#445566"
TEXT_GLOW  = "#e0f8ff"

FONT_TITLE  = ("Consolas", 18, "bold")
FONT_KUA    = ("Consolas", 15, "bold")
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Consolas", 12, "bold")
FONT_HUGE   = ("Consolas", 36, "bold")

TRIGRAM_SYMBOLS = {
    (1,1,1): "☰", (0,0,0): "☷", (1,0,0): "☳",
    (0,0,1): "☶", (0,1,1): "☴", (1,1,0): "☱",
    (1,0,1): "☵", (0,1,0): "☲",
}


# ══════════════════════════════════════════════
#  双行按钮辅助：中文大字 + 英文小字装饰
# ══════════════════════════════════════════════
def make_btn(parent, zh_text, en_text, bg, fg, cmd,
             active_bg=None, border_color=None,
             fill_x=False, pady=4):
    """创建中文主标题+英文副标题的赛博风格按钮Frame"""
    active_bg = active_bg or bg
    f = tk.Frame(parent, bg=border_color or bg,
                 padx=1 if border_color else 0,
                 pady=1 if border_color else 0,
                 cursor="hand2")

    inner = tk.Frame(f, bg=bg, cursor="hand2")
    inner.pack(fill="both", expand=True)

    lbl_zh = tk.Label(inner, text=zh_text,
                      font=("Microsoft YaHei", 11, "bold"),
                      bg=bg, fg=fg, cursor="hand2")
    lbl_zh.pack(pady=(5, 0))
    lbl_en = tk.Label(inner, text=en_text,
                      font=("Consolas", 7),
                      bg=bg, fg=fg, cursor="hand2",
                      pady=0)
    lbl_en.pack(pady=(0, 5))

    # 点击绑定到所有子组件
    def _on_click(e=None): cmd()
    def _on_enter(e=None):
        inner.config(bg=active_bg)
        lbl_zh.config(bg=active_bg)
        lbl_en.config(bg=active_bg)
    def _on_leave(e=None):
        inner.config(bg=bg)
        lbl_zh.config(bg=bg)
        lbl_en.config(bg=bg)

    for w in (f, inner, lbl_zh, lbl_en):
        w.bind("<Button-1>", _on_click)
        w.bind("<Enter>",    _on_enter)
        w.bind("<Leave>",    _on_leave)

    # 动态接口：set_text / set_state
    def set_text(zh=None, en=None):
        if zh: lbl_zh.config(text=zh)
        if en: lbl_en.config(text=en)
    def set_state(state):
        disabled = (state == "disabled")
        dim = TEXT_DIM if disabled else fg
        inner.config(bg=bg)
        lbl_zh.config(fg=dim)
        lbl_en.config(fg=dim)
        for w in (f, inner, lbl_zh, lbl_en):
            if disabled:
                w.unbind("<Button-1>")
                w.unbind("<Enter>")
                w.unbind("<Leave>")
                w.config(cursor="arrow")
            else:
                w.bind("<Button-1>", _on_click)
                w.bind("<Enter>",    _on_enter)
                w.bind("<Leave>",    _on_leave)
                w.config(cursor="hand2")
    f.set_text  = set_text
    f.set_state = set_state

    return f


# ══════════════════════════════════════════════
#  单枚铜钱 Widget
# ══════════════════════════════════════════════
class CoinWidget(tk.Canvas):
    def __init__(self, parent, index, **kw):
        super().__init__(parent, bg=BG_PANEL,
                         highlightthickness=1,
                         highlightbackground=DIM_CYAN, **kw)
        self.config(width=68, height=68)
        self.index = index
        self._face = None
        self._spinning = False
        self._tick = 0
        self._draw_idle()

    def _draw_idle(self):
        self.delete("all")
        cx, cy, r = 34, 34, 26
        self.create_oval(cx-r, cy-r, cx+r, cy+r,
                         outline=TEXT_DIM, width=1, fill=BG_PANEL)
        self.create_text(cx, cy, text=f"#{self.index+1}",
                         fill=TEXT_DIM, font=FONT_SMALL)

    def spin(self, result_yang: bool, callback=None):
        self._face = result_yang
        self._spinning = True
        self._tick = 0
        self._max = 16 + random.randint(0, 6)
        self._callback = callback
        self._do_spin()

    def _do_spin(self):
        if not self._spinning:
            return
        self.delete("all")
        cx, cy, r = 34, 34, 26
        phase = self._tick / self._max
        ry = max(1, int(r * abs(math.cos(phase * math.pi * 3))))
        shade = "#ffcc00" if (self._tick % 2 == 0) else "#cc9900"
        self.create_oval(cx-r, cy-ry, cx+r, cy+ry,
                         outline=NEON_YELL, width=2, fill=shade)
        self._tick += 1
        if self._tick < self._max:
            self.after(45, self._do_spin)
        else:
            self._spinning = False
            self._draw_result()
            if self._callback:
                self._callback()

    def _draw_result(self):
        self.delete("all")
        cx, cy, r = 34, 34, 26
        if self._face:
            color, border, symbol, glow = "#1a1000", NEON_YELL, "阳", NEON_YELL
        else:
            color, border, symbol, glow = "#0a0a1a", NEON_CYAN, "阴", NEON_CYAN
        self.create_oval(cx-r, cy-r, cx+r, cy+r,
                         outline=border, width=2, fill=color)
        ring = DIM_CYAN if border == NEON_CYAN else "#554400"
        self.create_oval(cx-r-3, cy-r-3, cx+r+3, cy+r+3,
                         outline=ring, width=1, fill="")
        self.create_text(cx, cy-6, text=symbol,
                         fill=glow, font=("Consolas", 12, "bold"))
        self.create_text(cx, cy+9, text="正" if self._face else "反",
                         fill=TEXT_DIM, font=FONT_SMALL)

    def reset(self):
        self._face = None
        self._spinning = False
        self._draw_idle()


# ══════════════════════════════════════════════
#  单爻显示控件（纯 Label，兼容 Python 3.14）
# ══════════════════════════════════════════════
class YaoWidget(tk.Frame):
    """单爻行：爻名 + Canvas绘制爻线 + 阴阳标注，固定高度，居中对称"""
    YAO_NAMES = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    ROW_H   = 22   # 行高
    LINE_H  = 3    # 线条粗细
    GAP     = 14   # 阴爻中间空隙宽度（px）
    NAME_W  = 36   # 爻名列宽
    TYPE_W  = 28   # 阴阳标注列宽

    def __init__(self, parent):
        super().__init__(parent, bg=BG_PANEL)
        # 爻名标签
        self._name_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                  bg=BG_PANEL, fg=TEXT_DIM,
                                  width=4, anchor="e")
        self._name_lbl.pack(side="left", padx=(6, 4))
        # Canvas：固定最大宽度，避免首次渲染宽度为0
        self._cv = tk.Canvas(self, bg=BG_PANEL, highlightthickness=0,
                             height=self.ROW_H, width=560)
        self._cv.pack(side="left", fill="x", expand=True)
        # 阴阳标注
        self._type_lbl = tk.Label(self, text="", font=FONT_SMALL,
                                  bg=BG_PANEL, fg=TEXT_DIM,
                                  width=2, anchor="center")
        self._type_lbl.pack(side="right", padx=(4, 8))
        # 绑定 resize 事件，宽度变化时重绘
        self._cv.bind("<Configure>", self._on_resize)
        self._state = None   # None / "empty" / True(阳) / False(阴)
        self._idx   = 0

    def _on_resize(self, event=None):
        if self._state is not None:
            self._redraw()

    def _redraw(self):
        self._cv.delete("all")
        w = self._cv.winfo_width()
        if w < 10:
            return
        cy = self.ROW_H // 2   # 垂直居中

        if self._state == "empty":
            # 虚线待定
            x = 0
            dash_len, dash_gap = 6, 4
            while x < w:
                x2 = min(x + dash_len, w)
                self._cv.create_line(x, cy, x2, cy,
                                     fill=TEXT_DIM, width=1)
                x += dash_len + dash_gap
        elif self._state is True:
            # 阳爻：整段实线
            self._cv.create_line(4, cy, w - 4, cy,
                                 fill=NEON_YELL, width=self.LINE_H,
                                 capstyle="round")
        else:
            # 阴爻：左段 + 空隙(居中) + 右段，严格对称
            half_gap = self.GAP // 2
            cx = w // 2
            # 左段：从 4 到 cx-half_gap
            self._cv.create_line(4, cy, cx - half_gap, cy,
                                 fill=NEON_CYAN, width=self.LINE_H,
                                 capstyle="round")
            # 右段：从 cx+half_gap 到 w-4
            self._cv.create_line(cx + half_gap, cy, w - 4, cy,
                                 fill=NEON_CYAN, width=self.LINE_H,
                                 capstyle="round")

    def draw_empty(self, idx):
        self._idx   = idx
        self._state = "empty"
        self._name_lbl.config(text=self.YAO_NAMES[idx], fg=TEXT_DIM)
        self._type_lbl.config(text="?",  fg=TEXT_DIM)
        self._redraw()

    def draw_yao(self, is_yang: bool, idx: int):
        self._idx   = idx
        self._state = is_yang
        color = NEON_YELL if is_yang else NEON_CYAN
        self._name_lbl.config(text=self.YAO_NAMES[idx], fg=TEXT_DIM)
        self._type_lbl.config(text="阳" if is_yang else "阴", fg=color)
        self._redraw()


# ══════════════════════════════════════════════
#  主应用
# ══════════════════════════════════════════════
class ShiWenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WIN_TITLE)
        self.geometry("1080x780")
        self.minsize(960, 700)
        self.configure(bg=BG_VOID)
        self.resizable(True, True)

        # 设置图标
        try:
            import os, sys
            base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.dirname(os.path.abspath(__file__))
            ico = os.path.join(base, "iching_icon.ico")
            if os.path.exists(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

        self._lines       = []
        self._throw_count = 0
        self._casting     = False

        self._build_ui()

    # ──────────── 界面构建 ────────────
    def _build_ui(self):
        self._build_header()

        # ══ 主体：左列（铜钱区）+ 右列（六爻+卦象+解读）
        body = tk.Frame(self, bg=BG_VOID)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # ── 左列：铜钱投掷区，固定宽度，不随内容变化
        left_col = tk.Frame(body, bg=BG_PANEL, width=360,
                            highlightthickness=1,
                            highlightbackground=DIM_CYAN)
        left_col.pack(side="left", fill="y", padx=(0, 6))
        left_col.pack_propagate(False)
        self._build_ctrl_panel(left_col)

        # ── 右列：上下分割
        right_col = tk.Frame(body, bg=BG_VOID)
        right_col.pack(side="left", fill="both", expand=True)

        # 右上：六爻状态 + 卦象，固定高度
        right_top = tk.Frame(right_col, bg=BG_PANEL, height=230,
                             highlightthickness=1,
                             highlightbackground=DIM_CYAN)
        right_top.pack(fill="x", pady=(0, 6))
        right_top.pack_propagate(False)
        self._build_yao_kua_panel(right_top)

        # 右下：解读文本，撑满剩余高度
        right_bot = tk.Frame(right_col, bg=BG_CARD,
                             highlightthickness=1,
                             highlightbackground=NEON_PURP_DIM)
        right_bot.pack(fill="both", expand=True)
        self._build_result_area(right_bot)

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_VOID)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=NEON_CYAN, height=3).pack(fill="x")
        inner = tk.Frame(hdr, bg=BG_VOID)
        inner.pack(fill="x", padx=20, pady=(8, 4))
        tk.Label(inner, text=f"▓▓  筮 · 问  //  CYBER I-CHING  ▓▓",
                 font=FONT_TITLE, bg=BG_VOID, fg=NEON_CYAN).pack(side="left")
        # 水印（右侧）
        tk.Label(inner, text=WATERMARK,
                 font=("Consolas", 9, "bold"), bg=BG_VOID, fg="#5a7a9a").pack(side="right", padx=(0, 4))
        tk.Label(inner, text=f"三枚铜钱法 / 六十四卦  {APP_VER}",
                 font=FONT_SMALL, bg=BG_VOID, fg=TEXT_DIM).pack(side="right", pady=4, padx=10)
        tk.Frame(hdr, bg=NEON_PINK, height=1).pack(fill="x")
        tk.Frame(hdr, bg=BG_VOID, height=4).pack(fill="x")

    def _build_ctrl_panel(self, parent):
        """左列：铜钱投掷控制区"""
        inner = tk.Frame(parent, bg=BG_PANEL)
        inner.pack(fill="both", expand=True, padx=12, pady=10)

        # 投掷轮次
        self._throw_lbl = tk.Label(inner, text="[ ROUND 0/2 ]  准备起卦",
                                   font=FONT_MONO, bg=BG_PANEL, fg=NEON_PINK)
        self._throw_lbl.pack(anchor="w")

        tk.Frame(inner, bg=DIM_CYAN, height=1).pack(fill="x", pady=(4, 6))

        # 铜钱行：标签在上，三枚铜钱横排在下
        tk.Label(inner, text="// 三枚铜钱 //",
                 font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM).pack(anchor="w", pady=(0, 4))
        coin_row = tk.Frame(inner, bg=BG_PANEL)
        coin_row.pack(anchor="center", pady=(0, 4))
        self._coins = []
        for i in range(3):
            cw = CoinWidget(coin_row, i)
            cw.pack(side="left", padx=6)
            self._coins.append(cw)

        # 爻位说明
        self._coin_info = tk.Label(inner,
            text="第1次→下卦（初/二/三爻）\n第2次→上卦（四/五/上爻）",
            font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM, justify="left")
        self._coin_info.pack(anchor="w", pady=(2, 8))

        # 主投掷按钮
        self._cast_btn = make_btn(
            inner, "投 掷 铜 钱", "CAST  ▶",
            bg=NEON_PINK, fg=BG_VOID,
            active_bg="#ff6bc4", cmd=self._cast_throw)
        self._cast_btn.pack(fill="x", pady=(0, 6))

        # 重置 / 自动 按钮行
        btn_row2 = tk.Frame(inner, bg=BG_PANEL)
        btn_row2.pack(fill="x")
        self._reset_btn = make_btn(
            btn_row2, "重  置", "RESET",
            bg=BG_INSET, fg=NEON_CYAN,
            active_bg=DIM_CYAN, border_color=DIM_CYAN,
            cmd=self._reset)
        self._reset_btn.pack(side="left", padx=(0, 4), fill="x", expand=True)
        make_btn(
            btn_row2, "一键起卦", "AUTO  ⚡",
            bg=BG_INSET, fg=NEON_PURP,
            active_bg=DIM_PINK, border_color=NEON_PURP_DIM,
            cmd=self._auto_cast).pack(side="left", fill="x", expand=True)

        tk.Frame(inner, bg=DIM_CYAN, height=1).pack(fill="x", pady=(8, 4))

        # 状态栏
        self._status_var = tk.StringVar(value="READY  //  点击 CAST 开始起卦")
        tk.Label(inner, textvariable=self._status_var,
                 font=FONT_SMALL, bg=BG_PANEL, fg=NEON_GREEN,
                 wraplength=240, justify="left").pack(anchor="w")

    def _build_yao_kua_panel(self, parent):
        """右上：六爻状态（中间自适应）+ 卦象预览（右侧固定）
        pack顺序：先right固定列，再left自适应，确保两端不被压缩"""

        # ① 先 pack 右侧卦象列（固定宽度，side=right 优先占位）
        kua_panel = tk.Frame(parent, bg=BG_PANEL, width=150)
        kua_panel.pack(side="right", fill="y", padx=(0, 10), pady=8)
        kua_panel.pack_propagate(False)

        tk.Label(kua_panel, text="// 卦 象 //",
                 font=FONT_SMALL, bg=BG_PANEL, fg=NEON_PURP).pack()
        tk.Frame(kua_panel, bg=NEON_CYAN_DIM, height=1).pack(fill="x", pady=(2, 4))

        self._kua_num_lbl = tk.Label(kua_panel, text="",
                                     font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM)
        self._kua_num_lbl.pack()
        self._kua_name_lbl = tk.Label(kua_panel, text="—",
                                      font=FONT_KUA, bg=BG_PANEL, fg=NEON_CYAN)
        self._kua_name_lbl.pack(pady=(2, 0))
        self._kua_sym_lbl = tk.Label(kua_panel, text="",
                                     font=("Consolas", 40), bg=BG_PANEL, fg=NEON_CYAN)
        self._kua_sym_lbl.pack()
        self._kua_pos_lbl = tk.Label(kua_panel, text="",
                                     font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM,
                                     wraplength=150, justify="center")
        self._kua_pos_lbl.pack(pady=(0, 4))

        # ② 分隔线（side=right，紧贴卦象列左侧）
        tk.Frame(parent, bg=DIM_CYAN, width=1).pack(side="right", fill="y", pady=8)

        # ③ 最后 pack 六爻区（side=left，fill+expand 吃剩余空间）
        yao_area = tk.Frame(parent, bg=BG_PANEL)
        yao_area.pack(side="left", fill="both", expand=True, padx=(10, 4), pady=8)

        tk.Label(yao_area, text="// 六 爻 状 态  ( 下→上 ) //",
                 font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM).pack(anchor="w")
        tk.Frame(yao_area, bg=DIM_CYAN, height=1).pack(fill="x", pady=(2, 4))

        self._yao_widgets = []
        for i in range(6):
            yw = YaoWidget(yao_area)
            yw.pack(fill="x", pady=2)
            yw.draw_empty(i)
            self._yao_widgets.append(yw)

    def _build_result_area(self, parent):
        """右下解读区：整块滚动文本"""
        # 标题行
        tk.Label(parent, text="//  卦 象 解 读  HEXAGRAM ANALYSIS  //",
                 font=FONT_BODY, bg=BG_CARD, fg=NEON_PURP).pack(
                 anchor="w", padx=12, pady=(6, 2))

        # 用 grid 布局的容器，确保 Text + Scrollbar 严格对齐
        txt_frame = tk.Frame(parent, bg=BG_INSET)
        txt_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        txt_frame.grid_rowconfigure(0, weight=1)
        txt_frame.grid_columnconfigure(0, weight=1)
        txt_frame.grid_columnconfigure(1, weight=0)

        self._text = tk.Text(txt_frame,
                             font=FONT_BODY, bg=BG_INSET, fg=TEXT_MAIN,
                             relief="flat", bd=0, wrap="word",
                             padx=12, pady=10,
                             state="disabled", cursor="arrow",
                             spacing1=3, spacing2=2, spacing3=3,
                             selectbackground=DIM_CYAN,
                             insertbackground=NEON_CYAN)
        self._text.grid(row=0, column=0, sticky="nsew")

        sb = tk.Scrollbar(txt_frame, orient="vertical",
                          bg=BG_INSET, troughcolor=BG_VOID,
                          activebackground=NEON_CYAN,
                          relief="flat", width=10, bd=0,
                          command=self._text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._text.config(yscrollcommand=sb.set)

        for tag, fg, fnt in [
            ("title",  NEON_CYAN,  ("Consolas", 11, "bold")),
            ("gushi",  NEON_YELL,  ("Consolas", 11)),
            ("body",   TEXT_MAIN,  FONT_BODY),
            ("dim",    TEXT_DIM,   FONT_SMALL),
            ("pink",   NEON_PINK,  ("Consolas", 10, "bold")),
            ("green",  NEON_GREEN, FONT_BODY),
            ("purp",   NEON_PURP,  ("Consolas", 10, "bold")),
            ("yao",    NEON_YELL,  ("Consolas", 10)),
            ("yaobai", TEXT_DIM,   FONT_SMALL),
            ("div",    DIM_CYAN,   ("Consolas", 8)),
        ]:
            self._text.tag_config(tag, foreground=fg, font=fnt)

        self._show_welcome()

        # 右下角水印
        wm = tk.Label(parent, text=WATERMARK,
                      font=("Consolas", 7, "bold"), bg=BG_CARD, fg="#4a6a8a")
        wm.pack(side="right", anchor="se", padx=6, pady=4)

    # ──────────── 文字 ────────────
    def _write_text(self, segments):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        for tag, content in segments:
            self._text.insert("end", content, tag)
        self._text.config(state="disabled")
        self._text.yview_moveto(0)

    def _show_welcome(self):
        self._write_text([
            ("title", "╔══════════════════════════════╗\n"),
            ("title", "║  筮问 · SHI WEN  CYBER v2.1  ║\n"),
            ("title", "╚══════════════════════════════╝\n\n"),
            ("body",  "《周易》六十四卦  //  赛博朋克占卜系统\n\n"),
            ("purp",  "◆ 起卦方式：三枚铜钱法\n"),
            ("body",
             "  • 正面(字) = 阳  ━━━━━━━━━━━\n"
             "  • 反面(花) = 阴  ━━━━━   ━━━━━\n\n"
             "  第1次投掷 → 下卦（初/二/三爻）\n"
             "  第2次投掷 → 上卦（四/五/上爻）\n\n"),
            ("purp",  "◆ 操作步骤：\n"),
            ("body",
             "  ① 点击 [CAST] 投掷第1次\n"
             "  ② 铜钱停止后再投第2次\n"
             "  ③ 自动生成卦象及完整解读\n\n"),
            ("dim",   ">> 或点击 [AUTO] 一键自动起卦\n\n"),
            ("div",   "─" * 44 + "\n"),
            ("dim",   "  天行健，君子以自强不息\n"
                      "  地势坤，君子以厚德载物\n"),
        ])

    # ──────────── 起卦逻辑 ────────────
    def _cast_throw(self):
        if self._casting or self._throw_count >= 2:
            return
        self._casting = True
        self._cast_btn.set_state("disabled")
        self._cast_btn.set_text(zh="投 掷 中…", en="CASTING...")
        results = [random.choice([True, False]) for _ in range(3)]
        for c in self._coins:
            c.reset()
        done_count = [0]
        def on_coin_done():
            done_count[0] += 1
            if done_count[0] == 3:
                self._on_throw_done(results)
        for i, coin in enumerate(self._coins):
            self.after(i * 120, lambda c=coin, r=results[i]: c.spin(r, on_coin_done))

    def _on_throw_done(self, results):
        yao_offset = self._throw_count * 3
        for i, is_yang in enumerate(results):
            yao_idx = yao_offset + i
            self._lines.append(is_yang)
            self._yao_widgets[yao_idx].draw_yao(is_yang, yao_idx)
        self._throw_count += 1
        self._casting = False
        if self._throw_count == 1:
            self._throw_lbl.config(text="[ ROUND 1/2 ]  下卦完成！")
            self._coin_info.config(text="下卦已生成 ✓  请点击 CAST 投掷第2次 → 上卦",
                                   fg=NEON_GREEN)
            self._cast_btn.set_state("normal")
            self._cast_btn.set_text(zh="投掷第二次", en="CAST ROUND 2  ▶")
            self._status_var.set("下卦(初/二/三爻)已生成 → 请投掷上卦")
        else:
            self._throw_lbl.config(text="[ ROUND 2/2 ]  卦成！")
            self._cast_btn.set_state("disabled")
            self._cast_btn.set_text(zh="卦 已 成", en="COMPLETE ✓")
            self._coin_info.config(text="六爻已全部生成！查看下方解读 ↓", fg=NEON_PINK)
            self._status_var.set("六爻完毕 // 正在解析卦象...")
            self.after(400, self._show_hexagram)

    def _auto_cast(self):
        if self._casting:
            return
        self._reset_silent()
        self._casting = True
        self._cast_btn.set_state("disabled")
        def do_second():
            r2 = [random.choice([True, False]) for _ in range(3)]
            for c in self._coins:
                c.reset()
            done = [0]
            def done2():
                done[0] += 1
                if done[0] == 3:
                    self._on_throw_done(r2)
            for i, coin in enumerate(self._coins):
                self.after(i * 100, lambda c=coin, r=r2[i]: c.spin(r, done2))
        r1 = [random.choice([True, False]) for _ in range(3)]
        done1 = [0]
        def done_first():
            done1[0] += 1
            if done1[0] == 3:
                self._on_throw_done(r1)
                self.after(600, do_second)
        for i, coin in enumerate(self._coins):
            self.after(i * 100, lambda c=coin, r=r1[i]: c.spin(r, done_first))

    def _reset_silent(self):
        self._lines = []
        self._throw_count = 0
        self._casting = False
        for c in self._coins:
            c.reset()
        for i, yw in enumerate(self._yao_widgets):
            yw.draw_empty(i)
        self._throw_lbl.config(text="[ ROUND 0/2 ]  准备起卦", fg=NEON_PINK)
        self._coin_info.config(
            text="第1次 → 下卦（初/二/三爻）  第2次 → 上卦（四/五/上爻）",
            fg=TEXT_DIM)
        self._kua_num_lbl.config(text="")
        self._kua_name_lbl.config(text="—")
        self._kua_sym_lbl.config(text="")
        self._kua_pos_lbl.config(text="")
        self._show_welcome()

    def _reset(self):
        self._reset_silent()
        self._cast_btn.set_state("normal")
        self._cast_btn.set_text(zh="投 掷 铜 钱", en="CAST  ▶")
        self._status_var.set("RESET  //  等待起卦")

    # ──────────── 卦象解读 ────────────
    def _show_hexagram(self):
        if len(self._lines) < 6:
            return
        int_lines = tuple(1 if v else 0 for v in self._lines)
        main_data = HEXAGRAMS.get(int_lines)
        if main_data is None:
            self._status_var.set("ERROR: 卦象查找失败")
            return
        seq, name, position, gushi, desc, baihua = main_data
        lower = int_lines[:3]
        upper = int_lines[3:]
        lower_t = TRIGRAMS.get(lower, ("?", "?", "?"))
        upper_t = TRIGRAMS.get(upper, ("?", "?", "?"))
        lower_sym = TRIGRAM_SYMBOLS.get(lower, "?")
        upper_sym = TRIGRAM_SYMBOLS.get(upper, "?")
        hex_symbol = upper_sym + lower_sym

        self._kua_num_lbl.config(text=f"第 {seq:02d} 卦")
        self._kua_name_lbl.config(text=f"{name}  卦")
        self._kua_sym_lbl.config(text=hex_symbol)
        self._kua_pos_lbl.config(text=f"{upper_t[2]}上{lower_t[2]}下\n{position}")

        yao_segs = []
        yao_names = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
        for i in range(6):
            yc_txt, yc_bai = get_yaoci(int_lines, i)
            is_yang = int_lines[i] == 1
            sym = "━━━━━" if is_yang else "━━ ━━"
            yao_segs += [
                ("purp",   f"\n  [{yao_names[i]}] {sym}\n"),
                ("yao",    f"  {yc_txt}\n"),
                ("yaobai", f"  → {yc_bai}\n"),
            ]

        segs = [
            ("title", f"┌─ 第 {seq:02d} 卦  [{name}卦] ──────────────────┐\n"),
            ("dim",   f"│  {position}\n"),
            ("dim",   f"│  {upper_t[2]}上{lower_t[2]}下\n"),
            ("title", "└─────────────────────────────────────────┘\n\n"),
            ("purp",  "◆ 卦辞\n"),
            ("gushi", f"  {gushi}\n\n"),
            ("purp",  "◆ 卦义\n"),
            ("body",  f"  {desc}\n\n"),
            ("purp",  "◆ 白话解析\n"),
            ("green", f"  {baihua}\n\n"),
            ("div",   "─" * 44 + "\n"),
            ("purp",  "◆ 爻辞逐爻解读\n"),
        ] + yao_segs + [
            ("div",   "\n" + "─" * 44 + "\n"),
            ("dim",   ">> 易以道阴阳，占以知吉凶。\n"),
            ("dim",   ">> 仅供参考，请以理性态度对待。\n"),
        ]
        self._write_text(segs)
        self._status_var.set(f"解读完毕 // 第{seq}卦  {name}卦")


def main():
    app = ShiWenApp()
    app.mainloop()


if __name__ == "__main__":
    main()