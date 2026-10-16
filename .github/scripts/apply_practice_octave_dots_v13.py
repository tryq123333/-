from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
LAYOUT = ROOT / "app/src/main/java/com/luoke/autopiano/InstrumentLayout.java"
LAYOUT_TEST = ROOT / "app/src/test/java/com/luoke/autopiano/InstrumentLayoutTest.java"
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "PRACTICE_OCTAVE_DOT_KEYMAP_V13"
OLD_MAP = "{8, 0, 1, 3, 2, 4, 5, 6, 7}"
NEW_MAP = "{8, 3, 4, 5, 6, 7, 0, 1, 2}"


def rep(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)


layout = LAYOUT.read_text(encoding="utf-8")
tests = LAYOUT_TEST.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")

# Atlas cell meanings from the actual game-key artwork:
# 0-2 = high 1/2/3 (black octave dot above), 3-7 = mid 3/4/5/6/7 (no dot),
# cell 8 = low 6 (black octave dot below).
if MARKER not in layout:
    if OLD_MAP in layout:
        layout = layout.replace(
            "    // The 3x3 atlas follows the photographed game's screen order, not MIDI pitch order.\n"
            "    private static final int[] GAME_KEY_ATLAS_CELL_BY_PITCH_INDEX = " + OLD_MAP + ";",
            "    // Octave markers are part of the real glyph: top-dot high 1-3, plain mid 3-7, bottom-dot low 6.\n"
            "    private static final int[] GAME_KEY_ATLAS_CELL_BY_PITCH_INDEX = " + NEW_MAP + ";",
            1,
        )
    elif NEW_MAP not in layout:
        raise SystemExit("Neither known key-atlas map is present; refusing to guess cell geometry.")
    layout = layout.replace(
        "public final class InstrumentLayout { // PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12",
        "public final class InstrumentLayout { // PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12 " + MARKER,
        1,
    )

# The note cells are intentionally not pitch order in the bitmap:
# low A2 uses the bottom-dot cell 8, middle pitches use plain cells 3-7,
# high C4/D4/E4 use cells 0/1/2 with the dot above the symbol.
test_method = """    @Test public void nineKeyPitchIconsMapToCorrectGameAtlasCells() {
        assertEquals(8, InstrumentLayout.gameKeyAtlasCellForPitch(45)); // A2: low 6, dot below
        assertEquals(3, InstrumentLayout.gameKeyAtlasCellForPitch(52)); // E3: mid 3, no dot
        assertEquals(4, InstrumentLayout.gameKeyAtlasCellForPitch(53)); // F3: mid 4, no dot
        assertEquals(5, InstrumentLayout.gameKeyAtlasCellForPitch(55)); // G3: mid 5, no dot
        assertEquals(6, InstrumentLayout.gameKeyAtlasCellForPitch(57)); // A3: mid 6, no dot
        assertEquals(7, InstrumentLayout.gameKeyAtlasCellForPitch(59)); // B3: mid 7, no dot
        assertEquals(0, InstrumentLayout.gameKeyAtlasCellForPitch(60)); // C4: high 1, dot above
        assertEquals(1, InstrumentLayout.gameKeyAtlasCellForPitch(62)); // D4: high 2, dot above
        assertEquals(2, InstrumentLayout.gameKeyAtlasCellForPitch(64)); // E4: high 3, dot above
        assertEquals(-1, InstrumentLayout.gameKeyAtlasCellForPitch(61));
    }
"""
if test_method.strip() not in tests:
    pattern = r"    @Test public void nineKeyPitchIconsMapToCorrectGameAtlasCells\(\) \{\n.*?\n    \}\n"
    tests, count = re.subn(pattern, test_method, tests, count=1, flags=re.S)
    if count != 1:
        raise SystemExit("Unable to update the nine-key atlas mapping test")
if MARKER not in tests:
    tests = tests.replace(
        "public class InstrumentLayoutTest {",
        "public class InstrumentLayoutTest { // " + MARKER,
        1,
    )

# Slightly enlarge normal roll icons so the octave dots remain visible on narrow mobile layouts.
old_size = "float iconSize = practiceGroupNote ? 18 * density : Math.min(16 * density,"
new_size = "float iconSize = practiceGroupNote ? 20 * density : Math.min(18 * density,"
if old_size in note:
    note = note.replace(old_size, new_size, 1)
elif new_size not in note:
    raise SystemExit("Unable to find note icon size expression")

if "gameKeyAtlasCellForPitch(pitch)" not in note:
    raise SystemExit("Note roll no longer uses pitch-aware atlas cells")
if MARKER not in note:
    note = note.replace(
        "ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10 PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12",
        "ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10 PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12 " + MARKER,
        1,
    )

build = BUILD.read_text(encoding="utf-8")
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode")
if int(m.group(1)) < 22:
    build = build[:m.start(1)] + "22" + build[m.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.3'", build, count=1)

LAYOUT.write_text(layout, encoding="utf-8")
LAYOUT_TEST.write_text(tests, encoding="utf-8")
NOTE.write_text(note, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

layout_check = LAYOUT.read_text(encoding="utf-8")
test_check = LAYOUT_TEST.read_text(encoding="utf-8")
note_check = NOTE.read_text(encoding="utf-8")
build_check = BUILD.read_text(encoding="utf-8")
checks = {
    "octave-aware mapping applied": NEW_MAP in layout_check and MARKER in layout_check,
    "low A2 maps to bottom-dot icon": "assertEquals(8, InstrumentLayout.gameKeyAtlasCellForPitch(45)); // A2: low 6, dot below" in test_check,
    "high 1/2/3 map to top-dot icons": all(s in test_check for s in [
        "gameKeyAtlasCellForPitch(60)); // C4: high 1, dot above",
        "gameKeyAtlasCellForPitch(62)); // D4: high 2, dot above",
        "gameKeyAtlasCellForPitch(64)); // E4: high 3, dot above",
    ]),
    "middle 3-7 use plain symbols": all(f"gameKeyAtlasCellForPitch({pitch})); // {name}: mid {degree}, no dot" in test_check for pitch, name, degree in [
        (52,"E3",3),(53,"F3",4),(55,"G3",5),(57,"A3",6),(59,"B3",7)
    ]),
    "note roll still uses the atlas mapping": "gameKeyAtlasCellForPitch(pitch)" in note_check,
    "roll icons enlarged to keep octave dot visible": "Math.min(18 * density" in note_check,
    "installable version bumped": "versionCode 22" in build_check and "versionName '1.9.3'" in build_check,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Octave-dot mapping V13 audit failed: " + "; ".join(failed))
print("Octave-dot mapping V13 applied.")
print("AUDIT OK: " + "; ".join(checks))
