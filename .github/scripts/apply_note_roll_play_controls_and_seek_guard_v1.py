from pathlib import Path

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MATH = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollGestureMath.java"
TEST = ROOT / "app/src/test/java/com/luoke/autopiano/NoteRollGestureMathTest.java"
MARKER = "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1"

note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")

if MARKER not in note:
    note = note.replace(
        "/** Compact resizable and seekable MIDI roll with icon-anchored controls. ICON_ANCHORED_HEADER_V3 AB_LOOP_FADE_BRAND_RESET_V3 NOTE_HEADER_INFO_V2 AB_LOOP_SETTINGS_V1 */",
        "/** Compact resizable and seekable MIDI roll with icon-anchored controls. ICON_ANCHORED_HEADER_V3 AB_LOOP_FADE_BRAND_RESET_V3 NOTE_HEADER_INFO_V2 AB_LOOP_SETTINGS_V1 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 */",
        1,
    )
    if MARKER not in note:
        raise SystemExit("Cannot mark NoteRollView patch: class comment anchor missing.")

    note = note.replace(
        "        void onTogglePlayPause();\n        void onEditSegment();",
        "        void onTogglePlayPause();\n        void onRewind();\n        void onEditSegment();",
        1,
    )
    note = note.replace(
        "    private static final int TOUCH_RANGE_EDIT = 8;\n",
        "    private static final int TOUCH_RANGE_EDIT = 8;\n    private static final int TOUCH_REWIND = 9;\n    private boolean absoluteSeekMoved;\n    private boolean windowGestureStarted;\n",
        1,
    )

    old_header = '''        // Close is deliberately the leftmost target; play/pause sits beside it.
        drawHeaderChip(canvas, new RectF(5 * density, buttonTop, 30 * density, buttonBottom),
                "×", 0xff455667, density);
        drawHeaderChip(canvas, new RectF(33 * density, buttonTop, 59 * density, buttonBottom),
                playing ? "Ⅱ" : "▶", playing ? 0xff4c8d80 : 0xff455667, density);
'''
    new_header = '''        // Stable three-control row: close, one start/pause toggle, and rewind.
        drawHeaderChip(canvas, new RectF(5 * density, buttonTop, 28 * density, buttonBottom),
                "×", 0xff455667, density);
        drawHeaderChip(canvas, new RectF(30 * density, buttonTop, 67 * density, buttonBottom),
                "演奏", playing ? 0xff4c8d80 : 0xff455667, density);
        drawHeaderChip(canvas, new RectF(69 * density, buttonTop, 93 * density, buttonBottom),
                "⏮︎", 0xff455667, density);
'''
    if old_header not in note:
        raise SystemExit("Cannot locate current note-roll header play control.")
    note = note.replace(old_header, new_header, 1)

    old_down = '''                if (y >= 3 * density && y < 27 * density
                        && x >= 4 * density && x <= 31 * density) {
                    touchMode = TOUCH_CLOSE;
                } else if (y >= 3 * density && y < 27 * density
                        && x > 31 * density && x <= 61 * density) {
                    touchMode = TOUCH_PLAY_PAUSE;
                } else if (y >= 50 * density && y < 72 * density
'''
    new_down = '''                windowGestureStarted = false;
                absoluteSeekMoved = false;
                if (y >= 3 * density && y < 27 * density
                        && x >= 4 * density && x <= 29 * density) {
                    touchMode = TOUCH_CLOSE;
                } else if (y >= 3 * density && y < 27 * density
                        && x > 29 * density && x <= 68 * density) {
                    touchMode = TOUCH_PLAY_PAUSE;
                } else if (y >= 3 * density && y < 27 * density
                        && x > 68 * density && x <= 95 * density) {
                    touchMode = TOUCH_REWIND;
                } else if (y >= 50 * density && y < 72 * density
'''
    if old_down not in note:
        raise SystemExit("Cannot locate NoteRollView touch-down control routing.")
    note = note.replace(old_down, new_down, 1)

    old_progress_down = '''                } else if (y >= h - 24 * density && y <= h - 12 * density) {
                    // The narrow strip is the precise progress target; the notes above it remain a gentle scrub surface.
                    touchMode = TOUCH_SEEK_ABSOLUTE;
                    scrubbing = true;
                    positionDuringScrub = absoluteSeekAt(x, density);
                    positionMicros = positionDuringScrub;
                    invalidate();
'''
    new_progress_down = '''                } else if (y >= h - 24 * density && y <= h - 12 * density) {
                    // Do not seek on ACTION_DOWN: a stray touch or a tiny pre-drag
                    // movement must not teleport the playhead before intent is clear.
                    touchMode = TOUCH_SEEK_ABSOLUTE;
                    absoluteSeekMoved = false;
                    positionDuringScrub = positionMicros;
'''
    if old_progress_down not in note:
        raise SystemExit("Cannot locate current immediate-seek-on-down block.")
    note = note.replace(old_progress_down, new_progress_down, 1)

    old_move_window = '''                if (touchMode == TOUCH_MOVE_WINDOW) {
                    notifyWindowGesture(MODE_MOVE, 0, Math.round(rawDx), Math.round(rawDy), PHASE_UPDATE);
                } else if (touchMode == TOUCH_RESIZE) {
                    notifyWindowGesture(MODE_RESIZE, touchEdges, Math.round(rawDx), Math.round(rawDy), PHASE_UPDATE);
                } else if (touchMode == TOUCH_RANGE_EDIT) {
'''
    new_move_window = '''                if (touchMode == TOUCH_MOVE_WINDOW) {
                    if (gestureMoved) {
                        windowGestureStarted = true;
                        notifyWindowGesture(MODE_MOVE, 0, Math.round(rawDx), Math.round(rawDy), PHASE_UPDATE);
                    }
                } else if (touchMode == TOUCH_RESIZE) {
                    if (gestureMoved) {
                        windowGestureStarted = true;
                        notifyWindowGesture(MODE_RESIZE, touchEdges, Math.round(rawDx), Math.round(rawDy), PHASE_UPDATE);
                    }
                } else if (touchMode == TOUCH_RANGE_EDIT) {
'''
    if old_move_window not in note:
        raise SystemExit("Cannot locate window gesture update block.")
    note = note.replace(old_move_window, new_move_window, 1)

    old_absolute_move = '''                } else if (touchMode == TOUCH_SEEK_ABSOLUTE) {
                    positionDuringScrub = absoluteSeekAt(x, density);
                    positionMicros = positionDuringScrub;
                    invalidate();
                } else if (touchMode == TOUCH_SCRUB && Math.abs(dx) > touchSlop
'''
    new_absolute_move = '''                } else if (touchMode == TOUCH_SEEK_ABSOLUTE) {
                    if (NoteRollGestureMath.shouldUpdateAbsoluteSeek(dx, dy, touchSlop)) {
                        absoluteSeekMoved = true;
                        scrubbing = true;
                        positionDuringScrub = absoluteSeekAt(x, density);
                        positionMicros = positionDuringScrub;
                        invalidate();
                    }
                } else if (touchMode == TOUCH_SCRUB && Math.abs(dx) > touchSlop
'''
    if old_absolute_move not in note:
        raise SystemExit("Cannot locate absolute seek move block.")
    note = note.replace(old_absolute_move, new_absolute_move, 1)

    old_scrub_delta = '''                    long window = visibleWindowMicros(w, 8 * density, w - 8 * density, density);
                    // A single swipe pans only a small fraction of the visible window, preventing accidental jumps to song end.
                    long delta = Math.round((-dx / Math.max(1f, w)) * Math.min(1_000_000L, window * .16f));
                    long safeEnd = safeScrubEnd();
'''
    new_scrub_delta = '''                    long window = visibleWindowMicros(w, 8 * density, w - 8 * density, density);
                    // Note-field swipes are intentionally gentle; the thin bottom rail
                    // remains the precise full-song seek target.
                    long delta = NoteRollGestureMath.gentlePanDelta(dx, w, window);
                    long safeEnd = safeScrubEnd();
'''
    if old_scrub_delta not in note:
        raise SystemExit("Cannot locate gentle note-pan delta calculation.")
    note = note.replace(old_scrub_delta, new_scrub_delta, 1)

    old_up_buttons = '''                } else if (touchMode == TOUCH_PLAY_PAUSE && !gestureMoved) {
                    if (interactionListener != null) interactionListener.onTogglePlayPause();
                } else if (touchMode == TOUCH_SEGMENT && !gestureMoved) {
'''
    new_up_buttons = '''                } else if (touchMode == TOUCH_PLAY_PAUSE && !gestureMoved) {
                    if (interactionListener != null) interactionListener.onTogglePlayPause();
                } else if (touchMode == TOUCH_REWIND && !gestureMoved) {
                    if (interactionListener != null) interactionListener.onRewind();
                } else if (touchMode == TOUCH_SEGMENT && !gestureMoved) {
'''
    if old_up_buttons not in note:
        raise SystemExit("Cannot locate play/pause click dispatch.")
    note = note.replace(old_up_buttons, new_up_buttons, 1)

    old_up_seek = '''                } else if ((touchMode == TOUCH_SCRUB && scrubbing) || touchMode == TOUCH_SEEK_ABSOLUTE) {
                    positionMicros = positionDuringScrub;
                    if (interactionListener != null) interactionListener.onSeek(positionMicros);
                    scrubbing = false;
                    invalidate();
                } else if (touchMode == TOUCH_MOVE_WINDOW) {
                    notifyWindowGesture(MODE_MOVE, 0, Math.round(dx), Math.round(dy), PHASE_END);
                } else if (touchMode == TOUCH_RESIZE) {
                    notifyWindowGesture(MODE_RESIZE, touchEdges, Math.round(dx), Math.round(dy), PHASE_END);
                }
'''
    new_up_seek = '''                } else if (touchMode == TOUCH_SEEK_ABSOLUTE) {
                    boolean isTap = !gestureMoved;
                    if (absoluteSeekMoved || isTap) {
                        if (isTap) positionDuringScrub = absoluteSeekAt(x, density);
                        positionMicros = positionDuringScrub;
                        if (interactionListener != null) interactionListener.onSeek(positionMicros);
                    }
                    scrubbing = false;
                    invalidate();
                } else if (touchMode == TOUCH_SCRUB && scrubbing) {
                    positionMicros = positionDuringScrub;
                    if (interactionListener != null) interactionListener.onSeek(positionMicros);
                    scrubbing = false;
                    invalidate();
                } else if (touchMode == TOUCH_MOVE_WINDOW) {
                    if (windowGestureStarted)
                        notifyWindowGesture(MODE_MOVE, 0, Math.round(dx), Math.round(dy), PHASE_END);
                } else if (touchMode == TOUCH_RESIZE) {
                    if (windowGestureStarted)
                        notifyWindowGesture(MODE_RESIZE, touchEdges, Math.round(dx), Math.round(dy), PHASE_END);
                }
'''
    if old_up_seek not in note:
        raise SystemExit("Cannot locate touch-up seek/window-finalization block.")
    note = note.replace(old_up_seek, new_up_seek, 1)

    old_cancel = '''            case MotionEvent.ACTION_CANCEL:
                if (touchMode == TOUCH_MOVE_WINDOW)
                    notifyWindowGesture(MODE_MOVE, 0, Math.round(event.getRawX() - downRawX), Math.round(event.getRawY() - downRawY), PHASE_END);
                else if (touchMode == TOUCH_RESIZE)
                    notifyWindowGesture(MODE_RESIZE, touchEdges, Math.round(event.getRawX() - downRawX), Math.round(event.getRawY() - downRawY), PHASE_END);
'''
    new_cancel = '''            case MotionEvent.ACTION_CANCEL:
                if (touchMode == TOUCH_MOVE_WINDOW && windowGestureStarted)
                    notifyWindowGesture(MODE_MOVE, 0, Math.round(event.getRawX() - downRawX), Math.round(event.getRawY() - downRawY), PHASE_END);
                else if (touchMode == TOUCH_RESIZE && windowGestureStarted)
                    notifyWindowGesture(MODE_RESIZE, touchEdges, Math.round(event.getRawX() - downRawX), Math.round(event.getRawY() - downRawY), PHASE_END);
'''
    if old_cancel not in note:
        raise SystemExit("Cannot locate touch-cancel window gesture block.")
    note = note.replace(old_cancel, new_cancel, 1)
    NOTE.write_text(note, encoding="utf-8")

