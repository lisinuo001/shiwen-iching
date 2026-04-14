# 出包规范 BUILD_SPEC

> 版本: v3.0 (总结 v10.0~v10.8 所有打包教训 + 自动 QA 管线)  
> 更新日期: 2026-04-14  
> 适用项目: 天机 TianJi (Kivy Android APK)  
> 状态: 🟢 ACTIVE

---

## 0. CORE RULES (read before every build)

> Five iron rules. Violating any one = wasted build:

1. MUST clean cache -- workflow must have `rm -rf .buildozer bin`
2. MUST verify version BEFORE push -- 3 places must match: buildozer.spec / artifact name / expected version (auto-checked by preflight_check.py)
3. MUST use Widget base -- interactive widgets inherit Widget, NOT BoxLayout
4. MUST keep config ASCII-only -- buildozer.spec and preflight_check.py: NO Chinese, NO emoji, NO BOM
5. MUST pass preflight before build -- preflight_check.py runs before buildozer, blocks if fail

---

## 1. Build Method

GitHub Actions cloud build. No local Linux needed.

| Item | Value |
|------|-------|
| Repo | https://github.com/lisinuo001/shiwen-iching |
| Trigger | push to main/master, or manual workflow_dispatch |
| Runner | ubuntu-22.04 |
| Timeout | 60 min |
| Artifact | Actions -> run -> Artifacts -> TianJi-APK-vX.Y.Z |
| Retention | 30 days |
| Full build time | ~25-35 min |

---

## 2. Pre-Build Checklist

### 2.1 Code Standards (Mobile Compat)

> PC OK != Phone OK. All rules from real failures.

- [ ] main.py runs with `py -3.11 main.py`, no crash
- [ ] NO ScreenManager/Screen -- pages inherit BoxLayout directly
- [ ] Interactive widgets (buttons, slots) inherit Widget, NOT BoxLayout
- [ ] Widget text uses `add_widget(Label)` + `bind(pos, size)` + `_layout()` manual positioning
- [ ] CoreLabel only for decorative canvas text
- [ ] No Python 3.11+ syntax (build env is Python 3.10)
- [ ] No new dependencies without updating buildozer.spec requirements

### 2.2 Resource Check

- [ ] NotoSansCJK.otf exists in kivy_app/
- [ ] icon.png exists in kivy_app/ (512x512 RGB PNG)
- [ ] iching_data.py and yaoci_data.py exist in repo root
- [ ] No external PNG textures for core rendering

### 2.3 Config Check

- [ ] buildozer.spec version updated
- [ ] title is ASCII-only (e.g. `tianji`), Chinese name set via `get_application_name()`
- [ ] buildozer.spec is PURE ASCII, NO BOM, LF line endings
  - Reason: PowerShell Set-Content writes UTF-8 BOM, configparser cannot parse BOM files
- [ ] icon.filename and presplash.filename use `./icon.png` (NOT `%(source.dir)s/icon.png`)
  - Reason: Python string escaping turns `%` into `%%` when writing spec via script
- [ ] source.include_patterns includes all required files
- [ ] requirements = python3,kivy,pillow (no version pinning)
- [ ] android.accept_sdk_license = True
- [ ] fullscreen = 1 (NOT 0! fullscreen=0 causes Kivy Window size bug)
- [ ] android.archs = arm64-v8a (NOT android.arch, which is deprecated)

### 2.4 Workflow Check

- [ ] build-apk.yml has `rm -rf .buildozer bin` clean step
- [ ] build-apk.yml has Pre-flight Check step BEFORE Build step
- [ ] JAVA_HOME set to JDK 17
- [ ] Command is `buildozer -v android debug` (no pipes, no `yes |`, no `tail`)
- [ ] Artifact name EXACTLY matches version (10.8.0 not 10.8)
- [ ] if-no-files-found: error is set

---

## 2.5 QA Script Check (v3.0)

- [ ] preflight_check.py is PURE ASCII (no Chinese comments, no emoji)
  - Reason: PowerShell corrupts non-ASCII chars
- [ ] preflight_check.py uses utf-8-sig encoding (handles BOM gracefully)
- [ ] QA script checks: version consistency, architecture, file integrity

---

## 3. Build Procedure

### Step 1: Update version

```
kivy_app/buildozer.spec         -> version = X.Y.Z
.github/workflows/build-apk.yml -> artifact name = TianJi-APK-vX.Y.Z
.github/workflows/build-apk.yml -> Expected version: X.Y.Z
```

Version rule: X=major, Y=minor, Z=patch

### Step 2: Local test

```bash
cd d:\snow\iching\kivy_app
py -3.11 main.py
```

### Step 2.5: Review Agent audit (recommended)

Open new CodeMaker chat, paste review prompt (see docs/REVIEW_AGENT_GUIDE.md).
Tell it to read `d:\snow\iching\kivy_app\main.py` and audit.
Fix issues before proceeding.

### Step 3: Commit and push

