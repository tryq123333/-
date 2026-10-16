from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "AB_DIALOG_NO_SILENT_DISMISS_V7"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

if MARKER not in service:
    # Native View touch handling understands Android touch slop and reliably forwards
    # ACTION_UP to OnClickListener. The previous hand-written listener could cancel
    # a click after tiny finger movement.
    service = replace_once(service,
        """    private void bindAbDialogActionTouch(TextView action) {
        action.setOnTouchListener((view, event) -> {
            float x = event.getX();
            float y = event.getY();
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    view.setPressed(true);
                    return true;
                case MotionEvent.ACTION_MOVE:
                    view.setPressed(x >= 0 && y >= 0 && x < view.getWidth() && y < view.getHeight());
                    return true;
                case MotionEvent.ACTION_UP:
                    boolean clicked = view.isPressed()
                            && x >= 0 && y >= 0 && x < view.getWidth() && y < view.getHeight();
                    view.setPressed(false);
                    if (clicked) view.performClick();
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    view.setPressed(false);
                    return true;
                default:
                    return true;
            }
        });
    }""",
        """    private void bindAbDialogActionTouch(TextView action) {
        // Let Android's native touch dispatcher handle press slop and click delivery.
        // Keep this helper so earlier patch-chain postconditions remain compatible.
        action.setClickable(true);
        action.setFocusable(true);
        action.setOnTouchListener(null);
    }""",
        "restore native clickable behavior")

    service = replace_once(service,
        """                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                        | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                PixelFormat.TRANSLUCENT);""",
        """                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT);""",
        "stop receiving outside-touch dismissal events for the A/B dialog")

    service = replace_once(service,
        """        card.setOnTouchListener((v, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_OUTSIDE) {
                dismissSegmentDialog();
                return true;
            }
            return false;
        });
""",
        """        // Do not dismiss the dialog on taps that miss a child hitbox. Keep it open
        // until the explicit × / Back / successfully saved Done action is invoked.
""",
        "remove silent outside-tap dismissal")

    service = replace_once(service,
        """        done.setOnClickListener(v -> {
            hideAbDialogKeyboard(aField, bField);
            if (saveAbLoopSettings(enabled, aField, bField)) {""",
        """        done.setOnClickListener(v -> {
            // Immediate feedback proves that the visible Done hit target actually fired.
            Toast.makeText(this, "已收到完成操作，正在保存 A/B 设置…", Toast.LENGTH_SHORT).show();
            hideAbDialogKeyboard(aField, bField);
            if (saveAbLoopSettings(enabled, aField, bField)) {""",
        "show immediate Done-tap feedback")

    service = service.replace(
        "AB_DIALOG_TRUE_BOUNDS_ORDER_V6 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_DIALOG_TRUE_BOUNDS_ORDER_V6 " + MARKER + " NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", 1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER, 1)

# Advance the version on every build that reaches this step; the previous steps may
# normalize the legacy version to 1.5.0 before the V7 changes are applied.
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode.")
if int(m.group(1)) < 16:
    build = build[:m.start(1)] + "16" + build[m.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.6.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
start = service.find("    private void showSegmentDialog() {")
end = service.find("    private void hideAbDialogKeyboard(", start)
dialog = service[start:end]
checks = {
    "native click listener is used": "action.setOnTouchListener(null);" in service
        and "done.setOnClickListener(v ->" in dialog
        and "bindAbDialogActionTouch(done);" in dialog,
    "outside tap can no longer silently close": "FLAG_WATCH_OUTSIDE_TOUCH" not in dialog
        and "MotionEvent.ACTION_OUTSIDE" not in dialog
        and "Do not dismiss the dialog on taps that miss a child hitbox." in dialog,
    "done tap gives immediate feedback": "已收到完成操作，正在保存 A/B 设置…" in dialog,
    "save still uses verified commit": ".commit();" in service
        and "prefs.getLong(KEY_RANGE_START_MS, -1L) != startMs" in service
        and "A/B 保存失败，请重试；设置窗口已保留。" in service,
    "success message shows values and close follows successful save only": "A/B 设置成功：" in dialog
        and "if (saveAbLoopSettings(enabled, aField, bField))" in dialog,
    "Done remains left of Reset": "optionRow.addView(done, doneParams);\n        optionRow.addView(reset, resetParams);" in dialog,
    "uniform real-layout scaling preserved": "scaleAbDialogTree(content, scale, scale, true, baselines);" in service
        and "content.setScaleX(1f)" in service and "content.setScaleY(1f)" in service,
    "accessibility service name prefixed": 'android:label="#奏乐触控服务"' in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"),
    "app identity stays 奏乐": "奏乐" in (ROOT / "app/src/main/res/values/strings.xml").read_text(encoding="utf-8")
        and 'android:icon="@drawable/launcher_luoke_v2"' in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"),
    "version 1.6.0": "versionCode 16" in build and "versionName '1.6.0'" in build,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("A/B no-silent-dismiss audit failed: " + "; ".join(failed))
print("V7 applied: native click handling restored, outside touches cannot dismiss silently, Done tap produces feedback, and verified persistence remains.")
print("AUDIT OK: " + "; ".join(checks.keys()))