math_source = '''package com.luoke.autopiano;

/** Pure gesture math shared by NoteRollView and JVM regression tests. */
final class NoteRollGestureMath {
    private NoteRollGestureMath() { }

    static long gentlePanDelta(float dx, float width, long visibleWindowMicros) {
        float safeWidth = Math.max(1f, width);
        long maximum = Math.min(500_000L, Math.max(0L, Math.round(visibleWindowMicros * 0.06f)));
        return Math.round((-dx / safeWidth) * maximum);
    }

    static boolean shouldUpdateAbsoluteSeek(float dx, float dy, int touchSlop) {
        return Math.abs(dx) > touchSlop && Math.abs(dx) > Math.abs(dy) * 0.85f;
    }
}
'''
if MATH.exists():
    if "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1" not in MATH.read_text(encoding="utf-8"):
        raise SystemExit("NoteRollGestureMath.java already exists without the expected marker.")
else:
    MATH.write_text(math_source.replace(
        "/** Pure gesture math shared by NoteRollView and JVM regression tests. */",
        "/** Pure gesture math shared by NoteRollView and JVM regression tests. NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 */"
    ), encoding="utf-8")

test_source = '''package com.luoke.autopiano;

import org.junit.Test;
import static org.junit.Assert.*;

public class NoteRollGestureMathTest {
    @Test public void shortSwipeProducesOnlySmallPositionDelta() {
        long delta = NoteRollGestureMath.gentlePanDelta(40f, 400f, 12_000_000L);
        assertTrue(Math.abs(delta) <= 60_000L);
    }

    @Test public void evenFullWidthSwipeIsCapped() {
        long delta = NoteRollGestureMath.gentlePanDelta(1000f, 1000f, 16_000_000L);
        assertTrue(Math.abs(delta) <= 500_000L);
    }

    @Test public void absoluteSeekNeedsAnIntentionalHorizontalGesture() {
        assertFalse(NoteRollGestureMath.shouldUpdateAbsoluteSeek(3f, 0f, 8));
        assertFalse(NoteRollGestureMath.shouldUpdateAbsoluteSeek(20f, 30f, 8));
        assertTrue(NoteRollGestureMath.shouldUpdateAbsoluteSeek(20f, 2f, 8));
    }
}
'''
TEST.parent.mkdir(parents=True, exist_ok=True)
TEST.write_text(test_source, encoding="utf-8")

