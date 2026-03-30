# -*- coding: utf-8 -*-
"""
用 Python 生成 筮问·SHI WEN Windows 安装程序（自解压 + 注册表 + 快捷方式）
运行方式: python3 make_installer.py
生成文件: installer\筮问-ShiWen_Setup_v2.2.0.exe  （赛博朋克风格安装向导）
"""
import os, sys, zipfile, shutil, subprocess

SRC_EXE  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "\u7b6e\u95ee-ShiWen.exe")
OUT_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "installer")
APP_NAME = "\u7b6e\u95ee-ShiWen"
APP_VER  = "2.2.0"

# ══════════════════════════════════════════════════════════════════
#  安装向导脚本（赛博朋克风格，内嵌于安装包 exe 中）
# ══════════════════════════════════════════════════════════════════
WIZARD_SCRIPT = r'''# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os, sys, zipfile, winreg, tempfile, subprocess, threading, math, time

APP_NAME    = "\u7b6e\u95ee-ShiWen"
APP_VER     = "2.2.0"
DEFAULT_DIR = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), APP_NAME)

# ── 赛博朋克配色（与主程序一致）
BG_VOID   = "#0a0a0f"
BG_PANEL  = "#0d1117"
BG_CARD   = "#111520"
BG_INSET  = "#0c1020"
NEON_CYAN = "#00f5ff"
NEON_PINK = "#ff2d9b"
NEON_GREEN= "#39ff14"
NEON_PURP = "#b44fff"
NEON_YELL = "#ffe600"
DIM_CYAN  = "#004d55"
DIM_PINK  = "#55003a"
TEXT_MAIN = "#c8d8e8"
TEXT_DIM  = "#445566"
NEON_CYAN_DIM = "#003d44"
NEON_PURP_DIM = "#2a1040"

FONT_TITLE = ("Consolas", 18, "bold")
FONT_BODY  = ("Consolas", 10)
FONT_SMALL = ("Consolas", 9)
FONT_MONO  = ("Consolas", 11, "bold")


class CyberInstaller(tk.Tk):
    def __init__(self, payload_zip):
        super().__init__()
        self.payload_zip  = payload_zip
        self.install_dir  = tk.StringVar(value=DEFAULT_DIR)
        self.create_desk  = tk.BooleanVar(value=True)
        self.create_start = tk.BooleanVar(value=True)
        self._scan_offset = 0
        self._installing  = False

        self.title("[ \u6613\u00b7\u7ecf\u00b7\u7b97\u00b7\u5366 ]  CYBER INSTALLER  v" + APP_VER)
        self.geometry("600x500")
        self.resizable(False, False)
        self.configure(bg=BG_VOID)
        self.overrideredirect(False)

        self._build_ui()
        self._animate_scan()

    # ─────────────── 构建界面 ───────────────
    def _build_ui(self):
        # 顶部霓虹标题栏
        tk.Frame(self, bg=NEON_CYAN, height=2).pack(fill="x")
        hdr = tk.Frame(self, bg=BG_VOID)
        hdr.pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(hdr, text="\u25d3\u25d3  \u6613 \u00b7 \u7ecf \u00b7 \u7b97 \u00b7 \u5366  //  CYBER INSTALLER  \u25d3\u25d3",
                 font=FONT_TITLE, bg=BG_VOID, fg=NEON_CYAN).pack(side="left")
        tk.Label(hdr, text="v" + APP_VER,
                 font=FONT_SMALL, bg=BG_VOID, fg=TEXT_DIM).pack(side="right", pady=6)
        tk.Frame(self, bg=NEON_PINK, height=1).pack(fill="x")
        tk.Frame(self, bg=BG_VOID, height=6).pack(fill="x")

        # 扫描线 Canvas（装饰）
        self._scan_cv = tk.Canvas(self, bg=BG_VOID, highlightthickness=0)
        self._scan_cv.config(height=2)
        self._scan_cv.pack(fill="x")

        # 主体 Frame
        body = tk.Frame(self, bg=BG_PANEL,
                        highlightthickness=1, highlightbackground=DIM_CYAN)
        body.pack(fill="both", expand=True, padx=16, pady=(6, 10))

        # ── ASCII 艺术 banner
        banner = tk.Label(body,
            text=(
                "  \u250f\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2513\n"
                "  \u2503  I-CHING CYBER DIVINATION  //  \u516d\u5341\u56db\u5366\u5360\u535c\u7cfb\u7edf  \u2503\n"
                "  \u2517\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u251b"
            ),
            font=("Consolas", 9), bg=BG_PANEL, fg=NEON_PURP,
            justify="left")
        banner.pack(anchor="w", padx=14, pady=(10, 2))

        tk.Frame(body, bg=NEON_CYAN_DIM, height=1).pack(fill="x", padx=14)

        # ── 安装路径
        tk.Label(body, text="> \u5b89\u88c5\u76ee\u5f55  [ INSTALL PATH ]",
                 font=FONT_BODY, bg=BG_PANEL, fg=NEON_GREEN).pack(
            anchor="w", padx=16, pady=(10, 2))

        path_row = tk.Frame(body, bg=BG_PANEL)
        path_row.pack(fill="x", padx=16, pady=(0, 8))
        path_entry = tk.Entry(path_row, textvariable=self.install_dir,
                              font=FONT_BODY, bg=BG_INSET, fg=NEON_GREEN,
                              insertbackground=NEON_GREEN, relief="flat",
                              bd=0, highlightthickness=1,
                              highlightbackground=DIM_CYAN,
                              highlightcolor=NEON_CYAN)
        path_entry.pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(path_row, text=" \u6d4f\u89c8 ",
                  font=FONT_SMALL, bg=BG_INSET, fg=NEON_CYAN,
                  activebackground=DIM_CYAN, activeforeground=NEON_CYAN,
                  relief="flat", bd=0, padx=8, cursor="hand2",
                  command=self._browse).pack(side="left", padx=(6, 0), ipady=5)

        tk.Frame(body, bg=NEON_CYAN_DIM, height=1).pack(fill="x", padx=14)

        # ── 安装选项
        tk.Label(body, text="> \u5b89\u88c5\u9009\u9879  [ OPTIONS ]",
                 font=FONT_BODY, bg=BG_PANEL, fg=NEON_GREEN).pack(
            anchor="w", padx=16, pady=(8, 2))

        for var, label in [
            (self.create_desk,  "  \u2714  \u521b\u5efa\u684c\u9762\u5feb\u6377\u65b9\u5f0f  [ DESKTOP SHORTCUT ]"),
            (self.create_start, "  \u2714  \u521b\u5efa\u5f00\u59cb\u83dc\u5355\u9879  [ START MENU ENTRY ]"),
        ]:
            cb = tk.Checkbutton(body, text=label, variable=var,
                                font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_MAIN,
                                selectcolor=BG_PANEL,
                                activebackground=BG_PANEL,
                                activeforeground=NEON_CYAN,
                                cursor="hand2")
            cb.pack(anchor="w", padx=16, pady=1)

        tk.Frame(body, bg=NEON_CYAN_DIM, height=1).pack(fill="x", padx=14, pady=(6, 0))

        # ── 进度区
        prog_frame = tk.Frame(body, bg=BG_PANEL)
        prog_frame.pack(fill="x", padx=16, pady=(8, 4))

        self._prog_lbl = tk.Label(prog_frame,
            text="[ READY ]  \u7b49\u5f85\u5b89\u88c5...",
            font=FONT_SMALL, bg=BG_PANEL, fg=NEON_PINK)
        self._prog_lbl.pack(anchor="w")

        # 自定义霓虹进度条（Canvas）
        self._bar_cv = tk.Canvas(body, bg=BG_INSET, highlightthickness=1,
                                 highlightbackground=DIM_CYAN)
        self._bar_cv.config(height=18)
        self._bar_cv.pack(fill="x", padx=16, pady=(2, 8))
        self._bar_pct = 0
        self._draw_bar(0)

        # ── 按钮区
        tk.Frame(body, bg=NEON_PURP_DIM, height=1).pack(fill="x", padx=14)
        btn_row = tk.Frame(body, bg=BG_PANEL)
        btn_row.pack(pady=12)

        self._install_btn = tk.Button(
            btn_row,
            text="\u25b6  INSTALL  \u5f00\u59cb\u5b89\u88c5",
            font=("Consolas", 11, "bold"),
            bg=NEON_PINK, fg=BG_VOID,
            activebackground="#ff6bc4", activeforeground=BG_VOID,
            relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
            command=self._start_install
        )
        self._install_btn.pack(side="left", padx=8)

        tk.Button(btn_row, text="CANCEL",
                  font=FONT_BODY, bg=BG_INSET, fg=TEXT_DIM,
                  activebackground=DIM_CYAN, activeforeground=NEON_CYAN,
                  relief="flat", bd=0, padx=12, pady=8,
                  cursor="hand2", command=self.destroy
        ).pack(side="left", padx=4)

        # 底部版权
        tk.Frame(self, bg=NEON_CYAN, height=1).pack(fill="x", side="bottom")
        tk.Label(self, text="CYBER DIVINATION SYSTEM  //  I-CHING v2.0  //  \u5929\u884c\u5065\uff0c\u541b\u5b50\u4ee5\u81ea\u5f3a\u4e0d\u606f",
                 font=("Consolas", 8), bg=BG_VOID, fg=TEXT_DIM).pack(
            side="bottom", pady=(2, 3))

    # ─────────────── 扫描线动画 ───────────────
    def _animate_scan(self):
        try:
            w = self.winfo_width() or 600
            self._scan_cv.delete("all")
            x = (self._scan_offset * 8) % (w + 40)
            self._scan_cv.create_rectangle(x-20, 0, x+20, 2,
                                           fill=NEON_CYAN, outline="")
            self._scan_offset += 1
            self.after(30, self._animate_scan)
        except Exception:
            pass

    # ─────────────── 霓虹进度条 ───────────────
    def _draw_bar(self, pct):
        self._bar_pct = pct
        self._bar_cv.delete("all")
        w = self._bar_cv.winfo_width() or 540
        filled = int(w * pct / 100)
        # 背景槽
        self._bar_cv.create_rectangle(0, 0, w, 18, fill=BG_INSET, outline="")
        if filled > 0:
            # 发光效果（暗色底）
            self._bar_cv.create_rectangle(0, 0, filled, 18, fill=DIM_CYAN, outline="")
            # 亮色主体
            self._bar_cv.create_rectangle(0, 3, filled, 15, fill=NEON_CYAN, outline="")
        # 百分比文字
        txt = f"{pct}%"
        self._bar_cv.create_text(w//2, 9, text=txt,
                                  fill=BG_VOID if filled > w//2 else NEON_CYAN,
                                  font=("Consolas", 8, "bold"))

    def _update_bar(self, pct):
        self._bar_cv.after(0, lambda: self._draw_bar(pct))

    # ─────────────── 交互 ───────────────
    def _browse(self):
        d = filedialog.askdirectory(title="\u9009\u62e9\u5b89\u88c5\u76ee\u5f55",
                                    initialdir=self.install_dir.get())
        if d:
            self.install_dir.set(os.path.normpath(d))

    def _start_install(self):
        if self._installing:
            return
        self._installing = True
        self._install_btn.config(state="disabled", text="INSTALLING...")
        t = threading.Thread(target=self._do_install, daemon=True)
        t.start()

    def _do_install(self):
        dst = self.install_dir.get()
        def status(msg, pct):
            self._prog_lbl.config(text=msg)
            self._update_bar(pct)
            self.update_idletasks()

        try:
            os.makedirs(dst, exist_ok=True)
        except Exception as e:
            messagebox.showerror("ERROR", "\u65e0\u6cd5\u521b\u5efa\u76ee\u5f55\uff1a" + str(e))
            self._install_btn.config(state="normal", text="\u25b6  INSTALL  \u5f00\u59cb\u5b89\u88c5")
            self._installing = False
            return

        status("[ 01/04 ]  \u89e3\u538b\u6587\u4ef6...", 10)

        try:
            with zipfile.ZipFile(self.payload_zip, "r") as zf:
                names = zf.namelist()
                for i, name in enumerate(names):
                    zf.extract(name, dst)
                    pct = 10 + int(60 * (i + 1) / len(names))
                    status(f"[ 02/04 ]  \u6b63\u5728\u5199\u5165: {name}", pct)
        except Exception as e:
            messagebox.showerror("ERROR", "\u89e3\u538b\u5931\u8d25\uff1a" + str(e))
            self._install_btn.config(state="normal", text="\u25b6  INSTALL  \u5f00\u59cb\u5b89\u88c5")
            self._installing = False
            return

        status("[ 03/04 ]  \u5199\u5165\u6ce8\u518c\u8868...", 75)
        exe_path = os.path.join(dst, APP_NAME + ".exe")

        # 卸载脚本
        uninstall = os.path.join(dst, "uninstall.bat")
        with open(uninstall, "w", encoding="gbk") as f:
            f.write("@echo off\n")
            f.write(f'rmdir /s /q "{dst}"\n')
            f.write(f'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /f\n')
            f.write("\u5378\u8f7d\u5b8c\u6210\u3002 & pause\n")

        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}")
            winreg.SetValueEx(key, "DisplayName",    0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VER)
            winreg.SetValueEx(key, "InstallLocation",0, winreg.REG_SZ, dst)
            winreg.SetValueEx(key, "UninstallString",0, winreg.REG_SZ, uninstall)
            winreg.CloseKey(key)
        except Exception:
            pass

        status("[ 04/04 ]  \u521b\u5efa\u5feb\u6377\u65b9\u5f0f...", 88)

        def make_lnk(lnk_path):
            vbs = (f'Set ws=WScript.CreateObject("WScript.Shell")\n'
                   f'Set sc=ws.CreateShortcut("{lnk_path}")\n'
                   f'sc.TargetPath="{exe_path}"\n'
                   f'sc.WorkingDirectory="{dst}"\n'
                   f'sc.Save\n')
            tmp = tempfile.mktemp(suffix=".vbs")
            with open(tmp, "w") as f:
                f.write(vbs)
            subprocess.call(["cscript", "//nologo", tmp])
            try: os.remove(tmp)
            except: pass

        LNK_NAME = "\u7b6e\u95ee"  # 快捷方式显示名 = 筮问
        if self.create_desk.get():
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            make_lnk(os.path.join(desktop, LNK_NAME + ".lnk"))

        if self.create_start.get():
            sm = os.path.join(os.environ.get("APPDATA", ""),
                "Microsoft", "Windows", "Start Menu", "Programs", APP_NAME)
            os.makedirs(sm, exist_ok=True)
            make_lnk(os.path.join(sm, LNK_NAME + ".lnk"))

        status("[ OK ]  \u5b89\u88c5\u5b8c\u6210  //  INSTALL COMPLETE", 100)

        if messagebox.askyesno(
            "INSTALL COMPLETE",
            f"\u7b6e\u95ee\u00b7SHI WEN  v{APP_VER} \u5b89\u88c5\u5b8c\u6210\uff01\n\n"
            f"\u5b89\u88c5\u8def\u5f84\uff1a{dst}\n\n"
            "\u662f\u5426\u73b0\u5728\u542f\u52a8\u7a0b\u5e8f\uff1f"
        ):
            subprocess.Popen([exe_path])
        self.destroy()


if __name__ == "__main__":
    if hasattr(sys, "_MEIPASS"):
        pz = os.path.join(sys._MEIPASS, "_payload.zip")
    elif len(sys.argv) > 1:
        pz = sys.argv[1]
    else:
        pz = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_payload.zip")

    if not os.path.exists(pz):
        import tkinter.messagebox as mb
        mb.showerror("ERROR",
            "\u627e\u4e0d\u5230\u5b89\u88c5\u6570\u636e\uff0c\u8bf7\u91cd\u65b0\u4e0b\u8f7d\u3002\n\u8def\u5f84\uff1a" + str(pz))
        sys.exit(1)

    app = CyberInstaller(pz)
    app.mainloop()
'''


