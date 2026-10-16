from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
JAVA_TEST = ROOT / "app/src/test/java/com/luoke/autopiano/AbLoopRangeMathTest.java"
JAVA_HELPER = ROOT / "app/src/main/java/com/luoke/autopiano/AbLoopRangeMath.java"
MARKER = "AB_DIALOG_VISIBLE_SAVE_FEEDBACK_V9"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

if MARKER not in service:
    service = replace_once(
        service,
        "    private CheckBox abDialogEnabledCheckbox;\n",
        "    private CheckBox abDialogEnabledCheckbox;\n"
        "    private TextView abDialogStatusView;\n",
        "add persistent in-dialog save status reference"
    )

    status_helper = r'''    private void setAbDialogStatus(String message, int color) {
        TextView status = abDialogStatusView;
        if (status == null) {
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
            return;
        }
        status.setText(message);
        status.setTextColor(color);
        status.setVisibility(View.VISIBLE);
        status.invalidate();
        status.requestLayout();
    }

'''
    service = replace_once(
        service,
        "    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {",
        status_helper + "    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {",
        "add persistent save feedback helper"
    )

    # Avoid rejecting the displayed end time when the actual MIDI duration has
    # sub-centisecond precision but the UI presents seconds rounded to 2 decimals.
    helper_source = r'''package com.luoke.autopiano;

/** Handles the A/B dialog's centisecond display rounding at the song end. */
final class AbLoopRangeMath {
    private static final long DISPLAY_ROUNDING_TOLERANCE_MS = 5L;

    private AbLoopRangeMath() { }

    /**
     * Returns the requested end time if valid, clamps only the tiny overrun that can
     * arise when a millisecond duration is rendered as a two-decimal seconds value,
     * and returns -1 for a genuine out-of-range value.
     */
    static long clampRoundedEndMs(long requestedEndMs, long durationMs) {
        if (durationMs <= 0L || requestedEndMs < 0L) return -1L;
        if (requestedEndMs <= durationMs) return requestedEndMs;
        long overrun = requestedEndMs - durationMs;
        return overrun <= DISPLAY_ROUNDING_TOLERANCE_MS ? durationMs : -1L;
    }
}
'''
    if JAVA_HELPER.exists():
        existing_helper = JAVA_HELPER.read_text(encoding="utf-8")
        if "clampRoundedEndMs" not in existing_helper:
            raise SystemExit("AbLoopRangeMath.java already exists with unexpected contents.")
    else:
        JAVA_HELPER.parent.mkdir(parents=True, exist_ok=True)
        JAVA_HELPER.write_text(helper_source, encoding="utf-8")

    test_source = r'''package com.luoke.autopiano;

import org.junit.Test;
import static org.junit.Assert.*;

public class AbLoopRangeMathTest {
    @Test public void clampsOnlyCentisecondDisplayRoundingAtSongEnd() {
        assertEquals(69_536L, AbLoopRangeMath.clampRoundedEndMs(69_540L, 69_536L));
        assertEquals(69_535L, AbLoopRangeMath.clampRoundedEndMs(69_540L, 69_535L));
    }

    @Test public void leavesAnEndInsideDurationUnchanged() {
        assertEquals(69_530L, AbLoopRangeMath.clampRoundedEndMs(69_530L, 69_536L));
        assertEquals(69_536L, AbLoopRangeMath.clampRoundedEndMs(69_536L, 69_536L));
    }

    @Test public void rejectsEndTimesMeaningfullyBeyondDuration() {
        assertEquals(-1L, AbLoopRangeMath.clampRoundedEndMs(69_542L, 69_536L));
        assertEquals(-1L, AbLoopRangeMath.clampRoundedEndMs(69_546L, 69_536L));
    }

    @Test public void rejectsInvalidDurationsAndNegativeEndTimes() {
        assertEquals(-1L, AbLoopRangeMath.clampRoundedEndMs(100L, 0L));
        assertEquals(-1L, AbLoopRangeMath.clampRoundedEndMs(-1L, 100L));
    }
}
'''
    if JAVA_TEST.exists():
        existing_test = JAVA_TEST.read_text(encoding="utf-8")
        if "clampsOnlyCentisecondDisplayRoundingAtSongEnd" not in existing_test:
            raise SystemExit("AbLoopRangeMathTest.java already exists with unexpected contents.")
    else:
        JAVA_TEST.parent.mkdir(parents=True, exist_ok=True)
        JAVA_TEST.write_text(test_source, encoding="utf-8")

    # Keep the same method/signature for existing callers and audits; make each
    # failure visible inside the dialog rather than relying on a transient Toast.
    save_start = service.find("    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {")
    save_end = service.find("\n    private String formatSecondsField(", save_start)
    if save_start < 0 or save_end < 0:
        raise SystemExit("Cannot isolate saveAbLoopSettings.")
    save_method = service[save_start:save_end]

    save_method = replace_once(
        save_method,
        '            toast("请先导入 MIDI 曲谱。");\n            return false;',
        '            setAbDialogStatus("请先导入 MIDI 曲谱。", 0xffb3261e);\n'
        '            toast("请先导入 MIDI 曲谱。");\n            return false;',
        "show missing-song error inline"
    )
    save_method = replace_once(
        save_method,
        '            toast("请输入有效的 A、B 时间（秒）。");\n            return false;',
        '            setAbDialogStatus("请输入有效的 A、B 时间（秒）。", 0xffb3261e);\n'
        '            toast("请输入有效的 A、B 时间（秒）。");\n            return false;',
        "show invalid-input error inline"
    )
    old_validation = '''        if (startMs >= durationMs || endMs > durationMs || endMs <= startMs) {
            toast("B 终点必须大于 A 起点，并且不能超过歌曲时长。");
            return false;
        }'''
    new_validation = '''        if (startMs >= durationMs) {
            setAbDialogStatus("A 起点必须早于歌曲结束。", 0xffb3261e);
            toast("A 起点必须早于歌曲结束。");
            return false;
        }
        long clampedEndMs = AbLoopRangeMath.clampRoundedEndMs(endMs, durationMs);
        if (clampedEndMs < 0L) {
            setAbDialogStatus("B 终点不能超过歌曲时长。", 0xffb3261e);
            toast("B 终点不能超过歌曲时长。");
            return false;
        }
        endMs = clampedEndMs;
        if (endMs <= startMs) {
            setAbDialogStatus("B 终点必须大于 A 起点。", 0xffb3261e);
            toast("B 终点必须大于 A 起点。");
            return false;
        }'''
    save_method = replace_once(save_method, old_validation, new_validation, "clamp rounded duration and validate A/B")
    save_method = replace_once(
        save_method,
        '            toast("A/B 保存失败，请重试；设置窗口已保留。");\n            return false;',
        '            setAbDialogStatus("A/B 保存失败，请重试；设置窗口已保留。", 0xffb3261e);\n'
        '            toast("A/B 保存失败，请重试；设置窗口已保留。");\n            return false;',
        "show commit/readback failure inline"
    )
    service = service[:save_start] + save_method + service[save_end:]

    # Clamp the runtime end to the actual song duration, not its rounded-up millisecond.
    service = replace_once(
        service,
        "        long effectiveEnd = loopEnabled ? endMicros : durationMs * 1000L;",
        "        long effectiveEnd = loopEnabled ? Math.min(endMicros, currentSong.durationMicros)\n"
        "                : currentSong.durationMicros;",
        "clamp active loop end to real MIDI duration"
    )

    dialog_start = service.find("    private void showSegmentDialog() {")
    dialog_end = service.find("    private void hideAbDialogKeyboard(", dialog_start)
    if dialog_start < 0 or dialog_end < 0:
        raise SystemExit("Cannot isolate A/B dialog.")
    dialog = service[dialog_start:dialog_end]

    status_block = '''        TextView status = new TextView(this);
        status.setText("修改 A/B 后点完成保存。");
        status.setTextColor(0xff718077);
        status.setTextSize(9);
        status.setGravity(Gravity.CENTER);
        status.setMaxLines(2);
        status.setMinHeight(dp(22));
        status.setMinimumHeight(dp(22));
        status.setPadding(dp(2), 0, dp(2), 0);
        status.setFocusable(false);
        content.addView(status, new LinearLayout.LayoutParams(-1, dp(22)));
        abDialogStatusView = status;

'''
    dialog = replace_once(
        dialog,
        '        TextView resizeHandle = new TextView(this);\n        resizeHandle.setText("↘ 拖动调整大小");',
        status_block + '        TextView resizeHandle = new TextView(this);\n        resizeHandle.setText("↘ 拖动调整大小");',
        "add persistent in-dialog status line"
    )

    old_done = '''        done.setOnClickListener(v -> {
            // Immediate feedback proves that the visible Done hit target actually fired.
            Toast.makeText(this, "已收到完成操作，正在保存 A/B 设置…", Toast.LENGTH_SHORT).show();
            hideAbDialogKeyboard(aField, bField);
            if (saveAbLoopSettings(enabled, aField, bField)) {
                long savedStartMs = prefs.getLong(KEY_RANGE_START_MS, -1L);
                long savedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
                boolean savedLoop = prefs.getBoolean(KEY_AB_LOOP_ENABLED, !enabled.isChecked());
                String message = "A/B 设置成功：A=" + formatSecondsField(savedStartMs)
                        + " 秒，B=" + formatSecondsField(savedEndMs)
                        + " 秒；循环" + (savedLoop ? "已开启。" : "未开启。");
                dismissSegmentDialog();
                toast(message);
            }
        });'''
    new_done = '''        done.setOnClickListener(v -> {
            // The inline status survives toast timing and makes the exact save path visible.
            setAbDialogStatus("已收到完成操作，正在保存 A/B 设置…", 0xff547c68);
            Toast.makeText(this, "已收到完成操作，正在保存 A/B 设置…", Toast.LENGTH_SHORT).show();
            done.setEnabled(false);
            done.setText("保存中…");
            hideAbDialogKeyboard(aField, bField);
            try {
                if (saveAbLoopSettings(enabled, aField, bField)) {
                    long savedStartMs = prefs.getLong(KEY_RANGE_START_MS, -1L);
                    long savedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
                    boolean savedLoop = prefs.getBoolean(KEY_AB_LOOP_ENABLED, !enabled.isChecked());
                    String message = "A/B 设置成功：A=" + formatSecondsField(savedStartMs)
                            + " 秒，B=" + formatSecondsField(savedEndMs)
                            + " 秒；循环" + (savedLoop ? "已开启。" : "未开启。");
                    setAbDialogStatus("保存成功：A=" + formatSecondsField(savedStartMs)
                            + " 秒，B=" + formatSecondsField(savedEndMs) + " 秒。", 0xff28734c);
                    done.setText("已保存");
                    toast(message);
                    // Keep the success state visible long enough to read it before closing.
                    mainHandler.postDelayed(() -> {
                        if (segmentOverlay == card) dismissSegmentDialog();
                    }, 1800L);
                } else {
                    done.setEnabled(true);
                    done.setText("完成");
                }
            } catch (RuntimeException ex) {
                android.util.Log.e("LuokeAB", "Unexpected exception while saving A/B settings.", ex);
                setAbDialogStatus("保存异常，窗口已保留，请重试。", 0xffb3261e);
                toast("保存异常，窗口已保留，请重试。");
                done.setEnabled(true);
                done.setText("完成");
            }
        });'''
    dialog = replace_once(dialog, old_done, new_done, "make save progress and result persistent")
    service = service[:dialog_start] + dialog + service[dialog_end:]

    # Clear the view reference only after the overlay has been removed.
    service = replace_once(
        service,
        "        abDialogEnabledCheckbox = null;\n        updatingAbDialogEnabledCheckbox = false;",
        "        abDialogEnabledCheckbox = null;\n        abDialogStatusView = null;\n        updatingAbDialogEnabledCheckbox = false;",
        "clear save status reference on dismiss"
    )

    service = service.replace(
        "AB_LOOP_TWO_WAY_DIALOG_SYNC_V8 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_LOOP_TWO_WAY_DIALOG_SYNC_V8 " + MARKER + " NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        1
    )
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER,
            1
        )

