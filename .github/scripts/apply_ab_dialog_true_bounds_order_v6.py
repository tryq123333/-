from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "AB_DIALOG_TRUE_BOUNDS_ORDER_V6"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

if MARKER not in service:
    # Keep scaling in actual layout geometry rather than a render-only matrix.
    # A transformed child can look clickable while its window hit box remains elsewhere.
    baseline_marker = "final int marginLeft, marginTop, marginRight, marginBottom;"
    service = replace_once(service,
        baseline_marker + "\n        final boolean hasMargins;",
        baseline_marker + "\n        final boolean hasMargins;\n        final int minimumWidth, minimumHeight;",
        "record minimum dimensions in the scale baseline")
    service = replace_once(service,
        "            paddingBottom = view.getPaddingBottom();\n            if (lp instanceof ViewGroup.MarginLayoutParams) {",
        "            paddingBottom = view.getPaddingBottom();\n            minimumWidth = view.getMinimumWidth();\n            minimumHeight = view.getMinimumHeight();\n            if (lp instanceof ViewGroup.MarginLayoutParams) {",
        "capture baseline minimum touch dimensions")
    service = replace_once(service,
        "        view.setPadding(scaleAbDimension(baseline.paddingLeft, scaleX),\n                scaleAbDimension(baseline.paddingTop, scaleY),\n                scaleAbDimension(baseline.paddingRight, scaleX),\n                scaleAbDimension(baseline.paddingBottom, scaleY));",
        "        view.setPadding(scaleAbDimension(baseline.paddingLeft, scaleX),\n                scaleAbDimension(baseline.paddingTop, scaleY),\n                scaleAbDimension(baseline.paddingRight, scaleX),\n                scaleAbDimension(baseline.paddingBottom, scaleY));\n"
        "        view.setMinimumWidth(scaleAbDimension(baseline.minimumWidth, scaleX));\n"
        "        view.setMinimumHeight(scaleAbDimension(baseline.minimumHeight, scaleY));",
        "scale minimum width and height with the controls")

    # Replace transform-only scaling with real layout sizing and centered margins.
    start = service.find("    private void applyAbDialogUniformScale(FrameLayout frame, View content,")
    end = service.find("\n    // AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5:", start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate the V5 matrix scaling helper.")
    helper = r'''    private void applyAbDialogUniformScale(FrameLayout frame, View content,
                                           int baseWidthPx, int baseHeightPx,
                                           Map<View, AbDialogViewBaseline> baselines) {
        if (frame == null || content == null || segmentOverlayParams == null) return;
        int windowWidth = Math.max(1, segmentOverlayParams.width);
        int windowHeight = Math.max(1, segmentOverlayParams.height);
        float widthRatio = windowWidth / (float) Math.max(1, baseWidthPx);
        float heightRatio = windowHeight / (float) Math.max(1, baseHeightPx);
        float scale = Math.max(0.35f, Math.min(1.8f, Math.min(widthRatio, heightRatio)));

        // No setScaleX/Y transforms: resize real child layout bounds, so drawing and
        // Android's hit-testing use the exact same coordinates.
        scaleAbDialogTree(content, scale, scale, true, baselines);
        int contentWidth = Math.max(1, Math.round(baseWidthPx * scale));
        int contentHeight = Math.max(1, Math.round(baseHeightPx * scale));
        ViewGroup.LayoutParams raw = content.getLayoutParams();
        FrameLayout.LayoutParams lp = raw instanceof FrameLayout.LayoutParams
                ? (FrameLayout.LayoutParams) raw
                : new FrameLayout.LayoutParams(contentWidth, contentHeight);
        lp.width = contentWidth;
        lp.height = contentHeight;
        lp.gravity = Gravity.TOP | Gravity.LEFT;
        lp.leftMargin = Math.max(0, (windowWidth - contentWidth) / 2);
        lp.topMargin = Math.max(0, (windowHeight - contentHeight) / 2);
        content.setScaleX(1f);
        content.setScaleY(1f);
        content.setTranslationX(0f);
        content.setTranslationY(0f);
        content.setLayoutParams(lp);
        content.invalidate();
        frame.invalidate();
    }

    private void bindAbDialogActionTouch(TextView action) {
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
    }

'''
    service = service[:start] + helper + service[end:]

    # Add a stable baseline map for real layout rescaling.
    service = replace_once(service,
        "        Runnable applyScale = () -> applyAbDialogUniformScale(card, content, baseWidth, baseHeight);",
        "        final Map<View, AbDialogViewBaseline> abDialogBaselines = new java.util.WeakHashMap<>();\n"
        "        Runnable applyScale = () -> applyAbDialogUniformScale(card, content, baseWidth, baseHeight, abDialogBaselines);",
        "use stable per-view dimensions while resizing")

    # Place Done before Reset (left-to-right), as requested.
    service = replace_once(service,
        "        optionRow.addView(reset, resetParams);\n        optionRow.addView(done, doneParams);",
        "        optionRow.addView(done, doneParams);\n        optionRow.addView(reset, resetParams);",
        "put complete to the left of reset")

    # Explicitly turn ACTION_UP into performClick on these touch-sensitive overlay chips.
    service = replace_once(service,
        "        close.setOnClickListener(v -> dismissSegmentDialog());",
        "        close.setOnClickListener(v -> dismissSegmentDialog());\n"
        "        bindAbDialogActionTouch(setA);\n"
        "        bindAbDialogActionTouch(setB);\n"
        "        bindAbDialogActionTouch(done);\n"
        "        bindAbDialogActionTouch(reset);",
        "bind action-chip physical touch handling")

    service = service.replace(
        "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5 " + MARKER + " NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", 1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER, 1)

# Always raise the app version even when this script is rerun from the synced source archive.
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode.")
if int(m.group(1)) < 15:
    build = build[:m.start(1)] + "15" + build[m.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.5.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
start = service.find("    private void showSegmentDialog() {")
end = service.find("    private void hideAbDialogKeyboard(", start)
dialog = service[start:end]
save_start = service.find("    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {")
save_end = service.find("\n    private String formatSecondsField(", save_start)
save = service[save_start:save_end]
checks = {
    "real layout scaling instead of transform hitboxes": "content.setScaleX(1f)" in service and "content.setScaleY(1f)" in service
        and "scaleAbDialogTree(content, scale, scale, true, baselines);" in service,
    "all controls use a stable baseline map": "abDialogBaselines" in dialog and "new java.util.WeakHashMap<>()" in dialog,
    "Done appears to the left of Reset": "optionRow.addView(done, doneParams);\n        optionRow.addView(reset, resetParams);" in dialog,
    "all action chips have explicit touch dispatch": all("bindAbDialogActionTouch(" + name + ")" in dialog for name in ("setA", "setB", "done", "reset")),
    "done only closes on a successful verified save": "if (saveAbLoopSettings(enabled, aField, bField))" in dialog
        and "A/B 设置成功：" in dialog and "prefs.getLong(KEY_RANGE_START_MS, -1L) != startMs" in save,
    "failure leaves the dialog open": "A/B 保存失败，请重试；设置窗口已保留。" in save,
    "loop state refresh remains": "noteRollView.setAbLoopEnabled(loopEnabled);" in save and "refreshNoteRollData();" in save,
    "service name prefix retained": 'android:label="#奏乐触控服务"' in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"),
    "app name and icon retained": "奏乐" in (ROOT / "app/src/main/res/values/strings.xml").read_text(encoding="utf-8")
        and 'android:icon="@drawable/launcher_luoke_v2"' in (ROOT / "app/src/main/AndroidManifest.xml").read_text(encoding="utf-8"),
    "version 1.5.0": int(re.search(r"versionCode\\s+(\\d+)", build).group(1)) >= 15 and "versionName '1.5.0'" in build,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("A/B V6 verification failed: " + "; ".join(failed))
print("V6 applied: real child geometry scales uniformly, tap hitboxes match, Done is left of Reset, and saved values are read back before success.")
print("AUDIT OK: " + "; ".join(checks.keys()))
