from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
STRINGS = ROOT / "app/src/main/res/values/strings.xml"
LAUNCHER_ICON = ROOT / "app/src/main/res/drawable/launcher_luoke_v2.xml"
LEGACY_ICON = ROOT / "app/src/main/res/drawable/ic_music_note.xml"
BUILD = ROOT / "app/build.gradle"

service = SERVICE.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
strings = STRINGS.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

# 1. When the A/B card is resized, scale its own content from a stable baseline.
# This changes child sizes, margins, padding and text size, not just the overlay bounds.
if "AB_DIALOG_CONTENT_RESPONSIVE_V1" not in service:
    if "import android.view.ViewGroup;" not in service:
        service = service.replace("import android.view.View;\n",
                                  "import android.view.View;\nimport android.view.ViewGroup;\n", 1)

    helpers = r'''    private static final class AbDialogViewBaseline {
        final int width, height;
        final int paddingLeft, paddingTop, paddingRight, paddingBottom;
        final int marginLeft, marginTop, marginRight, marginBottom;
        final boolean hasMargins;
        final float textSizePx;

        AbDialogViewBaseline(View view) {
            ViewGroup.LayoutParams lp = view.getLayoutParams();
            width = lp == null ? 0 : lp.width;
            height = lp == null ? 0 : lp.height;
            paddingLeft = view.getPaddingLeft();
            paddingTop = view.getPaddingTop();
            paddingRight = view.getPaddingRight();
            paddingBottom = view.getPaddingBottom();
            if (lp instanceof ViewGroup.MarginLayoutParams) {
                ViewGroup.MarginLayoutParams mlp = (ViewGroup.MarginLayoutParams) lp;
                marginLeft = mlp.leftMargin;
                marginTop = mlp.topMargin;
                marginRight = mlp.rightMargin;
                marginBottom = mlp.bottomMargin;
                hasMargins = true;
            } else {
                marginLeft = marginTop = marginRight = marginBottom = 0;
                hasMargins = false;
            }
            textSizePx = view instanceof TextView ? ((TextView) view).getTextSize() : -1f;
        }
    }

    private static int scaleAbDimension(int value, float scale) {
        return value > 0 ? Math.max(1, Math.round(value * scale)) : value;
    }

    private void scaleAbDialogTree(View view, float scaleX, float scaleY, boolean root) {
        Object tag = view.getTag();
        AbDialogViewBaseline baseline;
        if (tag instanceof AbDialogViewBaseline) {
            baseline = (AbDialogViewBaseline) tag;
        } else {
            baseline = new AbDialogViewBaseline(view);
            view.setTag(baseline);
        }

        view.setPadding(scaleAbDimension(baseline.paddingLeft, scaleX),
                scaleAbDimension(baseline.paddingTop, scaleY),
                scaleAbDimension(baseline.paddingRight, scaleX),
                scaleAbDimension(baseline.paddingBottom, scaleY));

        if (!root) {
            ViewGroup.LayoutParams lp = view.getLayoutParams();
            if (lp != null) {
                lp.width = scaleAbDimension(baseline.width, scaleX);
                lp.height = scaleAbDimension(baseline.height, scaleY);
                if (lp instanceof ViewGroup.MarginLayoutParams && baseline.hasMargins) {
                    ViewGroup.MarginLayoutParams mlp = (ViewGroup.MarginLayoutParams) lp;
                    mlp.setMargins(scaleAbDimension(baseline.marginLeft, scaleX),
                            scaleAbDimension(baseline.marginTop, scaleY),
                            scaleAbDimension(baseline.marginRight, scaleX),
                            scaleAbDimension(baseline.marginBottom, scaleY));
                }
                view.setLayoutParams(lp);
            }
        }

        if (view instanceof TextView && baseline.textSizePx > 0f) {
            ((TextView) view).setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,
                    baseline.textSizePx * Math.min(scaleX, scaleY));
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                scaleAbDialogTree(group.getChildAt(i), scaleX, scaleY, false);
            }
        }
        view.invalidate();
    }

'''
    anchor = "    private TextView abSettingsLabel(String text) {"
    if anchor not in service:
        raise SystemExit("A/B responsive layout helper insertion point not found.")
    service = service.replace(anchor, helpers + anchor, 1)

    add_anchor = '''        try {
            windowManager.addView(card, overlayParams);
            card.requestFocus();'''
    listener = r'''        // AB_DIALOG_CONTENT_RESPONSIVE_V1: scale card controls with the resized window.
        final float[] lastAbDialogScale = {-1f, -1f};
        card.addOnLayoutChangeListener((v, leftEdge, topEdge, rightEdge, bottomEdge,
                                        oldLeft, oldTop, oldRight, oldBottom) -> {
            int measuredWidth = rightEdge - leftEdge;
            int measuredHeight = bottomEdge - topEdge;
            if (measuredWidth <= 0 || measuredHeight <= 0) return;
            float scaleX = Math.max(0.62f, Math.min(1.65f, measuredWidth / (float) Math.max(1, defaultWidth)));
            float scaleY = Math.max(0.62f, Math.min(1.55f, measuredHeight / (float) Math.max(1, defaultHeight)));
            if (Math.abs(scaleX - lastAbDialogScale[0]) < 0.015f
                    && Math.abs(scaleY - lastAbDialogScale[1]) < 0.015f) return;
            lastAbDialogScale[0] = scaleX;
            lastAbDialogScale[1] = scaleY;
            scaleAbDialogTree(card, scaleX, scaleY, true);
        });

'''
    if service.count(add_anchor) != 1:
        raise SystemExit("Could not uniquely find A/B dialog attachment point.")
    service = service.replace(add_anchor, listener + add_anchor, 1)

    service = service.replace(
        "AB_LOOP_FIXES_V2 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        "AB_LOOP_FIXES_V2 AB_DIALOG_CONTENT_RESPONSIVE_V1 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1",
        1)

