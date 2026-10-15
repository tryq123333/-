from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
STRINGS = ROOT / "app/src/main/res/values/strings.xml"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
ICON = ROOT / "app/src/main/res/drawable/ic_music_note.xml"
MARKER = "AB_LOOP_FADE_BRAND_RESET_V3"

service = SERVICE.read_text(encoding="utf-8")
if "AB_LOOP_FIXES_V2" not in service or "重置 A/B" not in service:
    raise SystemExit("A/B reset and full-song playback patch must be applied before branding refinements.")

note = NOTE.read_text(encoding="utf-8")
if MARKER not in note:
    # Notes must flow behind the title/time labels. The header is drawn later by NoteRollView,
    # so removing this difference clip leaves text and controls on top of fading notes.
    note = note.replace(
        "        int noteClipSave = canvas.save();\n"
        "        canvas.clipRect(left, 0f, playheadX, 70 * density, android.graphics.Region.Op.DIFFERENCE);\n",
        "",
        1,
    )
    note = note.replace("        canvas.restoreToCount(noteClipSave);\n", "", 1)
    if "canvas.clipRect(left, 0f, playheadX, 70 * density, android.graphics.Region.Op.DIFFERENCE);" in note:
        raise SystemExit("Note-roll title/time exclusion clip was not removed.")

    # Keep the fade calculation after the playhead line, but draw those notes behind the header.
    if "float fade = rawX2 >= playheadX ? 1f" not in note:
        raise SystemExit("Expected playhead-relative fading formula is missing.")

    # Soften the bottom progress rail, selected-range overlay, and current-position marker.
    progress_start = note.find("// Full-song progress line with the selected practice range highlighted.")
    progress_end = note.find("// Low-contrast playhead line", progress_start)
    if progress_start < 0 or progress_end < 0:
        raise SystemExit("Could not find the bottom progress-line drawing block.")
    progress = note[progress_start:progress_end]
    for old, new in [
        ("0x315c7b90", "0x1c5c7b90"),
        ("0x5965dfb0", "0x2b65dfb0"),
        ("0xb3f7fbff", "0x75f7fbff"),
        ("0x665c7b90", "0x1c5c7b90"),
        ("0xaa65dfb0", "0x2b65dfb0"),
        ("0xfff7fbff", "0x75f7fbff"),
    ]:
        progress = progress.replace(old, new)
    if "0x1c5c7b90" not in progress:
        raise SystemExit("The progress rail color could not be faded further.")
    note = note[:progress_start] + progress + note[progress_end:]
    note = note.replace(
        "/** Compact, resizable and seekable MIDI roll overlay. NOTE_HEADER_INFO_V2 */",
        "/** Compact, resizable and seekable MIDI roll overlay. NOTE_HEADER_INFO_V2 AB_LOOP_FADE_BRAND_RESET_V3 */",
        1,
    )
    if MARKER not in note:
        # Some current source variants carry an extra marker comment.
        note = note.replace("ICON_ANCHORED_HEADER_V3", "ICON_ANCHORED_HEADER_V3 " + MARKER, 1)
    NOTE.write_text(note, encoding="utf-8")

# Rename the user-facing app label without changing its package/application identity.
if not STRINGS.exists():
    raise SystemExit("Could not find app string resources.")
strings = STRINGS.read_text(encoding="utf-8")
new_strings, count = re.subn(
    r'(<string\s+name="app_name"[^>]*>).*?(</string>)',
    r'\1洛克乐器演奏\2',
    strings,
    count=1,
    flags=re.S,
)
if count != 1:
    raise SystemExit("Could not find exactly one app_name string.")
STRINGS.write_text(new_strings, encoding="utf-8")

# Use a real vector-drawable music note for both launcher icon variants.
if not MANIFEST.exists():
    raise SystemExit("Could not find AndroidManifest.xml.")
manifest = MANIFEST.read_text(encoding="utf-8")
app_match = re.search(r"<application\b[\s\S]*?>", manifest)
if not app_match:
    raise SystemExit("Could not locate the manifest application element.")
tag = app_match.group(0)
for attr in ("icon", "roundIcon"):
    pattern = rf'android:{attr}="[^"]*"'
    replacement = f'android:{attr}="@drawable/ic_music_note"'
    if re.search(pattern, tag):
        tag = re.sub(pattern, replacement, tag, count=1)
    elif attr == "icon":
        tag = tag[:-1] + ' android:icon="@drawable/ic_music_note">'
    else:
        tag = tag[:-1] + ' android:roundIcon="@drawable/ic_music_note">'
manifest = manifest[:app_match.start()] + tag + manifest[app_match.end():]
MANIFEST.write_text(manifest, encoding="utf-8")

ICON.parent.mkdir(parents=True, exist_ok=True)
ICON.write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp"
    android:height="48dp"
    android:viewportWidth="48"
    android:viewportHeight="48">
    <path
        android:fillColor="#2E6D61"
        android:pathData="M0,0h48v48h-48z" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M28,5h14v6H34v20h-6z" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M18,35c0,-4.4 3.4,-7.8 7.7,-7.8s7.7,3.4 7.7,7.8s-3.4,7.8 -7.7,7.8s-7.7,-3.4 -7.7,-7.8z" />
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M28,5h14v5H28z" />
</vector>
""", encoding="utf-8")

# Postconditions protect against accidentally publishing a partial source package.
note = NOTE.read_text(encoding="utf-8")
if "canvas.clipRect(left, 0f, playheadX, 70 * density, android.graphics.Region.Op.DIFFERENCE);" in note:
    raise SystemExit("The title/time note-exclusion clip is still active.")
if "float fade = rawX2 >= playheadX ? 1f" not in note:
    raise SystemExit("The fading notes formula disappeared.")
if "0x1c5c7b90" not in note:
    raise SystemExit("The progress rail opacity adjustment is missing.")
if "洛克乐器演奏" not in STRINGS.read_text(encoding="utf-8"):
    raise SystemExit("New app name was not applied.")
if '@drawable/ic_music_note' not in MANIFEST.read_text(encoding="utf-8") or not ICON.exists():
    raise SystemExit("Music-note launcher icon is not installed in the manifest/resources.")
print("A/B settings reset + full-song playback behavior, fading notes behind title/time, subtler progress rail, app name and music-note icon applied.")
