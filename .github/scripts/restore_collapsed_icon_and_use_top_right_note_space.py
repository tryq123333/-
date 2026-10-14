from pathlib import Path

SERVICE = Path("LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java")
NOTE_VIEW = Path("LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/NoteRollView.java")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Cannot apply {label}: source anchor not found")
    return text.replace(old, new, 1)


service = SERVICE.read_text(encoding="utf-8")
if "COLLAPSE_TO_MUSIC_ICON_V1" not in service:
    service = replace_once(
        service,
        "        renderCollapsedBubble(playbackEverStarted && !statusBubbleDismissed);",
        "        // COLLAPSE_TO_MUSIC_ICON_V1: always return to the original single music icon.\n"
        "        renderCollapsedBubble(false);",
        "collapse to icon after playback",
    )
    service = replace_once(
        service,
        "        boolean shouldShowStatus = playbackEverStarted && !statusBubbleDismissed;",
        "        boolean shouldShowStatus = false; // COLLAPSE_TO_MUSIC_ICON_V1",
        "keep collapsed bubble icon-only during playback",
    )
    SERVICE.write_text(service, encoding="utf-8")

note = NOTE_VIEW.read_text(encoding="utf-8")
if "UPPER_RIGHT_NOTE_SPACE_V2" not in note:
    note = replace_once(
        note,
        "        // Use the whole usable window for notes. The metadata is painted as a small mask\n"
        "        // afterward, so upcoming notes can also occupy the formerly empty top-right space.\n"
        "        final float left = 8 * density;\n"
        "        final float right = w - 8 * density;\n"
        "        final float top = 30 * density;\n"
        "        final float bottom = h - 26 * density;",
        "        // UPPER_RIGHT_NOTE_SPACE_V2: use the transparent upper-right area for moving note blocks.\n"
        "        // Keep the title/control side clear while notes flow through the right-hand space.\n"
        "        final float left = 8 * density;\n"
        "        final float right = w - 8 * density;\n"
        "        final float top = 3 * density;\n"
        "        final float bottom = h - 26 * density;",
        "expand note field into transparent upper-right area",
    )
    note = replace_once(
        note,
        "        if (song != null && song.notes != null) {",
        "        // Do not let note badges clutter the close/play/title/time/segment controls on the left.\n"
        "        int noteClipSave = canvas.save();\n"
        "        canvas.clipRect(left, 0f, playheadX, 70 * density, android.graphics.Region.Op.DIFFERENCE);\n"
        "        if (song != null && song.notes != null) {",
        "clip controls but use right-hand blank space",
    )
    note = replace_once(
        note,
        "        // Full-song progress line with the selected practice range highlighted. The strip\n",
        "        canvas.restoreToCount(noteClipSave);\n\n"
        "        // Full-song progress line with the selected practice range highlighted. The strip\n",
        "restore note drawing clip before progress and controls",
    )
    NOTE_VIEW.write_text(note, encoding="utf-8")

service_check = SERVICE.read_text(encoding="utf-8")
note_check = NOTE_VIEW.read_text(encoding="utf-8")
if "COLLAPSE_TO_MUSIC_ICON_V1" not in service_check:
    raise SystemExit("Collapsed icon-only marker missing")
if "UPPER_RIGHT_NOTE_SPACE_V2" not in note_check:
    raise SystemExit("Upper-right note-space marker missing")
if "renderCollapsedBubble(false);" not in service_check:
    raise SystemExit("Collapse path does not return to the single icon")
if "canvas.clipRect(left, 0f, playheadX, 70 * density, android.graphics.Region.Op.DIFFERENCE);" not in note_check:
    raise SystemExit("Left-side controls clip was not applied")
print("Applied icon-only collapse and transparent upper-right note fill; lane backgrounds remain disabled.")
