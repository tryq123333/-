from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "PRACTICE_ROLL_PLAYHEAD_RING_BUTTON_SWAP_V14"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)


note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")

if MARKER not in note:
    note = replace_once(
        note,
        "boolean practiceGroupNote = practiceWaiting && practiceGroupPitches.contains(pitch)\n"
        "                        && Math.abs(noteStart - positionMicros) <= 10_000L;\n"
        "                boolean practiceNeedsTap = practiceWaitingPitches.contains(pitch);\n",
        "boolean practiceGroupNote = practiceWaiting && practiceGroupPitches.contains(pitch)\n"
        "                        && Math.abs(noteStart - positionMicros) <= 10_000L;\n"
        "                boolean practiceNeedsTap = practiceWaitingPitches.contains(pitch);\n"
        "                // Give the same playhead medallion in normal playback; practice mode simply holds it there.\n"
        "                boolean normalPlayheadNote = playing && Math.abs(noteStart - positionMicros) <= 70_000L;\n"
        "                boolean playheadFocusNote = practiceGroupNote || normalPlayheadNote;\n",
        "normal-playback playhead note detection",
    )

    note = replace_once(
        note,
        "float iconSize = practiceGroupNote ? 20 * density : Math.min(18 * density,",
        "float iconSize = playheadFocusNote ? 20 * density : Math.min(18 * density,",
        "increase focused icon in normal playback too",
    )
    note = replace_once(
        note,
        "boolean blockReady = practiceGroupNote\n"
        "                                || (iconSize >= 8 * density",
        "boolean blockReady = playheadFocusNote\n"
        "                                || (iconSize >= 8 * density",
        "ensure focused icon appears at playhead",
    )
    note = replace_once(
        note,
        "float iconCx = practiceGroupNote ? playheadX : bar.left + iconInset + iconSize / 2f;\n"
        "                            if (!practiceGroupNote) iconCx = Math.min(bar.right - iconInset - iconSize / 2f, iconCx);\n"
        "                            int revealAlpha = practiceGroupNote ? noteAlpha\n",
        "float iconCx = playheadFocusNote ? playheadX : bar.left + iconInset + iconSize / 2f;\n"
        "                            if (!playheadFocusNote) iconCx = Math.min(bar.right - iconInset - iconSize / 2f, iconCx);\n"
        "                            int revealAlpha = playheadFocusNote ? noteAlpha\n",
        "center icon on playhead in regular playback",
    )
    note = replace_once(
        note,
        "                                if (practiceGroupNote) {\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                    paint.setColor(practiceNeedsTap ? 0x9f48e69e : 0x6048e69e);\n"
        "                                    canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.68f, paint);\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                }\n",
        "                                if (playheadFocusNote) {\n"
        "                                    // Low-opacity ring in ordinary playback; stronger fill while a practice tap is pending.\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                    paint.setColor(practiceNeedsTap ? 0x9f48e69e : 0x6048e69e);\n"
        "                                    canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.68f, paint);\n"
        "                                    paint.setStyle(Paint.Style.STROKE);\n"
        "                                    paint.setStrokeWidth((practiceNeedsTap ? 1.8f : 1.2f) * density);\n"
        "                                    paint.setColor(practiceNeedsTap ? 0xc9a4ffce : 0x6848e69e);\n"
        "                                    canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.82f, paint);\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                    paint.setStrokeWidth(1f * density);\n"
        "                                }\n",
        "show green medallion ring outside practice too",
    )

    # Swap the AB chip and Practice chip vertically; rewind stays alongside the top chip.
    note = replace_once(
        note,
        "        drawHeaderChip(canvas, new RectF(left, 52 * density, left + 61 * density, 69 * density),\n"
        "                rangeEditing ? \"完成\" : \"A/B循环\",\n"
        "                rangeEditing ? 0xff4c8d80 : (abLoopEnabled ? 0xff477960 : 0xff455667), density);\n"
        "        drawHeaderChip(canvas, new RectF(70 * density, 52 * density, 95 * density, 69 * density),\n"
        "                \"⏮︎\", 0xff455667, density);\n"
        "        drawSpeedControl(canvas, w, density);\n"
        "        drawPracticeControl(canvas, w, density);\n",
        "        drawHeaderChip(canvas, new RectF(left, 96 * density, left + 61 * density, 114 * density),\n"
        "                rangeEditing ? \"完成\" : \"A/B循环\",\n"
        "                rangeEditing ? 0xff4c8d80 : (abLoopEnabled ? 0xff477960 : 0xff455667), density);\n"
        "        drawHeaderChip(canvas, new RectF(70 * density, 52 * density, 95 * density, 69 * density),\n"
        "                \"⏮︎\", 0xff455667, density);\n"
        "        drawSpeedControl(canvas, w, density);\n"
        "        drawPracticeControl(canvas, w, density);\n",
        "move AB loop chip to practice position",
    )
    note = replace_once(
        note,
        "        float left = 8 * density;\n"
        "        float top = 96 * density;\n"
        "        float right = Math.min(64 * density, width - 8 * density);\n"
        "        float bottom = 114 * density;\n",
        "        float left = 8 * density;\n"
        "        float top = 52 * density;\n"
        "        float right = Math.min(69 * density, width - 8 * density);\n"
        "        float bottom = 69 * density;\n",
        "move Practice chip to AB position",
    )

    # The top-left chip is Practice now; the bottom-left chip is AB.
    note = replace_once(
        note,
        "                } else if (y >= 50 * density && y < 72 * density\n"
        "                        && x >= 5 * density && x <= 69 * density) {\n"
        "                    touchMode = TOUCH_SEGMENT;\n"
        "                    segmentDownTimeMs = event.getEventTime();\n",
        "                } else if (y >= 50 * density && y < 72 * density\n"
        "                        && x >= 5 * density && x <= 69 * density) {\n"
        "                    touchMode = TOUCH_PRACTICE;\n",
        "top-left chip now toggles practice",
    )
    note = replace_once(
        note,
        "                } else if (y >= 71 * density && y <= 96 * density\n"
        "                        && x >= 5 * density && x <= Math.min(98 * density, w - 5 * density)) {\n",
        "                } else if (y >= 71 * density && y < 96 * density\n"
        "                        && x >= 5 * density && x <= Math.min(98 * density, w - 5 * density)) {\n",
        "avoid speed hitbox overlap with bottom AB chip",
    )
    note = replace_once(
        note,
        "                } else if (y >= 96 * density && y < 115 * density\n"
        "                        && x >= 5 * density && x <= Math.min(68 * density, w - 8 * density)) {\n"
        "                    touchMode = TOUCH_PRACTICE;\n",
        "                } else if (y >= 96 * density && y < 115 * density\n"
        "                        && x >= 5 * density && x <= Math.min(69 * density, w - 8 * density)) {\n"
        "                    touchMode = TOUCH_SEGMENT;\n"
        "                    segmentDownTimeMs = event.getEventTime();\n",
        "bottom-left chip now handles AB",
    )
    note = note.replace(
        "PRACTICE_OCTAVE_DOT_KEYMAP_V13 */",
        "PRACTICE_OCTAVE_DOT_KEYMAP_V13 " + MARKER + " */",
        1,
    )
    NOTE.write_text(note, encoding="utf-8")