if "@Override public void onRewind()" not in service:
    service = service.replace(
        "                @Override public void onTogglePlayPause() {\n                    if (playbackThread != null && playbackThread.isAlive()) togglePause();\n                    else startPlayback();\n                    refreshMiniPlaybackButton();\n                }\n                @Override public void onEditSegment()",
        "                @Override public void onTogglePlayPause() {\n                    if (playbackThread != null && playbackThread.isAlive()) togglePause();\n                    else startPlayback();\n                    refreshMiniPlaybackButton();\n                }\n                @Override public void onRewind() { rewindPlaybackToStart(); }\n                @Override public void onEditSegment()",
        1,
    )

service = service.replace('Button stop = smallButton("停止");', 'Button stop = smallButton("⏮︎");', 1)
service = service.replace(
    '            stop.setOnClickListener(v -> stopPlayback());',
    '            stop.setContentDescription("回到起始点");\n            stop.setOnClickListener(v -> rewindPlaybackToStart());',
    1,
)

if "private void rewindPlaybackToStart()" not in service:
    insert_before = "    private void stopPlayback() {\n"
    method = '''    private void rewindPlaybackToStart() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::rewindPlaybackToStart);
            return;
        }
        if (currentSong == null) currentSong = readCurrentSong();
        if (currentSong == null) {
            toast("请先导入 MIDI 曲谱，再回到起始点。");
            return;
        }
        long duration = Math.max(1L, currentSong.durationMicros);
        boolean loopEnabled = prefs.getBoolean(KEY_AB_LOOP_ENABLED, false);
        long target = 0L;
        long activeEnd = duration;
        if (loopEnabled) {
            long startMs = Math.max(0L, prefs.getLong(KEY_RANGE_START_MS, 0L));
            long storedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
            long start = Math.min(duration, startMs * 1000L);
            long end = (storedEndMs <= 0L || storedEndMs * 1000L > duration)
                    ? duration : Math.max(0L, storedEndMs * 1000L);
            if (end <= start) {
                start = 0L;
                end = duration;
            }
            target = Math.min(start, Math.max(0L, duration - 1L));
            activeEnd = Math.max(target + 1L, Math.min(duration, end));
        }
        playbackRangeStartMicros = loopEnabled ? target : 0L;
        playbackRangeEndMicros = loopEnabled ? activeEnd : duration;
        playbackPositionMicros = target;
        playbackBaseMicros = target;
        seekRequestMicros = target;
        Thread running = playbackThread;
        if (running != null && running.isAlive() && playbackActive) {
            seekRequestVersion++;
            synchronized (playbackLock) { playbackLock.notifyAll(); }
        }
        if (noteRollView != null) {
            noteRollView.setCursor(target, playbackActive && !paused);
            refreshNoteRollData();
        }
        refreshMiniPlaybackButton();
        toast(loopEnabled ? "已回到 A 点。" : "已回到歌曲起点。");
    }

'''
    if insert_before not in service:
        raise SystemExit("Cannot find stopPlayback method to insert rewind action.")
    service = service.replace(insert_before, method + insert_before, 1)

