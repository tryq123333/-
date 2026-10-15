from pathlib import Path
import base64
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
STRINGS = ROOT / "app/src/main/res/values/strings.xml"
ICON = ROOT / "app/src/main/res/drawable/ic_music_note.xml"
ASSET = ROOT / "app/src/main/res/drawable-nodpi/note_key_atlas.webp"
MARKER = "ROLL_REFERENCE_ICON_ANIMATION_V5"

# Clean crops from the user's latest 9-key reference image, in the visual key order
# T,Y,U / F,G,H,J,K / B. The full cream medallion and full symbol are retained.
ATLAS_B64 = """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"""
ASSET.parent.mkdir(parents=True, exist_ok=True)
ASSET.write_bytes(base64.b64decode(ATLAS_B64))

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": source anchor missing.")

note = NOTE.read_text(encoding="utf-8")
if MARKER not in note:
    # Draw the full key medallion, not a zoomed middle crop. That restores the cream rim
    # and makes the black/color glyph read at the scale shown in the latest reference.
    note = once(note,
        "int cellX = (index % 3) * 64;",
        "int cellX = (index % 3) * 32;",
        "reference atlas cell x")
    note = once(note,
        "int cellY = (index / 3) * 64;",
        "int cellY = (index / 3) * 32;",
        "reference atlas cell y")
    note = once(note,
        "Rect src = new Rect(cellX + 12, cellY + 12, cellX + 52, cellY + 52);",
        "Rect src = new Rect(cellX + 1, cellY + 1, cellX + 31, cellY + 31);",
        "full original key medallion crop")

    old_block = """                    if (useGameKeyIcons && keyIconIndex >= 0) {
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
    new_block = """                    if (useGameKeyIcons && keyIconIndex >= 0) {
                        float iconInset = 2.5f * density;
                        float iconSize = Math.min(16 * density,
                                Math.max(0f, Math.min(bar.height() - 4 * density, badgeHeight - density)));
                        // Stage the entrance: show a clearly visible colored note block first,
                        // then fade its full in-game key medallion in over a few dp of travel.
                        float reveal = (right - bar.left - iconSize - 2 * iconInset)
                                / Math.max(1f, 5 * density);
                        boolean blockReady = iconSize >= 8 * density
                                && bar.width() >= iconSize + 2 * iconInset + density
                                && bar.left <= right - iconSize - 2 * iconInset;
                        if (blockReady && reveal > 0f) {
                            float iconCx = bar.left + iconInset + iconSize / 2f;
                            iconCx = Math.min(bar.right - iconInset - iconSize / 2f, iconCx);
                            int revealAlpha = Math.round(noteAlpha * Math.min(1f, reveal));
                            if (revealAlpha > 0) {
                                drawOriginalGameKeyIcon(canvas, iconCx, badge.centerY(),
                                        iconSize, keyIconIndex, revealAlpha);
                            }
                        }
                    } else {"""
    note = once(note, old_block, new_block, "frame-first gradual key icon entrance")
    note = note.replace(
        "ROLL_SEEK_ICON_STABILITY_V4 */",
        "ROLL_SEEK_ICON_STABILITY_V4 " + MARKER + " */",
        1)
    if MARKER not in note:
        note = note.replace("ROLL_SEEK_ICON_STABILITY_V4",
                            "ROLL_SEEK_ICON_STABILITY_V4 " + MARKER, 1)
    NOTE.write_text(note, encoding="utf-8")

# Android's application label was hard-coded to an old name, overriding strings.xml.
strings = STRINGS.read_text(encoding="utf-8")
if re.search(r'<string\s+name="app_name"[^>]*>.*?</string>', strings, flags=re.S) is None:
    raise SystemExit("app_name resource missing.")
strings = re.sub(r'(<string\s+name="app_name"[^>]*>).*?(</string>)',
                 r'\1洛克乐器演奏\2', strings, count=1, flags=re.S)
STRINGS.write_text(strings, encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
match = re.search(r"<application\b[\s\S]*?>", manifest)
if not match:
    raise SystemExit("Manifest application tag missing.")
tag = match.group(0)
if re.search(r'android:label="[^"]*"', tag):
    tag = re.sub(r'android:label="[^"]*"',
                 'android:label="@string/app_name"', tag, count=1)
else:
    tag = tag[:-1] + ' android:label="@string/app_name">'
manifest = manifest[:match.start()] + tag + manifest[match.end():]
MANIFEST.write_text(manifest, encoding="utf-8")

# Invert the app mark colors: green background becomes white, former white glyph becomes black.
ICON.write_text("""<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp"
    android:height="48dp"
    android:viewportWidth="48"
    android:viewportHeight="48">
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M0,0h48v48h-48z" />
    <path
        android:fillColor="#000000"
        android:pathData="M28,5h14v6H34v20h-6z" />
    <path
        android:fillColor="#000000"
        android:pathData="M18,35c0,-4.4 3.4,-7.8 7.7,-7.8s7.7,3.4 7.7,7.8s-3.4,7.8 -7.7,7.8s-7.7,-3.4 -7.7,-7.8z" />
    <path
        android:fillColor="#000000"
        android:pathData="M28,5h14v5H28z" />
</vector>
""", encoding="utf-8")

# Postconditions catch regressions before Gradle packaging.
note = NOTE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
if "int cellX = (index % 3) * 32;" not in note or "Rect src = new Rect(cellX + 1, cellY + 1, cellX + 31, cellY + 31);" not in note:
    raise SystemExit("Full medallion crop missing.")
if "float reveal = (right - bar.left - iconSize - 2 * iconInset)" not in note:
    raise SystemExit("Frame-first icon entrance animation missing.")
if 'android:label="@string/app_name"' not in manifest:
    raise SystemExit("Application label does not reference app_name.")
if "洛克乐器演奏" not in STRINGS.read_text(encoding="utf-8"):
    raise SystemExit("Application display name incorrect.")
icon = ICON.read_text(encoding="utf-8")
if icon.count('android:fillColor="#000000"') < 3 or 'android:fillColor="#FFFFFF"' not in icon:
    raise SystemExit("Inverted launcher icon colors missing.")
if ImageBytes := ASSET.read_bytes():
    if len(ImageBytes) < 1000:
        raise SystemExit("Reference icon atlas looks incomplete.")
print("Applied full clean game-key medallions, frame-first entrance, correct app display name and inverted launcher icon colors.")
