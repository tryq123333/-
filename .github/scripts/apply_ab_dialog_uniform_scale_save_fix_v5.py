from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
BUILD = ROOT / "app/build.gradle"
MARKER = "AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing expected source anchor for " + label)


service = SERVICE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

# Uniformly scale one fixed-size content canvas inside the independently resizable overlay.
# This prevents drawn buttons from extending past the actual WindowManager touch bounds.
if MARKER not in service:
    scale_helper = r'''    private void applyAbDialogUniformScale(FrameLayout frame, View content,
                                           int baseWidthPx, int baseHeightPx) {
        if (frame == null || content == null || segmentOverlayParams == null) return;
        int windowWidth = Math.max(1, segmentOverlayParams.width);
        int windowHeight = Math.max(1, segmentOverlayParams.height);
        float scaleX = windowWidth / (float) Math.max(1, baseWidthPx);
        float scaleY = windowHeight / (float) Math.max(1, baseHeightPx);
        float scale = Math.max(0.35f, Math.min(1.8f, Math.min(scaleX, scaleY)));
        content.setPivotX(0f);
        content.setPivotY(0f);
        content.setScaleX(scale);
        content.setScaleY(scale);
        content.setTranslationX(Math.max(0f, (windowWidth - baseWidthPx * scale) / 2f));
        content.setTranslationY(Math.max(0f, (windowHeight - baseHeightPx * scale) / 2f));
        content.invalidate();
        frame.invalidate();
    }

'''
    if "private void applyAbDialogUniformScale(" not in service:
        service = replace_once(service,
            "    // AB_DIALOG_FIXED_LAYOUT_V4: one compact, fixed layout with all actions visible.\n"
            "    private void showSegmentDialog() {",
            scale_helper + "    // AB_DIALOG_UNIFORM_SCALE_SAVE_FIX_V5: one scaled canvas, exact touch bounds.\n"
            "    private void showSegmentDialog() {",
            "insert uniform-scale helper")

    start = service.find("    private void showSegmentDialog() {")
    end = service.find("    private void hideAbDialogKeyboard(", start)
    if start < 0 or end < 0:
        raise SystemExit("Cannot locate A/B dialog method.")
    dialog = r'''    private void showSegmentDialog() {
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

        final long durationMicros = Math.max(1L, currentSong.durationMicros);
        final long durationMs = Math.max(1L, (durationMicros + 999L) / 1000L);
        long startMs = Math.max(0L, Math.min(durationMs - 1L,
                prefs.getLong(KEY_RANGE_START_MS, 0L)));
        long storedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
        long endMs = storedEndMs <= 0L || storedEndMs > durationMs
                ? durationMs : storedEndMs;
        if (endMs <= startMs) {
            startMs = 0L;
            endMs = durationMs;
        }

        final int baseWidth = dp(260);
        final int baseHeight = dp(185);

        // Outer frame and inner controls keep one fixed coordinate system.
        // Resizing scales the entire content group equally in X and Y.
        FrameLayout card = new FrameLayout(this);
        card.setBackground(roundedBorder(0xfffcfdfb, 0xffd4ded7, dp(14)));
        card.setClipChildren(false);
        card.setClipToPadding(false);
        card.setClickable(true);
        card.setFocusableInTouchMode(true);

        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(8), dp(5), dp(8), dp(4));
        content.setClipChildren(false);
        content.setClipToPadding(false);
        FrameLayout.LayoutParams contentParams = new FrameLayout.LayoutParams(
                baseWidth, baseHeight, Gravity.TOP | Gravity.LEFT);
        card.addView(content, contentParams);

        LinearLayout titleRow = new LinearLayout(this);
        titleRow.setGravity(Gravity.CENTER_VERTICAL);
        TextView heading = new TextView(this);
        heading.setText("☷  练习设置");
        heading.setTextColor(0xff304b3e);
        heading.setTextSize(12);
        heading.setTypeface(null, android.graphics.Typeface.BOLD);
        heading.setGravity(Gravity.CENTER_VERTICAL);
        titleRow.addView(heading, new LinearLayout.LayoutParams(0, dp(23), 1f));
        TextView close = new TextView(this);
        close.setText("×");
        close.setTextSize(17);
        close.setTextColor(0xff304b3e);
        close.setGravity(Gravity.CENTER);
        titleRow.addView(close, new LinearLayout.LayoutParams(dp(24), dp(23)));
        content.addView(titleRow, new LinearLayout.LayoutParams(-1, dp(24)));

        // Row 2: loop checkbox on the left; compact Reset/Done controls on its right.
        LinearLayout optionRow = new LinearLayout(this);
        optionRow.setGravity(Gravity.CENTER_VERTICAL);
        CheckBox enabled = new CheckBox(this);
        enabled.setText("A/B 循环");
        enabled.setTextSize(11);
        enabled.setTextColor(0xff40594c);
        enabled.setButtonTintList(ColorStateList.valueOf(0xff547c68));
        enabled.setPadding(0, 0, 0, 0);
        enabled.setMinWidth(0);
        enabled.setMinimumWidth(0);
        enabled.setMinHeight(0);
        enabled.setMinimumHeight(0);
        enabled.setChecked(prefs.getBoolean(KEY_AB_LOOP_ENABLED, false));
        optionRow.addView(enabled, new LinearLayout.LayoutParams(0, dp(29), 1f));
        TextView reset = abDialogAction("重置 A/B", false);
        TextView done = abDialogAction("完成", true);
        reset.setTextSize(9);
        done.setTextSize(10);
        reset.setPadding(dp(5), 0, dp(5), 0);
        done.setPadding(dp(6), 0, dp(6), 0);
        reset.setMinWidth(0);
        reset.setMinimumWidth(0);
        done.setMinWidth(0);
        done.setMinimumWidth(0);
        LinearLayout.LayoutParams resetParams = new LinearLayout.LayoutParams(-2, dp(26));
        resetParams.setMargins(dp(2), 0, dp(3), 0);
        LinearLayout.LayoutParams doneParams = new LinearLayout.LayoutParams(-2, dp(26));
        doneParams.setMargins(dp(3), 0, 0, 0);
        optionRow.addView(reset, resetParams);
        optionRow.addView(done, doneParams);
        LinearLayout.LayoutParams optionParams = new LinearLayout.LayoutParams(-1, dp(30));
        optionParams.setMargins(0, dp(1), 0, dp(2));
        content.addView(optionRow, optionParams);

        // Narrow, equal-width A/B entry boxes; no ScrollView or oversized default Button.
        LinearLayout fieldsRow = new LinearLayout(this);
        fieldsRow.setGravity(Gravity.CENTER_HORIZONTAL);
        LinearLayout aColumn = new LinearLayout(this);
        aColumn.setOrientation(LinearLayout.VERTICAL);
        LinearLayout bColumn = new LinearLayout(this);
        bColumn.setOrientation(LinearLayout.VERTICAL);
        TextView aLabel = abSettingsLabel("A 起点（秒）");
        TextView bLabel = abSettingsLabel("B 终点（秒）");
        aLabel.setTextSize(10);
        bLabel.setTextSize(10);
        aColumn.addView(aLabel, new LinearLayout.LayoutParams(-1, dp(17)));
        bColumn.addView(bLabel, new LinearLayout.LayoutParams(-1, dp(17)));
        EditText aField = abSecondsField(formatSecondsField(startMs));
        EditText bField = abSecondsField(formatSecondsField(endMs));
        aField.setTextSize(15);
        bField.setTextSize(15);
        aField.setPadding(dp(6), dp(2), dp(6), dp(2));
        bField.setPadding(dp(6), dp(2), dp(6), dp(2));
        aField.setMinWidth(0);
        aField.setMinimumWidth(0);
        bField.setMinWidth(0);
        bField.setMinimumWidth(0);
        aField.setSingleLine(true);
        bField.setSingleLine(true);
        aField.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_DONE);
        bField.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_DONE);
        aColumn.addView(aField, new LinearLayout.LayoutParams(-1, dp(30)));
        bColumn.addView(bField, new LinearLayout.LayoutParams(-1, dp(30)));
        LinearLayout.LayoutParams aColumnParams = new LinearLayout.LayoutParams(dp(104), -2);
        aColumnParams.setMargins(0, 0, dp(5), 0);
        LinearLayout.LayoutParams bColumnParams = new LinearLayout.LayoutParams(dp(104), -2);
        bColumnParams.setMargins(dp(5), 0, 0, 0);
        fieldsRow.addView(aColumn, aColumnParams);
        fieldsRow.addView(bColumn, bColumnParams);
        content.addView(fieldsRow, new LinearLayout.LayoutParams(-1, dp(48)));

        // Set A is flush left with the A field. Set B is flush left with the B field.
        LinearLayout pointsRow = new LinearLayout(this);
        pointsRow.setGravity(Gravity.CENTER_HORIZONTAL);
        TextView setA = abDialogAction("当前设为 A", false);
        TextView setB = abDialogAction("当前设为 B", false);
        setA.setTextSize(9);
        setB.setTextSize(9);
        setA.setPadding(dp(4), 0, dp(4), 0);
        setB.setPadding(dp(4), 0, dp(4), 0);
        setA.setMinWidth(0);
        setA.setMinimumWidth(0);
        setB.setMinWidth(0);
        setB.setMinimumWidth(0);
        LinearLayout.LayoutParams setAParams = new LinearLayout.LayoutParams(dp(104), dp(26));
        setAParams.setMargins(0, 0, dp(5), 0);
        LinearLayout.LayoutParams setBParams = new LinearLayout.LayoutParams(dp(104), dp(26));
        setBParams.setMargins(dp(5), 0, 0, 0);
        pointsRow.addView(setA, setAParams);
        pointsRow.addView(setB, setBParams);
        content.addView(pointsRow, new LinearLayout.LayoutParams(-1, dp(29)));

        TextView resizeHandle = new TextView(this);
        resizeHandle.setText("↘ 拖动调整大小");
        resizeHandle.setTextColor(0xff839188);
        resizeHandle.setTextSize(8);
        resizeHandle.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        resizeHandle.setPadding(0, 0, dp(2), 0);
        content.addView(resizeHandle, new LinearLayout.LayoutParams(-1, dp(13)));

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

        reset.setOnClickListener(v -> {
            aField.setText("0");
            bField.setText(formatSecondsField(durationMs));
            enabled.setChecked(false);
            hideAbDialogKeyboard(aField, bField);
            toast("已将 A/B 设为整首歌曲范围；点击完成保存。");
        });

        done.setOnClickListener(v -> {
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
        });
        close.setOnClickListener(v -> dismissSegmentDialog());

        // The frame is the actual WindowManager hit box, and the scaled child stays inside it.
        final int screenWidth = getResources().getDisplayMetrics().widthPixels;
        final int screenHeight = getResources().getDisplayMetrics().heightPixels;
        if (!prefs.getBoolean("ab_dialog_uniform_scale_v5", false)) {
            prefs.edit().remove("ab_dialog_width_px").remove("ab_dialog_height_px")
                    .putBoolean("ab_dialog_uniform_scale_v5", true).apply();
        }
        final int minWidth = Math.min(dp(170), Math.max(dp(150), screenWidth - dp(12)));
        final int maxWidth = Math.max(minWidth, Math.min(screenWidth - dp(12), dp(410)));
        final int defaultWidth = Math.max(minWidth, Math.min(maxWidth, baseWidth));
        final int width = Math.max(minWidth, Math.min(maxWidth,
                prefs.getInt("ab_dialog_width_px", defaultWidth)));
        final int minHeight = Math.min(dp(120), Math.max(dp(100), screenHeight - dp(12)));
        final int maxHeight = Math.max(minHeight, Math.min(screenHeight - dp(12), dp(290)));
        final int defaultHeight = Math.max(minHeight, Math.min(maxHeight, baseHeight));
        final int height = Math.max(minHeight, Math.min(maxHeight,
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

        Runnable applyScale = () -> applyAbDialogUniformScale(card, content, baseWidth, baseHeight);
        card.addOnLayoutChangeListener((v, left, top, right, bottom, oldLeft, oldTop, oldRight, oldBottom) ->
                applyScale.run());

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
                            try { windowManager.updateViewLayout(card, segmentOverlayParams); }
                            catch (Exception ignored) { }
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
                            int maxW = Math.max(minWidth, Math.min(sw - dp(12), dp(410)));
                            int maxH = Math.max(minHeight, Math.min(sh - dp(12), dp(290)));
                            segmentOverlayParams.width = Math.max(minWidth, Math.min(maxW,
                                    startWidth + Math.round(dx)));
                            segmentOverlayParams.height = Math.max(minHeight, Math.min(maxH,
                                    startHeight + Math.round(dy)));
                            try {
                                windowManager.updateViewLayout(card, segmentOverlayParams);
                                applyScale.run();
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
        enabled.setOnCheckedChangeListener((buttonView, isChecked) ->
                applyAbLoopEnabledFromDialog(isChecked));

        try {
            windowManager.addView(card, overlayParams);
            card.requestFocus();
            applyScale.run();
        } catch (Exception ex) {
            segmentOverlay = null;
            segmentOverlayParams = null;
            toast("A/B 循环设置无法显示，请重新开启无障碍服务后重试。");
        }
    }

'''
    service = service[:start] + dialog + service[end:]

    # Save synchronously and read back persisted values before reporting success.
    old_save = '''        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled)
                .putLong(KEY_RANGE_START_MS, startMs).putLong(KEY_RANGE_END_MS, endMs).apply();
        playbackRangeStartMicros = effectiveStart;'''
    new_save = '''        boolean persisted = prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled)
                .putLong(KEY_RANGE_START_MS, startMs).putLong(KEY_RANGE_END_MS, endMs).commit();
        if (!persisted || prefs.getBoolean(KEY_AB_LOOP_ENABLED, !loopEnabled) != loopEnabled
                || prefs.getLong(KEY_RANGE_START_MS, -1L) != startMs
                || prefs.getLong(KEY_RANGE_END_MS, -1L) != endMs) {
            toast("A/B 保存失败，请重试；设置窗口已保留。");
            return false;
        }
        playbackRangeStartMicros = effectiveStart;'''
    service = replace_once(service, old_save, new_save, "commit and verify A/B persistence")

    service = service.replace(
        "AB_DIALOG_REDESIGN_FEEDBACK_V4 AB_DIALOG_FIXED_LAYOUT_V4",
        "AB_DIALOG_REDESIGN_FEEDBACK_V4 AB_DIALOG_FIXED_LAYOUT_V4 " + MARKER, 1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER, 1)