if MARKER not in service:
    service = service.replace(
        "/** Android touch-output, calibration overlay and playback controller. COLLAPSED_MUSIC_STATUS_BUBBLE_V1 TOP_LEFT_CALIBRATION_FLOW_V1 AB_LOOP_SETTINGS_V1 AB_LOOP_FIXES_V2 */",
        "/** Android touch-output, calibration overlay and playback controller. COLLAPSED_MUSIC_STATUS_BUBBLE_V1 TOP_LEFT_CALIBRATION_FLOW_V1 AB_LOOP_SETTINGS_V1 AB_LOOP_FIXES_V2 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 */",
        1,
    )
SERVICE.write_text(service, encoding="utf-8")

note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
if MARKER not in note or MARKER not in service or MARKER not in MATH.read_text(encoding="utf-8"):
    raise SystemExit("Gesture/playback patch marker missing after write.")
if '"演奏", playing ? 0xff4c8d80 : 0xff455667' not in note:
    raise SystemExit("The single highlighted 演奏 control was not installed.")
if '"⏮︎"' not in note or 'Button stop = smallButton("⏮︎")' not in service:
    raise SystemExit("The rewind icon is missing from one of the controls.")
if "private void rewindPlaybackToStart()" not in service:
    raise SystemExit("Rewind action was not wired to the playback service.")
print("Applied unified 演奏 state, A/track rewind, gentle-seek thresholds and window drag jitter guard.")
