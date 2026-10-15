from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
ACTIVITY = ROOT / "app/src/main/java/com/luoke/autopiano/MainActivity.java"
MARKER = "SONG_SPECIFIC_ROLL_UI_V2"


def once(source, old, new, label):
    if old not in source:
        raise SystemExit("Cannot patch " + label + ": anchor missing.")
    return source.replace(old, new, 1)


note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
activity = ACTIVITY.read_text(encoding="utf-8")

if MARKER not in note:
    note = note.replace(
        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 */",
        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 */", 1)
    if MARKER not in note:
        raise SystemExit("NoteRollView source marker was not found.")

    note = once(note,
        "        void onTogglePlayPause();\n        void onRewind();",
        "        void onTogglePlayPause();\n        void onRewind();\n        void onBeginSeekGesture();\n        void onEndSeekGesture();",
        "seek gesture callbacks")
    note = once(note,
        "    private boolean absoluteSeekMoved;\n    private boolean windowGestureStarted;",
        "    private boolean absoluteSeekMoved;\n    private boolean windowGestureStarted;\n    private boolean seekGestureStarted;\n    private boolean useGameKeyIcons = true;",
        "seek gesture state")

    note = once(note,
        "        this.playing = playing;\n        invalidate();",
        """        this.playing = playing;
        useGameKeyIcons = !InstrumentLayout.MODE_PIANO88.equals(
                getContext().getSharedPreferences(MainActivity.PREFS, Context.MODE_PRIVATE)
                        .getString(InstrumentLayout.KEY_LAYOUT_MODE, InstrumentLayout.MODE_NINE));
        invalidate();""",
        "mode-specific note labels")

    note = once(note,
        "                String noteLabel = MidiParser.noteName(pitch);\n                paint.setTextSize(Math.max(6.8f * density, Math.min(8.2f * density, laneHeight * .48f)));\n                paint.setFakeBoldText(true);\n                float labelTextWidth = paint.measureText(noteLabel);\n                float badgeWidth = labelTextWidth + 9 * density;",
        """                String noteLabel = MidiParser.noteName(pitch);
                int keyIconIndex = InstrumentLayout.indexOfPitch(pitch);
                paint.setTextSize(Math.max(6.8f * density, Math.min(8.2f * density, laneHeight * .48f)));
                paint.setFakeBoldText(true);
                float labelTextWidth = paint.measureText(noteLabel);
                float badgeWidth = useGameKeyIcons && keyIconIndex >= 0
                        ? 20 * density : labelTextWidth + 9 * density;""",
        "instrument key icon mapping")

    badge_start = note.find("                    // Every note gets a contrasting badge; minimum block width prevents missing pitch text.")
    badge_end_marker = "                    canvas.drawText(noteLabel, textX, textY, paint);"
    badge_end = note.find(badge_end_marker, badge_start)
    if badge_start < 0 or badge_end < 0:
        raise SystemExit("Cannot locate current note badge drawing block.")
    badge_end += len(badge_end_marker)
    badge_code = """                    // Nine-note handpan uses the same pictograms as the in-game keys.
                    // The 88-key piano mode keeps conventional pitch labels.
                    float availableBadgeWidth = Math.min(badgeWidth, Math.max(10 * density, right - left));
                    float badgeHeight = Math.max(9 * density, Math.min(bar.height() - 2 * density, 18 * density));
                    float badgeLeft = Math.max(left, Math.min(bar.left + 2 * density, right - availableBadgeWidth));
                    RectF badge = new RectF(badgeLeft, bar.centerY() - badgeHeight / 2f,
                            badgeLeft + availableBadgeWidth, bar.centerY() + badgeHeight / 2f);
                    if (useGameKeyIcons && keyIconIndex >= 0) {
                        drawGameKeyIcon(canvas, badge.centerX(), badge.centerY(),
                                Math.min(badge.width(), badge.height()) * .5f, keyIconIndex, noteAlpha);
                    } else {
                        paint.setColor(0xfff4f6f4);
                        paint.setAlpha(Math.min(245, noteAlpha));
                        canvas.drawRoundRect(badge, badgeHeight / 2f, badgeHeight / 2f, paint);
                        paint.setColor(0xff1d3039);
                        paint.setAlpha(noteAlpha);
                        paint.setTextSize(Math.max(6.5f * density, Math.min(8.2f * density, badgeHeight * .60f)));
                        paint.setFakeBoldText(true);
                        float actualTextWidth = paint.measureText(noteLabel);
                        float textX = badge.centerX() - actualTextWidth / 2f;
                        float textY = badge.centerY() - (paint.ascent() + paint.descent()) / 2f;
                        canvas.drawText(noteLabel, textX, textY, paint);
                    }"""
    note = note[:badge_start] + badge_code + note[badge_end:]

    note = once(note,
        """    private static float getPlayheadX(float width, float left, float right, float density) {
        float desired = width * .30f;
        float minimum = left + 34 * density;
        return Math.max(minimum, Math.min(right - 28 * density, desired));
    }""",
        """    private static float getPlayheadX(float width, float left, float right, float density) {
        // Keep the fade/playhead line just to the right of the ⏮︎ chip.
        float afterRewind = 100 * density;
        return Math.max(left + 92 * density, Math.min(right - 24 * density, afterRewind));
    }""",
        "playhead position")

    draw_icon = """    private void drawGameKeyIcon(Canvas canvas, float cx, float cy, float radius,
                                 int index, int alpha) {
        if (radius <= 0f) return;
        canvas.save();
        canvas.translate(cx - radius, cy - radius);
        float scale = radius * 2f / 100f;
        canvas.scale(scale, scale);
        paint.setStyle(Paint.Style.FILL);
        paint.setAlpha(alpha);
        paint.setColor(0xfff7efd9);
        canvas.drawCircle(50, 50, 48, paint);
        paint.setColor(0xffd9d0ba);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(2.2f);
        canvas.drawCircle(50, 50, 47, paint);
        paint.setStyle(Paint.Style.FILL);

        Path shape = new Path();
        switch (index) {
            case 0: // A2: low center note, dark blue crescent and lower dot.
                paint.setColor(0xff182b3c);
                shape.moveTo(28, 25); shape.lineTo(51, 25); shape.lineTo(51, 68);
                shape.lineTo(28, 58); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xff4b7e9b);
                shape.reset(); shape.moveTo(52, 27); shape.lineTo(72, 39);
                shape.lineTo(72, 56); shape.lineTo(52, 68); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xff17202a); canvas.drawCircle(51, 82, 5.2f, paint);
                break;
            case 1: // E3: green tapered stem.
                paint.setColor(0xff2b855b);
                shape.moveTo(34, 24); shape.lineTo(55, 24); shape.lineTo(55, 73);
                shape.lineTo(34, 88); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xff17202a); canvas.drawCircle(50, 16, 5, paint);
                break;
            case 2: // F3: purple upper bowl over a black foot.
                paint.setColor(0xff9b45c8);
                canvas.drawArc(new RectF(27, 24, 70, 66), 180, 180, true, paint);
                shape.reset(); shape.moveTo(28, 57); shape.lineTo(72, 57);
                shape.lineTo(60, 78); shape.lineTo(28, 78); shape.close();
                paint.setColor(0xff15191e); canvas.drawPath(shape, paint);
                paint.setColor(0xff17202a); canvas.drawCircle(50, 15, 5, paint);
                break;
            case 3: // G3: black upper flag and green lower bowl.
                paint.setColor(0xff15191e);
                shape.moveTo(31, 24); shape.lineTo(71, 24); shape.lineTo(62, 47);
                shape.lineTo(31, 47); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xff78a64a);
                canvas.drawArc(new RectF(29, 39, 70, 79), 0, 180, true, paint);
                paint.setColor(0xff17202a); canvas.drawCircle(50, 15, 5, paint);
                break;
            case 4: // A3: green bowl below a flat black cap.
                paint.setColor(0xff15191e);
                shape.moveTo(27, 24); shape.lineTo(72, 24); shape.lineTo(64, 40);
                shape.lineTo(27, 40); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xff78a64a);
                canvas.drawArc(new RectF(28, 37, 70, 79), 0, 180, true, paint);
                break;
            case 5: // B3: magenta half-disc and upright black bar.
                paint.setColor(0xffc13d85);
                canvas.drawArc(new RectF(24, 28, 65, 70), 90, 180, true, paint);
                paint.setColor(0xff15191e);
                canvas.drawRect(49, 27, 63, 70, paint);
                canvas.drawRect(49, 27, 74, 42, paint);
                break;
            case 6: // C4: orange lower wedge below black bar.
                paint.setColor(0xff15191e);
                canvas.drawRect(28, 25, 72, 40, paint);
                paint.setColor(0xffe98f27);
                shape.moveTo(49, 40); shape.lineTo(71, 40); shape.lineTo(60, 75);
                shape.lineTo(49, 84); shape.close(); canvas.drawPath(shape, paint);
                break;
            case 7: // D4: blue split key.
                paint.setColor(0xff15283d);
                shape.moveTo(29, 26); shape.lineTo(51, 26); shape.lineTo(51, 69);
                shape.lineTo(29, 69); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xff4f86b5);
                canvas.drawArc(new RectF(48, 39, 73, 68), 270, 180, true, paint);
                break;
            case 8: // E4: orange tapered foot below a black cap.
                paint.setColor(0xff15191e);
                shape.moveTo(24, 25); shape.lineTo(75, 25); shape.lineTo(69, 41);
                shape.lineTo(24, 41); shape.close(); canvas.drawPath(shape, paint);
                paint.setColor(0xffe98f27);
                shape.reset(); shape.moveTo(48, 41); shape.lineTo(69, 41);
                shape.lineTo(59, 76); shape.lineTo(48, 82); shape.close();
                canvas.drawPath(shape, paint);
                break;
            default:
                paint.setColor(0xff182b3c);
                canvas.drawCircle(50, 50, 17, paint);
        }
        paint.setAlpha(255);
        paint.setStyle(Paint.Style.FILL);
        canvas.restore();
    }

    private void beginSeekGesture() {
        if (seekGestureStarted) return;
        seekGestureStarted = true;
        if (interactionListener != null) interactionListener.onBeginSeekGesture();
    }

    private void endSeekGesture() {
        if (!seekGestureStarted) return;
        seekGestureStarted = false;
        if (interactionListener != null) interactionListener.onEndSeekGesture();
    }

"""
    note = once(note,
        "    private void drawResizeHandle(Canvas canvas, float w, float h, float density) {",
        draw_icon + "    private void drawResizeHandle(Canvas canvas, float w, float h, float density) {",
        "game key icon and seek callbacks")

    old_abs = """                    if (NoteRollGestureMath.shouldUpdateAbsoluteSeek(dx, dy, touchSlop)) {
                        absoluteSeekMoved = true;"""
    new_abs = """                    if (NoteRollGestureMath.shouldUpdateAbsoluteSeek(dx, dy, touchSlop)) {
                        beginSeekGesture();
                        absoluteSeekMoved = true;"""
    note = once(note, old_abs, new_abs, "absolute seek gesture pause")

    old_scrub = """                } else if (touchMode == TOUCH_SCRUB && Math.abs(dx) > touchSlop
                        && Math.abs(dx) > Math.abs(dy) * .85f) {
                    scrubbing = true;"""
    new_scrub = """                } else if (touchMode == TOUCH_SCRUB && Math.abs(dx) > touchSlop
                        && Math.abs(dx) > Math.abs(dy) * .85f) {
                    beginSeekGesture();
                    scrubbing = true;"""
    note = once(note, old_scrub, new_scrub, "note field seek gesture pause")

    old_up_abs = """                    scrubbing = false;
                    invalidate();
                } else if (touchMode == TOUCH_SCRUB && scrubbing) {
                    positionMicros = positionDuringScrub;
                    if (interactionListener != null) interactionListener.onSeek(positionMicros);
                    scrubbing = false;
                    invalidate();"""
    new_up_abs = """                    scrubbing = false;
                    endSeekGesture();
                    invalidate();
                } else if (touchMode == TOUCH_SCRUB && scrubbing) {
                    positionMicros = positionDuringScrub;
                    if (interactionListener != null) interactionListener.onSeek(positionMicros);
                    scrubbing = false;
                    endSeekGesture();
                    invalidate();"""
    note = once(note, old_up_abs, new_up_abs, "seek gesture resume after position commit")

    old_cancel = """                else if (touchMode == TOUCH_RANGE_EDIT) {
                    rangeStartMicros = rangeStartAtDown;
                    rangeEndMicros = rangeEndAtDown;
                }
                scrubbing = false;
                touchMode = TOUCH_NONE;"""
    new_cancel = """                else if (touchMode == TOUCH_RANGE_EDIT) {
                    rangeStartMicros = rangeStartAtDown;
                    rangeEndMicros = rangeEndAtDown;
                }
                scrubbing = false;
                endSeekGesture();
                touchMode = TOUCH_NONE;"""
    note = once(note, old_cancel, new_cancel, "cancel scrub cleanup")
    NOTE.write_text(note, encoding="utf-8")


# MainActivity stores each imported song's transpose separately, while keeping the legacy key
# mirrored for older code paths and for the selected song's main-screen slider.
if MARKER not in activity:
    activity = activity.replace(
        "    static final String KEY_SPEED = \"speed_percent\";",
        """    static final String KEY_SPEED = "speed_percent";

    static String songTransposePreferenceKey(String path) {
        return "song_transpose_" + Integer.toHexString(path == null ? 0 : path.hashCode());
    }

    static int songTranspose(SharedPreferences prefs, String path) {
        if (path == null || path.isEmpty()) return prefs.getInt(KEY_TRANSPOSE, 0);
        String key = songTransposePreferenceKey(path);
        if (prefs.contains(key)) return prefs.getInt(key, 0);
        return path.equals(prefs.getString(KEY_SONG_PATH, ""))
                ? prefs.getInt(KEY_TRANSPOSE, 0) : 0;
    }""",
        1)
    activity = once(activity,
        "        transposeBar.setProgress(prefs.getInt(KEY_TRANSPOSE, 0) + 12);",
        "        transposeBar.setProgress(songTranspose(prefs, prefs.getString(KEY_SONG_PATH, \"\")) + 12);",
        "initial song-specific transpose")
    activity = once(activity,
        """                int shift = progress - 12;
                prefs.edit().putInt(KEY_TRANSPOSE, shift).apply();""",
        """                int shift = progress - 12;
                String currentPath = prefs.getString(KEY_SONG_PATH, "");
                SharedPreferences.Editor transposeEdit = prefs.edit().putInt(KEY_TRANSPOSE, shift);
                if (currentPath != null && !currentPath.isEmpty()) {
                    transposeEdit.putInt(songTransposePreferenceKey(currentPath), shift);
                }
                transposeEdit.apply();""",
        "save transpose per song")
    activity = once(activity,
        """        pitchShiftValue.setText((prefs.getInt(KEY_TRANSPOSE, 0) > 0 ? "+" : "") + prefs.getInt(KEY_TRANSPOSE, 0) + " 半音");""",
        """        String activePath = prefs.getString(KEY_SONG_PATH, "");
        int activeTranspose = songTranspose(prefs, activePath);
        pitchShiftValue.setText((activeTranspose > 0 ? "+" : "") + activeTranspose + " 半音");""",
        "refresh per-song shift label")
    activity = once(activity,
        "            int transpose = prefs.getInt(KEY_TRANSPOSE, 0);\n            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);",
        "            int transpose = songTranspose(prefs, path);\n            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);",
        "range check with selected song transpose")
    activity = once(activity,
        """            prefs.edit().putString(KEY_SONG_PATH, out.getAbsolutePath()).putString(KEY_SONG_NAME, displayName)
                    .putString("song_label_" + out.getName(), displayName).apply();""",
        """            prefs.edit().putString(KEY_SONG_PATH, out.getAbsolutePath()).putString(KEY_SONG_NAME, displayName)
                    .putString("song_label_" + out.getName(), displayName)
                    .putInt(songTransposePreferenceKey(out.getAbsolutePath()), 0)
                    .putInt(KEY_TRANSPOSE, 0).apply();""",
        "new song default transpose")
    activity = activity.replace(
        "    static final String KEY_SPEED = \"speed_percent\";",
        "    static final String KEY_SPEED = \"speed_percent\";", 1)
    activity = activity.replace("    private static final int REQUEST_MIDI = 1001;",
        "    private static final int REQUEST_MIDI = 1001;\n    /** SONG_SPECIFIC_ROLL_UI_V2 */", 1)
    if "import android.content.SharedPreferences;" not in activity:
        activity = activity.replace("import android.content.Intent;", "import android.content.Intent;\nimport android.content.SharedPreferences;", 1)
    ACTIVITY.write_text(activity, encoding="utf-8")


# Floating panel controls are not duplicated while the note roll itself is open; calibration
# disappears after successful calibration until the user resets or changes the instrument layout.
if MARKER not in service:
    service = service.replace(
        "    private TextView pauseButton;",
        "    private TextView pauseButton;\n    private View startPlaybackButton;\n    private WindowManager.LayoutParams segmentOverlayParams;\n    private boolean playbackWasRunningBeforeNoteScrub;",
        1)
    service = service.replace(
        "        Button play = smallButton(\"开始\");",
        "        Button play = smallButton(\"开始\");\n        startPlaybackButton = play;",
        1)
    service = once(service,
        "        panel.addView(calibrate, flowButtonParams());",
        "        if (!calibrated) panel.addView(calibrate, flowButtonParams());",
        "hide completed calibration entry")
    service = once(service,
        "        calibrate.setOnClickListener(v -> beginCalibration());",
        "        calibrate.setOnClickListener(v -> beginCalibration());\n        updateControlPanelPlaybackButtons();",
        "panel playback action visibility")
    service = once(service,
        """                @Override public void onRewind() { rewindPlaybackToStart(); }
                @Override public void onEditSegment()""",
        """                @Override public void onRewind() { rewindPlaybackToStart(); }
                @Override public void onBeginSeekGesture() { beginNoteRollSeekGesture(); }
                @Override public void onEndSeekGesture() { endNoteRollSeekGesture(); }
                @Override public void onEditSegment()""",
        "wire pause-during-scrub")
    service = once(service,
        """                    noteRollView = null;
                    prefs.edit().putBoolean("note_roll_enabled", false).apply();""",
        """                    noteRollView = null;
                    updateControlPanelPlaybackButtons();
                    prefs.edit().putBoolean("note_roll_enabled", false).apply();""",
        "restore panel controls when roll closes")
    service = once(service,
        """        refreshNoteRollData();
    }

    private void beginRangeEditingFromControl()""",
        """        refreshNoteRollData();
        updateControlPanelPlaybackButtons();
    }

    private void beginRangeEditingFromControl()""",
        "hide duplicate panel controls when roll opens")
    service = once(service,
        """            removeOverlay(noteRollView);
            noteRollView = null;
            prefs.edit().putBoolean("note_roll_enabled", false).apply();""",
        """            removeOverlay(noteRollView);
            noteRollView = null;
            updateControlPanelPlaybackButtons();
            prefs.edit().putBoolean("note_roll_enabled", false).apply();""",
        "restore playback actions after toggle close")
    service = once(service,
        "    private void readCurrentSongUnused() {",
        "    private void readCurrentSongUnused() {",
        "placeholder",) if "    private void readCurrentSongUnused() {" in service else service

    # User-driven seeking temporarily pauses the scheduler, then seeks and resumes without
    # emitting pause/resume toast messages for every small swipe.
    seek_methods = """    private void beginNoteRollSeekGesture() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::beginNoteRollSeekGesture);
            return;
        }
        synchronized (playbackLock) {
            playbackWasRunningBeforeNoteScrub = playbackThread != null && playbackThread.isAlive()
                    && playbackActive && !paused && !stopRequested;
            if (playbackWasRunningBeforeNoteScrub) {
                paused = true;
                pauseStartedMs = SystemClock.elapsedRealtime();
                playbackLock.notifyAll();
            }
        }
    }

    private void endNoteRollSeekGesture() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::endNoteRollSeekGesture);
            return;
        }
        synchronized (playbackLock) {
            if (playbackWasRunningBeforeNoteScrub && playbackThread != null && playbackThread.isAlive()
                    && playbackActive && paused && !stopRequested) {
                long now = SystemClock.elapsedRealtime();
                pausedDurationMs += Math.max(0L, now - pauseStartedMs);
                paused = false;
            }
            playbackWasRunningBeforeNoteScrub = false;
            playbackLock.notifyAll();
        }
        refreshMiniPlaybackButton();
    }

    private void updateControlPanelPlaybackButtons() {
        int visibility = noteRollView == null ? View.VISIBLE : View.GONE;
        if (startPlaybackButton != null) startPlaybackButton.setVisibility(visibility);
        if (pauseButton != null) pauseButton.setVisibility(visibility);
    }

"""
    service = once(service,
        "    private void beginRangeEditingFromControl() {",
        seek_methods + "    private void beginRangeEditingFromControl() {",
        "pause/resume around user scrub")

    # Smaller A/B sheet, scrollable content, reliable close, and draggable/resizable window.
    dialog_start = service.find("    private void showSegmentDialog() {")
    dialog_end = service.find("    private void savePracticeRangeMicros(", dialog_start)
    if dialog_start < 0 or dialog_end < 0:
        raise SystemExit("Cannot locate A/B dialog boundaries.")
    dialog = service[dialog_start:dialog_end]
    dialog = once(dialog,
        '        close.setText("⌃");',
        '        close.setText("×");',
        "A/B close affordance")
    dialog = once(dialog,
        """        card.addView(titleRow);

        CheckBox enabled""",
        """        card.addView(titleRow);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        ScrollView bodyScroll = new ScrollView(this);
        bodyScroll.setFillViewport(false);
        bodyScroll.addView(body);
        card.addView(bodyScroll, new LinearLayout.LayoutParams(-1, 0, 1f));

        CheckBox enabled""",
        "A/B scrollable body")
    for old, new, label in [
        ("card.addView(enabled, checkParams);", "body.addView(enabled, checkParams);", "A/B checkbox placement"),
        ("card.addView(columns);", "body.addView(columns);", "A/B time fields placement"),
        ("card.addView(setButtons);", "body.addView(setButtons);", "A/B A/B buttons placement"),
        ("card.addView(footerButtons);", "body.addView(footerButtons);", "A/B footer placement"),
    ]:
        dialog = once(dialog, old, new, label)
    dialog = dialog.replace("new LinearLayout.LayoutParams(-1, dp(46))", "new LinearLayout.LayoutParams(-1, dp(40))", 1)
    dialog = dialog.replace("new LinearLayout.LayoutParams(-1, dp(64))", "new LinearLayout.LayoutParams(-1, dp(48))", 2)
    dialog = dialog.replace("new LinearLayout.LayoutParams(0, dp(48), 1f)", "new LinearLayout.LayoutParams(0, dp(40), 1f)", 2)
    dialog = dialog.replace("new LinearLayout.LayoutParams(0, dp(42), 1f)", "new LinearLayout.LayoutParams(0, dp(36), 1f)", 2)
    dialog = dialog.replace("setMargins(0, dp(14), dp(8), 0)", "setMargins(0, dp(8), dp(8), 0)", 1)
    dialog = dialog.replace("setMargins(dp(4), dp(14), 0, 0)", "setMargins(dp(4), dp(8), 0, 0)", 1)
    dialog = dialog.replace("setMargins(0, dp(12), dp(6), 0)", "setMargins(0, dp(8), dp(6), 0)", 1)
    dialog = dialog.replace("setMargins(dp(6), dp(12), 0, 0)", "setMargins(dp(6), dp(8), 0, 0)", 1)

    resize_insert = """        TextView resizeHandle = new TextView(this);
        resizeHandle.setText("↘ 拖动调整大小");
        resizeHandle.setTextColor(0xff71867a);
        resizeHandle.setTextSize(10);
        resizeHandle.setGravity(Gravity.RIGHT | Gravity.CENTER_VERTICAL);
        resizeHandle.setPadding(0, 0, dp(4), 0);
        card.addView(resizeHandle, new LinearLayout.LayoutParams(-1, dp(18)));

"""
    dialog = once(dialog,
        "        int screenWidth = getResources().getDisplayMetrics().widthPixels;",
        resize_insert + "        int screenWidth = getResources().getDisplayMetrics().widthPixels;",
        "A/B resize handle")
    old_params = """        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        WindowManager.LayoutParams overlayParams = new WindowManager.LayoutParams(
                Math.max(1, Math.min(screenWidth - dp(24), dp(520))),
                WindowManager.LayoutParams.WRAP_CONTENT,
                WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT);
        overlayParams.gravity = Gravity.TOP | Gravity.CENTER_HORIZONTAL;
        overlayParams.y = dp(42);
        overlayParams.softInputMode = WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE;
        segmentOverlay = card;
        close.setOnClickListener(v -> {
            if (saveAbLoopSettings(enabled, aField, bField)) dismissSegmentDialog();
        });"""
    new_params = """        int screenWidth = getResources().getDisplayMetrics().widthPixels;
        int screenHeight = getResources().getDisplayMetrics().heightPixels;
        int defaultWidth = Math.min(Math.max(dp(250), screenWidth - dp(20)), dp(350));
        int defaultHeight = Math.min(Math.max(dp(220), screenHeight - dp(24)), dp(280));
        int width = Math.max(dp(250), Math.min(screenWidth - dp(16),
                prefs.getInt("ab_dialog_width_px", defaultWidth)));
        int height = Math.max(dp(220), Math.min(screenHeight - dp(16),
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
                        downX = event.getRawX(); downY = event.getRawY();
                        startX = segmentOverlayParams.x; startY = segmentOverlayParams.y;
                        moved = false; return true;
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
                            try { windowManager.updateViewLayout(card, segmentOverlayParams); } catch (Exception ignored) { }
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (moved) prefs.edit().putInt("ab_dialog_x", segmentOverlayParams.x)
                                .putInt("ab_dialog_y", segmentOverlayParams.y).apply();
                        return true;
                    default: return true;
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
                        downX = event.getRawX(); downY = event.getRawY();
                        startWidth = segmentOverlayParams.width; startHeight = segmentOverlayParams.height;
                        moved = false; return true;
                    case MotionEvent.ACTION_MOVE:
                        float dx = event.getRawX() - downX;
                        float dy = event.getRawY() - downY;
                        if (Math.hypot(dx, dy) > dp(4)) moved = true;
                        if (moved) {
                            int maxW = getResources().getDisplayMetrics().widthPixels - dp(16);
                            int maxH = getResources().getDisplayMetrics().heightPixels - dp(16);
                            segmentOverlayParams.width = Math.max(dp(250), Math.min(maxW, startWidth + Math.round(dx)));
                            segmentOverlayParams.height = Math.max(dp(220), Math.min(maxH, startHeight + Math.round(dy)));
                            try { windowManager.updateViewLayout(card, segmentOverlayParams); } catch (Exception ignored) { }
                        }
                        return true;
                    case MotionEvent.ACTION_UP:
                        if (moved) prefs.edit().putInt("ab_dialog_width_px", segmentOverlayParams.width)
                                .putInt("ab_dialog_height_px", segmentOverlayParams.height).apply();
                        return true;
                    default: return true;
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
        close.setOnClickListener(v -> dismissSegmentDialog());"""
    dialog = once(dialog, old_params, new_params, "A/B compact draggable resizable window")
    dialog = once(dialog,
        """        try {
            windowManager.addView(card, overlayParams);
            card.requestFocus();
        } catch (Exception ex) {
            segmentOverlay = null;
            toast("A/B循环设置无法显示，请重新开启无障碍服务后重试。");
        }""",
        """        try {
            windowManager.addView(card, overlayParams);
            card.requestFocus();
        } catch (Exception ex) {
            segmentOverlay = null;
            segmentOverlayParams = null;
            toast("A/B循环设置无法显示，请重新开启无障碍服务后重试。");
        }""",
        "A/B window cleanup on failed open")
    service = service[:dialog_start] + dialog + service[dialog_end:]

    service = once(service,
        """    private void dismissSegmentDialog() {
        removeOverlay(segmentOverlay);
        segmentOverlay = null;
    }""",
        """    private void dismissSegmentDialog() {
        removeOverlay(segmentOverlay);
        segmentOverlay = null;
        segmentOverlayParams = null;
    }""",
        "release A/B window parameters")

    # Store/read transpose by imported file path so switching tracks restores its own shift.
    service = once(service,
        """        prefs.edit().putString(MainActivity.KEY_SONG_PATH, file.getAbsolutePath())
                .putString(MainActivity.KEY_SONG_NAME, displayName)
                .putLong(KEY_RANGE_START_MS, 0L).putLong(KEY_RANGE_END_MS, -1L).apply();""",
        """        String previousPath = prefs.getString(MainActivity.KEY_SONG_PATH, "");
        String transposeKey = MainActivity.songTransposePreferenceKey(file.getAbsolutePath());
        int selectedTranspose = prefs.contains(transposeKey) ? prefs.getInt(transposeKey, 0)
                : (file.getAbsolutePath().equals(previousPath) ? prefs.getInt(MainActivity.KEY_TRANSPOSE, 0) : 0);
        prefs.edit().putString(MainActivity.KEY_SONG_PATH, file.getAbsolutePath())
                .putString(MainActivity.KEY_SONG_NAME, displayName)
                .putInt(transposeKey, selectedTranspose).putInt(MainActivity.KEY_TRANSPOSE, selectedTranspose)
                .putLong(KEY_RANGE_START_MS, 0L).putLong(KEY_RANGE_END_MS, -1L).apply();""",
        "restore per-song transpose on selection")

    service = service.replace(
        "prefs.getInt(MainActivity.KEY_TRANSPOSE, 0), playbackPositionMicros,",
        "MainActivity.songTranspose(prefs, prefs.getString(MainActivity.KEY_SONG_PATH, \"\")), playbackPositionMicros,")
    service = service.replace(
        "int transpose = prefs.getInt(MainActivity.KEY_TRANSPOSE, 0);",
        "int transpose = MainActivity.songTranspose(prefs, prefs.getString(MainActivity.KEY_SONG_PATH, \"\"));")

    # Song picker displays a range result for each MIDI and stores each row's independent semitone shift.
    picker_start = service.find("    private void showSongPickerDialog() {")
    picker_end = service.find("    private void selectImportedSong(", picker_start)
    if picker_start < 0 or picker_end < 0:
        raise SystemExit("Cannot locate song picker boundaries.")
    picker = service[picker_start:picker_end]
    picker = once(picker,
        '        hint.setText("点选即可切换；演奏中切换会先停止当前曲目。");',
        '        hint.setText("点曲名切换歌曲；下方滑杆单独移调，音域检查会同步更新。");',
        "song picker hint")
    old_loop = """        for (ImportedSong imported : songs) {
            boolean selected = imported.file.getAbsolutePath().equals(currentPath);
            TextView item = new TextView(this);
            item.setText((selected ? "✓  " : "♪  ") + imported.name);
            item.setTextColor(selected ? 0xff125744 : 0xff253441);
            item.setTextSize(13);
            item.setMaxLines(2);
            item.setPadding(dp(11), dp(10), dp(11), dp(10));
            item.setBackground(rounded(selected ? 0xffc9f0e1 : 0xffe7edf3, dp(10)));
            LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(-1, -2);
            ip.setMargins(0, 0, 0, dp(5));
            rows.addView(item, ip);
            item.setOnClickListener(v -> selectImportedSong(imported.file.getAbsolutePath(), imported.name));
        }"""
    new_loop = """        for (ImportedSong imported : songs) {
            final String songPath = imported.file.getAbsolutePath();
            boolean selected = songPath.equals(currentPath);
            int shift = MainActivity.songTranspose(prefs, songPath);
            LinearLayout songCard = new LinearLayout(this);
            songCard.setOrientation(LinearLayout.VERTICAL);
            songCard.setPadding(dp(8), dp(6), dp(8), dp(4));
            songCard.setBackground(rounded(selected ? 0xffd9f0e6 : 0xffe7edf3, dp(10)));

            TextView item = new TextView(this);
            item.setText((selected ? "✓  " : "♪  ") + imported.name);
            item.setTextColor(selected ? 0xff125744 : 0xff253441);
            item.setTextSize(13);
            item.setMaxLines(2);
            item.setPadding(dp(3), dp(3), dp(3), dp(2));
            songCard.addView(item, new LinearLayout.LayoutParams(-1, -2));

            TextView rangeInfo = new TextView(this);
            rangeInfo.setText(describeSongRange(imported.file, shift));
            rangeInfo.setTextColor(0xff617583);
            rangeInfo.setTextSize(10);
            rangeInfo.setPadding(dp(3), 0, dp(3), 0);
            songCard.addView(rangeInfo, new LinearLayout.LayoutParams(-1, -2));

            SeekBar shiftBar = new SeekBar(this);
            shiftBar.setMax(24);
            shiftBar.setProgress(Math.max(0, Math.min(24, shift + 12)));
            songCard.addView(shiftBar, new LinearLayout.LayoutParams(-1, dp(34)));
            LinearLayout.LayoutParams ip = new LinearLayout.LayoutParams(-1, -2);
            ip.setMargins(0, 0, 0, dp(6));
            rows.addView(songCard, ip);
            item.setOnClickListener(v -> selectImportedSong(songPath, imported.name));
            shiftBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                @Override public void onProgressChanged(SeekBar bar, int progress, boolean fromUser) {
                    if (!fromUser) return;
                    int nextShift = progress - 12;
                    boolean selectedSong = songPath.equals(prefs.getString(MainActivity.KEY_SONG_PATH, ""));
                    if (selectedSong && playbackThread != null && playbackThread.isAlive()
                            && playbackActive && !stopRequested) stopPlayback();
                    SharedPreferences.Editor editor = prefs.edit()
                            .putInt(MainActivity.songTransposePreferenceKey(songPath), nextShift);
                    if (selectedSong) editor.putInt(MainActivity.KEY_TRANSPOSE, nextShift);
                    editor.apply();
                    rangeInfo.setText(describeSongRange(imported.file, nextShift));
                    if (selectedSong && noteRollView != null) refreshNoteRollData();
                }
                @Override public void onStartTrackingTouch(SeekBar bar) { }
                @Override public void onStopTrackingTouch(SeekBar bar) { }
            });
        }"""
    picker = once(picker, old_loop, new_loop, "per-song pitch range and transpose slider")
    service = service[:picker_start] + picker + service[picker_end:]

    describe_method = """    private String describeSongRange(File file, int transpose) {
        String shift = (transpose > 0 ? "+" : "") + transpose;
        try {
            MidiParser.MidiSong song = MidiParser.parse(file);
            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);
            if (missing.isEmpty()) return "移调 " + shift + " 半音 · 音域检查通过";
            StringBuilder text = new StringBuilder("移调 ").append(shift).append(" 半音 · 超出音域 ")
                    .append(missing.size()).append(" 种：");
            for (int i = 0; i < Math.min(4, missing.size()); i++) {
                if (i > 0) text.append("、");
                text.append(missing.get(i));
            }
            if (missing.size() > 4) text.append("…");
            return text.toString();
        } catch (Exception ex) {
            return "移调 " + shift + " 半音 · 曲谱读取失败";
        }
    }

"""
    service = once(service,
        "    private void selectImportedSong(String path, String displayName) {",
        describe_method + "    private void selectImportedSong(String path, String displayName) {",
        "song range summary helper")

    # Marker the service; subsequent workflow runs preserve the changes in the source archive.
    service = service.replace(
        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 */",
        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 */", 1)
    SERVICE.write_text(service, encoding="utf-8")

# Keep marker visible in all patched Java sources and validate key postconditions.
note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
activity = ACTIVITY.read_text(encoding="utf-8")
if MARKER not in note or MARKER not in service or MARKER not in activity:
    raise SystemExit("Song-specific roll UI marker missing.")
for check, label in [
    ('"演奏", playing ? 0xff4c8d80 : 0xff455667', "single highlighted performance control"),
    ('drawGameKeyIcon(canvas, badge.centerX()', "game key icon drawing"),
    ('float afterRewind = 100 * density;', "playhead next to rewind control"),
    ('void onBeginSeekGesture()', "scrub start callback"),
    ('void onEndSeekGesture()', "scrub end callback"),
]:
    if check not in note:
        raise SystemExit("Missing NoteRollView postcondition: " + label)
for check, label in [
    ('if (!calibrated) panel.addView(calibrate, flowButtonParams());', "hide completed calibration control"),
    ('close.setOnClickListener(v -> dismissSegmentDialog());', "unconditional A/B close action"),
    ('"↘ 拖动调整大小"', "A/B resize handle"),
    ('private void beginNoteRollSeekGesture()', "pause playback during swipe"),
    ('private String describeSongRange(File file, int transpose)', "per-song pitch range summary"),
    ('MainActivity.songTranspose(prefs, prefs.getString(MainActivity.KEY_SONG_PATH, ""))', "selected song transpose"),
]:
    if check not in service:
        raise SystemExit("Missing MusicAccessibilityService postcondition: " + label)
if "songTransposePreferenceKey" not in activity or "songTranspose(prefs, path)" not in activity:
    raise SystemExit("MainActivity per-song transpose helpers are missing.")

print("Applied per-song transpose/range checks, in-game key icons, unified roll controls, smaller draggable/resizable A/B window, calibration visibility, and playback-safe seeking.")
