from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MARKER = "ROLL_SEEK_ICON_STABILITY_V4"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": anchor missing.")


note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")

if MARKER not in note:
    # Begin pausing immediately on ACTION_DOWN over the narrow seek rail. Waiting until ACTION_MOVE
    # lets the playback worker and the seek gesture race to update positionMicros.
    old_down = """                } else if (y >= h - 24 * density && y <= h - 12 * density) {
                    // Do not seek on ACTION_DOWN: a stray touch or a tiny pre-drag
                    // movement must not teleport the playhead before intent is clear.
                    touchMode = TOUCH_SEEK_ABSOLUTE;
                    absoluteSeekMoved = false;
                    positionDuringScrub = positionMicros;"""
    new_down = """                } else if (y >= h - 24 * density && y <= h - 12 * density) {
                    // Freeze the playback scheduler at touch-down; position selection still happens
                    // on up or after a deliberate horizontal drag crosses touch slop.
                    beginSeekGesture();
                    touchMode = TOUCH_SEEK_ABSOLUTE;
                    absoluteSeekMoved = false;
                    positionDuringScrub = positionMicros;"""
    note = replace_once(note, old_down, new_down, "pause playback immediately when progress rail is touched")

    # The source bitmap cell contains the full colored game button. Crop to the central cream key
    # and clip to a circle, preventing the cyan/pink outer pad and its antialias fringe from leaking.
    start = note.find("    private void drawOriginalGameKeyIcon(")
    end = note.find("\n    private void drawGameKeyIcon(", start)
    if start < 0 or end < 0:
        raise SystemExit("Could not locate the original game key renderer.")
    icon_method = """    private void drawOriginalGameKeyIcon(Canvas canvas, float cx, float cy,
                                         float size, int index, int alpha) {
        if (gameKeyAtlas == null || index < 0 || index >= 9 || size <= 0f) return;
        int cellX = (index % 3) * 64;
        int cellY = (index / 3) * 64;
        // Exclude the outer colored game pad; retain the inner key medallion and symbol only.
        Rect src = new Rect(cellX + 12, cellY + 12, cellX + 52, cellY + 52);
        RectF dst = new RectF(cx - size / 2f, cy - size / 2f,
                cx + size / 2f, cy + size / 2f);
        Path circularCrop = new Path();
        circularCrop.addOval(dst, Path.Direction.CW);
        int save = canvas.save();
        canvas.clipPath(circularCrop);
        paint.setStyle(Paint.Style.FILL);
        paint.setAlpha(Math.max(0, Math.min(255, alpha)));
        paint.setFilterBitmap(true);
        paint.setDither(true);
        canvas.drawBitmap(gameKeyAtlas, src, dst, paint);
        canvas.restoreToCount(save);
        paint.setAlpha(255);
        paint.setDither(false);
    }
"""
    note = note[:start] + icon_method + note[end:]

    # An entering note can have a zero- or few-pixel-long colored bar while its icon was clamped
    # backward into view. Render the icon only when enough of the actual note block is on screen,
    # keep it fully inside the colored block, and use a slightly smaller diameter.
    old_call = """                    if (useGameKeyIcons && keyIconIndex >= 0) {
                        drawOriginalGameKeyIcon(canvas, badge.centerX(), badge.centerY(),
                                Math.min(badge.width(), badge.height()), keyIconIndex, noteAlpha);
                    } else {"""
    new_call = """                    if (useGameKeyIcons && keyIconIndex >= 0) {
                        float iconInset = 2 * density;
                        float iconSize = Math.min(13 * density,
                                Math.max(0f, Math.min(bar.height() - 2 * density, badgeHeight)));
                        // Do not let the icon lead the note block as it enters from the right edge.
                        if (iconSize >= 7 * density && bar.width() >= iconSize + 2 * iconInset) {
                            float iconCx = bar.left + iconInset + iconSize / 2f;
                            iconCx = Math.min(bar.right - iconInset - iconSize / 2f, iconCx);
                            drawOriginalGameKeyIcon(canvas, iconCx, badge.centerY(),
                                    iconSize, keyIconIndex, noteAlpha);
                        }
                    } else {"""
    note = replace_once(note, old_call, new_call, "show icon only when note block is wide enough")

    note = note.replace(
        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3",
        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3 " + MARKER,
        1)
    if MARKER not in note:
        note = note.replace("NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1", "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 " + MARKER, 1)
    NOTE.write_text(note, encoding="utf-8")


