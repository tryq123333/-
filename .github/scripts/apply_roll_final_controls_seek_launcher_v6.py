from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MATH = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollGestureMath.java"
TEST = ROOT / "app/src/test/java/com/luoke/autopiano/NoteRollGestureMathTest.java"
MANIFEST = ROOT / "app/src/main/AndroidManifest.xml"
STRINGS = ROOT / "app/src/main/res/values/strings.xml"
BUILD = ROOT / "app/build.gradle"
OLD_ICON = ROOT / "app/src/main/res/drawable/ic_music_note.xml"
NEW_ICON = ROOT / "app/src/main/res/drawable/launcher_luoke_v2.xml"
MARKER = "ROLL_FINAL_CONTROLS_SEEK_LAUNCHER_V6"

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": anchor missing.")

note = NOTE.read_text(encoding="utf-8")
if MARKER not in note:
    # Remove ⏮︎ from the note-roll header itself; this was distinct from the same control
    # in the main floating panel, which V4 already hides while the roll is open.
    note = once(note,
        """        // Stable three-control row: close, one start/pause toggle, and rewind.
        drawHeaderChip(canvas, new RectF(5 * density, buttonTop, 28 * density, buttonBottom),
                "×", 0xff455667, density);
        drawHeaderChip(canvas, new RectF(30 * density, buttonTop, 67 * density, buttonBottom),
                "演奏", playing ? 0xff4c8d80 : 0xff455667, density);
        drawHeaderChip(canvas, new RectF(69 * density, buttonTop, 93 * density, buttonBottom),
                "⏮︎", 0xff455667, density);""",
        """        // Only close and the unified 演奏 control remain in the note-roll header.
        drawHeaderChip(canvas, new RectF(5 * density, buttonTop, 28 * density, buttonBottom),
                "×", 0xff455667, density);
        drawHeaderChip(canvas, new RectF(30 * density, buttonTop, 95 * density, buttonBottom),
                "演奏", playing ? 0xff4c8d80 : 0xff455667, density);""",
        "hide rewind from note-roll header")

    note = once(note,
        """                } else if (y >= 3 * density && y < 27 * density
                        && x > 29 * density && x <= 68 * density) {
                    touchMode = TOUCH_PLAY_PAUSE;
                } else if (y >= 3 * density && y < 27 * density
                        && x > 68 * density && x <= 95 * density) {
                    touchMode = TOUCH_REWIND;""",
        """                } else if (y >= 3 * density && y < 27 * density
                        && x > 29 * density && x <= 95 * density) {
                    touchMode = TOUCH_PLAY_PAUSE;""",
        "route widened 演奏 hitbox")

    # A note only enters after its leading edge is 24dp inside the canvas. That leaves enough
    # space for the colored bar and its key medallion to be drawn together rather than showing
    # the key picture at the rightmost edge before its surrounding block is visible.
    note = once(note,
        "                if (rawX2 < left || rawX1 > right) continue;",
        "                if (rawX2 < left || !NoteRollGestureMath.pastEntranceBuffer(rawX1, right, density)) continue;",
        "defer note entrance until inside reserved right-edge buffer")
    note = note.replace(
        "ROLL_SEEK_ICON_STABILITY_V4 */",
        "ROLL_SEEK_ICON_STABILITY_V4 " + MARKER + " */",
        1)
    if MARKER not in note:
        note = note.replace("ROLL_SEEK_ICON_STABILITY_V4",
                            "ROLL_SEEK_ICON_STABILITY_V4 " + MARKER, 1)
    NOTE.write_text(note, encoding="utf-8")

