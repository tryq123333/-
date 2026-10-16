from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MATH = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollGestureMath.java"
TEST = ROOT / "app/src/test/java/com/luoke/autopiano/NoteRollGestureMathTest.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "NOTE_ROLL_PLAYBACK_ADAPTIVE_HEIGHT_V1"

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": anchor missing.")

service = SERVICE.read_text(encoding="utf-8")
math = MATH.read_text(encoding="utf-8")
test = TEST.read_text(encoding="utf-8")

if MARKER not in service:
    service = once(service,
        "    private WindowManager.LayoutParams noteRollParams;",
        "    private WindowManager.LayoutParams noteRollParams;\n"
        "    // Base height is the user's saved/manual size; playing may temporarily expand the window.\n"
        "    private int noteRollBaseHeightPx = -1;\n"
        "    private int noteRollLastSizingState = -1;",
        "adaptive roll size state fields")

    old_min = "int minHeight = Math.min(dp(100), Math.max(dp(78), screenHeight - dp(12)));"
    new_min = "int minHeight = Math.min(dp(124), Math.max(dp(78), screenHeight - dp(12)));"
    if old_min in service:
        service = service.replace(old_min, new_min)
    elif new_min not in service:
        raise SystemExit("Could not find note-roll minimum height declarations.")

    init_anchor = "int height = noteLayoutV3 ? Math.max(minHeight, Math.min(maxHeight, prefs.getInt(\"note_roll_height_px\", defaultHeight))) : defaultHeight;"
    if init_anchor in service:
        service = service.replace(init_anchor, init_anchor + "\n            noteRollBaseHeightPx = height;\n            noteRollLastSizingState = -1;", 1)
    elif "noteRollBaseHeightPx = height;" not in service:
        raise SystemExit("Cannot initialize adaptive note-roll base height.")

    helper = """    private void syncNoteRollWindowToPlaybackState() {
        if (noteRollView == null || noteRollParams == null || windowManager == null) return;
        boolean isPlaying = playbackThread != null && playbackThread.isAlive()
                && playbackActive && !paused && !stopRequested;
        int state = isPlaying ? 1 : 0;
        if (state == noteRollLastSizingState) return;

        android.util.DisplayMetrics metrics = getResources().getDisplayMetrics();
        int screenHeight = Math.max(1, metrics.heightPixels);
        int minHeight = Math.min(dp(124), Math.max(dp(78), screenHeight - dp(12)));
        int maxHeight = Math.max(minHeight,
                Math.min(screenHeight - dp(8), (int) (screenHeight * .58f)));
        if (noteRollBaseHeightPx <= 0) {
            noteRollBaseHeightPx = Math.max(minHeight, noteRollParams.height);
        }
        int requiredHeight = dp(isPlaying ? 148 : 124);
        int targetHeight = NoteRollGestureMath.playbackOverlayHeight(
                noteRollBaseHeightPx, isPlaying, minHeight, requiredHeight);
        targetHeight = Math.max(minHeight, Math.min(maxHeight, targetHeight));
        if (targetHeight == noteRollParams.height) {
            noteRollLastSizingState = state;
            return;
        }
        int oldHeight = noteRollParams.height;
        int oldY = noteRollParams.y;
        noteRollParams.height = targetHeight;
        noteRollParams.y = Math.max(0, Math.min(screenHeight - targetHeight, oldY));
        try {
            windowManager.updateViewLayout(noteRollView, noteRollParams);
            noteRollLastSizingState = state;
        } catch (Exception ignored) {
            noteRollParams.height = oldHeight;
            noteRollParams.y = oldY;
            noteRollLastSizingState = -1;
        }
    }

"""
    service = once(service,
        "    private void refreshMiniPlaybackButton() {",
        helper + "    private void refreshMiniPlaybackButton() {",
        "insert responsive note-roll window sizing helper")

    refresh_anchor = """        refreshUnifiedPlaybackButton();
    }

    private void removeControlPanel() {"""
    refresh_new = """        refreshUnifiedPlaybackButton();
        // Recompute only on play/pause state changes; never relayout the window every frame.
        syncNoteRollWindowToPlaybackState();
    }

    private void removeControlPanel() {"""
    service = once(service, refresh_anchor, refresh_new,
                   "resize note-roll when playback state changes")

    # Keep a user's chosen/base size separate from the temporary active-playback height.
    gesture_end_old = """        } else if (phase == NoteRollView.PHASE_END) {
            prefs.edit().putInt("note_roll_width_px", noteRollParams.width)
                    .putInt("note_roll_height_px", noteRollParams.height)
                    .putInt("note_roll_x", noteRollParams.x)
                    .putInt("note_roll_y", noteRollParams.y).apply();
            refreshNoteRollData();
        }"""
    gesture_end_new = """        } else if (phase == NoteRollView.PHASE_END) {
            if (mode == NoteRollView.MODE_RESIZE) {
                noteRollBaseHeightPx = noteRollParams.height;
                boolean isPlayingNow = playbackThread != null && playbackThread.isAlive()
                        && playbackActive && !paused && !stopRequested;
                noteRollLastSizingState = isPlayingNow ? 1 : 0;
            }
            int savedBaseHeight = noteRollBaseHeightPx > 0
                    ? noteRollBaseHeightPx : noteRollParams.height;
            prefs.edit().putInt("note_roll_width_px", noteRollParams.width)
                    .putInt("note_roll_height_px", savedBaseHeight)
                    .putInt("note_roll_x", noteRollParams.x)
                    .putInt("note_roll_y", noteRollParams.y).apply();
            refreshNoteRollData();
        }"""
    service = once(service, gesture_end_old, gesture_end_new,
                   "persist manual height but not temporary playback expansion")

    # Ensure sizing initializes when the roll is opened during an already-running song.
    show_anchor = """        refreshNoteRollData();
        updateControlPanelPlaybackButtons();
    }

    private void beginNoteRollSeekGesture() {"""
    show_new = """        refreshNoteRollData();
        syncNoteRollWindowToPlaybackState();
        updateControlPanelPlaybackButtons();
    }

    private void beginNoteRollSeekGesture() {"""
    service = once(service, show_anchor, show_new,
                   "fit the roll window when opened mid-playback")

    service = service.replace(
        "ROLL_FINAL_CONTROLS_SEEK_LAUNCHER_V6 */",
        "ROLL_FINAL_CONTROLS_SEEK_LAUNCHER_V6 " + MARKER + " */",
        1)
    if MARKER not in service:
        service = service.replace(
            "public class MusicAccessibilityService extends AccessibilityService {",
            "public class MusicAccessibilityService extends AccessibilityService { // " + MARKER,
            1)