# 2. Subtle outline for the otherwise fully transparent scrolling-note window.
if "ROLL_BOTTOM_TIME_AND_SUBTLE_FRAME_V1" not in note:
    note = note.replace(
        "ROLL_REFERENCE_ICON_ANIMATION_V5 */",
        "ROLL_REFERENCE_ICON_ANIMATION_V5 ROLL_BOTTOM_TIME_AND_SUBTLE_FRAME_V1 */", 1)

    note = note.replace(
        "        if (right <= left || timelineHeight <= 0) {\n"
        "            drawResizeHandle(canvas, w, h, density);\n"
        "            if (playing) postInvalidateDelayed(80L);\n"
        "            return;\n"
        "        }",
        "        if (right <= left || timelineHeight <= 0) {\n"
        "            drawResizeHandle(canvas, w, h, density);\n"
        "            drawSubtleWindowBorder(canvas, w, h, density);\n"
        "            if (playing) postInvalidateDelayed(80L);\n"
        "            return;\n"
        "        }", 1)

    note = note.replace(
        "        float progressY = h - 21 * density;",
        "        float progressY = h - 15 * density;", 1)

    # Add an elapsed/total time label that follows the progress cursor along the rail.
    anchor = '''                paint.setFakeBoldText(false);
            }
        }

        // Low-contrast playhead line restored without a background strip.'''
    time_label = '''                paint.setFakeBoldText(false);
            }
            paint.setStyle(Paint.Style.FILL);
            paint.setFakeBoldText(false);
            paint.setTextSize(5.8f * density);
            paint.setColor(0x70c8d4db);
            String progressTimeLabel = formatTime(positionMicros) + " / " + formatTime(durationMicros);
            float progressTimeWidth = paint.measureText(progressTimeLabel);
            float minTimeX = left;
            float maxTimeX = Math.max(minTimeX, progressRight - progressTimeWidth - 7 * density);
            float progressTimeX = Math.max(minTimeX, Math.min(maxTimeX, cursorX - progressTimeWidth / 2f));
            canvas.drawText(progressTimeLabel, progressTimeX, h - 4.2f * density, paint);
        }

        // Low-contrast playhead line restored without a background strip.'''
    if anchor not in note:
        raise SystemExit("Cannot place moving time label below the note-roll progress rail.")
    note = note.replace(anchor, time_label, 1)

    # The green accent was too saturated; lower its opacity and soften the thumb.
    replacements = [
        ("paint.setColor(0xbfeaf0f4);", "paint.setColor(0x78dce5eb);"),
        ("paint.setColor(0x777c8d99);", "paint.setColor(0x4c7c8d99);"),
        ("paint.setColor(0xff70d9ba);", "paint.setColor(0x758dbdaf);"),
        ("paint.setColor(0xffedf7f4);", "paint.setColor(0xbfdce7e4);"),
        ("paint.setColor(0xff4c8d80);", "paint.setColor(0x887da59a);"),
    ]
    for old, new in replacements:
        if old not in note:
            raise SystemExit("Speed-control color anchor missing: " + old)
        note = note.replace(old, new, 1)

    border_helper = r'''    private void drawSubtleWindowBorder(Canvas canvas, float w, float h, float density) {
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(0.8f * density);
        paint.setColor(0x339bb1c1);
        canvas.drawRoundRect(new RectF(0.8f * density, 0.8f * density,
                        w - 0.8f * density, h - 0.8f * density),
                9 * density, 9 * density, paint);
        paint.setStrokeWidth(1f * density);
        paint.setStyle(Paint.Style.FILL);
        paint.setAlpha(255);
    }

'''
    resize_anchor = "    private void drawResizeHandle(Canvas canvas, float w, float h, float density) {"
    if resize_anchor not in note:
        raise SystemExit("Cannot find note-roll resize-handle helper.")
    note = note.replace(resize_anchor, border_helper + resize_anchor, 1)

    normal_end = '''        drawHeaderOverlay(canvas, w, h, density);
        drawResizeHandle(canvas, w, h, density);
        if (playing) postInvalidateDelayed(80L);'''
    normal_new = '''        drawHeaderOverlay(canvas, w, h, density);
        drawResizeHandle(canvas, w, h, density);
        drawSubtleWindowBorder(canvas, w, h, density);
        if (playing) postInvalidateDelayed(80L);'''
    if normal_end not in note:
        raise SystemExit("Cannot wire subtle border into the normal note-roll draw path.")
    note = note.replace(normal_end, normal_new, 1)

