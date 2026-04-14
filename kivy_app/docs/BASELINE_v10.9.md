# BASELINE v10.9 -- UI State Freeze

> Created: 2026-04-14
> Git Tag: `v10.9-baseline`
> Status: FROZEN (do not modify this doc, only append comparison notes)
> Recovery: `git checkout v10.9-baseline`

---

## Purpose

This document records the exact visual state of v10.9 on a real Android phone.
All future optimization must be compared against this baseline.
If any change makes things worse, revert to this tag.

---

## Screen 1: Main Page (Idle State)

**ID: MAIN-IDLE**

| Element | Name | Current State |
|---------|------|---------------|
| Top-left debug label | `DBG_LABEL` | "v10.9 | Win 1200x2464 | self 1200x2464 | d=3.0" (to be hidden later) |
| Title | `TITLE` | "天机" sp(24) bold white, left-aligned |
| Subtitle | `SUBTITLE` | "TIANJI CONSOLE" sp(10) gray, center area |
| Status indicator | `STATUS_DOT` | Green dot + "READY" sp(11), right-aligned |
| Log line | `LOG_LINE` | "TIANJI_LINK 14:33 等待起卦指令..." cyan+gray sp(11) |
| Yao slots x6 | `SLOT_1` to `SLOT_6` | Each shows position name (初爻~上爻) + dash + thin separator line |
| Hold button | `BTN_HOLD` | "按住 · 感应天机 / HOLD 1.5s" pink border chamfer box, sp(18)+sp(10) |
| Reset button | `BTN_RESET` | "重置 / RESET" gray border chamfer box, sp(16)+sp(10) |
| Background | `BG` | Dark navy #0f1119 solid fill |
| Smoke particles | `SMOKE` | Not visible in idle state |

**Layout:**
- All elements fill full screen width (with dp(16) padding on each side)
- 6 yao slots take equal vertical space between log line and buttons
- Buttons at bottom with dp(10) spacing between them
- No WADJY watermark (MISSING -- was lost during v10.8 rewrite)

---

## Screen 2: Main Page (After Casting)

**ID: MAIN-CAST**

| Element | Change from IDLE |
|---------|-----------------|
| `STATUS_DOT` | Yellow/cyan dot + "6/6" |
| `LOG_LINE` | "TIANJI_LINK 上爻 = 1 (阳爻)" with color |
| `SLOT_1` to `SLOT_6` | Each revealed: position name + value (0/1) + yao line + type label |
| Yang yao (1) | Gold (#ffd633) solid line, background highlight, "阳爻" label |
| Yin yao (0) | Cyan (#00def2) broken line (gap in middle), "阴爻" label |
| `BTN_HOLD` | Text changes to "天机已成 / DIVINATION COMPLETE", border turns green |
| `SMOKE` | Particles may be visible if recently triggered |

**Yao line rendering:**
- Yang (1): single continuous horizontal line, gold color
- Yin (0): two segments with gap in center, cyan color
- Each slot has dark background fill when revealed
- Value digit (0/1) displayed large next to the line

---

## Screen 3: Result Page

**ID: RESULT**

| Element | Name | Current State |
|---------|------|---------------|
| Hero section | `HERO` | Left: hexagram display (6 lines), Right: name + gushi + seq + trigrams |
| Hexagram display | `HEX_DISPLAY` | 6 horizontal lines (gold solid / cyan broken), dp(90) wide, dark bg with border |
| Hexagram name | `HEX_NAME` | e.g. "噬嗑" cyan sp(38) bold |
| Gushi | `GUSHI` | e.g. "亨，利用狱" gold sp(15) |
| Sequence | `SEQ` | e.g. "第21卦 HEXAGRAM #21" gray sp(12) |
| Trigrams | `TRIG` | e.g. "坎水上 艮山下 离上震下" gray sp(12) |
| Section: 卦象含义 | `SEC_MEANING` | Cyan left-bar + horizontal rule + title sp(16) |
| Meaning body | `BODY_MEANING` | Gray-white text sp(16), wraps naturally |
| Section: 白话解读 | `SEC_BAIHUA` | Green left-bar + horizontal rule + title sp(16) |
| Baihua body | `BODY_BAIHUA` | Green text sp(16), includes hardcoded "建议：..." paragraph |
| Section: 六爻详解 | `SEC_YAO` | Purple left-bar + horizontal rule + title sp(16) |
| Yao detail x6 | `YAO_1` to `YAO_6` | Header: "初爻 [0] 阴爻" purple+colored sp(13). Body: yaoci gold + explanation gray sp(13) |
| Footer | `FOOTER` | "易以道阴阳 · 卦象仅供参考" gray sp(11) centered |
| Back button | `BTN_BACK` | "重新起卦 / NEW DIVINATION" pink border chamfer box |

**Layout:**
- Hero section fixed height dp(160), non-scrollable
- Everything below hero is in ScrollView
- Sections separated by colored left-bar + thin horizontal line
- All text left-aligned
- No WADJY watermark (MISSING)

---

## Known Issues at Baseline

| ID | Issue | Severity | Note |
|----|-------|----------|------|
| K1 | WADJY watermark missing | LOW | Lost during v10.8 rewrite, needs restoration |
| K2 | Debug label visible | LOW | Should be hidden or made toggle-able for release |
| K3 | Icon has scan lines, hard to see | MED | User reported, needs redesign |
| K4 | Splash/loading screen is small centered image | MED | Should be full-screen |
| K5 | Result page sections not visually separated enough | MED | User wants card-style modules |
| K6 | Six yao detail takes too much scroll space | LOW | User wants collapsible or separate view |
| K7 | Baihua text same size as meaning text | LOW | User wants baihua larger as primary content |

---

## Color Palette (frozen reference)

| Name | Hex | Usage |
|------|-----|-------|
| BG | #0f1119 | Background |
| CYAN | #00def2 | Yin yao, links, section bar |
| GOLD | #ffd633 | Yang yao, yaoci text |
| PINK | #f24494 | Hold button, back button |
| GREEN | #4deb66 | Ready dot, baihua text, complete state |
| PURPLE | #9e66fa | Yao detail section |
| WHITE | #e8ecf1 | Title, primary text |
| SOFT | #c8d4e0 | Body text |
| DIM | #2a3040 | Reset button, inactive elements |
| GRAY | #66708a | Secondary text, subtitles |

---

## Recovery Procedure

If a future version is worse than baseline:

```bash
# Option 1: Full revert
git checkout v10.9-baseline

# Option 2: Revert specific file
git checkout v10.9-baseline -- kivy_app/main.py

# Option 3: Compare what changed
git diff v10.9-baseline..HEAD -- kivy_app/main.py
```

---

> This is the "save point". Every future change must be better than this, or be reverted.