```bash
cd d:\snow\iching
git add .
git commit -m "vX.Y.Z: description"
git push origin main
```

### Step 4: Monitor build

1. Open https://github.com/lisinuo001/shiwen-iching/actions
2. Check Pre-flight step first -- if it fails, build is blocked (saves 30 min)
3. Wait for green (~25-35 min for full build)
4. If failed: search for FAILURE, Error, gradle failed in logs

### Step 5: Download APK

1. Workflow run -> Artifacts -> download ZIP
2. Version consistency is already guaranteed by preflight_check.py (auto-blocks mismatched builds)

### Step 6: Install and test

1. Transfer to phone
2. Install (enable unknown sources)
3. Follow Section 7 test checklist

---

## 4. Frozen Environment Params

DO NOT change without testing:

| Param | Value | Risk |
|-------|-------|------|
| Runner | ubuntu-22.04 | HIGH |
| Python | 3.10 | HIGH -- 3.11+ breaks p4a |
| JDK | openjdk-17 | HIGH -- API 33 requires it |
| Cython | 0.29.36 | MED |
| JAVA_HOME | /usr/lib/jvm/java-17-openjdk-amd64 | HIGH |
| Android API | 33 | MED |
| Min API | 21 | LOW |
| NDK | 25b | HIGH |
| Arch | arm64-v8a | LOW |

---

## 5. Bug Log (sorted by severity)

### P0 -- Wrong version installed

#### B1. Buildozer cache serves old APK
- Versions: v10.3~v10.5 (3 consecutive stale builds)
- Symptom: Artifact says v10.5, APK filename says tianji-10.3.0
- Cause: .buildozer cached first successful build, never recompiled
- Fix: `rm -rf .buildozer bin` before every build

### P0 -- APK fails to generate

#### B2. `yes | buildozer` Broken Pipe
- Symptom: Build "succeeds" but Artifacts empty
- Cause: `yes |` triggers SIGPIPE
- Fix: Remove `yes |`, use `android.accept_sdk_license = True`

#### B3. Gradle fail (JDK 11 vs 17)
- Symptom: `gradle failed!` buried in 30K line log
- Cause: Default JAVA_HOME points to JDK 11, API 33 needs 17
- Fix: Explicitly set JAVA_HOME in workflow

#### B4. `tail -50` silently kills build
- Symptom: Exit 0 but no APK
- Cause: Pipe truncation kills buildozer process
- Fix: No pipes on buildozer command ever

#### B5. Kivy version pinning fails
- Symptom: `kivy==2.3.0` causes p4a compile error
- Fix: Write `kivy` without version

#### B6. buildozer.spec BOM crashes configparser (v10.8)
- Symptom: `MissingSectionHeaderError`, log shows `\ufeff\n`
- Cause: PowerShell writes UTF-8 BOM, configparser chokes on BOM before `[app]`
- Fix: NEVER use PowerShell for spec. Use Python io.open or CodeMaker edit tools
- Prevention: Keep spec pure ASCII

#### B7. preflight_check.py emoji corrupted by PowerShell (v10.8)
- Symptom: `SyntaxError: unterminated string literal`
- Cause: PowerShell corrupts UTF-8 emoji chars
- Fix: All CI scripts pure ASCII only: [OK], [FAIL], [WARN]

#### B8. Artifact version precision mismatch (v10.8)
- Symptom: preflight reports `spec(10.8.0) != artifact(10.8)`
- Cause: Artifact name missing `.0`
- Fix: Always use full 3-segment version in artifact name

#### B9. icon/presplash path with escaped percent (v10.8)
- Symptom: `shutil.copy` FileNotFoundError during packaging
- Cause: Python `%%` escaping in spec turns `%(source.dir)s` into literal `%%(source.dir)s`
- Fix: Use `./icon.png` instead of `%(source.dir)s/icon.png`

#### BA. android.arch deprecated (v10.8)
- Symptom: Warning about migration to android.archs
- Fix: Change `android.arch` to `android.archs`

### P1 -- Phone UI broken

#### B11. CoreLabel canvas coords reset to (0,0) on Android
- Symptom: All text piled at bottom-left corner
- Cause: CoreLabel absolute coords, timing differs on Android
- Fix: Use native Label + bind(pos, size) + _layout()

#### B12. BoxLayout children intercept touch events
- Symptom: Buttons unresponsive
- Cause: BoxLayout child Labels intercept on_touch_down
- Fix: Inherit Widget, not BoxLayout

#### B13. BoxLayout canvas.before coordinates drift
- Symptom: Button border at wrong position
- Cause: Layout timing vs canvas draw timing inconsistent on Android
- Fix: Widget base + bind -> _layout() unified update

#### B14. Screen(RelativeLayout) causes half-screen layout (v10.5~v10.7)
- Versions: v10.5~v10.7, 3 versions unfixed
- Symptom: All UI ~40% width, left side only, huge blank space above
- Cause: Screen=RelativeLayout size_hint bug + fullscreen=0 Window size bug
- Failed attempts: FloatLayout wrapper, explicit size_hint, extra size_hint_x -- all no effect
- Correct fix: Remove ScreenManager entirely, BoxLayout pages, fullscreen=1