# Keep the service entry easy to locate.
manifest = re.sub(
    r'android:label="[^"]*"(?=\s*android:permission="android\.permission\.BIND_ACCESSIBILITY_SERVICE")',
    'android:label="#奏乐触控服务"',
    manifest,
    count=1
)
match = re.search(r"versionCode\s+(\d+)", build)
if not match:
    raise SystemExit("Cannot find versionCode.")
build = build[:match.start(1)] + "14" + build[match.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.4.0'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
MANIFEST.write_text(manifest, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
start = service.find("    private void showSegmentDialog() {")
end = service.find("    private void hideAbDialogKeyboard(", start)
dialog = service[start:end]
save_start = service.find("    private boolean saveAbLoopSettings(CheckBox enabled, EditText aField, EditText bField) {")
save_end = service.find("\n    private String formatSecondsField(", save_start)
save_method = service[save_start:save_end]
checks = {
    "uniform scale only": "applyAbDialogUniformScale(card, content, baseWidth, baseHeight)" in dialog
        and "content.setScaleX(scale)" in service and "content.setScaleY(scale)" in service,
    "A/B row has reset and done beside checkbox": "optionRow.addView(enabled" in dialog and "optionRow.addView(reset" in dialog and "optionRow.addView(done" in dialog,
    "narrow fields": "new LinearLayout.LayoutParams(dp(104), -2)" in dialog and "new LinearLayout.LayoutParams(-1, dp(30))" in dialog,
    "set-A button left aligned within A column": "aColumn.addView(aField" in dialog and "pointsRow.addView(setA" in dialog
        and "new LinearLayout.LayoutParams(dp(104), dp(26))" in dialog,
    "no nested scrolling view": "card.addView(bodyScroll" not in dialog and "ScrollView bodyScroll =" not in dialog,
    "save uses commit and verifies readback": ".commit();" in save_method and "prefs.getLong(KEY_RANGE_START_MS, -1L) != startMs" in save_method,
    "save syncs note-roll state": "noteRollView.setAbLoopEnabled(loopEnabled);" in save_method and "refreshNoteRollData();" in save_method,
    "success feedback reads saved values": "A/B 设置成功：" in dialog and "prefs.getLong(KEY_RANGE_START_MS, -1L)" in dialog,
    "failed save stays open": "if (saveAbLoopSettings(enabled, aField, bField))" in dialog and "A/B 保存失败" in save_method,
    "service list label prefixed": 'android:label="#奏乐触控服务"' in manifest,
    "old icon and app name preserved": 'android:icon="@drawable/launcher_luoke_v2"' in manifest and "奏乐" in (ROOT / "app/src/main/res/values/strings.xml").read_text(encoding="utf-8"),
    "version 1.4.0": "versionCode 14" in build and "versionName '1.4.0'" in build,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("Uniform-scale A/B/save audit failed: " + "; ".join(failed))
print("Applied A/B 1.4 layout: checkbox row has Reset/Done, set-A aligned to A field, narrow values, whole canvas scales uniformly.")
print("A/B settings are synchronously committed and read back before success feedback.")
print("AUDIT OK: " + "; ".join(checks.keys()))