# ══════════════════════════════════════════════════════════════════
#  打包流程
# ══════════════════════════════════════════════════════════════════
def build_installer():
    if not os.path.exists(SRC_EXE):
        print("[错误] 找不到 dist\\易经算卦.exe，请先运行 PyInstaller 打包！")
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)

    print("[1/4] 创建 payload zip...")
    tmp_zip = os.path.join(OUT_DIR, "_payload.zip")
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(SRC_EXE, os.path.basename(SRC_EXE))
    print(f"      payload: {os.path.getsize(tmp_zip)/1024/1024:.1f} MB")

    print("[2/4] 写出安装向导脚本...")
    wizard_py = os.path.join(OUT_DIR, "_wizard.py")
    with open(wizard_py, "w", encoding="utf-8") as f:
        f.write(WIZARD_SCRIPT)

    print("[3/4] 用 PyInstaller 打包安装向导...")
    spec_content = """# -*- coding: utf-8 -*-
block_cipher = None
a = Analysis(['{wizard}'],
    pathex=[], binaries=[],
    datas=[('{payload}', '.')],
    hiddenimports=['tkinter','tkinter.ttk','tkinter.filedialog',
                   'tkinter.messagebox','winreg'],
    hookspath=[], runtime_hooks=[], excludes=[],
    cipher=block_cipher, noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='{name}',
    debug=False, bootloader_ignore_signals=False,
    strip=False, upx=True, upx_exclude=[],
    runtime_tmpdir=None, console=False,
    disable_windowed_traceback=False,
    argv_emulation=False, target_arch=None,
    codesign_identity=None, entitlements_file=None)
""".format(
        wizard  = wizard_py.replace("\\", "\\\\"),
        payload = tmp_zip.replace("\\", "\\\\"),
        name    = APP_NAME + "_Setup_v" + APP_VER,
    )

    spec_path = os.path.join(OUT_DIR, "_installer.spec")
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)

    ret = subprocess.call([
        sys.executable, "-m", "PyInstaller",
        spec_path, "--clean", "--noconfirm",
        "--distpath", OUT_DIR,
        "--workpath", os.path.join(OUT_DIR, "_build_tmp"),
    ])

    # 清理临时文件
    for p in [tmp_zip, wizard_py, spec_path,
              os.path.join(OUT_DIR, "_build_tmp"),
              os.path.join(OUT_DIR, "__pycache__")]:
        try:
            import shutil as _sh
            if os.path.isdir(p): _sh.rmtree(p)
            elif os.path.exists(p): os.remove(p)
        except Exception:
            pass

    final = os.path.join(OUT_DIR, APP_NAME + "_Setup_v" + APP_VER + ".exe")
    if ret == 0 and os.path.exists(final):
        print(f"\n[✓] 安装包生成成功！")
        print(f"    路径：{final}")
        print(f"    大小：{os.path.getsize(final)/1024/1024:.1f} MB")
    else:
        print("\n[✗] 安装包生成失败，请检查输出信息。")


if __name__ == "__main__":
    build_installer()