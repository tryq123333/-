from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
MAIN = ROOT / "app/src/main/java/com/luoke/autopiano/MainActivity.java"
BUILD = ROOT / "app/build.gradle"
HELPER = ROOT / "app/src/main/java/com/luoke/autopiano/AbLoopRepeatPolicy.java"
TEST = ROOT / "app/src/test/java/com/luoke/autopiano/AbLoopRepeatPolicyTest.java"
MARKER = "AB_REPEAT_CALIBRATION_NOTE_VISIBILITY_V19"


def replace_once(source, old, new, label):
    if new in source:
        return source
    if old in source:
        return source.replace(old, new, 1)
    raise SystemExit("Missing source anchor: " + label)


service = SERVICE.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

service = replace_once(
    service,
    '    private static final String KEY_AB_LOOP_ENABLED = "ab_loop_enabled";\n',
    '    private static final String KEY_AB_LOOP_ENABLED = "ab_loop_enabled";\n'
    '    private static final String KEY_AB_REPEAT_ENABLED = "ab_loop_repeat_enabled"; // ' + MARKER + '\n',
    "add repeat preference")

main = replace_once(
    main,
    '        reset.setOnClickListener(v -> {\n'
    '            InstrumentLayout.clearCurrentLayout(prefs);\n'
    '            refreshUi();\n'
    '            Toast.makeText(this, "音符位置已清除", Toast.LENGTH_SHORT).show();\n'
    '        });',
    '        reset.setOnClickListener(v -> {\n'
    '            InstrumentLayout.clearCurrentLayout(prefs);\n'
    '            MusicAccessibilityService service = MusicAccessibilityService.getInstance();\n'
    '            if (service != null) service.onCalibrationReset();\n'
    '            refreshUi();\n'
    '            Toast.makeText(this, "音符位置已清除；请回到游戏点悬浮面板中的“校准”重新校准", Toast.LENGTH_LONG).show();\n'
    '        });',
    "refresh floating controls after calibration reset")
if MARKER not in main:
    main = main.replace("public class MainActivity extends Activity {",
                        "public class MainActivity extends Activity { // " + MARKER, 1)

old_calibration = '''        public void prepareCalibration() {
        mainHandler.post(() -> {
            if (calibrating) {
                toast("正在校准，请直接点击游戏中的音符位置。");
                return;
            }
            toast("请切回洛克王国：世界，点悬浮音乐图标展开控制，再点“校准”。这样不会被本应用界面挡住。");
        });
    }
'''
new_calibration = '''    /** Refresh the floating controls after the main screen resets calibration. */
    public void onCalibrationReset() {
        mainHandler.post(() -> {
            if (calibrating) {
                calibrating = false;
                removeOverlay(calibrationOverlay);
                calibrationOverlay = null;
            }
            showControlPanel();
            toast("校准入口已刷新；请切回游戏，点悬浮面板中的“校准”逐个重新校准。");
        });
    }

    public void prepareCalibration() {
        mainHandler.post(() -> {
            if (calibrating) {
                toast("正在校准，请直接点击游戏中的音符位置。");
                return;
            }
            showControlPanel();
            if (isCurrentLayoutCalibrated()) {
                toast("当前乐器仍有完整校准位置；请先点“重置当前乐器的校准位置”，再重新校准。");
            } else {
                toast("校准入口已刷新。请切回洛克王国：世界，点悬浮面板中的“校准”，按提示逐个点击音符。");
            }
        });
    }
'''
service = replace_once(service, old_calibration, new_calibration, "repair recalibration entry point")
service = replace_once(
    service,
    '                @Override public void onToggleAbLoop() { toggleAbLoopEnabled(); }\n',
    '                @Override public void onToggleAbLoop() { toggleAbLoopEnabled(); }\n'
    '                @Override public void onToggleAbRepeat() { toggleAbRepeatEnabled(); }\n',
    "connect repeat-button callback")