# This step runs after V7/V8 normalize the app version on every workflow run.
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode.")
if int(m.group(1)) < 18:
    build = build[:m.start(1)] + "18" + build[m.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.8.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
dialog_start = service.find("    private void showSegmentDialog() {")
dialog_end = service.find("    private void hideAbDialogKeyboard(", dialog_start)
dialog = service[dialog_start:dialog_end]
save_start = service.find("    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {")
save_end = service.find("\n    private String formatSecondsField(", save_start)
save_method = service[save_start:save_end]
checks = {
    "inline status field is connected to dialog": "abDialogStatusView = status;" in dialog and "setAbDialogStatus(String message, int color)" in service,
    "Done click immediately exposes progress": "setAbDialogStatus(\"已收到完成操作，正在保存 A/B 设置…\"" in dialog,
    "successful save remains visibly confirmed before close": "保存成功：A=" in dialog and "}, 1800L);" in dialog,
    "failed validation remains in dialog with an explicit message": "B 终点不能超过歌曲时长。" in save_method and "A/B 保存失败，请重试；设置窗口已保留。" in save_method,
    "rounded song duration no longer blocks a valid displayed B": "AbLoopRangeMath.clampRoundedEndMs(endMs, durationMs)" in save_method,
    "runtime range is clamped to exact song end": "Math.min(endMicros, currentSong.durationMicros)" in save_method,
    "same commit/readback persistence checks remain": ".commit();" in save_method and "prefs.getLong(KEY_RANGE_START_MS, -1L) != startMs" in save_method and "prefs.getLong(KEY_RANGE_END_MS, -1L) != endMs" in save_method,
    "external loop checkbox sync remains": "AB_LOOP_TWO_WAY_DIALOG_SYNC_V8" in service and "syncAbDialogCheckboxFromExternalState(enabled);" in service,
    "Done-before-Reset ordering preserved": "optionRow.addView(done, doneParams);\n        optionRow.addView(reset, resetParams);" in dialog,
    "native touch dispatch and no outside-dismiss remain": "action.setOnTouchListener(null);" in service and "Do not dismiss the dialog on taps that miss a child hitbox." in dialog,
    "unit test covers duration-display rounding": JAVA_TEST.exists() and "clampsOnlyCentisecondDisplayRoundingAtSongEnd" in JAVA_TEST.read_text(encoding="utf-8"),
    "version 1.8.0": "versionCode 18" in build and "versionName '1.8.0'" in build,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("A/B visible feedback/persistence audit failed: " + "; ".join(failed))
print("V9 applied: end-time display rounding is clamped safely; save progress/success/errors remain visible in the dialog.")
print("AUDIT OK: " + "; ".join(checks.keys()))