math = MATH.read_text(encoding="utf-8")
if "pastEntranceBuffer(" not in math:
    math = once(math,
        """    static boolean shouldUpdateAbsoluteSeek(float dx, float dy, int touchSlop) {
        return Math.abs(dx) > touchSlop && Math.abs(dx) > Math.abs(dy) * 0.85f;
    }
}""",
        """    static boolean shouldUpdateAbsoluteSeek(float dx, float dy, int touchSlop) {
        return Math.abs(dx) > touchSlop && Math.abs(dx) > Math.abs(dy) * 0.85f;
    }

    static boolean pastEntranceBuffer(float noteStartX, float rightEdge, float density) {
        float reserve = 24f * Math.max(0f, density);
        return noteStartX <= rightEdge - reserve;
    }
}""",
        "add tested note entrance boundary")
    MATH.write_text(math, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
if "entranceWaitsUntilBlockHasIconSpace" not in test:
    test = test.rstrip()[:-1] + """
    @Test public void entranceWaitsUntilBlockHasIconSpace() {
        assertFalse(NoteRollGestureMath.pastEntranceBuffer(392f, 400f, 1f));
        assertFalse(NoteRollGestureMath.pastEntranceBuffer(378f, 400f, 1f));
        assertTrue(NoteRollGestureMath.pastEntranceBuffer(376f, 400f, 1f));
        assertTrue(NoteRollGestureMath.pastEntranceBuffer(350f, 400f, 1f));
    }
}
"""
    TEST.write_text(test, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
if MARKER not in service:
    service = once(service,
        "    private volatile long playbackPositionMicros;",
        "    private volatile long playbackPositionMicros;\n    private volatile long playbackUiGeneration;",
        "playback UI generation field")

    # Incrementing the generation at gesture start, seek commit and gesture end invalidates any
    # cursor frames already queued on the UI thread. A frame posted before or during a seek can
    # therefore never overwrite the chosen target after playback resumes.
    service = once(service,
        """        synchronized (playbackLock) {
            playbackWasRunningBeforeNoteScrub = playbackThread != null && playbackThread.isAlive()
                    && playbackActive && !paused && !stopRequested;""",
        """        playbackUiGeneration++;
        synchronized (playbackLock) {
            playbackWasRunningBeforeNoteScrub = playbackThread != null && playbackThread.isAlive()
                    && playbackActive && !paused && !stopRequested;""",
        "invalidate queued frames as seek gesture begins")
    service = once(service,
        """        synchronized (playbackLock) {
            if (playbackWasRunningBeforeNoteScrub && playbackThread != null && playbackThread.isAlive()""",
        """        playbackUiGeneration++;
        synchronized (playbackLock) {
            if (playbackWasRunningBeforeNoteScrub && playbackThread != null && playbackThread.isAlive()""",
        "invalidate queued frames as seek gesture ends")
    service = once(service,
        """        long target = Math.max(start, Math.min(Math.max(start, end - 1L), requestedPositionMicros));
        playbackPositionMicros = target;""",
        """        long target = Math.max(start, Math.min(Math.max(start, end - 1L), requestedPositionMicros));
        playbackUiGeneration++;
        playbackPositionMicros = target;""",
        "invalidate stale UI frames when seek target commits")

    old_frame = """                    final long cursor = playbackPositionMicros;
                    final boolean isRunning = playbackActive && !paused && !stopRequested;
                    mainHandler.post(() -> {
                        // Drop queued frames while playback is paused/stopped or a seek gesture is
                        // active; they otherwise move the visible note window after it is frozen.
                        if (playbackActive && !stopRequested && !paused && noteRollView != null) {
                            noteRollView.setCursor(cursor, isRunning);
                        }
                        refreshMiniPlaybackButton();
                    });"""
    new_frame = """                    final long cursor = playbackPositionMicros;
                    final boolean isRunning = playbackActive && !paused && !stopRequested;
                    final long cursorGeneration = playbackUiGeneration;
                    mainHandler.post(() -> {
                        // A generation check discards frames posted before a seek or while a finger
                        // is dragging. This remains safe even if the UI queue drains after resume.
                        if (cursorGeneration == playbackUiGeneration
                                && playbackActive && !stopRequested && !paused && noteRollView != null) {
                            noteRollView.setCursor(cursor, isRunning);
                        }
                        refreshMiniPlaybackButton();
                    });"""
    service = once(service, old_frame, new_frame, "drop stale cursor frames after seek")
    service = service.replace(
        "ROLL_SEEK_ICON_STABILITY_V4 */",
        "ROLL_SEEK_ICON_STABILITY_V4 " + MARKER + " */",
        1)
    if MARKER not in service:
        service = service.replace("ROLL_SEEK_ICON_STABILITY_V4",
                                  "ROLL_SEEK_ICON_STABILITY_V4 " + MARKER, 1)
    SERVICE.write_text(service, encoding="utf-8")

# Force the next package to advertise a new launcher resource identity and a higher version so
# Android updates the installed package instead of leaving the previously cached icon/label.
strings = STRINGS.read_text(encoding="utf-8")
if '<string name="launcher_app_name">' not in strings:
    strings = strings.replace(
        "</resources>",
        '    <string name="launcher_app_name">洛克乐器演奏</string>\n</resources>',
        1)
else:
    strings = re.sub(r'(<string\s+name="launcher_app_name"[^>]*>).*?(</string>)',
                     r'\1洛克乐器演奏\2', strings, count=1, flags=re.S)
STRINGS.write_text(strings, encoding="utf-8")

icon_content = OLD_ICON.read_text(encoding="utf-8")
NEW_ICON.parent.mkdir(parents=True, exist_ok=True)
NEW_ICON.write_text(icon_content, encoding="utf-8")

manifest = MANIFEST.read_text(encoding="utf-8")
app_match = re.search(r"<application\b[\s\S]*?>", manifest)
if not app_match:
    raise SystemExit("AndroidManifest application tag missing.")
app_tag = app_match.group(0)
def set_attr(tag, name, value):
    pattern = r'\b' + re.escape(name) + r'="[^"]*"'
    if re.search(pattern, tag):
        return re.sub(pattern, name + '="' + value + '"', tag, count=1)
    return tag[:-1] + ' ' + name + '="' + value + '">'
app_tag = set_attr(app_tag, "android:label", "@string/launcher_app_name")
app_tag = set_attr(app_tag, "android:icon", "@drawable/launcher_luoke_v2")
app_tag = set_attr(app_tag, "android:roundIcon", "@drawable/launcher_luoke_v2")
manifest = manifest[:app_match.start()] + app_tag + manifest[app_match.end():]
MANIFEST.write_text(manifest, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 2", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.2.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

# Verify critical state and visible-resource identity before Gradle starts.
note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
math = MATH.read_text(encoding="utf-8")
test = TEST.read_text(encoding="utf-8")
manifest = MANIFEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
if 'drawHeaderChip(canvas, new RectF(69 * density' in note or '"⏮︎", 0xff455667' in note:
    raise SystemExit("Rewind is still drawn in the note-roll header.")
if "x > 29 * density && x <= 95 * density" not in note:
    raise SystemExit("Unified 演奏 hitbox not expanded.")
if "pastEntranceBuffer(rawX1, right, density)" not in note or "pastEntranceBuffer(" not in math:
    raise SystemExit("Reserved right-edge note entrance was not applied.")
if "cursorGeneration == playbackUiGeneration" not in service:
    raise SystemExit("Playback UI generation guard missing.")
if "entranceWaitsUntilBlockHasIconSpace" not in test:
    raise SystemExit("Entrance boundary unit test missing.")
if 'android:label="@string/launcher_app_name"' not in manifest:
    raise SystemExit("Launcher label resource not updated.")
if 'android:icon="@drawable/launcher_luoke_v2"' not in manifest or 'android:roundIcon="@drawable/launcher_luoke_v2"' not in manifest:
    raise SystemExit("New launcher icon resource is not used for both icons.")
if "versionCode 2" not in build or "versionName '0.2.0'" not in build:
    raise SystemExit("Application version wasn't bumped.")
print("Applied note-roll rewind hiding, reserved entrance space, stale-frame invalidation and versioned launcher identity.")