SERVICE.write_text(service, encoding="utf-8")
NOTE.write_text(note, encoding="utf-8")

# 3. Audit/fix the old launcher resource reference: the intended white/black icon existed
# but the manifest had silently reverted to the previous green/white resource.
manifest = re.sub(r'android:icon="@drawable/[^"]+"',
                  'android:icon="@drawable/launcher_luoke_v2"', manifest, count=1)
manifest = re.sub(r'android:roundIcon="@drawable/[^"]+"',
                  'android:roundIcon="@drawable/launcher_luoke_v2"', manifest, count=1)
MANIFEST.write_text(manifest, encoding="utf-8")

icon_xml = '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp"
    android:height="48dp"
    android:viewportWidth="48"
    android:viewportHeight="48">
    <path android:fillColor="#FFFFFF" android:pathData="M0,0h48v48h-48z" />
    <path android:fillColor="#000000" android:pathData="M28,5h14v6H34v20h-6z" />
    <path android:fillColor="#000000" android:pathData="M18,35c0,-4.4 3.4,-7.8 7.7,-7.8s7.7,3.4 7.7,7.8s-3.4,7.8 -7.7,7.8s-7.7,-3.4 -7.7,-7.8z" />
    <path android:fillColor="#000000" android:pathData="M28,5h14v5H28z" />
</vector>
'''
LEGACY_ICON.write_text(icon_xml, encoding="utf-8")
LAUNCHER_ICON.write_text(icon_xml, encoding="utf-8")

# Raise the install version without incrementing again on future patch-chain reruns.
m = re.search(r'versionCode\s+(\d+)', build)
if not m:
    raise SystemExit("Cannot find application versionCode.")
if int(m.group(1)) < 10:
    build = build[:m.start(1)] + "10" + build[m.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]",
               "versionName '1.0.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

# 4. Guard against the earlier features being accidentally lost in future source rebuilds.
service = SERVICE.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
strings = STRINGS.read_text(encoding="utf-8")
main = (ROOT / "app/src/main/java/com/luoke/autopiano/MainActivity.java").read_text(encoding="utf-8")
checks = {
    "A/B inner content resizes": "AB_DIALOG_CONTENT_RESPONSIVE_V1" in service and "scaleAbDialogTree(card, scaleX, scaleY, true)" in service,
    "note-roll window remains separate": "toggleNoteRoll()" in service and "noteRollTemporarilyHiddenByCollapse" not in service,
    "note-roll original key atlas": "drawOriginalGameKeyIcon(canvas" in note and "R.drawable.note_key_atlas" in note,
    "subtle note-roll border": "drawSubtleWindowBorder(canvas, w, h, density)" in note,
    "moving elapsed/total time": "progressTimeLabel" in note,
    "soft speed colors": "paint.setColor(0x758dbdaf)" in note and "paint.setColor(0x78dce5eb)" in note,
    "rewind beside A/B": "ROLL_REWIND_NEXT_TO_AB_V7" in note and '⏮︎' in note,
    "per-song transpose/range": "SONG_SPECIFIC_ROLL_UI_V2" in note,
    "unified play button": "ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3" in note and "演奏" in note,
    "seek generation guard": "ROLL_SEEK_ICON_STABILITY_V4" in note,
    "launcher app name": 'android:label="@string/launcher_app_name"' in manifest and "洛克乐器演奏" in strings,
    "white/black launcher icon": 'android:icon="@drawable/launcher_luoke_v2"' in manifest and 'android:roundIcon="@drawable/launcher_luoke_v2"' in manifest and '#FFFFFF' in LAUNCHER_ICON.read_text(encoding="utf-8") and '#000000' in LAUNCHER_ICON.read_text(encoding="utf-8"),
    "batch MIDI import": "BATCH_MIDI_IMPORT_V1" in main,
    "live song search and scroll restore": "SONG_PICKER_LIVE_SEARCH_V1" in service and "SONG_LIST_SCROLL_RESTORE_V2" in service,
    "roll speed and remove songs": "ROLL_SPEED_CONTROL_AND_SONG_REMOVAL_V1" in note and "ROLL_SPEED_CONTROL_AND_SONG_REMOVAL_V1" in service,
    "main floating panel auto height": "CONTROL_PANEL_CONTENT_SIZING_V1" in service and "syncControlPanelHeightToContent()" in service,
    "version 1.0.0": "versionCode 10" in BUILD.read_text(encoding="utf-8") and "versionName '1.0.0'" in BUILD.read_text(encoding="utf-8"),
}
failed = [label for label, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Feature audit failed: " + "; ".join(failed))
print("Applied responsive A/B dialog, faint note-roll border, lower-contrast speed rail, moving time label, restored launcher icon reference and feature audit.")
print("AUDIT OK: " + "; ".join(checks.keys()))
