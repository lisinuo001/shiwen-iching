# -*- coding: utf-8 -*-
"""
TIANJI Pre-flight Check 鈥?鏋勫缓鍓嶈嚜鍔ㄨ川妫€鑴氭湰
鍦?GitHub Actions 涓簬 buildozer 涔嬪墠杩愯锛屼笉鍚堟牸鍒欓樆鏂瀯寤恒€?

鐢ㄦ硶: python preflight_check.py
閫€鍑虹爜: 0=閫氳繃, 1=鏈夎嚧鍛介敊璇?
"""
import re, sys, os

PASS = "鉁?
FAIL = "鉂?
WARN = "鈿狅笍"
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
    with open(full, "r", encoding="utf-8-sig") as f:
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
    print("\n[1] 鐗堟湰涓€鑷存€ф鏌?)

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
              f"spec鐗堟湰({spec_ver}) 涓?workflow artifact鐗堟湰({artifact_ver}) 涓€鑷?)

        expected_match = re.search(r"Expected version:\s*([\d.]+)", wf)
        if expected_match:
            expected_ver = expected_match.group(1)
            check(spec_ver == expected_ver,
                  f"spec鐗堟湰({spec_ver}) 涓?workflow expected鐗堟湰({expected_ver}) 涓€鑷?)
    else:
        warn(False, "鏈壘鍒?workflow 鏂囦欢锛岃烦杩囩増鏈氦鍙夋鏌?)

    # ============================================================
    # 2. ARCHITECTURE CHECK 鈥?v10.8+ uses direct BoxLayout pages
    # ============================================================
    print("\n[2] 鏋舵瀯妫€鏌?)

    # v10.8: Should NOT use ScreenManager/Screen (causes RelativeLayout issues)
    has_screen_import = bool(re.search(r"^\s*from kivy\.uix\.screenmanager import", main_py, re.M))
    check(not has_screen_import,
          "涓嶄娇鐢?ScreenManager/Screen (v10.8 鏀逛负鐩存帴 BoxLayout 椤甸潰鍒囨崲)")

    # Pages should inherit BoxLayout directly
    for cls_name in ["MainPage", "ResultPage"]:
        pattern = rf"class\s+{cls_name}\(BoxLayout\):"
        found = bool(re.search(pattern, main_py))
        check(found, f"{cls_name} 缁ф壙鑷?BoxLayout")

    # App.build should return a simple widget (FloatLayout or BoxLayout)
    build_match = re.search(r"class\s+TianJiApp.*?def build\(self\):(.*?)(?=\n    def |\Z)", main_py, re.S)
    if build_match:
        build_body = build_match.group(1)
        has_screen_mgr = "ScreenManager" in build_body
        check(not has_screen_mgr, "App.build() 涓嶄娇鐢?ScreenManager")

    # fullscreen should be 1 (to avoid Kivy Window size bug on Android)
    check("fullscreen = 1" in spec, "鍏ㄥ睆妯″紡 (fullscreen = 1) 閬垮厤 Window 灏哄 bug")

    # ============================================================
    # 3. SIZE_HINT 妫€鏌?鈥?鍏抽敭 Widget 蹇呴』鏄惧紡璁剧疆
    # ============================================================
    print("\n[3] size_hint 鏄惧紡澹版槑妫€鏌?)

    # Root BoxLayout inside _build should have size_hint=(1, 1)
    root_boxes = re.findall(
        r"root\s*=\s*BoxLayout\([^)]*\)", main_py
    )
    for rb in root_boxes:
        has_size_hint = "size_hint" in rb
        check(has_size_hint,
              f"root BoxLayout 鏄惧紡璁剧疆浜?size_hint: {rb[:60]}...")

    # pos_hint check for root
    for rb in root_boxes:
        has_pos_hint = "pos_hint" in rb
        check(has_pos_hint,
              f"root BoxLayout 鏄惧紡璁剧疆浜?pos_hint")

    # ============================================================
    # 4. 绂佹鍗遍櫓鍐欐硶
    # ============================================================
    print("\n[4] 鍗遍櫓鍐欐硶妫€鏌?)

    # 4a. Custom widgets should NOT inherit from BoxLayout
    custom_boxlayout = re.findall(
        r"class\s+(\w+)\(BoxLayout\):", main_py
    )
    # Exclude pure container widgets, only flag interactive ones
    interactive_keywords = ["Button", "Slot", "Display", "Hold", "Tap"]
    for cls in custom_boxlayout:
        is_interactive = any(kw in cls for kw in interactive_keywords)
        check(not is_interactive,
              f"浜や簰缁勪欢 {cls} 涓嶇户鎵?BoxLayout (搴旂户鎵?Widget)")

    # 4b. CoreLabel should not be used for primary UI text
    # canvas text helper is OK, but direct CoreLabel in widget __init__ is bad
    corelabel_in_init = re.findall(
        r"class\s+\w+.*?def __init__.*?CoreLabel\(",
        main_py, re.S
    )
    warn(len(corelabel_in_init) == 0,
         f"Widget.__init__ 涓娇鐢?CoreLabel 鏁伴噺: {len(corelabel_in_init)} (寤鸿涓?锛岀敤 Label 鏇夸唬)")

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
         "Window.size 涓嶅湪妯″潡椤跺眰 (搴斾粎鍦?__main__ 鍧椾腑)")

    # ============================================================
    # 5. 鏂囦欢瀹屾暣鎬?
    # ============================================================
    print("\n[5] 鏂囦欢瀹屾暣鎬ф鏌?)

    required_files = ["main.py", "buildozer.spec", "NotoSansCJK.otf"]
    for f in required_files:
        exists = read(f) is not None or os.path.exists(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
        )
        check(exists, f"蹇呴渶鏂囦欢瀛樺湪: {f}")

    # icon.png
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    check(os.path.exists(icon_path), "icon.png 瀛樺湪")
    if os.path.exists(icon_path):
        size = os.path.getsize(icon_path)
        check(size > 1000, f"icon.png 澶у皬鍚堢悊 ({size} bytes)")

    # ============================================================
    # 6. 鏁版嵁鏂囦欢寮曠敤妫€鏌?
    # ============================================================
    print("\n[6] 鏁版嵁鏂囦欢寮曠敤妫€鏌?)

    check("from iching_data import" in main_py or "import iching_data" in main_py,
          "main.py 寮曠敤浜?iching_data")
    check("from yaoci_data import" in main_py or "import yaoci_data" in main_py,
          "main.py 寮曠敤浜?yaoci_data")

    # source.include_patterns in spec
    check("iching_data.py" in spec, "buildozer.spec 鍖呭惈 iching_data.py")
    check("yaoci_data.py" in spec, "buildozer.spec 鍖呭惈 yaoci_data.py")
    check("NotoSansCJK.otf" in spec, "buildozer.spec 鍖呭惈 NotoSansCJK.otf")

    # ============================================================
    # 7. Android 鍏煎鎬ф鏌?
    # ============================================================
    print("\n[7] Android 鍏煎鎬ф鏌?)

    check("fullscreen = 1" in spec, "鍏ㄥ睆妯″紡 (fullscreen = 1) 鈥?閬垮厤 Window 灏哄 bug")
    check("orientation = portrait" in spec, "绔栧睆妯″紡 (portrait)")

    # v10.8: should use direct BoxLayout pages, not Screen
    has_no_screen = "ScreenManager" not in main_py or "# ScreenManager removed" in main_py
    check(has_no_screen, "涓嶄娇鐢?ScreenManager (v10.8 鏋舵瀯)")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    total_checks = len(errors) + len(warnings) + sum(
        1 for line in main_py.split("\n") if "# checked" in line
    )

    if errors:
        print(f"  {FAIL} 妫€鏌ユ湭閫氳繃锛佸彂鐜?{len(errors)} 涓嚧鍛介敊璇?")
        for e in errors:
            print(f"     - {e}")
        if warnings:
            print(f"  {WARN} 鍙︽湁 {len(warnings)} 涓鍛?)
        print("=" * 60)
        print("  *** 鏋勫缓宸查樆鏂紝璇蜂慨澶嶄笂杩伴敊璇悗閲嶆柊鎺ㄩ€?***")
        sys.exit(1)
    elif warnings:
        print(f"  {PASS} 鏃犺嚧鍛介敊璇紝浣嗘湁 {len(warnings)} 涓鍛?")
        for w in warnings:
            print(f"     - {w}")
        print("=" * 60)
        print("  *** 鏋勫缓灏嗙户缁紝浣嗗缓璁叧娉ㄤ互涓婅鍛?***")
        sys.exit(0)
    else:
        print(f"  {PASS} 鍏ㄩ儴妫€鏌ラ€氳繃锛佸彲浠ュ畨鍏ㄦ瀯寤恒€?)
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()

