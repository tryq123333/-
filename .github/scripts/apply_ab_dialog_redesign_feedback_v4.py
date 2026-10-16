from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
BUILD = ROOT / "app/build.gradle"
MARKER = "AB_DIALOG_REDESIGN_FEEDBACK_V4"
FIXED_LAYOUT = "AB_DIALOG_FIXED_LAYOUT_V4"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

# Use self-measuring text chips, not Android Button widgets. The old button defaults
# imposed minimum touch dimensions and the old recursive scaler could clip outlines.
if FIXED_LAYOUT not in service:
    helper = """    private TextView abDialogAction(String text, boolean primary) {
        TextView action = new TextView(this);
        action.setText(text);
        action.setTextColor(primary ? Color.WHITE : 0xff304b3e);
        action.setTextSize(10);
        action.setGravity(Gravity.CENTER);
        action.setPadding(dp(7), dp(3), dp(7), dp(3));
        action.setMinHeight(dp(27));
        action.setMinimumHeight(dp(27));
        action.setClickable(true);
        action.setFocusable(true);
        action.setBackground(roundedBorder(
                primary ? 0xff547c68 : 0xfff8fbf8,
                primary ? 0xff547c68 : 0xffcbd8cf, dp(8)));
        return action;
    }

"""
    if "private TextView abDialogAction(" not in service:
        service = replace_once(service,
            "    // A compact, keyboard-focusable floating card patterned after the user's reference image.\n"
            "    private void showSegmentDialog() {",
            helper + "    // AB_DIALOG_FIXED_LAYOUT_V4: one compact, fixed layout with all actions visible.\n"
            "    private void showSegmentDialog() {",
            "insert the redesigned A/B action-chip helper")

    method_start = service.find("    private void showSegmentDialog() {")
    method_end = service.find("    private void hideAbDialogKeyboard(", method_start)
    if method_start < 0 or method_end < 0:
        raise SystemExit("Cannot isolate A/B settings dialog implementation.")

    method = r'''    private void showSegmentDialog() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::showSegmentDialog);
            return;
        }
        if (windowManager == null) return;
        if (currentSong == null) currentSong = readCurrentSong();
        if (currentSong == null) {
            toast("请先导入 MIDI 曲谱。");
            return;
        }
        dismissSegmentDialog();
        if (playbackActive && !paused) togglePause();

        long durationMicros = Math.max(1L, currentSong.durationMicros);
        long durationMs = Math.max(1L, (durationMicros + 999L) / 1000L);
        long startMs = Math.max(0L, Math.min(durationMs - 1L,
                prefs.getLong(KEY_RANGE_START_MS, 0L)));
        long storedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
        long endMs = storedEndMs <= 0L || storedEndMs > durationMs
                ? durationMs : storedEndMs;
        if (endMs <= startMs) {
            startMs = 0L;
            endMs = durationMs;
        }

        // AB_DIALOG_FIXED_LAYOUT_V4: no nested ScrollView and no recursive child scaling;
        // every action has its own visible row and its own touch bounds.
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(8), dp(7), dp(8), dp(6));
        card.setBackground(roundedBorder(0xfffcfdfb, 0xffd4ded7, dp(14)));
        card.setClickable(true);
        card.setFocusableInTouchMode(true);

        LinearLayout titleRow = new LinearLayout(this);
        titleRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView heading = new TextView(this);
        heading.setText("☷  练习设置");
        heading.setTextColor(0xff304b3e);
        heading.setTextSize(12);
        heading.setTypeface(null, android.graphics.Typeface.BOLD);
        heading.setGravity(Gravity.CENTER_VERTICAL);
        titleRow.addView(heading, new LinearLayout.LayoutParams(0, dp(25), 1f));
        TextView close = new TextView(this);
        close.setText("×");
        close.setTextSize(17);
        close.setTextColor(0xff304b3e);
        close.setGravity(Gravity.CENTER);
        titleRow.addView(close, new LinearLayout.LayoutParams(dp(25), dp(25)));
        card.addView(titleRow, new LinearLayout.LayoutParams(-1, dp(26)));

        CheckBox enabled = new CheckBox(this);
        enabled.setText("A/B 循环");
        enabled.setTextSize(11);
        enabled.setTextColor(0xff40594c);
        enabled.setButtonTintList(ColorStateList.valueOf(0xff547c68));
        enabled.setPadding(0, 0, 0, 0);
        enabled.setMinHeight(dp(24));
        enabled.setMinimumHeight(dp(24));
        enabled.setChecked(prefs.getBoolean(KEY_AB_LOOP_ENABLED, false));
        LinearLayout.LayoutParams checkParams = new LinearLayout.LayoutParams(-1, dp(25));
        checkParams.setMargins(0, dp(1), 0, dp(2));
        card.addView(enabled, checkParams);

        LinearLayout fieldsRow = new LinearLayout(this);
        fieldsRow.setOrientation(LinearLayout.HORIZONTAL);
        LinearLayout aColumn = new LinearLayout(this);
        aColumn.setOrientation(LinearLayout.VERTICAL);
        LinearLayout bColumn = new LinearLayout(this);
        bColumn.setOrientation(LinearLayout.VERTICAL);
        TextView aLabel = abSettingsLabel("A 起点（秒）");
        aLabel.setTextSize(11);
        TextView bLabel = abSettingsLabel("B 终点（秒）");
        bLabel.setTextSize(11);
        aColumn.addView(aLabel, new LinearLayout.LayoutParams(-1, dp(18)));
        bColumn.addView(bLabel, new LinearLayout.LayoutParams(-1, dp(18)));
        EditText aField = abSecondsField(formatSecondsField(startMs));
        EditText bField = abSecondsField(formatSecondsField(endMs));
        aField.setTextSize(16);
        bField.setTextSize(16);
        aField.setPadding(dp(8), dp(2), dp(8), dp(2));
        bField.setPadding(dp(8), dp(2), dp(8), dp(2));
        aField.setMinimumHeight(dp(31));
        bField.setMinimumHeight(dp(31));
        aField.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_DONE);
        bField.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_DONE);
        LinearLayout.LayoutParams fieldParams = new LinearLayout.LayoutParams(-1, dp(32));
        fieldParams.setMargins(0, dp(2), 0, 0);
        aColumn.addView(aField, fieldParams);
        LinearLayout.LayoutParams bFieldParams = new LinearLayout.LayoutParams(-1, dp(32));
        bFieldParams.setMargins(0, dp(2), 0, 0);
        bColumn.addView(bField, bFieldParams);
        LinearLayout.LayoutParams aColumnParams = new LinearLayout.LayoutParams(0, -2, 1f);
        aColumnParams.setMargins(0, 0, dp(4), 0);
        LinearLayout.LayoutParams bColumnParams = new LinearLayout.LayoutParams(0, -2, 1f);
        bColumnParams.setMargins(dp(4), 0, 0, 0);
        fieldsRow.addView(aColumn, aColumnParams);
        fieldsRow.addView(bColumn, bColumnParams);
        card.addView(fieldsRow, new LinearLayout.LayoutParams(-1, dp(52)));

        LinearLayout setButtons = new LinearLayout(this);
        setButtons.setOrientation(LinearLayout.HORIZONTAL);
        setButtons.setGravity(Gravity.CENTER);
        TextView setA = abDialogAction("当前设为 A", false);
        TextView setB = abDialogAction("当前设为 B", false);
        LinearLayout.LayoutParams setAParams = new LinearLayout.LayoutParams(-2, dp(28));
        setAParams.setMargins(0, dp(4), dp(4), 0);
        LinearLayout.LayoutParams setBParams = new LinearLayout.LayoutParams(-2, dp(28));
        setBParams.setMargins(dp(4), dp(4), 0, 0);
        setButtons.addView(setA, setAParams);
        setButtons.addView(setB, setBParams);
        card.addView(setButtons, new LinearLayout.LayoutParams(-1, dp(32)));
        setA.setOnClickListener(v -> {
            aField.setText(formatSecondsField(playbackPositionMicros / 1000L));
            hideAbDialogKeyboard(aField, bField);
            toast("A 点已设为当前播放位置：" + aField.getText().toString() + " 秒。");
        });
        setB.setOnClickListener(v -> {
            bField.setText(formatSecondsField(playbackPositionMicros / 1000L));
            hideAbDialogKeyboard(aField, bField);
            toast("B 点已设为当前播放位置：" + bField.getText().toString() + " 秒。");
        });

        LinearLayout footerButtons = new LinearLayout(this);
        footerButtons.setOrientation(LinearLayout.HORIZONTAL);
        footerButtons.setGravity(Gravity.CENTER);
        TextView reset = abDialogAction("重置 A/B", false);
        TextView done = abDialogAction("完成", true);
        LinearLayout.LayoutParams resetParams = new LinearLayout.LayoutParams(-2, dp(29));
        resetParams.setMargins(0, dp(3), dp(4), 0);
        LinearLayout.LayoutParams doneParams = new LinearLayout.LayoutParams(-2, dp(29));
        doneParams.setMargins(dp(4), dp(3), 0, 0);
        footerButtons.addView(reset, resetParams);
        footerButtons.addView(done, doneParams);
        card.addView(footerButtons, new LinearLayout.LayoutParams(-1, dp(33)));

        reset.setOnClickListener(v -> {
            long resetDurationMs = Math.max(1L, (currentSong.durationMicros + 999L) / 1000L);
            aField.setText("0");
            bField.setText(formatSecondsField(resetDurationMs));
            prefs.edit().putLong(KEY_RANGE_START_MS, 0L)
                    .putLong(KEY_RANGE_END_MS, resetDurationMs).apply();
            playbackRangeStartMicros = 0L;
            playbackRangeEndMicros = Math.max(1L, currentSong.durationMicros);
            if (noteRollView != null) {
                noteRollView.setAbLoopEnabled(enabled.isChecked());
                refreshNoteRollData();
            }
            toast("A/B 起止点已重置：A=0，B=整首歌时长。");
        });

        TextView resizeHandle = new TextView(this);
        resizeHandle.setText("↘ 拖动调整大小");
        resizeHandle.setTextColor(0xff839188);
        resizeHandle.setTextSize(8);
        resizeHandle.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        resizeHandle.setPadding(0, 0, dp(3), 0);
        card.addView(resizeHandle, new LinearLayout.LayoutParams(-1, dp(15)));

        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        if (!prefs.getBoolean("ab_dialog_redesign_v4", false)) {
            prefs.edit().remove("ab_dialog_width_px").remove("ab_dialog_height_px")
                    .putBoolean("ab_dialog_redesign_v4", true).apply();
        }
        int minWidth = Math.min(dp(230), Math.max(dp(160), screenWidth - dp(16)));
        int maxWidth = Math.max(minWidth, Math.min(screenWidth - dp(12), dp(285)));
        int defaultWidth = Math.max(minWidth, Math.min(maxWidth, dp(260)));
        int width = Math.max(minWidth, Math.min(maxWidth,
                prefs.getInt("ab_dialog_width_px", defaultWidth)));
        int minHeight = Math.min(dp(200), Math.max(dp(170), screenHeight - dp(16)));
        int maxHeight = Math.max(minHeight, Math.min(screenHeight - dp(12), dp(255)));
        int defaultHeight = Math.max(minHeight, Math.min(maxHeight, dp(220)));
        int height = Math.max(minHeight, Math.min(maxHeight,
                prefs.getInt("ab_dialog_height_px", defaultHeight)));

        WindowManager.LayoutParams overlayParams = new WindowManager.LayoutParams(
                width, height,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                        | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                        | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                PixelFormat.TRANSLUCENT);
        overlayParams.gravity = Gravity.TOP | Gravity.LEFT;
        overlayParams.x = Math.max(0, Math.min(screenWidth - width,
                prefs.getInt("ab_dialog_x", Math.max(0, (screenWidth - width) / 2))));
        overlayParams.y = Math.max(0, Math.min(screenHeight - height,
                prefs.getInt("ab_dialog_y", dp(24))));
        overlayParams.softInputMode = WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE;
        segmentOverlay = card;
        segmentOverlayParams = overlayParams;

        heading.setOnTouchListener(new View.OnTouchListener() {
            float downX, downY;
            int startX, startY;
            boolean moved;
            @Override public boolean onTouch(View v, MotionEvent event) {
                if (segmentOverlayParams == null) return false;
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downX = event.getRawX();
                        downY = event.getRawY();
                        startX = segmentOverlayParams.x;
                        startY = segmentOverlayParams.y;
                        moved = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx = event.getRawX() - downX;
                        float dy = event.getRawY() - downY;
                        if (Math.hypot(dx, dy) > dp(4)) moved = true;
                        if (moved) {
                            segmentOverlayParams.x = Math.max(0, Math.min(
                                    getResources().getDisplayMetrics().widthPixels - segmentOverlayParams.width,
                                    startX + Math.round(dx)));
                            segmentOverlayParams.y = Math.max(0, Math.min(
                                    getResources().getDisplayMetrics().heightPixels - segmentOverlayParams.height,
                                    startY + Math.round(dy)));
                            try {
                                windowManager.updateViewLayout(card, segmentOverlayParams);
                            } catch (Exception ignored) { }
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (moved) prefs.edit().putInt("ab_dialog_x", segmentOverlayParams.x)
                                .putInt("ab_dialog_y", segmentOverlayParams.y).apply();
                        return true;
                    default:
                        return true;
                }
            }
        });

        resizeHandle.setOnTouchListener(new View.OnTouchListener() {
            float downX, downY;
            int startWidth, startHeight;
            boolean moved;
            @Override public boolean onTouch(View v, MotionEvent event) {
                if (segmentOverlayParams == null) return false;
                switch (event.getActionMasked()) {
                    case MotionEvent.ACTION_DOWN:
                        downX = event.getRawX();
                        downY = event.getRawY();
                        startWidth = segmentOverlayParams.width;
                        startHeight = segmentOverlayParams.height;
                        moved = false;
                        return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx = event.getRawX() - downX;
                        float dy = event.getRawY() - downY;
                        if (Math.hypot(dx, dy) > dp(4)) moved = true;
                        if (moved) {
                            int sw = getResources().getDisplayMetrics().widthPixels;
                            int sh = getResources().getDisplayMetrics().heightPixels;
                            int maxW = Math.max(minWidth, Math.min(sw - dp(12), dp(285)));
                            int maxH = Math.max(minHeight, Math.min(sh - dp(12), dp(255)));
                            segmentOverlayParams.width = Math.max(minWidth, Math.min(maxW,
                                    startWidth + Math.round(dx)));
                            segmentOverlayParams.height = Math.max(minHeight, Math.min(maxH,
                                    startHeight + Math.round(dy)));
                            try {
                                windowManager.updateViewLayout(card, segmentOverlayParams);
                            } catch (Exception ignored) { }
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (moved) prefs.edit()
                                .putInt("ab_dialog_width_px", segmentOverlayParams.width)
                                .putInt("ab_dialog_height_px", segmentOverlayParams.height).apply();
                        return true;
                    default:
                        return true;
                }
            }
        });

        card.setOnKeyListener((v, keyCode, event) -> {
            if (keyCode == android.view.KeyEvent.KEYCODE_BACK
                    && event.getAction() == android.view.KeyEvent.ACTION_UP) {
                dismissSegmentDialog();
                return true;
            }
            return false;
        });
        card.setOnTouchListener((v, event) -> {
            if (event.getActionMasked() == MotionEvent.ACTION_OUTSIDE) {
                dismissSegmentDialog();
                return true;
            }
            return false;
        });
        close.setOnClickListener(v -> dismissSegmentDialog());
        enabled.setOnCheckedChangeListener((buttonView, isChecked) ->
                applyAbLoopEnabledFromDialog(isChecked));
        done.setOnClickListener(v -> {
            hideAbDialogKeyboard(aField, bField);
            if (saveAbLoopSettings(enabled, aField, bField)) {
                boolean loopOn = enabled.isChecked();
                String message = "A/B 设置成功：A=" + aField.getText().toString().trim()
                        + " 秒，B=" + bField.getText().toString().trim()
                        + " 秒；循环" + (loopOn ? "已开启。" : "未开启。");
                dismissSegmentDialog();
                toast(message);
            }
        });

        try {
            windowManager.addView(card, overlayParams);
            card.requestFocus();
        } catch (Exception ex) {
            segmentOverlay = null;
            segmentOverlayParams = null;
            toast("A/B 循环设置无法显示，请重新开启无障碍服务后重试。");
        }
    }

'''
    service = service[:method_start] + method + service[method_end:]

    # Saving a valid range must also update the displayed loop state inside NoteRollView.
    save_start = service.find("    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {")
    save_end = service.find("\n    private String formatSecondsField(", save_start)
    if save_start < 0 or save_end < 0:
        raise SystemExit("Cannot locate A/B save method.")
    save_method = service[save_start:save_end]
    save_method = replace_once(save_method,
        "        if (noteRollView != null) refreshNoteRollData();\n        return true;",
        "        if (noteRollView != null) {\n"
        "            noteRollView.setAbLoopEnabled(loopEnabled);\n"
        "            refreshNoteRollData();\n"
        "        }\n"
        "        return true;",
        "refresh A/B loop state after saving")
    service = service[:save_start] + save_method + service[save_end:]

    service = service.replace(
        "AB_DIALOG_SYNC_AND_COMPACT_V3 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_DIALOG_SYNC_AND_COMPACT_V3 " + MARKER + " " + FIXED_LAYOUT + " NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", 1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER + " " + FIXED_LAYOUT, 1)