service = replace_once(
    service,
    '        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, enabled).apply();\n',
    '        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, enabled)\n'
    '                .putBoolean(KEY_AB_REPEAT_ENABLED, false).apply();\n',
    "reset repeat mode when toolbar A/B changes")
service = replace_once(
    service,
    '        if (noteRollView != null) {\n'
    '            noteRollView.setAbLoopEnabled(enabled);\n'
    '            refreshNoteRollData();\n'
    '        }\n'
    '        toast(enabled ? "A/B循环已开启；长按谱面上的 A/B循环 可编辑起止点。"',
    '        if (noteRollView != null) {\n'
    '            noteRollView.setAbLoopEnabled(enabled);\n'
    '            noteRollView.setAbLoopRepeatEnabled(false);\n'
    '            refreshNoteRollData();\n'
    '        }\n'
    '        toast(enabled ? "A/B循环已开启；长按谱面上的 A/B循环 可编辑起止点。"',
    "reset repeat button visual after A/B toggle")

if "private void toggleAbRepeatEnabled()" not in service:
    repeat_method = '''    private void toggleAbRepeatEnabled() {
        if (!prefs.getBoolean(KEY_AB_LOOP_ENABLED, false)) return;
        boolean enabled = !prefs.getBoolean(KEY_AB_REPEAT_ENABLED, false);
        prefs.edit().putBoolean(KEY_AB_REPEAT_ENABLED, enabled).apply();
        if (noteRollView != null) noteRollView.setAbLoopRepeatEnabled(enabled);
        toast(enabled ? "A/B片段循环播放已开启。" : "A/B片段播放一遍后停止。");
    }

'''
    service = replace_once(service, "    private void applyAbLoopEnabledFromDialog(boolean loopEnabled) {",
                           repeat_method + "    private void applyAbLoopEnabledFromDialog(boolean loopEnabled) {",
                           "add repeat toggle handler")
service = replace_once(
    service,
    '        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled).apply();\n',
    '        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled)\n'
    '                .putBoolean(KEY_AB_REPEAT_ENABLED, loopEnabled && prefs.getBoolean(KEY_AB_REPEAT_ENABLED, false))\n'
    '                .apply();\n',
    "clear repeat if A/B is disabled in settings")
service = replace_once(
    service,
    '        boolean persisted = prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled)\n'
    '                .putLong(KEY_RANGE_START_MS, startMs).putLong(KEY_RANGE_END_MS, endMs).commit();',
    '        boolean persisted = prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled)\n'
    '                .putBoolean(KEY_AB_REPEAT_ENABLED, loopEnabled && prefs.getBoolean(KEY_AB_REPEAT_ENABLED, false))\n'
    '                .putLong(KEY_RANGE_START_MS, startMs).putLong(KEY_RANGE_END_MS, endMs).commit();',
    "persist repeat flag with A/B settings")

service = replace_once(
    service,
    '        noteRollView.setAbLoopEnabled(loopEnabled);\n'
    '        noteRollView.setPracticeModeEnabled(practiceModeEnabled);',
    '        noteRollView.setAbLoopEnabled(loopEnabled);\n'
    '        noteRollView.setAbLoopRepeatEnabled(prefs.getBoolean(KEY_AB_REPEAT_ENABLED, false));\n'
    '        noteRollView.setPracticeModeEnabled(practiceModeEnabled);',
    "sync repeat state when refreshing roll")

