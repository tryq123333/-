from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
MAIN = ROOT / "app/src/main/java/com/luoke/autopiano/MainActivity.java"
LAYOUT = ROOT / "app/src/main/java/com/luoke/autopiano/InstrumentLayout.java"
STRINGS = ROOT / "app/src/main/res/values/strings.xml"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
BUILD = ROOT / "app/build.gradle"
MATH = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollGestureMath.java"
TEST = ROOT / "app/src/test/java/com/luoke/autopiano/NoteRollGestureMathTest.java"
MARKER = "SONGLE_FADE_IN_NAME_AND_AB_DIALOG_ACTIONS_V2"


def require_replace(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing expected source anchor for " + label)

service = SERVICE.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")
layout = LAYOUT.read_text(encoding="utf-8")
strings = STRINGS.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
math = MATH.read_text(encoding="utf-8")
test = TEST.read_text(encoding="utf-8")

# Fade newly entering note blocks in while preserving the existing playhead fade-out.
if "NOTE_ENTRY_FADE_IN_V1" not in note:
    old = """                // Notes stay opaque until passing the invisible playhead; then fade smoothly leftward.
                float fade = rawX2 >= playheadX ? 1f
                        : Math.max(0f, Math.min(1f, (rawX2 - left) / Math.max(1f, playheadX - left)));
                int noteAlpha = Math.max(0, Math.min(255, Math.round(255f * fade)));"""
    new = """                // NOTE_ENTRY_FADE_IN_V1: fade in from the right edge while playing; keep
                // the existing opposite fade-out as notes pass the playhead to the left.
                float fadeOut = rawX2 >= playheadX ? 1f
                        : Math.max(0f, Math.min(1f, (rawX2 - left) / Math.max(1f, playheadX - left)));
                float fadeIn = 1f;
                if (playing) {
                    fadeIn = NoteRollGestureMath.enteringNoteFadeIn(rawX1, right, density);
                }
                int noteAlpha = Math.max(0, Math.min(255,
                        Math.round(255f * fadeOut * fadeIn)));"""
    if old not in note:
        raise SystemExit("Cannot locate existing note fade-out calculation.")
    note = note.replace(old, new, 1)
    note = note.replace("NOTE_REFERENCE_ICON_AND_STAGED_ENTRANCE_V5",
                        "NOTE_REFERENCE_ICON_AND_STAGED_ENTRANCE_V5 NOTE_ENTRY_FADE_IN_V1", 1)

# Keep fade-in math deterministic and cover its endpoints in JVM tests.
if "static float enteringNoteFadeIn(" not in math:
    math = require_replace(math,
        """    static boolean pastEntranceBuffer(float noteStartX, float rightEdge, float density) {
        float reserve = 24f * Math.max(0f, density);
        return noteStartX <= rightEdge - reserve;
    }
}""",
        """    static boolean pastEntranceBuffer(float noteStartX, float rightEdge, float density) {
        float reserve = 24f * Math.max(0f, density);
        return noteStartX <= rightEdge - reserve;
    }

    static float enteringNoteFadeIn(float noteStartX, float rightEdge, float density) {
        float safeDensity = Math.max(0.01f, density);
        float travelledInside = rightEdge - noteStartX - 24f * safeDensity;
        return Math.max(0f, Math.min(1f, travelledInside / (30f * safeDensity)));
    }
}""",
        "note entrance fade helper")
if "enteringNoteFadeInStartsAtZeroAndReachesFullOpacity" not in test:
    test = test.rstrip()
    if not test.endswith("}"):
        raise SystemExit("Unexpected gesture test file ending.")
    test = test[:-1] + """

    @Test public void enteringNoteFadeInStartsAtZeroAndReachesFullOpacity() {
        assertEquals(0f, NoteRollGestureMath.enteringNoteFadeIn(176f, 200f, 1f), 0.001f);
        assertEquals(0.5f, NoteRollGestureMath.enteringNoteFadeIn(161f, 200f, 1f), 0.001f);
        assertEquals(1f, NoteRollGestureMath.enteringNoteFadeIn(146f, 200f, 1f), 0.001f);
        assertEquals(1f, NoteRollGestureMath.enteringNoteFadeIn(100f, 200f, 1f), 0.001f);
    }
}
"""

# Fix A/B actions and responsive scale bookkeeping.
if "AB_DIALOG_ACTIONS_STICKY_V1" not in service:
    # Do not use the single unkeyed View.setTag() slot for resize baselines.
    old_method_start = service.find("    private void scaleAbDialogTree(View view, float scaleX, float scaleY, boolean root) {")
    old_method_end = service.find("\n    private TextView abSettingsLabel(", old_method_start)
    if old_method_start < 0 or old_method_end < 0:
        raise SystemExit("Cannot locate A/B dialog scaling helper.")
    method = """    private void scaleAbDialogTree(View view, float scaleX, float scaleY, boolean root,
                                   Map<View, AbDialogViewBaseline> baselines) {
        AbDialogViewBaseline baseline = baselines.get(view);
        if (baseline == null) {
            baseline = new AbDialogViewBaseline(view);
            baselines.put(view, baseline);
        }
        view.setPadding(scaleAbDimension(baseline.paddingLeft, scaleX),
                scaleAbDimension(baseline.paddingTop, scaleY),
                scaleAbDimension(baseline.paddingRight, scaleX),
                scaleAbDimension(baseline.paddingBottom, scaleY));
        if (!root) {
            ViewGroup.LayoutParams lp = view.getLayoutParams();
            if (lp != null) {
                lp.width = scaleAbDimension(baseline.width, scaleX);
                lp.height = scaleAbDimension(baseline.height, scaleY);
                if (lp instanceof ViewGroup.MarginLayoutParams && baseline.hasMargins) {
                    ViewGroup.MarginLayoutParams mlp = (ViewGroup.MarginLayoutParams) lp;
                    mlp.setMargins(scaleAbDimension(baseline.marginLeft, scaleX),
                            scaleAbDimension(baseline.marginTop, scaleY),
                            scaleAbDimension(baseline.marginRight, scaleX),
                            scaleAbDimension(baseline.marginBottom, scaleY));
                }
                view.setLayoutParams(lp);
            }
        }
        if (view instanceof TextView && baseline.textSizePx > 0f) {
            ((TextView) view).setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,
                    baseline.textSizePx * Math.min(scaleX, scaleY));
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                scaleAbDialogTree(group.getChildAt(i), scaleX, scaleY, false, baselines);
            }
        }
        view.invalidate();
    }
"""
    service = service[:old_method_start] + method + service[old_method_end:]

    dialog_start = service.find("    private void showSegmentDialog() {")
    dialog_end = service.find("    private void savePracticeRangeMicros(", dialog_start)
    if dialog_start < 0 or dialog_end < 0:
        raise SystemExit("Cannot isolate A/B dialog method.")
    dialog = service[dialog_start:dialog_end]
    replacements = [
        ("card.setPadding(dp(10), dp(7), dp(10), dp(8));", "card.setPadding(dp(8), dp(5), dp(8), dp(6));"),
        ('titleRow.addView(heading, new LinearLayout.LayoutParams(0, dp(34), 1f));', 'titleRow.addView(heading, new LinearLayout.LayoutParams(0, dp(27), 1f));'),
        ('heading.setTextSize(17);', 'heading.setTextSize(14);'),
        ('close.setTextSize(21);', 'close.setTextSize(18);'),
        ('titleRow.addView(close, new LinearLayout.LayoutParams(dp(34), dp(34)));', 'titleRow.addView(close, new LinearLayout.LayoutParams(dp(29), dp(29)));'),
        ('enabled.setTextSize(15);', 'enabled.setTextSize(12);'),
        ('new LinearLayout.LayoutParams(-1, dp(31));', 'new LinearLayout.LayoutParams(-1, dp(27));'),
        ('checkParams.setMargins(0, dp(2), 0, dp(4));', 'checkParams.setMargins(0, dp(1), 0, dp(2));'),
        ('new LinearLayout.LayoutParams(-1, dp(36));', 'new LinearLayout.LayoutParams(-1, dp(29));'),
        ('inputParams.setMargins(0, dp(4), 0, 0);', 'inputParams.setMargins(0, dp(3), 0, 0);'),
        ('new LinearLayout.LayoutParams(0, dp(36), 1f);', 'new LinearLayout.LayoutParams(0, dp(30), 1f);'),
        ('bInputParams.setMargins(0, dp(8), 0, 0);', 'bInputParams.setMargins(0, dp(5), 0, 0);'),
        ('aColParams.setMargins(0, 0, dp(7), 0);', 'aColParams.setMargins(0, 0, dp(5), 0);'),
        ('bColParams.setMargins(dp(4), 0, 0, 0);', 'bColParams.setMargins(dp(3), 0, 0, 0);'),
        ('new LinearLayout.LayoutParams(0, dp(32), 1f);', 'new LinearLayout.LayoutParams(0, dp(28), 1f);'),
        ('setAParams.setMargins(0, dp(8), dp(8), 0);', 'setAParams.setMargins(0, dp(6), dp(6), 0);'),
        ('new LinearLayout.LayoutParams(0, dp(40), 1f);', 'new LinearLayout.LayoutParams(0, dp(30), 1f);'),
        ('setBParams.setMargins(dp(4), dp(8), 0, 0);', 'setBParams.setMargins(dp(3), dp(6), 0, 0);'),
        ('new LinearLayout.LayoutParams(0, dp(30), 1f);', 'new LinearLayout.LayoutParams(0, dp(26), 1f);'),
        ('resetParams.setMargins(0, dp(8), dp(6), 0);', 'resetParams.setMargins(0, dp(6), dp(5), 0);'),
        ('doneParams.setMargins(dp(6), dp(8), 0, 0);', 'doneParams.setMargins(dp(5), dp(6), 0, 0);'),
        ('resizeHandle.setTextSize(9);', 'resizeHandle.setTextSize(8);'),
        ('new LinearLayout.LayoutParams(-1, dp(15)));', 'new LinearLayout.LayoutParams(-1, dp(13)));'),
        ('int defaultWidth = Math.min(Math.max(dp(230), screenWidth - dp(36)), dp(310));', 'int defaultWidth = Math.min(Math.max(dp(200), screenWidth - dp(36)), dp(250));'),
        ('int defaultHeight = Math.min(Math.max(dp(190), screenHeight - dp(40)), dp(245));', 'int defaultHeight = Math.min(Math.max(dp(160), screenHeight - dp(40)), dp(185));'),
        ('int width = Math.max(dp(220), Math.min(Math.min(screenWidth - dp(24), dp(310)),', 'int width = Math.max(dp(190), Math.min(Math.min(screenWidth - dp(20), dp(270)),'),
        ('int height = Math.max(dp(185), Math.min(Math.min(screenHeight - dp(24), dp(245)),', 'int height = Math.max(dp(145), Math.min(Math.min(screenHeight - dp(20), dp(210)),'),
        ('body.addView(footerButtons);', 'card.addView(footerButtons);'),
    ]
    for old, new in replacements:
        if old in dialog:
            dialog = dialog.replace(old, new, 1)
        elif new not in dialog:
            raise SystemExit("Missing A/B dialog sizing/layout anchor: " + old)

    dialog = require_replace(dialog,
        '        setA.setOnClickListener(v -> aField.setText(formatSecondsField(playbackPositionMicros / 1000L)));',
        '        setA.setOnClickListener(v -> {\n            aField.setText(formatSecondsField(playbackPositionMicros / 1000L));\n            hideAbDialogKeyboard(aField, bField);\n        });',
        "set A action and hide keyboard")
    dialog = require_replace(dialog,
        '        setB.setOnClickListener(v -> bField.setText(formatSecondsField(playbackPositionMicros / 1000L)));',
        '        setB.setOnClickListener(v -> {\n            bField.setText(formatSecondsField(playbackPositionMicros / 1000L));\n            hideAbDialogKeyboard(aField, bField);\n        });',
        "set B action and hide keyboard")
    dialog = require_replace(dialog,
        '        done.setOnClickListener(v -> {\n            if (saveAbLoopSettings(enabled, aField, bField)) dismissSegmentDialog();\n        });',
        '        done.setOnClickListener(v -> {\n            hideAbDialogKeyboard(aField, bField);\n            if (saveAbLoopSettings(enabled, aField, bField)) dismissSegmentDialog();\n        });',
        "complete saves after dismissing keyboard")

    dialog = require_replace(dialog,
        '        final float[] lastAbDialogScale = {-1f, -1f};',
        '        final float[] lastAbDialogScale = {-1f, -1f};\n        final Map<View, AbDialogViewBaseline> dialogBaselines = new java.util.WeakHashMap<>();',
        "isolated A/B content baselines")
    dialog = require_replace(dialog,
        '            int measuredWidth = rightEdge - leftEdge;\n            int measuredHeight = bottomEdge - topEdge;\n            if (measuredWidth <= 0 || measuredHeight <= 0) return;\n            float scaleX = Math.max(0.62f, Math.min(1.65f, measuredWidth / (float) Math.max(1, defaultWidth)));\n            float scaleY = Math.max(0.62f, Math.min(1.55f, measuredHeight / (float) Math.max(1, defaultHeight)));',
        '            if (overlayParams.width <= 0 || overlayParams.height <= 0) return;\n            float scaleX = Math.max(0.62f, Math.min(1.65f, overlayParams.width / (float) Math.max(1, defaultWidth)));\n            float scaleY = Math.max(0.62f, Math.min(1.55f, overlayParams.height / (float) Math.max(1, defaultHeight)));',
        "scale from chosen overlay size rather than IME layout")
    dialog = require_replace(dialog,
        '            scaleAbDialogTree(card, scaleX, scaleY, true);',
        '            scaleAbDialogTree(card, scaleX, scaleY, true, dialogBaselines);',
        "map-backed dialog scaling")

    service = service[:dialog_start] + dialog + service[dialog_end:]
    service = service.replace("        label.setTextSize(15);", "        label.setTextSize(13);", 1)
    service = service.replace("        field.setTextSize(22);", "        field.setTextSize(18);", 1)
    service = service.replace("        field.setPadding(dp(12), dp(6), dp(12), dp(6));", "        field.setPadding(dp(9), dp(4), dp(9), dp(4));", 1)
    hide_helper = """    private void hideAbDialogKeyboard(EditText... fields) {
        Object token = null;
        for (EditText field : fields) {
            if (field != null) {
                if (token == null) token = field.getWindowToken();
                field.clearFocus();
            }
        }
        android.view.inputmethod.InputMethodManager imm =
                (android.view.inputmethod.InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
        if (imm != null && token != null) imm.hideSoftInputFromWindow((android.os.IBinder) token, 0);
    }

"""
    service = require_replace(service,
        '    private void savePracticeRangeMicros(long startMicros, long endMicros) {',
        hide_helper + '    private void savePracticeRangeMicros(long startMicros, long endMicros) {',
        "hide keyboard helper")
    service = service.replace(
        "AB_DIALOG_CONTENT_RESPONSIVE_V1 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_DIALOG_CONTENT_RESPONSIVE_V1 AB_DIALOG_ACTIONS_STICKY_V1 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", 1)

# 3. Rename the app and remove the 88-key option while preserving the nine-key mapping.
main = main.replace('text("洛克自动琴", 27, true)', 'text("奏乐", 27, true)')
main = main.replace('安卓触控原型 · 九键手碟与可选 88 键钢琴', '洛克王国世界九键手碟 MIDI 演奏助手')
mode_start = main.find('        TextView modeLabel = text("乐器模式", 16, true);')
mode_end = main.find('        Button enable = button("1. 开启无障碍触控服务");', mode_start)
if mode_start >= 0 and mode_end >= 0:
    main = main[:mode_start] + '        TextView modeLabel = text("当前乐器：九键手碟", 16, true);\n        content.addView(modeLabel, margin(0, 0, 0, dp(12)));\n\n' + main[mode_end:]
elif 'text("当前乐器：九键手碟", 16, true)' not in main:
    raise SystemExit("Cannot remove 88-key mode selector from the main UI.")
for imp in ('import android.widget.ArrayAdapter;\n', 'import android.widget.AdapterView;\n', 'import android.widget.Spinner;\n'):
    main = main.replace(imp, '')
main = require_replace(main,
    '                "默认九键手碟映射 A2、E3、F3、G3、A3、B3、C4、D4、E4。为未来可能出现的宽音域乐器，也提供了 88 键钢琴模式；它需要游戏实际显示完整 A0–C8 键盘，并校准四个基准点。请选择与游戏当前乐器一致的模式。\\n\\n" +',
    '                "当前仅支持九键手碟，映射为 A2、E3、F3、G3、A3、B3、C4、D4、E4。先完成九键校准，再选择曲谱并检查音域；超出九键音域的曲谱可尝试移调。\\n\\n" +',
    "update app help to nine-key only")
main = main.replace('"当前布局已校准 " + InstrumentLayout.calibratedCount(prefs) + "/" + InstrumentLayout.calibrationSteps(prefs) +\n                (InstrumentLayout.MODE_PIANO88.equals(InstrumentLayout.selectedMode(prefs)) ? " 个钢琴基准点" : " 个音符") +',
                    '"当前九键手碟已校准 " + InstrumentLayout.calibratedCount(prefs) + "/9 个音符" +')
main = require_replace(main,
    '        calibrateButton.setText(InstrumentLayout.MODE_PIANO88.equals(InstrumentLayout.selectedMode(prefs))\n                ? "3. 准备 88 键校准（回游戏点悬浮图标）" : "3. 准备九键校准（回游戏点悬浮图标）");',
    '        calibrateButton.setText("3. 准备九键校准（回游戏点悬浮图标）");',
    "simplify calibration action label")
main = require_replace(main,
    '                text.append(InstrumentLayout.MODE_PIANO88.equals(InstrumentLayout.selectedMode(prefs))\n                        ? "音域检查：通过（全部音符在 A0–C8 范围内）"\n                        : "音域检查：通过（全部音符都有九键映射）");',
    '                text.append("音域检查：通过（全部音符都有九键映射）");',
    "simplify nine-key range description")
layout = require_replace(layout,
    '    public static String selectedMode(SharedPreferences prefs) {\n        return prefs.getString(KEY_LAYOUT_MODE, MODE_NINE);\n    }',
    '    public static String selectedMode(SharedPreferences prefs) {\n        String previousMode = prefs.getString(KEY_LAYOUT_MODE, MODE_NINE);\n        if (!MODE_NINE.equals(previousMode)) {\n            prefs.edit().putString(KEY_LAYOUT_MODE, MODE_NINE).apply();\n        }\n        return MODE_NINE;\n    }',
    "force and persist the remaining nine-key instrument mode")

for name in ("洛克乐器演奏", "洛克自动琴"):
    main = main.replace(name, "奏乐")
    service = service.replace(name, "奏乐")
    note = note.replace(name, "奏乐")
strings = strings.replace("洛克乐器演奏", "奏乐")
strings = strings.replace("用于把所选 MIDI 曲谱转换为游戏乐器上的触控点击。仅在用户启动演奏时输入，可随时暂停或停止。",
                          "奏乐将所选 MIDI 曲谱转换为游戏九键手碟上的触控点击。仅在用户启动演奏时输入，可随时暂停或停止。")
manifest = manifest.replace('android:label="洛克自动琴触控服务"', 'android:label="奏乐触控服务"')

version_match = re.search(r'versionCode\s+(\d+)', build)
if not version_match:
    raise SystemExit("Cannot find versionCode.")
if int(version_match.group(1)) < 11:
    build = build[:version_match.start(1)] + "11" + build[version_match.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.1.0'", build, count=1)

checks = {
    "note entrance fade-in and playhead fade-out": "NOTE_ENTRY_FADE_IN_V1" in note and "fadeOut * fadeIn" in note and "enteringNoteFadeIn(" in math,
    "fade-in alpha regression test": "enteringNoteFadeInStartsAtZeroAndReachesFullOpacity" in test,
    "A/B complete is sticky outside ScrollView": "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5" in service or "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or ("card.addView(footerButtons);" in service and "body.addView(footerButtons);" not in service),
    "A/B scaling avoids overwriting View tags": "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5" in service or "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or ("view.setTag(baseline)" not in service and "dialogBaselines" in service),
    "A/B sizing follows overlay size rather than keyboard layout": "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5" in service or "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or "overlayParams.width / (float) Math.max(1, defaultWidth)" in service,
    "A/B set point hides keyboard": "hideAbDialogKeyboard(aField, bField)" in service,
    "new brand visible in app": 'text("奏乐", 27, true)' in main and "<string name=\"app_name\">奏乐</string>" in strings,
    "88-key UI is removed": "88 键钢琴" not in main and "88 键钢琴模式" not in main and 'String[] modes =' not in main,
    "nine-key mode migrated": "return MODE_NINE;" in layout and "prefs.edit().putString(KEY_LAYOUT_MODE, MODE_NINE).apply();" in layout,
    "note roll remains independently controllable": "noteRollTemporarilyHiddenByCollapse" not in service,
    "original game key icons retained": "drawOriginalGameKeyIcon(canvas" in note and "R.drawable.note_key_atlas" in note,
    "rewind and seek guard retained": "ROLL_REWIND_NEXT_TO_AB_V7" in note and "playbackUiGeneration" in service,
    "live search/batch import/song removal retained": "SONG_PICKER_LIVE_SEARCH_V1" in service and "BATCH_MIDI_IMPORT_V1" in main and "ROLL_SPEED_CONTROL_AND_SONG_REMOVAL_V1" in service,
    "white/black launcher icon retained": 'android:icon="@drawable/launcher_luoke_v2"' in manifest,
    "new app version": "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5" in service or ("versionCode 11" in build and "versionName '1.1.0'" in build),
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Preserved-feature audit failed: " + "; ".join(failed))

SERVICE.write_text(service, encoding="utf-8")
NOTE.write_text(note, encoding="utf-8")
MATH.write_text(math, encoding="utf-8")
TEST.write_text(test, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")
LAYOUT.write_text(layout, encoding="utf-8")
STRINGS.write_text(strings, encoding="utf-8")
MANIFEST.write_text(manifest, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")
print("Applied note fade-in, 奏乐 branding, nine-key-only UI, reliable A/B actions and smaller responsive dialog.")
print("AUDIT OK: " + "; ".join(checks.keys()))
