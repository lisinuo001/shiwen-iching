# -*- coding: utf-8 -*-
"""
YiCORE Pre-flight Check
Run before buildozer to block bad builds.
Exit: 0=pass, 1=fatal
"""
import re, sys, os

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"
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
    print("  YiCORE PRE-FLIGHT CHECK")
    print("=" * 60)

    main_py = read("main.py")
    spec = read("buildozer.spec")

    if not main_py:
        print(f"  {FAIL} main.py not found!")
        sys.exit(1)
    if not spec:
        print(f"  {FAIL} buildozer.spec not found!")
        sys.exit(1)

    # 1. VERSION CONSISTENCY
    print("\n[1] Version consistency")

    spec_ver = re.search(r"^version\s*=\s*(.+)$", spec, re.M)
    spec_ver = spec_ver.group(1).strip() if spec_ver else "NOT_FOUND"
    print(f"     buildozer.spec version = {spec_ver}")

    wf = read("../.github/workflows/build-apk.yml")
    if wf:
        artifact_match = re.search(r"name:\s*YiCORE-APK-v([\d.]+)", wf)
        artifact_ver = artifact_match.group(1) if artifact_match else "NOT_FOUND"
        print(f"     workflow artifact version = {artifact_ver}")
        check(spec_ver == artifact_ver,
              f"spec({spec_ver}) == artifact({artifact_ver})")

        expected_match = re.search(r"Expected version:\s*([\d.]+)", wf)
        if expected_match:
            expected_ver = expected_match.group(1)
            check(spec_ver == expected_ver,
                  f"spec({spec_ver}) == expected({expected_ver})")
    else:
        warn(False, "workflow file not found")

    # 2. ARCHITECTURE CHECK
    print("\n[2] Architecture")

    has_screen_import = bool(re.search(
        r"^\s*from kivy\.uix\.screenmanager import", main_py, re.M))
    check(not has_screen_import, "No ScreenManager import (v10.8+)")

    for cls_name in ["MainPage", "ResultPage"]:
        found = bool(re.search(rf"class\s+{cls_name}\(BoxLayout\):", main_py))
        check(found, f"{cls_name} extends BoxLayout")

    check("fullscreen = 1" in spec, "fullscreen = 1")

    # 3. DANGEROUS PATTERNS
    print("\n[3] Dangerous patterns")

    custom_boxlayout = re.findall(r"class\s+(\w+)\(BoxLayout\):", main_py)
    bad_kw = ["Button", "Slot", "Display", "Hold", "Tap"]
    for cls in custom_boxlayout:
        is_interactive = any(kw in cls for kw in bad_kw)
        check(not is_interactive,
              f"Interactive {cls} does not extend BoxLayout")

    module_level_window = re.search(r"^Window\.size\s*=", main_py, re.M)
    warn(not module_level_window, "Window.size not at module level")

    # 4. FILE INTEGRITY
    print("\n[4] File integrity")

    here = os.path.dirname(os.path.abspath(__file__))
    for f in ["main.py", "buildozer.spec"]:
        check(os.path.exists(os.path.join(here, f)), f"Required: {f}")

    icon_path = os.path.join(here, "icon.png")
    check(os.path.exists(icon_path), "icon.png exists")
    presplash_path = os.path.join(here, "presplash.png")
    check(os.path.exists(presplash_path), "presplash.png exists")

    # 5. DATA REFS
    print("\n[5] Data references")

    check("iching_data" in main_py, "main.py refs iching_data")
    check("yaoci_data" in main_py, "main.py refs yaoci_data")
    check("iching_data.py" in spec, "spec includes iching_data.py")
    check("yaoci_data.py" in spec, "spec includes yaoci_data.py")

    # 6. ANDROID COMPAT
    print("\n[6] Android compat")

    check("fullscreen = 1" in spec, "fullscreen = 1 (avoid Window size bug)")
    check("orientation = portrait" in spec, "portrait mode")

    # SUMMARY
    print("\n" + "=" * 60)
    if errors:
        print(f"  {FAIL} BLOCKED: {len(errors)} error(s):")
        for e in errors:
            print(f"     - {e}")
        print("=" * 60)
        sys.exit(1)
    elif warnings:
        print(f"  {PASS} Passed with {len(warnings)} warning(s)")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f"  {PASS} All checks passed!")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()