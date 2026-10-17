from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "PRACTICE_NORMAL_PLAYHEAD_RING_ONLY_IN_PRACTICE_V15"


note = NOTE.read_text(encoding="utf-8")
pattern = r"boolean normalPlayheadNote = (?:practiceModeEnabled && )?playing && Math\.abs\(noteStart - positionMicros\) <= 70_000L;"
match = re.search(pattern, note)
if not match:
    raise SystemExit("Could not find the normal playhead ring condition; refusing to alter drawing logic blindly.")
desired = "boolean normalPlayheadNote = practiceModeEnabled && playing && Math.abs(noteStart - positionMicros) <= 70_000L;"
note = note[:match.start()] + desired + note[match.end():]
if MARKER not in note:
    note = note.replace(desired, desired + " // " + MARKER, 1)
NOTE.write_text(note, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode")
if int(m.group(1)) < 24:
    build = build[:m.start(1)] + "24" + build[m.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.5'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

note_check = NOTE.read_text(encoding="utf-8")
build_check = BUILD.read_text(encoding="utf-8")
checks = {
    "normal ring only active while practice mode is on": desired in note_check and MARKER in note_check,
    "practice playhead medallion remains": "boolean practiceGroupNote = practiceWaiting && practiceGroupPitches.contains(pitch)" in note_check
        and "if (playheadFocusNote)" in note_check,
    "practice waiting ring still remains": "practiceNeedsTap ? 0x9f48e69e : 0x6048e69e" in note_check,
    "regular playback still uses playhead only when practice enabled": "playheadFocusNote = practiceGroupNote || normalPlayheadNote" in note_check,
    "app bumped to 1.9.5": "versionCode 24" in build_check and "versionName '1.9.5'" in build_check,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Practice-only playhead ring V15 audit failed: " + "; ".join(failed))
print("Practice-only playhead ring V15 applied.")
print("AUDIT OK: " + "; ".join(checks))
