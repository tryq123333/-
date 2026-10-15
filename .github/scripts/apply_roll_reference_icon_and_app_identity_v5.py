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
        "Rect src = new Rect(cellX + 12, cellY + 12, cellX + 52, cellY + 52);",
        "Rect src = new Rect(cellX + 2, cellY + 2, cellX + 62, cellY + 62);",
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
if "Rect src = new Rect(cellX + 2, cellY + 2, cellX + 62, cellY + 62);" not in note:
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