### P2 -- Build details

#### B15. APK artifact path wrong
- Fix: Use `kivy_app/bin/*.apk` + `if-no-files-found: error`

#### B16. .github directory in wrong location
- Fix: Must be at Git repo root

---

## 6. Kivy Mobile Dev Rules

### 6.1 Widget Architecture
- Interactive widgets MUST inherit Widget
- Text via add_widget(Label) + bind(pos, size) + _layout()
- on_touch_down directly on Widget, not through BoxLayout children

### 6.2 Page Architecture (v10.8)
- Pages inherit BoxLayout directly (NOT Screen)
- App.build() returns FloatLayout
- Page switching via clear_widgets() + add_widget()
- NO ScreenManager

### 6.3 Coordinate Rules
- Widget.canvas + bind: OK on both PC and Android
- BoxLayout.canvas.before: BROKEN on Android
- CoreLabel: decoration only, never for main UI
- add_widget(Label) + bind: RECOMMENDED for everything

### 6.4 Touch Rules
- Widget: direct touch -- RECOMMENDED
- BoxLayout: children intercept -- AVOID

---

## 7. Post-Install Test Checklist

- [ ] APK filename version == spec version (do first!)
- [ ] Title displayed, not cut off
- [ ] All text at correct position (not bottom-left pile)
- [ ] UI fills FULL screen width (not just left 40%)
- [ ] 6 yao slots evenly distributed
- [ ] Hold button fills width
- [ ] 1.5s long press triggers generation
- [ ] 6 yao reveal one by one
- [ ] Auto navigate to result page
- [ ] Result page scrollable
- [ ] "New divination" works
- [ ] Portrait locked, no crash
- [ ] Chinese font renders correctly
- [ ] Debug label visible: `v10.8 | Win WxH | density=X`

---

## 8. File Index

```
d:\snow\iching\
  .github/workflows/build-apk.yml   -- CI/CD (preflight + clean + build)
  iching_data.py                     -- 64 hexagram data
  yaoci_data.py                      -- yao text data
  kivy_app/
    main.py                          -- main program
    buildozer.spec                   -- config (ASCII only!)
    preflight_check.py               -- auto QA gate (ASCII only!)
    gen_icon.py                      -- icon generator
    NotoSansCJK.otf                  -- CJK font
    icon.png                         -- app icon 512x512
    docs/
      BUILD_SPEC.md                  -- this file
      MOBILE_COMPAT_SPEC.md          -- Kivy Android rules
      REVIEW_AGENT_GUIDE.md          -- review agent setup
```

---

## 9. Version History

| Version | Date | Change | Result |
|---------|------|--------|--------|
| 2.1.0 | 04-08 | Initial APK | OK |
| 2.2.0 | 04-09 | PC + APK | OK |
| 10.0.0 | 04-10 | v10 rewrite | PARTIAL |
| 10.1.0 | 04-10 | BoxLayout + Label | FAIL -- text bottom-left |
| 10.2.0 | 04-10 | Icon + rename | FAIL -- stale build |
| 10.3.0 | 04-10 | Fix native Label | FAIL -- cache |
| 10.4.0 | 04-13 | Fix touch + HUD | FAIL -- cache |
| 10.5.0 | 04-13 | Widget base + clean | PARTIAL -- layout left-biased |
| 10.6.0 | 04-13 | Remove HUD spacer | FAIL -- half-screen |
| 10.7.0 | 04-13 | FloatLayout wrapper | FAIL -- spec not updated |
| 10.8.0 | 04-14 | Remove ScreenManager + fullscreen=1 + preflight | BUILDING |

---

## 10. Auto QA Pipeline (v3.0)

```
Code change -> Review Agent -> git push -> preflight_check.py
                                             |
                                   PASS -> buildozer -> APK
                                   FAIL -> blocked, check [FAIL] lines
```

preflight checks: version match, architecture, dangerous patterns, file integrity, data refs, Android compat.

---

## 11. AI Assistant Memo

1. NEVER skip clean cache
2. NEVER inherit BoxLayout for interactive widgets
3. NEVER use CoreLabel for button text
4. NEVER pipe buildozer command
5. NEVER pin kivy version
6. Version consistency is auto-enforced by preflight -- do not rely on post-build manual checks
7. PC OK != Phone OK
8. NEVER use ScreenManager/Screen
9. NEVER use PowerShell to edit config files
10. ALL CI scripts must be pure ASCII
11. NEVER push without preflight + Review Agent
12. NEVER write spec via Python with %% escaping (v10.8)
13. icon/presplash use ./icon.png not %(source.dir)s (v10.8)
14. Use android.archs (plural) not android.arch (v10.8)

---

> 8 builds, 11 failures. Read Section 0 and 2 before EVERY build.