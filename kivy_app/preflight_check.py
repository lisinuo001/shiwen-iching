# -*- coding: utf-8 -*-
"""
TIANJI Pre-flight Check — 构建前自动质检脚本
在 GitHub Actions 中于 buildozer 之前运行，不合格则阻断构建。

用法: python preflight_check.py
退出码: 0=通过, 1=有致命错误
"""
import re, sys, os

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
errors = []
warnings = []


def check(ok, msg):
    if ok:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {FAIL} {msg}")
        errors.append(msg)


def warn(ok, msg):
    if ok:
        print(f"  {PASS} {msg}")
    else:
        print(f"  {WARN} {msg}")
        warnings.append(msg)


def read(path):
    here = os.path.dirname(os.path.abspath(__file__))
    full = os.path.join(here, path)
    if not os.path.exists(full):
        return None
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def main():
    print("=" * 60)
    print("  TIANJI PRE-FLIGHT CHECK")
    print("=" * 60)

    main_py = read("main.py")
    spec = read("buildozer.spec")

    if not main_py:
        print(f"  {FAIL} main.py not found!")
        sys.exit(1)
    if not spec:
        print(f"  {FAIL} buildozer.spec not found!")
        sys.exit(1)

    # ============================================================
    # 1. VERSION CONSISTENCY
    # ============================================================
    print("\n[1] 版本一致性检查")

    spec_ver = re.search(r"^version\s*=\s*(.+)$", spec, re.M)
    spec_ver = spec_ver.group(1).strip() if spec_ver else "NOT_FOUND"
    print(f"     buildozer.spec version = {spec_ver}")

    # Check workflow file
    wf = read("../.github/workflows/build-apk.yml")
    if wf:
        artifact_match = re.search(r"name:\s*TianJi-APK-v([\d.]+)", wf)
        artifact_ver = artifact_match.group(1) if artifact_match else "NOT_FOUND"
        print(f"     workflow artifact version = {artifact_ver}")
        check(spec_ver == artifact_ver,
              f"spec版本({spec_ver}) 与 workflow artifact版本({artifact_ver}) 一致")

        expected_match = re.search(r"Expected version:\s*([\d.]+)", wf)
        if expected_match:
            expected_ver = expected_match.group(1)
            check(spec_ver == expected_ver,
                  f"spec版本({spec_ver}) 与 workflow expected版本({expected_ver}) 一致")
    else:
        warn(False, "未找到 workflow 文件，跳过版本交叉检查")

    # ============================================================
    # 2. SCREEN STRUCTURE — 核心布局检查
    # ============================================================
    print("\n[2] Screen 布局结构检查")

    # Rule: Screen children should NOT be added directly without a wrapper
    # Bad:  self.add_widget(SmokeLayer()); self.add_widget(root)
    # Good: wrapper = FloatLayout(); wrapper.add_widget(root); self.add_widget(wrapper)

    # Count self.add_widget calls inside Screen classes
    screen_classes = re.findall(
        r"class\s+(\w+)\(Screen\):.*?(?=\nclass\s|\Z)", main_py, re.S
    )
    for block_match in re.finditer(
        r"class\s+(\w+)\(Screen\):.*?(?=\nclass\s|\Z)", main_py, re.S
    ):
        cls_name = block_match.group(1)
        block = block_match.group(0)
        # Count direct self.add_widget() calls in _build method
        build_match = re.search(r"def _build\(self\):(.*?)(?=\n    def |\Z)", block, re.S)
        if build_match:
            build_body = build_match.group(1)
            direct_adds = re.findall(r"self\.add_widget\(", build_body)
            check(len(direct_adds) <= 1,
                  f"{cls_name}._build() 中 self.add_widget 只调用1次 (实际: {len(direct_adds)}次)")

    # ============================================================
    # 3. SIZE_HINT 检查 — 关键 Widget 必须显式设置
    # ============================================================
    print("\n[3] size_hint 显式声明检查")

    # Root BoxLayout inside _build should have size_hint=(1, 1)
    root_boxes = re.findall(
        r"root\s*=\s*BoxLayout\([^)]*\)", main_py
    )
    for rb in root_boxes:
        has_size_hint = "size_hint" in rb
        check(has_size_hint,
              f"root BoxLayout 显式设置了 size_hint: {rb[:60]}...")

    # pos_hint check for root
    for rb in root_boxes:
        has_pos_hint = "pos_hint" in rb
        check(has_pos_hint,
              f"root BoxLayout 显式设置了 pos_hint")

    # ============================================================
    # 4. 禁止危险写法
    # ============================================================
    print("\n[4] 危险写法检查")

    # 4a. Custom widgets should NOT inherit from BoxLayout
    custom_boxlayout = re.findall(
        r"class\s+(\w+)\(BoxLayout\):", main_py
    )
    # Exclude pure container widgets, only flag interactive ones
    interactive_keywords = ["Button", "Slot", "Display", "Hold", "Tap"]
    for cls in custom_boxlayout:
        is_interactive = any(kw in cls for kw in interactive_keywords)
        check(not is_interactive,
              f"交互组件 {cls} 不继承 BoxLayout (应继承 Widget)")

    # 4b. CoreLabel should not be used for primary UI text
    # canvas text helper is OK, but direct CoreLabel in widget __init__ is bad
    corelabel_in_init = re.findall(
        r"class\s+\w+.*?def __init__.*?CoreLabel\(",
        main_py, re.S
    )
    warn(len(corelabel_in_init) == 0,
         f"Widget.__init__ 中使用 CoreLabel 数量: {len(corelabel_in_init)} (建议为0，用 Label 替代)")

    # 4c. Window.size should only be in __main__ block
    window_size_lines = []
    for i, line in enumerate(main_py.split("\n"), 1):
        if "Window.size" in line and "if __name__" not in line:
            window_size_lines.append(i)
    # Check if all Window.size are inside if __name__ block
    in_main_block = re.search(
        r'if __name__\s*==\s*["\']__main__["\'].*?Window\.size', main_py, re.S
    )
    main_block_start = main_py.find('if __name__')
    outside_main = [
        ln for ln in window_size_lines
        if main_block_start < 0 or ln < main_py[:main_block_start].count("\n")
    ]
    # Simplified: just check Window.size isn't at module level
    module_level_window = re.search(
        r"^Window\.size\s*=", main_py, re.M
    )
    warn(not module_level_window,
         "Window.size 不在模块顶层 (应仅在 __main__ 块中)")

    # ============================================================
    # 5. 文件完整性
    # ============================================================
    print("\n[5] 文件完整性检查")

    required_files = ["main.py", "buildozer.spec", "NotoSansCJK.otf"]
    for f in required_files:
        exists = read(f) is not None or os.path.exists(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
        )
        check(exists, f"必需文件存在: {f}")

    # icon.png
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    check(os.path.exists(icon_path), "icon.png 存在")
    if os.path.exists(icon_path):
        size = os.path.getsize(icon_path)
        check(size > 1000, f"icon.png 大小合理 ({size} bytes)")

    # ============================================================
    # 6. 数据文件引用检查
    # ============================================================
    print("\n[6] 数据文件引用检查")

    check("from iching_data import" in main_py or "import iching_data" in main_py,
          "main.py 引用了 iching_data")
    check("from yaoci_data import" in main_py or "import yaoci_data" in main_py,
          "main.py 引用了 yaoci_data")

    # source.include_patterns in spec
    check("iching_data.py" in spec, "buildozer.spec 包含 iching_data.py")
    check("yaoci_data.py" in spec, "buildozer.spec 包含 yaoci_data.py")
    check("NotoSansCJK.otf" in spec, "buildozer.spec 包含 NotoSansCJK.otf")

    # ============================================================
    # 7. Android 兼容性检查
    # ============================================================
    print("\n[7] Android 兼容性检查")

    check("fullscreen = 0" in spec, "非全屏模式 (fullscreen = 0)")
    check("orientation = portrait" in spec, "竖屏模式 (portrait)")

    # Check for FloatLayout wrapper pattern
    has_floatlayout_import = "FloatLayout" in main_py
    warn(has_floatlayout_import,
         "使用了 FloatLayout 包装 Screen 子 widget")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    total_checks = len(errors) + len(warnings) + sum(
        1 for line in main_py.split("\n") if "# checked" in line
    )

    if errors:
        print(f"  {FAIL} 检查未通过！发现 {len(errors)} 个致命错误:")
        for e in errors:
            print(f"     - {e}")
        if warnings:
            print(f"  {WARN} 另有 {len(warnings)} 个警告")
        print("=" * 60)
        print("  *** 构建已阻断，请修复上述错误后重新推送 ***")
        sys.exit(1)
    elif warnings:
        print(f"  {PASS} 无致命错误，但有 {len(warnings)} 个警告:")
        for w in warnings:
            print(f"     - {w}")
        print("=" * 60)
        print("  *** 构建将继续，但建议关注以上警告 ***")
        sys.exit(0)
    else:
        print(f"  {PASS} 全部检查通过！可以安全构建。")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