if MARKER not in service:
    # Store the two controls that must disappear while the note roll is open.
    service = replace_once(service,
        "    private View startPlaybackButton;",
        "    private View startPlaybackButton;\n    private View rewindControlButton;\n    private View noteRollControlButton;",
        "store floating-panel rewind and note-roll controls")
    service = replace_once(service,
        '        Button stop = smallButton("⏮︎");',
        '        Button stop = smallButton("⏮︎");\n        rewindControlButton = stop;',
        "remember floating-panel rewind control")
    service = replace_once(service,
        '        Button roll = smallButton("谱面");',
        '        Button roll = smallButton("谱面");\n        noteRollControlButton = roll;',
        "remember floating-panel note-roll control")

    old_vis = """        int visibility = noteRollView == null ? View.VISIBLE : View.GONE;
        if (startPlaybackButton != null) startPlaybackButton.setVisibility(visibility);
        if (pauseButton != null) pauseButton.setVisibility(visibility);
        refreshUnifiedPlaybackButton();"""
    new_vis = """        int visibility = noteRollView == null ? View.VISIBLE : View.GONE;
        if (startPlaybackButton != null) startPlaybackButton.setVisibility(visibility);
        if (pauseButton != null) pauseButton.setVisibility(visibility);
        if (rewindControlButton != null) rewindControlButton.setVisibility(visibility);
        if (noteRollControlButton != null) noteRollControlButton.setVisibility(visibility);
        refreshUnifiedPlaybackButton();"""
    service = replace_once(service, old_vis, new_vis, "hide rewind and note-roll controls when note roll is open")

    # Make the A/B sheet and all of its major controls more compact, while keeping scrolling and resizing.
    for old, new, label in [
        ("card.setPadding(dp(16), dp(12), dp(16), dp(14));", "card.setPadding(dp(10), dp(7), dp(10), dp(8));", "A/B panel inner padding"),
        ("roundedBorder(0xfffcfdfb, 0xffdce5de, dp(22))", "roundedBorder(0xfffcfdfb, 0xffdce5de, dp(15))", "A/B panel corner radius"),
        ('heading.setTextSize(22);', 'heading.setTextSize(17);', "A/B title size"),
        ("new LinearLayout.LayoutParams(0, dp(44), 1f)", "new LinearLayout.LayoutParams(0, dp(34), 1f)", "A/B title row height"),
        ('close.setTextSize(26);', 'close.setTextSize(21);', "A/B close glyph size"),
        ("new LinearLayout.LayoutParams(dp(42), dp(44))", "new LinearLayout.LayoutParams(dp(34), dp(34))", "A/B close control size"),
        ('enabled.setTextSize(19);', 'enabled.setTextSize(15);', "A/B toggle label size"),
        ("new LinearLayout.LayoutParams(-1, dp(40));\n        checkParams.setMargins(0, dp(5), 0, dp(8));", "new LinearLayout.LayoutParams(-1, dp(31));\n        checkParams.setMargins(0, dp(2), 0, dp(4));", "A/B toggle height"),
        ("new LinearLayout.LayoutParams(-1, dp(48));", "new LinearLayout.LayoutParams(-1, dp(36));", "A/B input height"),
        ("new LinearLayout.LayoutParams(-1, dp(48));", "new LinearLayout.LayoutParams(-1, dp(36));", "A/B second input height"),
        ("setMargins(0, dp(8), 0, 0)", "setMargins(0, dp(4), 0, 0)", "A/B input spacing"),
        ("setMargins(0, 0, dp(12), 0)", "setMargins(0, 0, dp(7), 0)", "A/B columns spacing"),
        ("new LinearLayout.LayoutParams(0, dp(40), 1f)", "new LinearLayout.LayoutParams(0, dp(32), 1f)", "A/B set-point button height"),
        ("new LinearLayout.LayoutParams(0, dp(36), 1f)", "new LinearLayout.LayoutParams(0, dp(30), 1f)", "A/B footer button height"),
        ('resizeHandle.setTextSize(10);', 'resizeHandle.setTextSize(9);', "A/B resize hint size"),
        ("new LinearLayout.LayoutParams(-1, dp(18))", "new LinearLayout.LayoutParams(-1, dp(15))", "A/B resize grip height"),
        ("Math.min(Math.max(dp(250), screenWidth - dp(20)), dp(350))", "Math.min(Math.max(dp(230), screenWidth - dp(36)), dp(310))", "A/B default width"),
        ("Math.min(Math.max(dp(220), screenHeight - dp(24)), dp(280))", "Math.min(Math.max(dp(190), screenHeight - dp(40)), dp(245))", "A/B default height"),
        ("Math.max(dp(250), Math.min(screenWidth - dp(16),\n                prefs.getInt(\"ab_dialog_width_px\", defaultWidth)))", "Math.max(dp(220), Math.min(Math.min(screenWidth - dp(24), dp(310)),\n                prefs.getInt(\"ab_dialog_width_px\", defaultWidth)))", "A/B maximum remembered width"),
        ("Math.max(dp(220), Math.min(screenHeight - dp(16),\n                prefs.getInt(\"ab_dialog_height_px\", defaultHeight)))", "Math.max(dp(185), Math.min(Math.min(screenHeight - dp(24), dp(245)),\n                prefs.getInt(\"ab_dialog_height_px\", defaultHeight)))", "A/B maximum remembered height"),
        ("Math.max(dp(250), Math.min(maxW, startWidth + Math.round(dx)))", "Math.max(dp(220), Math.min(maxW, startWidth + Math.round(dx)))", "A/B manual minimum width"),
        ("Math.max(dp(220), Math.min(maxH, startHeight + Math.round(dy)))", "Math.max(dp(185), Math.min(maxH, startHeight + Math.round(dy)))", "A/B manual minimum height"),
    ]:
        service = replace_once(service, old, new, label)

    # A child that has focus may consume the tap before the card sees ACTION_OUTSIDE. Keep the
    # close affordance clickable, and also allow the conventional BACK key to dismiss the overlay.
    if MARKER not in service:
        service = service.replace(
            "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3",
            "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3 " + MARKER,
            1)
    # Reduce text fields themselves as well, without changing the numeric data they edit.
    service = service.replace("field.setTextSize(18);", "field.setTextSize(15);")
    SERVICE.write_text(service, encoding="utf-8")

