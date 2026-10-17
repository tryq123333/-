from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "PRACTICE_OUTERMOST_STANDALONE_RING_REMOVED_V16"

note = NOTE.read_text(encoding="utf-8")
outer = "                                    canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.82f, paint);"
if outer not in note:
    if MARKER not in note:
        raise SystemExit("Expected outermost playhead ring not found; refusing to modify unrelated drawing.")
else:
    note = note.replace(outer + "\n", "", 1)
    anchor = "                                    canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.68f, paint);"
    idx = note.find(anchor)
    if idx < 0:
        raise SystemExit("Inner playhead circle missing; refusing to leave no focus effect.")
    note = note[:idx] + note[idx:].replace(anchor, anchor + " // " + MARKER, 1)
NOTE.write_text(note, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode")
build = build[:m.start(1)] + "25" + build[m.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.6'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

note_check = NOTE.read_text(encoding="utf-8")
build_check = BUILD.read_text(encoding="utf-8")
checks = {
    "outer standalone circle is absent": "canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.82f, paint);" not in note_check,
    "inner highlight circle remains": "canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.68f, paint);" in note_check and MARKER in note_check,
    "practice focus logic remains": "playheadFocusNote = practiceGroupNote || normalPlayheadNote" in note_check,
    "normal playback ring remains disabled when practice is off": "normalPlayheadNote = practiceModeEnabled && playing" in note_check,
    "app bumped to 1.9.6": "versionCode 25" in build_check and "versionName '1.9.6'" in build_check,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("V16 outer ring audit failed: " + "; ".join(failed))
print("V16 outer standalone playhead ring removed.")
print("AUDIT OK: " + "; ".join(checks))
