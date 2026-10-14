from pathlib import Path

NOTE = Path("LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/NoteRollView.java")
SERVICE = Path("LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java")
MARKER = "NOTE_ROLL_HEADER_ANCHOR_V1"


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit("Cannot patch " + label + ": source anchor not found.")
    return text.replace(old, new, 1)


note = NOTE.read_text(encoding="utf-8")
if MARKER not in note:
    # Keep just one copy of title, time and close UI. The gradient header below is the
    # authoritative rendering and masks into the same background as the note lanes.
    start = note.index("        final float headerHeight = Math.min(49 * density, h * .40f);")
    end = note.index("        // Use the whole usable window for notes.", start)
    note = note[:start] + note[end:]

    note = replace_once(
        note,
        """        final long windowMicros = visibleWindowMicros(w, left, right, density);
        final float scale = (right - left) / (float) windowMicros;
""",
        """        // NOTE_ROLL_HEADER_ANCHOR_V1: playhead stays just to the right of the title/time fade.
        final float playheadX = getPlayheadX(w, left, right, density);
        final long windowMicros = visibleWindowMicros(w, left, right, density);
        final float horizontalSpan = Math.max(1f, right - left);
        final long pastMicros = (long) (windowMicros * ((playheadX - left) / horizontalSpan));
        final long futureMicros = (long) (windowMicros * ((right - playheadX) / horizontalSpan));
        final long visibleStart = Math.max(0L, positionMicros - pastMicros);
        final long visibleEnd = Math.min(durationMicros, positionMicros + futureMicros);
        final float scale = horizontalSpan / (float) Math.max(1L, windowMicros);
""",
        "playhead time mapping"
    )

    note = replace_once(
        note,
        """            long visibleEnd = positionMicros + windowMicros;
            long visibleStart = Math.max(0L, positionMicros - 500_000L);
            List<MidiParser.NoteEvent> notes = song.notes;
            int low = 0, high = notes.size();
            while (low < high) {
                int mid = (low + high) >>> 1;
                if (notes.get(mid).startMicros < visibleStart) low = mid + 1;
                else high = mid;
            }
""",
        """            List<MidiParser.NoteEvent> notes = song.notes;
            // Include a short look-behind for sustained notes that began just before the window.
            long searchFrom = Math.max(0L, visibleStart - Math.min(8_000_000L, windowMicros / 2L));
            int low = 0, high = notes.size();
            while (low < high) {
                int mid = (low + high) >>> 1;
                if (notes.get(mid).startMicros < searchFrom) low = mid + 1;
                else high = mid;
            }
""",
        "visible-note search"
    )

    note = replace_once(
        note,
        """                long noteDuration = note.durationMicros > 0 ? note.durationMicros : 260_000L;
                long noteEnd = noteStart + noteDuration;
                if (noteEnd < positionMicros) continue;
                if (noteStart < rangeStartMicros || noteStart >= rangeEndMicros) continue;
                long clippedStart = Math.max(noteStart, positionMicros);
                long clippedEnd = Math.min(Math.max(noteEnd, clippedStart + 180_000L), visibleEnd);
                float x1 = left + (clippedStart - positionMicros) * scale;
                float x2 = left + (clippedEnd - positionMicros) * scale;
                x1 = Math.max(left, x1);
                x2 = Math.min(right, Math.max(x1 + 12 * density, x2));
                int lane = pitchLane(pitch, lanes);
                float y = top + lane * laneHeight + 1.5f * density;
                float bh = Math.max(5 * density, laneHeight - 3 * density);
                RectF bar = new RectF(x1, y, x2, Math.min(bottom, y + bh));
                paint.setColor(colors[Math.floorMod(pitch, colors.length)]);
                canvas.drawRoundRect(bar, 5 * density, 5 * density, paint);
                if (bar.width() > 20 * density && laneHeight > 15 * density) {
                    paint.setColor(0xff142029);
                    paint.setTextSize(Math.min(8 * density, laneHeight * .38f));
                    paint.setFakeBoldText(true);
                    canvas.drawText(MidiParser.noteName(pitch), x1 + 4 * density,
                            bar.centerY() + 3 * density, paint);
                    paint.setFakeBoldText(false);
                }
""",
        """                long noteDuration = note.durationMicros > 0 ? note.durationMicros : 260_000L;
                long noteEnd = Math.min(rangeEndMicros, noteStart + noteDuration);
                if (noteEnd < visibleStart) continue;
                if (noteStart < rangeStartMicros || noteStart >= rangeEndMicros) continue;
                float rawX1 = playheadX + (noteStart - positionMicros) * scale;
                float rawX2 = playheadX + (noteEnd - positionMicros) * scale;
                if (rawX2 < left || rawX1 > right) continue;
                float x1 = Math.max(left, rawX1);
                float x2 = Math.min(right, Math.max(x1 + 12 * density, rawX2));
                int lane = pitchLane(pitch, lanes);
                float y = top + lane * laneHeight + 1.5f * density;
                float bh = Math.max(5 * density, laneHeight - 3 * density);
                RectF bar = new RectF(x1, y, x2, Math.min(bottom, y + bh));
                // A note keeps its normal opacity while approaching the playhead. Once its
                // trailing edge passes the line, it fades toward the left edge of the panel.
                float fade = rawX2 >= playheadX ? 1f
                        : Math.max(0f, Math.min(1f, (rawX2 - left) / Math.max(1f, playheadX - left)));
                int noteAlpha = Math.max(0, Math.min(255, Math.round(255f * fade)));
                paint.setColor(colors[Math.floorMod(pitch, colors.length)]);
                paint.setAlpha(noteAlpha);
                canvas.drawRoundRect(bar, 5 * density, 5 * density, paint);
                if (bar.width() > 20 * density && laneHeight > 15 * density && noteAlpha > 12) {
                    paint.setColor(0xff142029);
                    paint.setAlpha(noteAlpha);
                    paint.setTextSize(Math.min(8 * density, laneHeight * .38f));
                    paint.setFakeBoldText(true);
                    canvas.drawText(MidiParser.noteName(pitch), x1 + 4 * density,
                            bar.centerY() + 3 * density, paint);
                    paint.setFakeBoldText(false);
                }
                paint.setAlpha(255);
""",
        "note movement and fade"
    )

    note = replace_once(
        note,
        "canvas.drawLine(left, top, left, bottom + 1 * density, paint);",
        "canvas.drawLine(playheadX, top, playheadX, bottom + 1 * density, paint);",
        "playhead drawing"
    )
    note = replace_once(
        note,
        "Math.min(w - 82 * density, w * .46f)",
        "Math.min(w - 72 * density, w * .50f)",
        "header fade width"
    )
    note = replace_once(
        note,
        'if (y < 34 * density && x > w - 35 * density) {',
        'if (y < 34 * density && x > w - 34 * density) {',
        "close hit zone"
    )
    note = replace_once(
        note,
        '} else if (y < 34 * density && x > w - 60 * density) {',
        '} else if (y < 34 * density && x > w - 63 * density) {',
        "segment hit zone"
    )
    note = replace_once(
        note,
        '} else if (y < 34 * density && x > w - 85 * density) {',
        '} else if (y < 34 * density && x > w - 91 * density) {',
        "play/pause hit zone"
    )
    note = replace_once(
        note,
        'new RectF(w - 83 * density, buttonTop, w - 60 * density, buttonBottom)',
        'new RectF(w - 89 * density, buttonTop, w - 64 * density, buttonBottom)',
        "play/pause chip"
    )
    note = replace_once(
        note,
        'new RectF(w - 58 * density, buttonTop, w - 34 * density, buttonBottom)',
        'new RectF(w - 61 * density, buttonTop, w - 35 * density, buttonBottom)',
        "segment chip"
    )
    note = replace_once(
        note,
        """        paint.setColor(0xe9f7f9fc);
        paint.setStrokeWidth(1.8f * density);
        float closeX = w - 17 * density;
        float closeY = 15 * density;
        float closeSize = 8 * density;
        canvas.drawLine(closeX - closeSize / 2, closeY - closeSize / 2,
                closeX + closeSize / 2, closeY + closeSize / 2, paint);
        canvas.drawLine(closeX - closeSize / 2, closeY + closeSize / 2,
                closeX + closeSize / 2, closeY - closeSize / 2, paint);
        paint.setStrokeWidth(1 * density);
""",
        """        // A dedicated close chip stays visually and interactively separate from the segment chip.
        drawHeaderChip(canvas, new RectF(w - 32 * density, buttonTop, w - 6 * density, buttonBottom),
                "×", 0xff455667, density);
""",
        "single close chip"
    )
    note = replace_once(
        note,
        "    private static long visibleWindowMicros(float width, float left, float right, float density) {",
        """    private static float getPlayheadX(float width, float left, float right, float density) {
        float desired = width * .54f;
        float minimum = left + 34 * density;
        return Math.max(minimum, Math.min(right - 28 * density, desired));
    }

    private static long visibleWindowMicros(float width, float left, float right, float density) {""",
        "playhead anchor helper"
    )
    NOTE.write_text(note, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
service_marker = "SEGMENT_EDIT_IN_ROLL_ONLY_V1"
if service_marker not in service:
    start = service.index("    private void showSegmentDialog() {")
    end = service.index("    private Button dialogButton(", start)
    service = service[:start] + """    // SEGMENT_EDIT_IN_ROLL_ONLY_V1: select a slice directly on the note roll; never create a fullscreen blocker.
    private void showSegmentDialog() {
        beginRangeEditingFromControl();
    }

""" + service[end:]

    toggle_start = service.index("    private void toggleNoteRoll() {")
    toggle_end = service.index("    private MidiParser.MidiSong readCurrentSong()", toggle_start)
    toggle = service[toggle_start:toggle_end]
    if "dismissSegmentDialog();" not in toggle:
        pivot = "        }\n        if (noteRollView != null) {"
        toggle = replace_once(toggle, pivot, "        }\n        dismissSegmentDialog();\n        if (noteRollView != null) {", "stale overlay dismissal")
        service = service[:toggle_start] + toggle + service[toggle_end:]
    SERVICE.write_text(service, encoding="utf-8")

# Ensure repeat runs safely skip already-patched source.
note_check = NOTE.read_text(encoding="utf-8")
service_check = SERVICE.read_text(encoding="utf-8")
if MARKER not in note_check or "SEGMENT_EDIT_IN_ROLL_ONLY_V1" not in service_check:
    raise SystemExit("The note-roll refinement markers are missing.")
print("Applied: single header/close rendering, right-offset playhead, post-line note fade, separate hit zones, and no modal segment overlay.")