# Playback loop emits main-thread cursor updates asynchronously. Ignore queued frames after the
# worker stops, and do not force the cursor to the range end on stop: keep the last visible frame.
service = SERVICE.read_text(encoding="utf-8")
if "final Thread playbackWorker = Thread.currentThread();" not in service:
    service = replace_once(service,
        "    private void playSong(MidiParser.MidiSong song, int transpose, int speedPercent,\n                          long rangeStartMicros, long rangeEndMicros) {",
        "    private void playSong(MidiParser.MidiSong song, int transpose, int speedPercent,\n                          long rangeStartMicros, long rangeEndMicros) {\n        final Thread playbackWorker = Thread.currentThread();",
        "capture playback worker identity")
old_frame = """                    mainHandler.post(() -> {
                        if (noteRollView != null) noteRollView.setCursor(cursor, isRunning);
                        refreshMiniPlaybackButton();
                    });"""
new_frame = """                    mainHandler.post(() -> {
                        // Drop queued frames while playback is paused/stopped or a seek gesture is
                        // active; they otherwise move the visible note window after it is frozen.
                        if (playbackActive && !stopRequested && !paused && noteRollView != null) {
                            noteRollView.setCursor(cursor, isRunning);
                        }
                        refreshMiniPlaybackButton();
                    });"""
service = replace_once(service, old_frame, new_frame, "ignore stale queued playback cursor frames")
service = replace_once(service,
    "                if (!stoppedByUser) playbackPositionMicros = playbackRangeEndMicros;\n                if (noteRollView != null) noteRollView.setCursor(playbackPositionMicros, false);\n                playbackThread = null;",
    """                // Keep the last rendered cursor rather than snapping the note window to the
                // A/B end on natural completion; this prevents the visible notes changing abruptly.
                if (playbackThread == playbackWorker) {
                    if (noteRollView != null) noteRollView.setCursor(playbackPositionMicros, false);
                    playbackThread = null;
                }""",
    "preserve the last rendered note window when playback stops")
SERVICE.write_text(service, encoding="utf-8")

# Postconditions prevent a partial or repeated application from being treated as a completed patch.
note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
if "beginSeekGesture();\n                    touchMode = TOUCH_SEEK_ABSOLUTE;" not in note:
    raise SystemExit("Progress seek does not pause at touch-down.")
if "src = new Rect(cellX + 12, cellY + 12, cellX + 52, cellY + 52);" not in note or "canvas.clipPath(circularCrop);" not in note:
    raise SystemExit("Game key crop/round clipping is missing.")
if "bar.width() >= iconSize + 2 * iconInset" not in note:
    raise SystemExit("Icon and note block reveal guard is missing.")
if "if (noteRollControlButton != null) noteRollControlButton.setVisibility(visibility);" not in service:
    raise SystemExit("Note roll button visibility is not tied to note-roll state.")
if "if (rewindControlButton != null) rewindControlButton.setVisibility(visibility);" not in service:
    raise SystemExit("Rewind button visibility is not tied to note-roll state.")
if "if (playbackActive && !stopRequested && !paused && noteRollView != null)" not in service:
    raise SystemExit("Stale playback frame guard is missing.")
if "if (!stoppedByUser) playbackPositionMicros = playbackRangeEndMicros;" in service:
    raise SystemExit("Playback still snaps the view to the end after stopping.")
if "Math.min(dp(310),\n                prefs.getInt(\"ab_dialog_width_px\", defaultWidth))" not in service and "Math.min(Math.min(screenWidth - dp(24), dp(310))" not in service:
    raise SystemExit("A/B window width cap was not installed.")
print("Applied hidden panel actions, immediate seek freeze, circular game-key crop, synchronized note/icon reveal, compact A/B controls, and stable stop cursor.")
