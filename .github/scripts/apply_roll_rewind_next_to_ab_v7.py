from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "ROLL_REWIND_NEXT_TO_AB_V7"

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": anchor missing.")

note = NOTE.read_text(encoding="utf-8")
if MARKER not in note:
    # Keep the scroll-note window's own rewind chip. Put it on the A/B row, immediately
    # after the A/B button, so it is independent from the floating panel's hidden button.
    old_ab = """        drawHeaderChip(canvas, new RectF(left, 52 * density, left + 61 * density, 69 * density),
                rangeEditing ? "完成" : "A/B循环",
                rangeEditing ? 0xff4c8d80 : (abLoopEnabled ? 0xff477960 : 0xff455667), density);"""
    new_ab = old_ab + """
        drawHeaderChip(canvas, new RectF(70 * density, 52 * density, 95 * density, 69 * density),
                "⏮︎", 0xff455667, density);"""
    note = once(note, old_ab, new_ab, "add rewind beside note-roll A/B chip")

    old_touch = """                } else if (y >= 50 * density && y < 72 * density
                        && x >= 5 * density && x <= 69 * density) {
                    touchMode = TOUCH_SEGMENT;
                    segmentDownTimeMs = event.getEventTime();
                } else if (touchEdges != 0) {"""
    new_touch = """                } else if (y >= 50 * density && y < 72 * density
                        && x >= 5 * density && x <= 69 * density) {
                    touchMode = TOUCH_SEGMENT;
                    segmentDownTimeMs = event.getEventTime();
                } else if (y >= 50 * density && y < 72 * density
                        && x > 69 * density && x <= 97 * density) {
                    touchMode = TOUCH_REWIND;
                } else if (touchEdges != 0) {"""
    note = once(note, old_touch, new_touch, "wire rewind touch area beside A/B")
    note = note.replace(
        "ROLL_FINAL_CONTROLS_SEEK_LAUNCHER_V6",
        "ROLL_FINAL_CONTROLS_SEEK_LAUNCHER_V6 " + MARKER,
        1)
    NOTE.write_text(note, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 3", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.3.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

note = NOTE.read_text(encoding="utf-8")
if 'new RectF(70 * density, 52 * density, 95 * density, 69 * density)' not in note:
    raise SystemExit("Rewind chip is not positioned immediately beside the A/B chip.")
if 'touchMode = TOUCH_REWIND;' not in note or 'x > 69 * density && x <= 97 * density' not in note:
    raise SystemExit("Rewind touch target is not wired beside the A/B chip.")
if "versionCode 3" not in BUILD.read_text(encoding="utf-8") or "versionName '0.3.0'" not in BUILD.read_text(encoding="utf-8"):
    raise SystemExit("Version bump missing.")
print("Restored scroll-note rewind directly beside A/B, wired its touch target, and bumped app version to 0.3.0.")