if MARKER not in service:
    service = replace_once(
        service,
        "        int size = dp(46);\n"
        "        if (nearest != Double.MAX_VALUE) size = Math.min(size, (int) Math.floor(nearest * 0.78d));\n"
        "        return Math.max(30, size);\n",
        "        int size = dp(60);\n"
        "        if (nearest != Double.MAX_VALUE) size = Math.min(size, (int) Math.floor(nearest * 0.88d));\n"
        "        return Math.max(30, size);\n",
        "increase game-key guide circles",
    )
    service = service.replace(
        "PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12",
        "PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12 " + MARKER,
        1,
    )
    service = service.replace(
        "guidePaint.setStrokeWidth(2.2f * density);",
        "guidePaint.setStrokeWidth(2.6f * density);",
        1,
    )
    SERVICE.write_text(service, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode")
if int(m.group(1)) < 23:
    build = build[:m.start(1)] + "23" + build[m.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.4'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
checks = {
    "V14 marker present": MARKER in note and MARKER in service,
    "playhead focus logic is present": ("normalPlayheadNote = playing && Math.abs(noteStart - positionMicros) <= 70_000L" in note
        or "normalPlayheadNote = practiceModeEnabled && playing && Math.abs(noteStart - positionMicros) <= 70_000L" in note)
        and "if (playheadFocusNote)" in note,
    "practice waiting retains stronger medallion": "practiceNeedsTap ? 0x9f48e69e : 0x6048e69e" in note,
    "guide circle is larger": "int size = dp(60);" in service and "nearest * 0.88d" in service
        and "guidePaint.setStrokeWidth(2.6f * density);" in service,
    "practice chip moved to previous AB location": "float top = 52 * density;" in note and "float bottom = 69 * density;" in note,
    "AB chip moved below speed slider": 'new RectF(left, 96 * density, left + 61 * density, 114 * density)' in note,
    "practice tap hitbox swapped to top-left": "touchMode = TOUCH_PRACTICE;" in note and "y >= 50 * density && y < 72 * density" in note,
    "AB tap hitbox swapped to bottom-left": "touchMode = TOUCH_SEGMENT;" in note and "y >= 96 * density && y < 115 * density" in note,
    "new app version": "versionCode 23" in build and "versionName '1.9.4'" in build,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Practice roll polish V14 audit failed: " + "; ".join(failed))
print("Practice roll polish V14 applied.")
print("AUDIT OK: " + "; ".join(checks))
