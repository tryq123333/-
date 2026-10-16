from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "AB_DIALOG_SYNC_AND_COMPACT_V3"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

if MARKER not in service:
    start = service.find("    private void showSegmentDialog() {")
    end = service.find("    private void hideAbDialogKeyboard(", start)
    if start < 0 or end < 0:
        raise SystemExit("Cannot locate full A/B settings dialog method.")
    dialog = service[start:end]

    # Keep the input fields scrollable if the IME reduces the available area,
    # but leave both set-point buttons and the final actions outside the scroll region.
    dialog = replace_once(dialog,
        '        card.addView(bodyScroll, new LinearLayout.LayoutParams(-1, 0, 1f));',
        '        card.addView(bodyScroll, new LinearLayout.LayoutParams(-1, dp(70)));',
        "fixed compact A/B field viewport")

    dialog = replace_once(dialog,
        '        setButtons.setOrientation(LinearLayout.HORIZONTAL);',
        '        setButtons.setOrientation(LinearLayout.HORIZONTAL);\n        setButtons.setGravity(Gravity.CENTER);',
        "center set-point controls")

    dialog = replace_once(dialog,
        '''        LinearLayout.LayoutParams setAParams = new LinearLayout.LayoutParams(0, dp(28), 1f);
        setAParams.setMargins(0, dp(6), dp(6), 0);
        LinearLayout.LayoutParams setBParams = new LinearLayout.LayoutParams(0, dp(26), 1f);
        setBParams.setMargins(dp(3), dp(6), 0, 0);
        setButtons.addView(setA, setAParams);
        setButtons.addView(setB, setBParams);
        body.addView(setButtons);''',
        '''        setA.setTextSize(10);
        setB.setTextSize(10);
        setA.setMinWidth(dp(82));
        setB.setMinWidth(dp(82));
        setA.setMinimumWidth(dp(82));
        setB.setMinimumWidth(dp(82));
        setA.setMinHeight(0);
        setB.setMinHeight(0);
        setA.setMinimumHeight(dp(25));
        setB.setMinimumHeight(dp(25));
        setA.setPadding(dp(4), 0, dp(4), 0);
        setB.setPadding(dp(4), 0, dp(4), 0);
        LinearLayout.LayoutParams setAParams = new LinearLayout.LayoutParams(-2, dp(25));
        setAParams.setMargins(0, dp(3), dp(4), 0);
        LinearLayout.LayoutParams setBParams = new LinearLayout.LayoutParams(-2, dp(25));
        setBParams.setMargins(dp(4), dp(3), 0, 0);
        setButtons.addView(setA, setAParams);
        setButtons.addView(setB, setBParams);
        card.addView(setButtons, new LinearLayout.LayoutParams(-1, dp(27)));''',
        "place compact set-point buttons in fixed visible row")

    dialog = replace_once(dialog,
        '''        LinearLayout.LayoutParams resetParams = new LinearLayout.LayoutParams(0, dp(30), 1f);
        resetParams.setMargins(0, dp(6), dp(5), 0);
        LinearLayout.LayoutParams doneParams = new LinearLayout.LayoutParams(0, dp(30), 1f);
        doneParams.setMargins(dp(5), dp(6), 0, 0);
        footerButtons.addView(reset, resetParams);
        footerButtons.addView(done, doneParams);''',
        '''        footerButtons.setGravity(Gravity.CENTER);
        reset.setTextSize(10);
        done.setTextSize(10);
        reset.setMinWidth(dp(64));
        done.setMinWidth(dp(58));
        reset.setMinimumWidth(dp(64));
        done.setMinimumWidth(dp(58));
        reset.setMinHeight(0);
        done.setMinHeight(0);
        reset.setMinimumHeight(dp(27));
        done.setMinimumHeight(dp(27));
        reset.setPadding(dp(5), 0, dp(5), 0);
        done.setPadding(dp(5), 0, dp(5), 0);
        LinearLayout.LayoutParams resetParams = new LinearLayout.LayoutParams(-2, dp(27));
        resetParams.setMargins(0, dp(3), dp(4), 0);
        LinearLayout.LayoutParams doneParams = new LinearLayout.LayoutParams(-2, dp(27));
        doneParams.setMargins(dp(4), dp(3), 0, 0);
        footerButtons.addView(reset, resetParams);
        footerButtons.addView(done, doneParams);''',
        "narrow reset and complete controls")

    dialog = replace_once(dialog,
        '        card.setPadding(dp(8), dp(5), dp(8), dp(6));',
        '        card.setPadding(dp(6), dp(4), dp(6), dp(4));',
        "reduce card padding")
    dialog = replace_once(dialog,
        'titleRow.addView(heading, new LinearLayout.LayoutParams(0, dp(27), 1f));',
        'titleRow.addView(heading, new LinearLayout.LayoutParams(0, dp(24), 1f));',
        "reduce title row height")
    dialog = replace_once(dialog,
        '        heading.setTextSize(14);',
        '        heading.setTextSize(12);',
        "reduce title font")
    dialog = replace_once(dialog,
        '        close.setTextSize(18);',
        '        close.setTextSize(16);',
        "reduce close button font")
    dialog = replace_once(dialog,
        'titleRow.addView(close, new LinearLayout.LayoutParams(dp(29), dp(29)));',
        'titleRow.addView(close, new LinearLayout.LayoutParams(dp(25), dp(25)));',
        "reduce close button size")
    dialog = replace_once(dialog,
        '        enabled.setTextSize(12);',
        '        enabled.setTextSize(11);',
        "reduce checkbox font")
    dialog = replace_once(dialog,
        'LinearLayout.LayoutParams checkParams = new LinearLayout.LayoutParams(-1, dp(27));',
        'LinearLayout.LayoutParams checkParams = new LinearLayout.LayoutParams(-1, dp(23));',
        "reduce checkbox row")
    dialog = replace_once(dialog,
        'checkParams.setMargins(0, dp(1), 0, dp(2));',
        'checkParams.setMargins(0, 0, 0, 0);',
        "reduce checkbox margins")
    dialog = replace_once(dialog,
        'LinearLayout.LayoutParams inputParams = new LinearLayout.LayoutParams(-1, dp(29));',
        'LinearLayout.LayoutParams inputParams = new LinearLayout.LayoutParams(-1, dp(27));',
        "reduce A input height")
    dialog = replace_once(dialog,
        'inputParams.setMargins(0, dp(3), 0, 0);',
        'inputParams.setMargins(0, dp(2), 0, 0);',
        "reduce A input margin")
    dialog = replace_once(dialog,
        'LinearLayout.LayoutParams bInputParams = new LinearLayout.LayoutParams(-1, dp(36));',
        'LinearLayout.LayoutParams bInputParams = new LinearLayout.LayoutParams(-1, dp(27));',
        "align B input height to A")
    dialog = replace_once(dialog,
        'bInputParams.setMargins(0, dp(5), 0, 0);',
        'bInputParams.setMargins(0, dp(2), 0, 0);',
        "reduce B input margin")
    dialog = replace_once(dialog,
        'aColParams.setMargins(0, 0, dp(5), 0);',
        'aColParams.setMargins(0, 0, dp(3), 0);',
        "tighten A column margin")
    dialog = replace_once(dialog,
        'bColParams.setMargins(dp(3), 0, 0, 0);',
        'bColParams.setMargins(dp(2), 0, 0, 0);',
        "tighten B column margin")
    dialog = replace_once(dialog,
        '        resizeHandle.setTextSize(8);',
        '        resizeHandle.setTextSize(7);',
        "reduce resize hint text")
    dialog = replace_once(dialog,
        'card.addView(resizeHandle, new LinearLayout.LayoutParams(-1, dp(13)));',
        'card.addView(resizeHandle, new LinearLayout.LayoutParams(-1, dp(10)));',
        "reduce resize-handle row")

    # On a compact card, keep enough height to show title, fields, set-point row and footer.
    dialog = replace_once(dialog,
        '        int defaultWidth = Math.min(Math.max(dp(200), screenWidth - dp(36)), dp(250));',
        '        if (!prefs.getBoolean("ab_dialog_compact_v3", false)) {\n'
        '            prefs.edit().remove("ab_dialog_width_px").remove("ab_dialog_height_px")\n'
        '                    .putBoolean("ab_dialog_compact_v3", true).apply();\n'
        '        }\n'
        '        int defaultWidth = Math.min(Math.max(dp(195), screenWidth - dp(36)), dp(225));',
        "migrate previous oversized dialog dimensions")
    dialog = replace_once(dialog,
        '        int defaultHeight = Math.min(Math.max(dp(160), screenHeight - dp(40)), dp(185));',
        '        int defaultHeight = Math.min(Math.max(dp(172), screenHeight - dp(40)), dp(185));',
        "set compact default height")
    dialog = replace_once(dialog,
        '        int width = Math.max(dp(190), Math.min(Math.min(screenWidth - dp(20), dp(270)),',
        '        int width = Math.max(dp(195), Math.min(Math.min(screenWidth - dp(20), dp(240)),',
        "reduce dialog width bounds")
    dialog = replace_once(dialog,
        '        int height = Math.max(dp(145), Math.min(Math.min(screenHeight - dp(20), dp(210)),',
        '        int height = Math.max(dp(172), Math.min(Math.min(screenHeight - dp(20), dp(195)),',
        "reduce dialog height bounds")

    dialog = replace_once(dialog,
        'segmentOverlayParams.width = Math.max(dp(220), Math.min(maxW, startWidth + Math.round(dx)));',
        'segmentOverlayParams.width = Math.max(dp(195), Math.min(Math.min(maxW, dp(255)), startWidth + Math.round(dx)));',
        "resize width bounds match compact default")
    dialog = replace_once(dialog,
        'segmentOverlayParams.height = Math.max(dp(185), Math.min(maxH, startHeight + Math.round(dy)));',
        'segmentOverlayParams.height = Math.max(dp(172), Math.min(Math.min(maxH, dp(220)), startHeight + Math.round(dy)));',
        "resize height bounds match compact default")

    dialog = replace_once(dialog,
        '        enabled.setChecked(prefs.getBoolean(KEY_AB_LOOP_ENABLED, false));',
        '        enabled.setChecked(prefs.getBoolean(KEY_AB_LOOP_ENABLED, false));\n'
        '        enabled.setOnCheckedChangeListener((buttonView, isChecked) ->\n'
        '                applyAbLoopEnabledFromDialog(isChecked));',
        "sync checkbox changes immediately")

    service = service[:start] + dialog + service[end:]

    # Apply the checkbox toggle immediately to persisted mode, active range and NoteRoll display.
    helper = """    private void applyAbLoopEnabledFromDialog(boolean loopEnabled) {
        if (currentSong == null) currentSong = readCurrentSong();
        if (currentSong == null) return;

        long durationMicros = Math.max(1L, currentSong.durationMicros);
        long durationMs = Math.max(1L, (durationMicros + 999L) / 1000L);
        long startMs = Math.max(0L, Math.min(durationMs - 1L,
                prefs.getLong(KEY_RANGE_START_MS, 0L)));
        long storedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
        long endMs = storedEndMs <= 0L || storedEndMs > durationMs
                ? durationMs : storedEndMs;
        if (endMs <= startMs) { startMs = 0L; endMs = durationMs; }

        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled).apply();
        long nextStart = loopEnabled ? startMs * 1000L : 0L;
        long nextEnd = loopEnabled ? Math.min(durationMicros, endMs * 1000L) : durationMicros;
        boolean rangeChanged = nextStart != playbackRangeStartMicros
                || nextEnd != playbackRangeEndMicros;
        playbackRangeStartMicros = nextStart;
        playbackRangeEndMicros = Math.max(nextStart + 1L, nextEnd);

        if (loopEnabled && (playbackPositionMicros < nextStart || playbackPositionMicros >= nextEnd)) {
            playbackPositionMicros = nextStart;
            playbackBaseMicros = nextStart;
        }
        if (rangeChanged && playbackThread != null && playbackThread.isAlive()
                && playbackActive && !stopRequested) {
            stopPlayback();
        }
        if (noteRollView != null) {
            noteRollView.setAbLoopEnabled(loopEnabled);
            refreshNoteRollData();
        }
    }

"""
    service = replace_once(service,
        '    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {',
        helper + '    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {',
        "insert immediate A/B checkbox application")

    service = replace_once(service,
        '        if (rangeChanged && playbackThread != null && playbackThread.isAlive()) {\n'
        '            // The running worker captured the old scope. Stop cleanly; the next start uses the new scope.\n'
        '            stopPlayback();\n'
        '        }',
        '        if (rangeChanged && playbackThread != null && playbackThread.isAlive()\n'
        '                && playbackActive && !stopRequested) {\n'
        '            // The running worker captured the old scope. Stop cleanly; the next start uses the new scope.\n'
        '            stopPlayback();\n'
        '        }',
        "avoid duplicate playback stop after immediate checkbox change")

    service = service.replace(
        "AB_DIALOG_ACTIONS_STICKY_V1 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_DIALOG_ACTIONS_STICKY_V1 " + MARKER + " NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", 1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER, 1)

