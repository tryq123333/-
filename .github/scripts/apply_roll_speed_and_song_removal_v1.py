from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "ROLL_SPEED_CONTROL_AND_SONG_REMOVAL_V1"

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": anchor missing.")

note = NOTE.read_text(encoding="utf-8")
if MARKER not in note:
    note = once(note,
        "        void onEditSegment();\n        void onToggleAbLoop();",
        "        void onEditSegment();\n        void onToggleAbLoop();\n        void onSpeedChange(int speedPercent);",
        "add note-roll speed callback")

    note = once(note,
        "    private static final int TOUCH_REWIND = 9;",
        "    private static final int TOUCH_REWIND = 9;\n    private static final int TOUCH_SPEED = 10;",
        "add speed slider touch mode")
    note = once(note,
        "    private int speedPercent = 100;",
        "    private int speedPercent = 100;\n    private int speedAtDown = 100;",
        "remember speed at gesture start")

    note = once(note,
        """        drawHeaderChip(canvas, new RectF(70 * density, 52 * density, 95 * density, 69 * density),
                "⏮︎", 0xff455667, density);
    }""",
        """        drawHeaderChip(canvas, new RectF(70 * density, 52 * density, 95 * density, 69 * density),
                "⏮︎", 0xff455667, density);
        drawSpeedControl(canvas, w, density);
    }

    private void drawSpeedControl(Canvas canvas, float width, float density) {
        float left = 8 * density;
        float right = Math.min(95 * density, width - 8 * density);
        if (right - left < 24 * density) return;
        paint.setStyle(Paint.Style.FILL);
        paint.setFakeBoldText(true);
        paint.setTextSize(7.5f * density);
        paint.setColor(0xbfeaf0f4);
        canvas.drawText("速度 " + speedPercent + "%", left, 79 * density, paint);
        paint.setFakeBoldText(false);

        float trackLeft = left;
        float trackRight = right;
        float trackY = 88 * density;
        float fraction = (speedPercent - 50) / 150f;
        float thumbX = trackLeft + (trackRight - trackLeft) * fraction;
        paint.setStrokeWidth(2.5f * density);
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setColor(0x777c8d99);
        canvas.drawLine(trackLeft, trackY, trackRight, trackY, paint);
        paint.setColor(0xff70d9ba);
        canvas.drawLine(trackLeft, trackY, thumbX, trackY, paint);
        paint.setStrokeCap(Paint.Cap.BUTT);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(0xffedf7f4);
        canvas.drawCircle(thumbX, trackY, 3 * density, paint);
        paint.setColor(0xff4c8d80);
        canvas.drawCircle(thumbX, trackY, 1.6f * density, paint);
    }

    private int speedFromX(float x, float density, float width) {
        float left = 8 * density;
        float right = Math.min(95 * density, width - 8 * density);
        float fraction = Math.max(0f, Math.min(1f, (x - left) / Math.max(1f, right - left)));
        int raw = Math.round(50 + fraction * 150);
        return Math.max(50, Math.min(200, Math.round(raw / 5f) * 5));
    }""",
        "draw compact speed slider directly beneath A/B row")

    note = once(note,
        """                } else if (y >= 50 * density && y < 72 * density
                        && x > 69 * density && x <= 97 * density) {
                    touchMode = TOUCH_REWIND;
                } else if (touchEdges != 0) {""",
        """                } else if (y >= 50 * density && y < 72 * density
                        && x > 69 * density && x <= 97 * density) {
                    touchMode = TOUCH_REWIND;
                } else if (y >= 71 * density && y <= 96 * density
                        && x >= 5 * density && x <= Math.min(98 * density, w - 5 * density)) {
                    touchMode = TOUCH_SPEED;
                    speedAtDown = speedPercent;
                    speedPercent = speedFromX(x, density, w);
                    invalidate();
                } else if (touchEdges != 0) {""",
        "recognize touch on speed slider")

    note = once(note,
        """                if (Math.hypot(rawDx, rawDy) > touchSlop) gestureMoved = true;
                if (touchMode == TOUCH_MOVE_WINDOW) {""",
        """                if (Math.hypot(rawDx, rawDy) > touchSlop) gestureMoved = true;
                if (touchMode == TOUCH_SPEED) {
                    speedPercent = speedFromX(x, density, w);
                    invalidate();
                } else if (touchMode == TOUCH_MOVE_WINDOW) {""",
        "update speed slider while dragging")

    note = once(note,
        """                if (touchMode == TOUCH_CLOSE && !gestureMoved) {""",
        """                if (touchMode == TOUCH_SPEED) {
                    if (interactionListener != null && speedPercent != speedAtDown) {
                        interactionListener.onSpeedChange(speedPercent);
                    }
                } else if (touchMode == TOUCH_CLOSE && !gestureMoved) {""",
        "commit speed change on release")

    note = once(note,
        """                else if (touchMode == TOUCH_RANGE_EDIT) {
                    rangeStartMicros = rangeStartAtDown;
                    rangeEndMicros = rangeEndAtDown;
                }
                scrubbing = false;""",
        """                else if (touchMode == TOUCH_RANGE_EDIT) {
                    rangeStartMicros = rangeStartAtDown;
                    rangeEndMicros = rangeEndAtDown;
                } else if (touchMode == TOUCH_SPEED) {
                    speedPercent = speedAtDown;
                }
                scrubbing = false;""",
        "restore speed when gesture cancelled")

    note = note.replace(
        "ROLL_REWIND_NEXT_TO_AB_V7",
        "ROLL_REWIND_NEXT_TO_AB_V7 " + MARKER,
        1)
    NOTE.write_text(note, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
if MARKER not in service:
    if "import android.app.AlertDialog;" not in service:
        service = service.replace("import android.accessibilityservice.AccessibilityService;",
                                  "import android.accessibilityservice.AccessibilityService;\nimport android.app.AlertDialog;", 1)

    speed_callback = "                @Override public void onSpeedChange(int speedPercent) { changePlaybackSpeedFromNoteRoll(speedPercent); }"
    if speed_callback not in service:
        service = once(service,
            "                @Override public void onToggleAbLoop() { toggleAbLoopEnabled(); }",
            "                @Override public void onToggleAbLoop() { toggleAbLoopEnabled(); }\n" + speed_callback,
            "connect speed slider to playback controller")

    # Put each song's remove button alongside its title, without changing the title click selection.
    old_title = """            TextView item = new TextView(this);
            item.setText((selected ? "✓  " : "♪  ") + imported.name);
            item.setTextColor(selected ? 0xff125744 : 0xff253441);
            item.setTextSize(13);
            item.setMaxLines(2);
            item.setPadding(dp(3), dp(3), dp(3), dp(2));
            songCard.addView(item, new LinearLayout.LayoutParams(-1, -2));"""
    new_title = """            LinearLayout titleRow = new LinearLayout(this);
            titleRow.setOrientation(LinearLayout.HORIZONTAL);
            titleRow.setGravity(Gravity.CENTER_VERTICAL);
            TextView item = new TextView(this);
            item.setText((selected ? "✓  " : "♪  ") + imported.name);
            item.setTextColor(selected ? 0xff125744 : 0xff253441);
            item.setTextSize(13);
            item.setMaxLines(2);
            item.setPadding(dp(3), dp(3), dp(3), dp(2));
            titleRow.addView(item, new LinearLayout.LayoutParams(0, -2, 1f));
            Button removeSongButton = dialogButton("移除", 0xffa94f50);
            LinearLayout.LayoutParams removeSongParams = new LinearLayout.LayoutParams(dp(48), dp(29));
            removeSongParams.setMargins(dp(5), dp(1), 0, dp(1));
            titleRow.addView(removeSongButton, removeSongParams);
            songCard.addView(titleRow, new LinearLayout.LayoutParams(-1, -2));
            removeSongButton.setOnClickListener(v -> confirmRemoveImportedSong(imported));"""
    service = once(service, old_title, new_title, "add per-song remove button")

    helper_anchor = "    private String describeSongRange(File file, int transpose) {"
    helper = """    private void confirmRemoveImportedSong(ImportedSong imported) {
        if (imported == null || imported.file == null) return;
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("移除曲目")
                .setMessage("确定从本应用曲目列表移除“" + imported.name
                        + "”吗？只删除应用内导入副本，不会删除下载目录中的原始文件。")
                .setNegativeButton("取消", (d, which) -> d.dismiss())
                .setPositiveButton("移除", (d, which) -> removeImportedSongNow(imported))
                .create();
        try {
            if (dialog.getWindow() != null) {
                dialog.getWindow().setType(WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY);
            }
            dialog.show();
        } catch (Exception ex) {
            toast("无法显示移除确认窗口，请稍后重试。");
        }
    }

    private void removeImportedSongNow(ImportedSong imported) {
        if (imported == null || imported.file == null) return;
        String path = imported.file.getAbsolutePath();
        String selectedPath = prefs.getString(MainActivity.KEY_SONG_PATH, "");
        boolean selected = path.equals(selectedPath);

        if (selected && playbackThread != null && playbackThread.isAlive()) {
            if (!stopRequested) stopPlayback();
            mainHandler.postDelayed(() -> removeImportedSongNow(imported), 100L);
            return;
        }

        if (imported.file.exists() && !imported.file.delete()) {
            toast("移除失败：文件暂时无法删除。");
            return;
        }

        SharedPreferences.Editor editor = prefs.edit()
                .remove("song_label_" + imported.file.getName())
                .remove(MainActivity.songTransposePreferenceKey(path));
        if (selected) {
            editor.remove(MainActivity.KEY_SONG_PATH)
                    .remove(MainActivity.KEY_SONG_NAME)
                    .putInt(MainActivity.KEY_TRANSPOSE, 0)
                    .remove(KEY_RANGE_START_MS)
                    .remove(KEY_RANGE_END_MS)
                    .putBoolean("note_roll_enabled", false);
            playbackPositionMicros = 0L;
            playbackBaseMicros = 0L;
            seekRequestMicros = 0L;
            currentSong = null;
            if (noteRollView != null) {
                removeOverlay(noteRollView);
                noteRollView = null;
            }
        }
        editor.apply();
        if (selected) updateControlPanelPlaybackButtons();
        toast("已移除曲目：" + imported.name);
        dismissSegmentDialog();
        showSongPickerDialog();
    }

"""
    if helper_anchor not in service and "private void confirmRemoveImportedSong(" not in service:
        raise SystemExit("Cannot locate insertion point for song removal helpers.")
    if "private void confirmRemoveImportedSong(" not in service:
        service = service.replace(helper_anchor, helper + helper_anchor, 1)

    # Runtime speed applies to the running playback after a clean timeline rebase, or is saved for next start.
    speed_anchor = "    private void savePracticeRange(long startMs, long endMs, int speed) {"
    speed_helper = """    private void changePlaybackSpeedFromNoteRoll(int requestedSpeed) {
        int nextSpeed = Math.max(50, Math.min(200, Math.round(requestedSpeed / 5f) * 5));
        int previousSpeed = activeSpeedPercent;
        boolean running = playbackThread != null && playbackThread.isAlive()
                && playbackActive && !stopRequested;
        if (running) {
            synchronized (playbackLock) {
                long now = SystemClock.elapsedRealtime();
                long cursor = playbackPositionMicros;
                if (!paused) {
                    long elapsed = Math.max(0L, now - playbackStartMs - pausedDurationMs);
                    cursor = playbackBaseMicros + elapsed * Math.max(50, Math.min(200, previousSpeed)) * 10L;
                }
                long start = playbackRangeStartMicros;
                long end = Math.max(start + 1L, playbackRangeEndMicros);
                cursor = Math.max(start, Math.min(end - 1L, cursor));
                playbackPositionMicros = cursor;
                playbackBaseMicros = cursor;
                seekRequestMicros = cursor;
                seekRequestVersion++;
                playbackUiGeneration++;
                activeSpeedPercent = nextSpeed;
                prefs.edit().putInt(MainActivity.KEY_SPEED, nextSpeed).apply();
                playbackLock.notifyAll();
            }
        } else {
            activeSpeedPercent = nextSpeed;
            prefs.edit().putInt(MainActivity.KEY_SPEED, nextSpeed).apply();
        }
        if (noteRollView != null) noteRollView.setCursor(playbackPositionMicros, playbackActive && !paused);
        toast("演奏速度：" + nextSpeed + "%");
    }

"""
    if speed_anchor not in service and "private void changePlaybackSpeedFromNoteRoll(" not in service:
        raise SystemExit("Cannot locate insertion point for playback speed handler.")
    if "private void changePlaybackSpeedFromNoteRoll(" not in service:
        service = service.replace(speed_anchor, speed_helper + speed_anchor, 1)

    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER,
            1)
    SERVICE.write_text(service, encoding="utf-8")

    # The scheduler reads the live speed for the next note batch. Speed changes also bump the
    # seek version, so a wait already in progress exits and recalculates from the rebased cursor.
    service = SERVICE.read_text(encoding="utf-8")
    speed_refresh_line = "                    speedPercent = Math.max(50, Math.min(200, activeSpeedPercent));"
    scheduler_anchor = """                    index = firstNoteAtOrAfter(song, baseMicros);
                    mainHandler.post(() -> {"""
    if speed_refresh_line not in service and scheduler_anchor in service:
        service = service.replace(scheduler_anchor,
            """                    index = firstNoteAtOrAfter(song, baseMicros);
    """ + speed_refresh_line + """
                    mainHandler.post(() -> {""", 1)
    elif speed_refresh_line not in service:
        raise SystemExit("Cannot locate playback scheduler anchor for speed refresh.")
    SERVICE.write_text(service, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 6", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.6.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
picker_start = service.find("    private void showSongPickerDialog()")
picker_end = service.find("    private void confirmRemoveImportedSong(", picker_start)
picker = service[picker_start:picker_end]
if "速度 " not in note or "drawSpeedControl(canvas, w, density);" not in note:
    raise SystemExit("Speed control drawing is missing.")
if "touchMode = TOUCH_SPEED;" not in note or "onSpeedChange(speedPercent)" not in note:
    raise SystemExit("Speed control touch interaction is missing.")
if "changePlaybackSpeedFromNoteRoll(int requestedSpeed)" not in service:
    raise SystemExit("Live speed callback is missing.")
if 'dialogButton("移除", 0xffa94f50)' not in picker or "confirmRemoveImportedSong(imported)" not in picker:
    raise SystemExit("Per-song remove button is missing.")
if "private void removeImportedSongNow(ImportedSong imported)" not in service:
    raise SystemExit("Remove song handler is missing.")
if "versionCode 6" not in BUILD.read_text(encoding="utf-8") or "versionName '0.6.0'" not in BUILD.read_text(encoding="utf-8"):
    raise SystemExit("Application version bump missing.")
print("Added compact note-roll speed control with live playback rebasing and per-song remove confirmation.")
