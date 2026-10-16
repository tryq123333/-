from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "AB_LOOP_TWO_WAY_DIALOG_SYNC_V8"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

if MARKER not in service:
    service = replace_once(service,
        "    private WindowManager.LayoutParams segmentOverlayParams;\n",
        "    private WindowManager.LayoutParams segmentOverlayParams;\n"
        "    private CheckBox abDialogEnabledCheckbox;\n"
        "    private boolean updatingAbDialogEnabledCheckbox;\n",
        "store the active A/B dialog checkbox")

    sync_method = r'''    private void syncAbDialogCheckboxFromExternalState(boolean loopEnabled) {
        Runnable sync = () -> {
            CheckBox checkbox = abDialogEnabledCheckbox;
            if (checkbox == null || checkbox.isChecked() == loopEnabled) return;
            updatingAbDialogEnabledCheckbox = true;
            try {
                checkbox.setChecked(loopEnabled);
            } finally {
                updatingAbDialogEnabledCheckbox = false;
            }
        };
        if (Looper.myLooper() == Looper.getMainLooper()) sync.run();
        else mainHandler.post(sync);
    }

'''
    service = replace_once(service,
        "    private void toggleAbLoopEnabled() {",
        sync_method + "    private void toggleAbLoopEnabled() {",
        "add two-way loop status sync")
    
    toggle_start = service.find("    private void toggleAbLoopEnabled() {")
    toggle_end = service.find("    private void applyAbLoopEnabledFromDialog(", toggle_start)
    if toggle_start < 0 or toggle_end < 0:
        raise SystemExit("Cannot isolate external A/B toggle method.")
    toggle = service[toggle_start:toggle_end]
    toggle = replace_once(toggle,
        '        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, enabled).apply();',
        '        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, enabled).apply();\n'
        '        syncAbDialogCheckboxFromExternalState(enabled);',
        "update modal checkbox when note-roll toggle changes")
    service = service[:toggle_start] + toggle + service[toggle_end:]

    service = replace_once(service,
        '        enabled.setChecked(prefs.getBoolean(KEY_AB_LOOP_ENABLED, false));',
        '        enabled.setChecked(prefs.getBoolean(KEY_AB_LOOP_ENABLED, false));\n'
        '        abDialogEnabledCheckbox = enabled;',
        "remember the checkbox belonging to the visible dialog")

    service = replace_once(service,
        '''        enabled.setOnCheckedChangeListener((buttonView, isChecked) ->
                applyAbLoopEnabledFromDialog(isChecked));''',
        '''        enabled.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (!updatingAbDialogEnabledCheckbox) {
                applyAbLoopEnabledFromDialog(isChecked);
            }
        });''',
        "guard against recursive updates when external toolbar changes loop state")

    service = replace_once(service,
        '''    private void dismissSegmentDialog() {
        removeOverlay(segmentOverlay);
        segmentOverlay = null;
        segmentOverlayParams = null;
    }''',
        '''    private void dismissSegmentDialog() {
        removeOverlay(segmentOverlay);
        segmentOverlay = null;
        segmentOverlayParams = null;
        abDialogEnabledCheckbox = null;
        updatingAbDialogEnabledCheckbox = false;
    }''',
        "clear the modal checkbox reference after the dialog closes")

    service = service.replace(
        "AB_DIALOG_NO_SILENT_DISMISS_V7 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_DIALOG_NO_SILENT_DISMISS_V7 " + MARKER + " NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", 1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER, 1)

# The V1 chain normalizes older version numbers; only raise version when lower than 17.
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode.")
if int(m.group(1)) < 17:
    build = build[:m.start(1)] + "17" + build[m.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.7.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
toggle_start = service.find("    private void toggleAbLoopEnabled() {")
toggle_end = service.find("    private void applyAbLoopEnabledFromDialog(", toggle_start)
toggle = service[toggle_start:toggle_end]
dialog_start = service.find("    private void showSegmentDialog() {")
dialog_end = service.find("    private void hideAbDialogKeyboard(", dialog_start)
dialog = service[dialog_start:dialog_end]
dismiss_start = service.find("    private void dismissSegmentDialog() {")
dismiss_end = service.find("\n    }", dismiss_start)
dismiss = service[dismiss_start:dismiss_end + 6]
checks = {
    "toolbar toggle updates open dialog": "syncAbDialogCheckboxFromExternalState(enabled);" in toggle
        and "abDialogEnabledCheckbox = enabled;" in dialog,
    "checkbox listener avoids recursive update": "if (!updatingAbDialogEnabledCheckbox)" in dialog,
    "programmatic checkbox change does not re-run settings apply": "updatingAbDialogEnabledCheckbox = true;" in service
        and "finally {\n                updatingAbDialogEnabledCheckbox = false;" in service,
    "dialog checkbox reference cleared on close": "abDialogEnabledCheckbox = null;" in dismiss,
    "Done tap feedback remains": "已收到完成操作，正在保存 A/B 设置…" in dialog,
    "verified save is still required": "if (saveAbLoopSettings(enabled, aField, bField))" in dialog
        and "A/B 设置成功：" in dialog and "A/B 保存失败，请重试；设置窗口已保留。" in service,
    "Done remains left of Reset": "optionRow.addView(done, doneParams);\n        optionRow.addView(reset, resetParams);" in dialog,
    "native clicks and no silent outside dismiss remain": "action.setOnTouchListener(null);" in service
        and "Do not dismiss the dialog on taps that miss a child hitbox." in dialog,
    "uniform layout scaling and service label preserved": "scaleAbDialogTree(content, scale, scale, true, baselines);" in service
        and 'android:label="#奏乐触控服务"' in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"),
    "version 1.7.0": int(re.search(r"versionCode\\s+(\\d+)", build).group(1)) >= 17 and "versionName '1.7.0'" in build,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("A/B two-way sync audit failed: " + "; ".join(failed))
print("A/B modal and note-roll toolbar now synchronize in both directions; external updates do not recursively restart the loop logic.")
print("Done feedback/verified commit and Done-before-Reset order remain enabled.")
print("AUDIT OK: " + "; ".join(checks.keys()))