# Bump version to 1.2.0 and retain the white/black icon state.
match = re.search(r"versionCode\s+(\d+)", build)
if not match:
    raise SystemExit("Cannot find versionCode.")
build = build[:match.start(1)] + str(max(12, int(match.group(1)) + (0 if int(match.group(1)) >= 12 else 1))) + build[match.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.2.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
dialog_start = service.find("    private void showSegmentDialog() {")
dialog_end = service.find("    private void hideAbDialogKeyboard(", dialog_start)
dialog = service[dialog_start:dialog_end]
checks = {
    "fixed height keeps core fields visible": "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or "new LinearLayout.LayoutParams(-1, dp(70))" in dialog,
    "set A/B actions outside scrollview": "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or ("card.addView(setButtons, new LinearLayout.LayoutParams(-1, dp(27)));" in dialog
        and "body.addView(setButtons);" not in dialog),
    "narrow wrap-content set buttons": "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or "new LinearLayout.LayoutParams(-2, dp(25))" in dialog,
    "narrow wrap-content footer buttons": "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or "new LinearLayout.LayoutParams(-2, dp(27))" in dialog,
    "checkbox immediately synchronizes": "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or ("applyAbLoopEnabledFromDialog(isChecked)" in dialog
        and "private void applyAbLoopEnabledFromDialog(boolean loopEnabled)" in service),
    "loop checkbox updates NoteRollView": "noteRollView.setAbLoopEnabled(loopEnabled);" in service,
    "resize bounds are compact": "AB_DIALOG_REDESIGN_FEEDBACK_V4" in service or "Math.max(dp(195), Math.min(Math.min(maxW, dp(255))" in dialog,
    "earlier UI and app naming remain": "ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3" in service
        and 'android:icon="@drawable/launcher_luoke_v2"' in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        and "<string name=\"app_name\">奏乐</string>" in (ROOT / "app/src/main/res/values/strings.xml").read_text(encoding="utf-8"),
    "version 1.2.0": "versionCode 12" in BUILD.read_text(encoding="utf-8") and "versionName '1.2.0'" in BUILD.read_text(encoding="utf-8"),
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("A/B dialog regression audit failed: " + "; ".join(failed))
print("A/B dialog v3 applied: set-point row is fixed/visible, footer compact, checkbox updates persisted state and NoteRoll, resize limits reduced.")
print("AUDIT OK: " + "; ".join(checks.keys()))