# Accessibility settings sort labels alphabetically; prefix the service label with #.
manifest = re.sub(
    r'android:label="[^"]*"(?=\s*android:permission="android\.permission\.BIND_ACCESSIBILITY_SERVICE")',
    'android:label="#奏乐触控服务"',
    manifest,
    count=1
)

version_match = re.search(r"versionCode\s+(\d+)", build)
if not version_match:
    raise SystemExit("Cannot find app versionCode.")
build = build[:version_match.start(1)] + "13" + build[version_match.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.3.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
MANIFEST.write_text(manifest, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
dialog_start = service.find("    private void showSegmentDialog() {")
dialog_end = service.find("    private void hideAbDialogKeyboard(", dialog_start)
dialog = service[dialog_start:dialog_end]
save_start = service.find("    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {")
save_end = service.find("\n    private String formatSecondsField(", save_start)
save_method = service[save_start:save_end]
checks = {
    "no clipped scroll area": "ScrollView" not in dialog and "bodyScroll" not in dialog,
    "compact set-point chips": 'abDialogAction("当前设为 A", false)' in dialog
        and 'abDialogAction("当前设为 B", false)' in dialog,
    "fixed complete action visible": 'abDialogAction("完成", true)' in dialog
        and "card.addView(footerButtons" in dialog,
    "success feedback after save": "A/B 设置成功：" in dialog and "if (saveAbLoopSettings(enabled, aField, bField))" in dialog,
    "loop state is applied after save": "noteRollView.setAbLoopEnabled(loopEnabled);" in save_method,
    "checkbox applies loop state live": "applyAbLoopEnabledFromDialog(isChecked)" in dialog,
    "service label begins with hash": 'android:label="#奏乐触控服务"' in manifest,
    "fixed layout marker": MARKER in service and FIXED_LAYOUT in service,
    "old recursive scaler is not connected": "scaleAbDialogTree(card, scaleX" not in dialog,
    "white black launcher icon kept": 'android:icon="@drawable/launcher_luoke_v2"' in manifest,
    "version 1.3.0": "versionCode 13" in build and "versionName '1.3.0'" in build,
    "older resize/move settings retained": "resizeHandle.setOnTouchListener" in dialog and "heading.setOnTouchListener" in dialog,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("A/B redesign audit failed: " + "; ".join(failed))
print("Applied fixed compact A/B dialog, reliable feedback/sync, and # service label.")
print("AUDIT OK: " + "; ".join(checks.keys()))