if "playbackOverlayHeight(" not in math:
    math = once(math,
        """    static boolean pastEntranceBuffer(float noteStartX, float rightEdge, float density) {
        float reserve = 24f * Math.max(0f, density);
        return noteStartX <= rightEdge - reserve;
    }
}""",
        """    static boolean pastEntranceBuffer(float noteStartX, float rightEdge, float density) {
        float reserve = 24f * Math.max(0f, density);
        return noteStartX <= rightEdge - reserve;
    }

    static int playbackOverlayHeight(int baseHeight, boolean playing,
                                     int pausedMinimumHeight, int playingMinimumHeight) {
        int stateMinimum = Math.max(0, playing ? playingMinimumHeight : pausedMinimumHeight);
        return Math.max(Math.max(0, baseHeight), stateMinimum);
    }
}""",
        "add pure adaptive window-height calculation")
if "playbackStateExpandsSmallWindowButRestoresBaseWhenPaused" not in test:
    test = test.rstrip()
    if not test.endswith("}"):
        raise SystemExit("Unexpected NoteRollGestureMathTest ending.")
    test = test[:-1] + """
    @Test public void playbackStateExpandsSmallWindowButRestoresBaseWhenPaused() {
        assertEquals(132, NoteRollGestureMath.playbackOverlayHeight(132, false, 124, 148));
        assertEquals(148, NoteRollGestureMath.playbackOverlayHeight(132, true, 124, 148));
        assertEquals(124, NoteRollGestureMath.playbackOverlayHeight(100, false, 124, 148));
        assertEquals(148, NoteRollGestureMath.playbackOverlayHeight(100, true, 124, 148));
    }

    @Test public void adaptiveWindowPreservesLargerManualHeight() {
        assertEquals(176, NoteRollGestureMath.playbackOverlayHeight(176, false, 124, 148));
        assertEquals(176, NoteRollGestureMath.playbackOverlayHeight(176, true, 124, 148));
    }
}
"""
SERVICE.write_text(service, encoding="utf-8")
MATH.write_text(math, encoding="utf-8")
TEST.write_text(test, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 8", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.8.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
math = MATH.read_text(encoding="utf-8")
test = TEST.read_text(encoding="utf-8")
if "syncNoteRollWindowToPlaybackState();" not in service:
    raise SystemExit("Playback-driven window sizing is not wired.")
if "noteRollBaseHeightPx = noteRollParams.height;" not in service:
    raise SystemExit("Manual base height is not retained.")
if "int minHeight = Math.min(dp(124)" not in service:
    raise SystemExit("Safe minimum height for the speed control/progress rail is missing.")
if "playbackStateExpandsSmallWindowButRestoresBaseWhenPaused" not in test or "adaptiveWindowPreservesLargerManualHeight" not in test:
    raise SystemExit("Adaptive height regression tests are missing.")
if "versionCode 8" not in BUILD.read_text(encoding="utf-8") or "versionName '0.8.0'" not in BUILD.read_text(encoding="utf-8"):
    raise SystemExit("Version bump missing.")
print("Added play/pause-aware note-roll height, protected manual sizing, and JVM height tests; version 0.8.0.")