old_worker = '''                if (index >= song.notes.size() || song.notes.get(index).startMicros >= rangeEndMicros) {
                    if (!stopRequested && prefs.getBoolean(KEY_AB_LOOP_ENABLED, false)) {
                        int loopStartIndex = firstNoteAtOrAfter(song, rangeStartMicros);
                        if (loopStartIndex >= song.notes.size()
                                || song.notes.get(loopStartIndex).startMicros >= rangeEndMicros) break;
                        baseMicros = rangeStartMicros;
                        playbackBaseMicros = baseMicros;
                        playbackPositionMicros = baseMicros;
                        playbackStartMs = SystemClock.elapsedRealtime();
                        pausedDurationMs = 0L;
                        index = loopStartIndex;
                        final long loopRestart = baseMicros;
                        mainHandler.post(() -> {
                            if (noteRollView != null) noteRollView.setCursor(loopRestart, playbackActive && !paused);
                            refreshMiniPlaybackButton();
                        });
                        continue;
                    }
                    break;
                }
'''
new_worker = '''                if (index >= song.notes.size() || song.notes.get(index).startMicros >= rangeEndMicros) {
                    if (!stopRequested && prefs.getBoolean(KEY_AB_LOOP_ENABLED, false)) {
                        // Wait for B even if the final note starts earlier; then either repeat or stop.
                        long endOffsetMs = Math.round(Math.max(0L, rangeEndMicros - baseMicros)
                                / 1000.0 * (100.0 / Math.max(1, speedPercent)));
                        if (!awaitTarget(endOffsetMs, observedSeekVersion)) {
                            if (stopRequested) break;
                            continue;
                        }
                        if (seekRequestVersion != observedSeekVersion) continue;
                        boolean shouldRepeat = AbLoopRepeatPolicy.shouldRepeat(
                                prefs.getBoolean(KEY_AB_LOOP_ENABLED, false),
                                prefs.getBoolean(KEY_AB_REPEAT_ENABLED, false));
                        if (shouldRepeat && !stopRequested) {
                            int loopStartIndex = firstNoteAtOrAfter(song, rangeStartMicros);
                            if (loopStartIndex >= song.notes.size()
                                    || song.notes.get(loopStartIndex).startMicros >= rangeEndMicros) break;
                            baseMicros = rangeStartMicros;
                            playbackBaseMicros = baseMicros;
                            playbackPositionMicros = baseMicros;
                            playbackStartMs = SystemClock.elapsedRealtime();
                            pausedDurationMs = 0L;
                            index = loopStartIndex;
                            final long loopRestart = baseMicros;
                            mainHandler.post(() -> {
                                if (noteRollView != null) noteRollView.setCursor(loopRestart, playbackActive && !paused);
                                refreshMiniPlaybackButton();
                            });
                            continue;
                        }
                    }
                    break;
                }
'''
service = replace_once(service, old_worker, new_worker, "wait until B then repeat or stop")
if MARKER not in service:
    service = service.replace("public class MusicAccessibilityService extends AccessibilityService {",
                              "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER, 1)

note = replace_once(note, "        void onToggleAbLoop();\n",
                    "        void onToggleAbLoop();\n        void onToggleAbRepeat();\n",
                    "add repeat callback")
note = replace_once(note, "    private boolean abLoopEnabled;\n",
                    "    private boolean abLoopEnabled;\n    private boolean abRepeatEnabled;\n",
                    "store repeat toggle state")
note = replace_once(note, "    private static final int TOUCH_PRACTICE = 11;\n",
                    "    private static final int TOUCH_PRACTICE = 11;\n    private static final int TOUCH_AB_REPEAT = 12;\n",
                    "add repeat touch mode")
note = replace_once(
    note,
    '    public void setAbLoopEnabled(boolean enabled) {\n'
    '        abLoopEnabled = enabled;\n'
    '        invalidate();\n'
    '    }\n',
    '    public void setAbLoopEnabled(boolean enabled) {\n'
    '        abLoopEnabled = enabled;\n'
    '        if (!enabled) abRepeatEnabled = false;\n'
    '        invalidate();\n'
    '    }\n\n'
    '    public void setAbLoopRepeatEnabled(boolean enabled) {\n'
    '        abRepeatEnabled = abLoopEnabled && enabled;\n'
    '        invalidate();\n'
    '    }\n',
    "expose repeat switch to view")
note = replace_once(
    note,
    '                long noteEnd = Math.min(rangeEndMicros, noteStart + noteDuration);\n'
    '                if (noteEnd < visibleStart) continue;\n'
    '                if (noteStart < rangeStartMicros || noteStart >= rangeEndMicros) continue;',
    '                long noteEnd = Math.min(abLoopEnabled ? rangeEndMicros : durationMicros, noteStart + noteDuration);\n'
    '                if (noteEnd < visibleStart) continue;\n'
    '                if (abLoopEnabled && (noteStart < rangeStartMicros || noteStart >= rangeEndMicros)) continue;',
    "show all notes when A/B playback is disabled")
note = replace_once(
    note,
    '        drawHeaderChip(canvas, new RectF(left, 96 * density, left + 61 * density, 114 * density),\n'
    '                rangeEditing ? "完成" : "A/B循环",\n'
    '                rangeEditing ? 0xff4c8d80 : (abLoopEnabled ? 0xff477960 : 0xff455667), density);\n',
    '        drawHeaderChip(canvas, new RectF(left, 96 * density, left + 61 * density, 114 * density),\n'
    '                rangeEditing ? "完成" : "A/B循环",\n'
    '                rangeEditing ? 0xff4c8d80 : (abLoopEnabled ? 0xff477960 : 0xff455667), density);\n'
    '        if (abLoopEnabled && w >= 100 * density) {\n'
    '            drawHeaderChip(canvas, new RectF(71 * density, 96 * density, 95 * density, 114 * density),\n'
    '                    "♻️", abRepeatEnabled ? 0xff9dd8b8 : 0x667f929b, density);\n'
    '        }\n',
    "draw dim/highlight repeat chip beside A/B")
note = replace_once(
    note,
    '                } else if (y >= 96 * density && y < 115 * density\n'
    '                        && x >= 5 * density && x <= Math.min(69 * density, w - 8 * density)) {\n'
    '                    touchMode = TOUCH_SEGMENT;\n'
    '                    segmentDownTimeMs = event.getEventTime();\n'
    '                } else if (touchEdges != 0) {',
    '                } else if (y >= 96 * density && y < 115 * density\n'
    '                        && x >= 5 * density && x <= Math.min(69 * density, w - 8 * density)) {\n'
    '                    touchMode = TOUCH_SEGMENT;\n'
    '                    segmentDownTimeMs = event.getEventTime();\n'
    '                } else if (y >= 96 * density && y < 115 * density\n'
    '                        && x > 69 * density && x <= Math.min(96 * density, w - 5 * density)) {\n'
    '                    touchMode = TOUCH_AB_REPEAT;\n'
    '                } else if (touchEdges != 0) {',
    "claim tap in repeat-chip hitbox")
note = replace_once(
    note,
    '                } else if (touchMode == TOUCH_SEGMENT && !gestureMoved) {\n'
    '                    if (interactionListener != null) {\n'
    '                        long heldMs = event.getEventTime() - segmentDownTimeMs;\n'
    '                        if (rangeEditing || heldMs >= 450L) interactionListener.onEditSegment();\n'
    '                        else interactionListener.onToggleAbLoop();\n'
    '                    }\n'
    '                } else if (touchMode == TOUCH_RANGE_EDIT) {',
    '                } else if (touchMode == TOUCH_SEGMENT && !gestureMoved) {\n'
    '                    if (interactionListener != null) {\n'
    '                        long heldMs = event.getEventTime() - segmentDownTimeMs;\n'
    '                        if (rangeEditing || heldMs >= 450L) interactionListener.onEditSegment();\n'
    '                        else interactionListener.onToggleAbLoop();\n'
    '                    }\n'
    '                } else if (touchMode == TOUCH_AB_REPEAT && !gestureMoved && abLoopEnabled) {\n'
    '                    if (interactionListener != null) interactionListener.onToggleAbRepeat();\n'
    '                } else if (touchMode == TOUCH_RANGE_EDIT) {',
    "toggle repeat when repeat chip is tapped")
if MARKER not in note:
    note = note.replace("PRACTICE_ROLL_PLAYHEAD_RING_BUTTON_SWAP_V14",
                        "PRACTICE_ROLL_PLAYHEAD_RING_BUTTON_SWAP_V14 " + MARKER, 1)

HELPER.parent.mkdir(parents=True, exist_ok=True)
TEST.parent.mkdir(parents=True, exist_ok=True)
HELPER.write_text(
    "package com.luoke.autopiano;\n\n"
    "/** Decides whether a completed A/B pass should return to A. */\n"
    "final class AbLoopRepeatPolicy {\n"
    "    private AbLoopRepeatPolicy() { }\n"
    "    static boolean shouldRepeat(boolean abLoopEnabled, boolean repeatEnabled) {\n"
    "        return abLoopEnabled && repeatEnabled;\n"
    "    }\n"
    "}\n", encoding="utf-8")
TEST.write_text(
    "package com.luoke.autopiano;\n\n"
    "import org.junit.Test;\nimport static org.junit.Assert.*;\n\n"
    "public class AbLoopRepeatPolicyTest {\n"
    "    @Test public void repeatsOnlyWhenBothAbAndRepeatAreEnabled() {\n"
    "        assertTrue(AbLoopRepeatPolicy.shouldRepeat(true, true));\n"
    "    }\n"
    "    @Test public void stopsAfterOnePassWhenRepeatIsOff() {\n"
    "        assertFalse(AbLoopRepeatPolicy.shouldRepeat(true, false));\n"
    "    }\n"
    "    @Test public void neverRepeatsWhenAbIsOff() {\n"
    "        assertFalse(AbLoopRepeatPolicy.shouldRepeat(false, true));\n"
    "        assertFalse(AbLoopRepeatPolicy.shouldRepeat(false, false));\n"
    "    }\n"
    "}\n", encoding="utf-8")

SERVICE.write_text(service, encoding="utf-8")
NOTE.write_text(note, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode")
if int(m.group(1)) < 28:
    build = build[:m.start(1)] + "28" + build[m.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.9'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
checks = {
    "calibration reset refreshes overlay": "service.onCalibrationReset()" in main and "public void onCalibrationReset()" in service,
    "repeat defaults off": 'KEY_AB_REPEAT_ENABLED = "ab_loop_repeat_enabled"' in service and '.putBoolean(KEY_AB_REPEAT_ENABLED, false)' in service,
    "repeat toggle callback wired": "onToggleAbRepeat() { toggleAbRepeatEnabled(); }" in service and "void onToggleAbRepeat();" in note,
    "repeat chip is conditional and has a dim state": 'if (abLoopEnabled && w >= 100 * density)' in note and 'abRepeatEnabled ? 0xff9dd8b8 : 0x667f929b' in note,
    "playback waits to B and gates repeats": "awaitTarget(endOffsetMs, observedSeekVersion)" in service and "AbLoopRepeatPolicy.shouldRepeat" in service,
    "full-song notes shown with A/B disabled": "if (abLoopEnabled && (noteStart < rangeStartMicros || noteStart >= rangeEndMicros)) continue;" in note and "Math.min(abLoopEnabled ? rangeEndMicros : durationMicros" in note,
    "repeat-policy unit tests exist": "stopsAfterOnePassWhenRepeatIsOff" in TEST.read_text(encoding="utf-8"),
    "version bumped to 1.9.9 / code 28": "versionName '1.9.9'" in build and "versionCode 28" in build,
    "V19 marker present": MARKER in service and MARKER in note and MARKER in main,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V19 audit failed: " + "; ".join(failed))
print("V19 patch applied; all postcondition checks passed: " + "; ".join(checks))
