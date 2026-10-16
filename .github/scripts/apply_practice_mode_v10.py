from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10"

def rep(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)

note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")

if MARKER not in note and MARKER not in service:
    # Low-contrast practice chip underneath the speed control.
    note = rep(note, "        void onSpeedChange(int speedPercent);\n",
        "        void onSpeedChange(int speedPercent);\n        void onTogglePracticeMode();\n", "practice callback")
    note = rep(note, "    private boolean abLoopEnabled;\n",
        "    private boolean abLoopEnabled;\n    private boolean practiceModeEnabled;\n", "practice UI state")
    note = rep(note, "    private static final int TOUCH_SPEED = 10;\n",
        "    private static final int TOUCH_SPEED = 10;\n    private static final int TOUCH_PRACTICE = 11;\n", "practice touch mode")
    note = rep(note, "    public void setAbLoopEnabled(boolean enabled) {\n        abLoopEnabled = enabled;\n        invalidate();\n    }\n",
        "    public void setAbLoopEnabled(boolean enabled) {\n        abLoopEnabled = enabled;\n        invalidate();\n    }\n\n"
        "    public void setPracticeModeEnabled(boolean enabled) {\n        practiceModeEnabled = enabled;\n        invalidate();\n    }\n\n"
        "    public boolean isPracticeModeEnabled() { return practiceModeEnabled; }\n", "practice setter")
    note = rep(note, "        drawSpeedControl(canvas, w, density);\n",
        "        drawSpeedControl(canvas, w, density);\n        drawPracticeControl(canvas, w, density);\n", "draw practice chip")
    draw = '''    private void drawPracticeControl(Canvas canvas, float width, float density) {
        float left = 8 * density;
        float top = 96 * density;
        float right = Math.min(64 * density, width - 8 * density);
        float bottom = 114 * density;
        if (right - left < 28 * density || bottom > getHeight() - 16 * density) return;
        RectF chip = new RectF(left, top, right, bottom);
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(practiceModeEnabled ? 0x994a8a72 : 0x263e5662);
        canvas.drawRoundRect(chip, 5 * density, 5 * density, paint);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(0.8f * density);
        paint.setColor(practiceModeEnabled ? 0xb4a7ebc5 : 0x3fbdcbd0);
        canvas.drawRoundRect(chip, 5 * density, 5 * density, paint);
        paint.setStyle(Paint.Style.FILL);
        paint.setTextSize(7.5f * density);
        paint.setFakeBoldText(practiceModeEnabled);
        paint.setColor(practiceModeEnabled ? 0xffe4f8ee : 0x8ebac6cc);
        String label = practiceModeEnabled ? "练习  ●" : "练习";
        float textX = chip.centerX() - paint.measureText(label) / 2f;
        float textY = chip.centerY() - (paint.ascent() + paint.descent()) / 2f;
        canvas.drawText(label, textX, textY, paint);
        paint.setFakeBoldText(false);
    }

'''
    note = rep(note, "    private int speedFromX(float x, float density, float width) {",
        draw + "    private int speedFromX(float x, float density, float width) {", "practice chip drawing method")
    note = rep(note, "                } else if (touchEdges != 0) {\n                    touchMode = TOUCH_RESIZE;",
        "                } else if (y >= 96 * density && y < 115 * density\n"
        "                        && x >= 5 * density && x <= Math.min(68 * density, w - 8 * density)) {\n"
        "                    touchMode = TOUCH_PRACTICE;\n"
        "                } else if (touchEdges != 0) {\n                    touchMode = TOUCH_RESIZE;", "practice hitbox")
    note = rep(note, "                if (touchMode == TOUCH_SPEED) {\n                    if (interactionListener != null && speedPercent != speedAtDown) {\n                        interactionListener.onSpeedChange(speedPercent);\n                    }\n                } else if (touchMode == TOUCH_CLOSE && !gestureMoved) {",
        "                if (touchMode == TOUCH_SPEED) {\n                    if (interactionListener != null && speedPercent != speedAtDown) {\n                        interactionListener.onSpeedChange(speedPercent);\n                    }\n                } else if (touchMode == TOUCH_PRACTICE && !gestureMoved) {\n"
        "                    if (interactionListener != null) interactionListener.onTogglePracticeMode();\n"
        "                } else if (touchMode == TOUCH_CLOSE && !gestureMoved) {", "practice click")
    note = note.replace("ROLL_BOTTOM_TIME_AND_SUBTLE_FRAME_V1 */",
                        "ROLL_BOTTOM_TIME_AND_SUBTLE_FRAME_V1 " + MARKER + " */", 1)

if MARKER not in service:
    service = rep(service, "import android.graphics.Path;\n",
        "import android.graphics.Path;\nimport android.graphics.Paint;\n", "guide paint import")
    service = rep(service, "import java.util.ArrayList;\nimport java.util.LinkedHashMap;\nimport java.util.List;\nimport java.util.Map;\n",
        "import java.util.ArrayList;\nimport java.util.Collections;\nimport java.util.LinkedHashMap;\nimport java.util.LinkedHashSet;\nimport java.util.List;\nimport java.util.Map;\nimport java.util.Set;\n", "practice collection imports")
    service = rep(service, "    private boolean updatingAbDialogEnabledCheckbox;\n",
        "    private boolean updatingAbDialogEnabledCheckbox;\n"
        "    private volatile boolean practiceModeEnabled;\n"
        "    private volatile boolean practiceAwaitingInput;\n"
        "    private volatile Set<Integer> practiceExpectedPitches = Collections.emptySet();\n"
        "    private final PracticeNoteGate practiceNoteGate = new PracticeNoteGate();\n"
        "    private final Map<Integer, PracticeKeyTargetView> practiceKeyTargetViews = new LinkedHashMap<>();\n"
        "    private final Map<Integer, WindowManager.LayoutParams> practiceKeyTargetParams = new LinkedHashMap<>();\n", "practice state fields")
    service = rep(service, "    private static final long CHORD_WINDOW_MICROS = 3_000L;\n",
        "    private static final long CHORD_WINDOW_MICROS = 3_000L;\n"
        "    private static final int PRACTICE_RESULT_ABORTED = -1;\n"
        "    private static final int PRACTICE_RESULT_AUTOPLAY = 0;\n"
        "    private static final int PRACTICE_RESULT_MATCHED = 1;\n", "practice result constants")
    service = rep(service, "        prefs = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE);\n",
        "        prefs = getSharedPreferences(MainActivity.PREFS, MODE_PRIVATE);\n"
        "        practiceModeEnabled = prefs.getBoolean(\"practice_mode_enabled\", false);\n", "restore practice preference")
    service = rep(service, "        stopPlayback();\n        removeOverlay(calibrationOverlay);",
        "        stopPlayback();\n        clearPracticeKeyTargetWindows();\n        removeOverlay(calibrationOverlay);", "cleanup target windows")
    service = rep(service, "        if (noteRollView != null) {\n            removeOverlay(noteRollView);\n            noteRollView = null;\n            updateControlPanelPlaybackButtons();",
        "        if (noteRollView != null) {\n            setPracticeModeEnabled(false, false);\n            clearPracticeKeyTargetWindows();\n            removeOverlay(noteRollView);\n            noteRollView = null;\n            updateControlPanelPlaybackButtons();", "disable practice when hiding roll")
    service = rep(service, "                @Override public void onClose() {\n                    removeOverlay(noteRollView);\n                    noteRollView = null;\n                    updateControlPanelPlaybackButtons();",
        "                @Override public void onClose() {\n                    setPracticeModeEnabled(false, false);\n                    clearPracticeKeyTargetWindows();\n                    removeOverlay(noteRollView);\n                    noteRollView = null;\n                    updateControlPanelPlaybackButtons();", "disable practice on close")
    service = rep(service, "                @Override public void onSpeedChange(int speedPercent) { changePlaybackSpeedFromNoteRoll(speedPercent); }\n",
        "                @Override public void onSpeedChange(int speedPercent) { changePlaybackSpeedFromNoteRoll(speedPercent); }\n"
        "                @Override public void onTogglePracticeMode() { togglePracticeModeFromNoteRoll(); }\n", "wire practice chip")
    service = rep(service, "        noteRollView.setAbLoopEnabled(loopEnabled);\n        noteRollView.setData(currentSong,",
        "        noteRollView.setAbLoopEnabled(loopEnabled);\n        noteRollView.setPracticeModeEnabled(practiceModeEnabled);\n        noteRollView.setData(currentSong,", "sync practice button state")
    service = rep(service, "        playbackEverStarted = true;\n        statusBubbleDismissed = false;\n        playbackActive = true;\n",
        "        playbackEverStarted = true;\n        statusBubbleDismissed = false;\n"
        "        practiceModeEnabled = prefs.getBoolean(\"practice_mode_enabled\", practiceModeEnabled);\n"
        "        playbackActive = true;\n", "restore practice before playback")
    anchor = '''                // A scrub that lands while a chord is waiting must reposition before sending it.
                if (seekRequestVersion != observedSeekVersion) continue;
                List<Point> points = new ArrayList<>();'''
    replacement = '''                // A scrub that lands while a chord is waiting must reposition before sending it.
                if (seekRequestVersion != observedSeekVersion) continue;
                boolean noteWasPracticed = false;
                if (practiceModeEnabled) {
                    int practiceResult = awaitPracticeBatch(batch, transpose, at, observedSeekVersion);
                    if (practiceResult == PRACTICE_RESULT_ABORTED) {
                        if (stopRequested) break;
                        continue;
                    }
                    if (practiceResult == PRACTICE_RESULT_MATCHED) noteWasPracticed = true;
                    // Rebase at the answered note so waiting time never makes following notes catch up.
                    if (practiceResult == PRACTICE_RESULT_MATCHED
                            || practiceResult == PRACTICE_RESULT_AUTOPLAY) {
                        baseMicros = at;
                        playbackBaseMicros = at;
                        playbackPositionMicros = at;
                        playbackStartMs = SystemClock.elapsedRealtime();
                        pausedDurationMs = 0L;
                        speedPercent = Math.max(50, Math.min(200, activeSpeedPercent));
                    }
                    if (practiceResult == PRACTICE_RESULT_AUTOPLAY
                            && !awaitTarget(0L, observedSeekVersion)) {
                        if (stopRequested) break;
                        continue;
                    }
                }
                // In practice mode, successful physical taps already played this note group.
                if (noteWasPracticed) {
                    sentBatches++;
                    continue;
                }
                List<Point> points = new ArrayList<>();'''
    service = rep(service, anchor, replacement, "insert wait at each note group")

    methods = r'''    private void togglePracticeModeFromNoteRoll() {
        setPracticeModeEnabled(!practiceModeEnabled, true);
    }

    private void setPracticeModeEnabled(boolean enabled, boolean showFeedback) {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(() -> setPracticeModeEnabled(enabled, showFeedback));
            return;
        }
        practiceModeEnabled = enabled;
        prefs.edit().putBoolean("practice_mode_enabled", enabled).apply();
        if (noteRollView != null) noteRollView.setPracticeModeEnabled(enabled);
        if (!enabled) clearPracticeKeyTargetWindows();
        else updatePracticeKeyTargetOverlays();
        synchronized (playbackLock) { playbackLock.notifyAll(); }
        if (showFeedback) toast(enabled
                ? "练习模式已开启：音符停在白线处，点击对应游戏键继续。"
                : "练习模式已关闭：恢复正常滚动与自动演奏。");
    }

    private int awaitPracticeBatch(List<MidiParser.NoteEvent> batch, int transpose,
                                  long noteAtMicros, int expectedSeekVersion) {
        LinkedHashSet<Integer> expected = new LinkedHashSet<>();
        for (MidiParser.NoteEvent note : batch) {
            int pitch = note.pitch + transpose;
            // Notes outside the calibrated instrument have no tappable target; don't wait forever for them.
            if (InstrumentLayout.pointForPitch(prefs, pitch) != null) expected.add(pitch);
        }
        synchronized (playbackLock) {
            if (!practiceModeEnabled) return PRACTICE_RESULT_AUTOPLAY;
            practiceNoteGate.begin(expected);
            practiceAwaitingInput = !practiceNoteGate.isComplete();
            practiceExpectedPitches = practiceNoteGate.remaining();
            playbackPositionMicros = noteAtMicros;
            mainHandler.post(() -> {
                if (practiceAwaitingInput && practiceModeEnabled && noteRollView != null) {
                    noteRollView.setCursor(noteAtMicros, playbackActive && !paused);
                }
                updatePracticeKeyTargetOverlays();
            });
            while (!stopRequested && seekRequestVersion == expectedSeekVersion && practiceModeEnabled
                    && (!practiceNoteGate.isComplete() || paused)) {
                try { playbackLock.wait(); }
                catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    practiceNoteGate.clear();
                    practiceAwaitingInput = false;
                    practiceExpectedPitches = Collections.emptySet();
                    mainHandler.post(this::updatePracticeKeyTargetOverlays);
                    return PRACTICE_RESULT_ABORTED;
                }
            }
            int result;
            if (stopRequested || seekRequestVersion != expectedSeekVersion) result = PRACTICE_RESULT_ABORTED;
            else if (!practiceModeEnabled) result = PRACTICE_RESULT_AUTOPLAY;
            else if (practiceNoteGate.isComplete() && !paused) result = PRACTICE_RESULT_MATCHED;
            else result = PRACTICE_RESULT_ABORTED;
            practiceNoteGate.clear();
            practiceAwaitingInput = false;
            practiceExpectedPitches = Collections.emptySet();
            mainHandler.post(this::updatePracticeKeyTargetOverlays);
            return result;
        }
    }

    private void updatePracticeKeyTargetOverlays() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::updatePracticeKeyTargetOverlays);
            return;
        }
        Set<Integer> desired = practiceModeEnabled && practiceAwaitingInput && playbackActive && noteRollView != null
                ? practiceExpectedPitches : Collections.emptySet();
        for (Integer pitch : new ArrayList<>(practiceKeyTargetViews.keySet())) {
            if (!desired.contains(pitch)) removePracticeKeyTargetWindow(pitch);
        }
        for (Integer pitch : desired) {
            if (practiceKeyTargetViews.containsKey(pitch)) continue;
            Point point = InstrumentLayout.pointForPitch(prefs, pitch);
            if (point == null) continue;
            int size = practiceTargetSizePx(pitch, point);
            PracticeKeyTargetView target = new PracticeKeyTargetView(pitch, point);
            WindowManager.LayoutParams p = new WindowManager.LayoutParams(
                    size, size, WindowManager.LayoutParams.TYPE_ACCESSIBILITY_OVERLAY,
                    WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                            | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                            | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                    PixelFormat.TRANSLUCENT);
            p.gravity = Gravity.TOP | Gravity.LEFT;
            int sw = getResources().getDisplayMetrics().widthPixels;
            int sh = getResources().getDisplayMetrics().heightPixels;
            p.x = Math.max(0, Math.min(sw - size, point.x - size / 2));
            p.y = Math.max(0, Math.min(sh - size, point.y - size / 2));
            try {
                windowManager.addView(target, p);
                practiceKeyTargetViews.put(pitch, target);
                practiceKeyTargetParams.put(pitch, p);
            } catch (Exception e) {
                android.util.Log.e("LuokePractice", "Unable to show key guide for pitch " + pitch, e);
                clearPracticeKeyTargetWindows();
                practiceModeEnabled = false;
                prefs.edit().putBoolean("practice_mode_enabled", false).apply();
                if (noteRollView != null) noteRollView.setPracticeModeEnabled(false);
                synchronized (playbackLock) { playbackLock.notifyAll(); }
                toast("练习键位引导无法显示，已自动关闭练习模式。");
                return;
            }
        }
    }

    private int practiceTargetSizePx(int pitch, Point point) {
        double nearest = Double.MAX_VALUE;
        for (int otherPitch : InstrumentLayout.PITCHES) {
            if (otherPitch == pitch) continue;
            Point other = InstrumentLayout.pointForPitch(prefs, otherPitch);
            if (other == null) continue;
            double distance = Math.hypot((double) other.x - point.x, (double) other.y - point.y);
            if (distance > 0d) nearest = Math.min(nearest, distance);
        }
        int size = dp(32);
        if (nearest != Double.MAX_VALUE) size = Math.min(size, (int) Math.floor(nearest * 0.62d));
        return Math.max(22, size);
    }

    private void forwardPracticeKeyTap(PracticeKeyTargetView target) {
        if (target == null || practiceKeyTargetViews.get(target.pitch) != target) return;
        removePracticeKeyTargetWindow(target.pitch);
        Path path = new Path();
        path.moveTo(target.point.x, target.point.y);
        path.lineTo(target.point.x + 1f, target.point.y + 1f);
        GestureDescription.Builder builder = new GestureDescription.Builder();
        builder.addStroke(new GestureDescription.StrokeDescription(path, 0, TAP_DURATION_MS));
        boolean accepted;
        try {
            accepted = dispatchGesture(builder.build(), new GestureResultCallback() {
                @Override public void onCompleted(GestureDescription gestureDescription) {
                    synchronized (playbackLock) {
                        if (practiceModeEnabled && practiceAwaitingInput && practiceNoteGate.accept(target.pitch)) {
                            practiceExpectedPitches = practiceNoteGate.remaining();
                            if (practiceNoteGate.isComplete()) playbackLock.notifyAll();
                        }
                    }
                    updatePracticeKeyTargetOverlays();
                }
                @Override public void onCancelled(GestureDescription gestureDescription) {
                    updatePracticeKeyTargetOverlays();
                    toast("游戏键位触控未送达，请再点一次对应键。");
                }
            }, mainHandler);
        } catch (Exception e) { accepted = false; }
        if (!accepted) {
            updatePracticeKeyTargetOverlays();
            toast("游戏键位触控未送达，请再点一次对应键。");
        }
    }

    private void removePracticeKeyTargetWindow(int pitch) {
        PracticeKeyTargetView view = practiceKeyTargetViews.remove(pitch);
        practiceKeyTargetParams.remove(pitch);
        if (view != null) removeOverlay(view);
    }

    private void clearPracticeKeyTargetWindows() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::clearPracticeKeyTargetWindows);
            return;
        }
        for (Integer pitch : new ArrayList<>(practiceKeyTargetViews.keySet())) removePracticeKeyTargetWindow(pitch);
        practiceKeyTargetViews.clear();
        practiceKeyTargetParams.clear();
    }

    private final class PracticeKeyTargetView extends View {
        final int pitch;
        final Point point;
        private final Paint guidePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        private final float density;
        private float downX, downY;
        private boolean moved;

        PracticeKeyTargetView(int pitch, Point point) {
            super(MusicAccessibilityService.this);
            this.pitch = pitch;
            this.point = new Point(point.x, point.y);
            density = getResources().getDisplayMetrics().density;
            setClickable(true);
            setContentDescription("练习提示键 " + MidiParser.noteName(pitch));
        }

        @Override protected void onDraw(android.graphics.Canvas canvas) {
            super.onDraw(canvas);
            float cx = getWidth() / 2f;
            float cy = getHeight() / 2f;
            float radius = Math.min(getWidth(), getHeight()) * 0.42f;
            guidePaint.setStyle(Paint.Style.FILL);
            guidePaint.setColor(0x3828e89a);
            canvas.drawCircle(cx, cy, radius, guidePaint);
            guidePaint.setStyle(Paint.Style.STROKE);
            guidePaint.setStrokeWidth(2.2f * density);
            guidePaint.setColor(0xf4a4ffce);
            canvas.drawCircle(cx, cy, radius * 0.84f, guidePaint);
            guidePaint.setStrokeWidth(1f * density);
            guidePaint.setColor(0xafa4ffce);
            canvas.drawCircle(cx, cy, radius * 0.57f, guidePaint);
            guidePaint.setStyle(Paint.Style.FILL);
            guidePaint.setTextSize(Math.max(7f * density, Math.min(9f * density, getWidth() * 0.22f)));
            guidePaint.setFakeBoldText(true);
            guidePaint.setColor(0xffeffff6);
            String label = MidiParser.noteName(pitch);
            canvas.drawText(label, cx - guidePaint.measureText(label) / 2f,
                    cy + guidePaint.getTextSize() * 0.35f, guidePaint);
            guidePaint.setFakeBoldText(false);
        }

        @Override public boolean onTouchEvent(MotionEvent event) {
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    downX = event.getX();
                    downY = event.getY();
                    moved = false;
                    invalidate();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    if (Math.hypot(event.getX() - downX, event.getY() - downY) > dp(8)) moved = true;
                    return true;
                case MotionEvent.ACTION_UP:
                    if (!moved) {
                        performClick();
                        mainHandler.post(() -> forwardPracticeKeyTap(this));
                    }
                    invalidate();
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    moved = true;
                    invalidate();
                    return true;
                default: return true;
            }
        }

        @Override public boolean performClick() {
            super.performClick();
            return true;
        }
    }

'''
    service = rep(service, '    private void togglePause() {', methods + '    private void togglePause() {', "practice wait and guides")

    service = rep(service, '        } finally {\n            final int finalSentBatches = sentBatches;',
        '        } finally {\n            synchronized (playbackLock) {\n'
        '                practiceNoteGate.clear();\n'
        '                practiceAwaitingInput = false;\n'
        '                practiceExpectedPitches = Collections.emptySet();\n'
        '                playbackLock.notifyAll();\n'
        '            }\n'
        '            mainHandler.post(this::updatePracticeKeyTargetOverlays);\n'
        '            final int finalSentBatches = sentBatches;', "clear practice state when playback exits")
    service = rep(service,
        '    private void stopPlayback() {\n        synchronized (playbackLock) {\n            stopRequested = true;\n            paused = false;\n            playbackLock.notifyAll();\n        }',
        '    private void stopPlayback() {\n        synchronized (playbackLock) {\n'
        '            stopRequested = true;\n'
        '            paused = false;\n'
        '            practiceNoteGate.clear();\n'
        '            practiceAwaitingInput = false;\n'
        '            practiceExpectedPitches = Collections.emptySet();\n'
        '            playbackLock.notifyAll();\n'
        '        }\n'
        '        clearPracticeKeyTargetWindows();', "release practice wait on stop")
    service = service.replace('int minHeight = Math.min(dp(100), Math.max(dp(78), screenHeight - dp(12)));',
                              'int minHeight = Math.min(dp(132), Math.max(dp(100), screenHeight - dp(12)));')
    service = service.replace('AB_DIALOG_VISIBLE_SAVE_FEEDBACK_V9 NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1',
        'AB_DIALOG_VISIBLE_SAVE_FEEDBACK_V9 ' + MARKER + ' NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1', 1)
    if MARKER not in service:
        service = service.replace('public class MusicAccessibilityService extends AccessibilityService {',
            'public class MusicAccessibilityService extends AccessibilityService { // ' + MARKER, 1)

helper = ROOT / "app/src/main/java/com/luoke/autopiano/PracticeNoteGate.java"
tests = ROOT / "app/src/test/java/com/luoke/autopiano/PracticeNoteGateTest.java"
helper.write_text('''package com.luoke.autopiano;

import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.Set;

/** Tracks the distinct pitches that need a learner tap before a note group can advance. */
final class PracticeNoteGate {
    private final LinkedHashSet<Integer> remaining = new LinkedHashSet<>();

    void begin(Collection<Integer> pitches) {
        remaining.clear();
        if (pitches != null) remaining.addAll(pitches);
    }

    boolean accept(int pitch) { return remaining.remove(pitch); }
    boolean isComplete() { return remaining.isEmpty(); }
    Set<Integer> remaining() {
        return Collections.unmodifiableSet(new LinkedHashSet<>(remaining));
    }
    void clear() { remaining.clear(); }
}
''', encoding="utf-8")
tests.write_text('''package com.luoke.autopiano;

import org.junit.Test;
import java.util.Arrays;
import java.util.LinkedHashSet;
import static org.junit.Assert.*;

public class PracticeNoteGateTest {
    @Test public void singleNoteWaitsForItsExactPitch() {
        PracticeNoteGate gate = new PracticeNoteGate();
        gate.begin(Arrays.asList(60));
        assertFalse(gate.isComplete());
        assertFalse(gate.accept(62));
        assertFalse(gate.isComplete());
        assertTrue(gate.accept(60));
        assertTrue(gate.isComplete());
    }

    @Test public void chordRequiresEveryDistinctPitch() {
        PracticeNoteGate gate = new PracticeNoteGate();
        gate.begin(Arrays.asList(60, 64, 67, 60));
        assertEquals(new LinkedHashSet<>(Arrays.asList(60, 64, 67)), gate.remaining());
        assertTrue(gate.accept(64));
        assertFalse(gate.isComplete());
        assertTrue(gate.accept(60));
        assertFalse(gate.accept(60));
        assertFalse(gate.isComplete());
        assertTrue(gate.accept(67));
        assertTrue(gate.isComplete());
    }

    @Test public void clearResetsPendingPitches() {
        PracticeNoteGate gate = new PracticeNoteGate();
        gate.begin(Arrays.asList(45, 52));
        gate.clear();
        assertTrue(gate.isComplete());
        assertTrue(gate.remaining().isEmpty());
        assertFalse(gate.accept(45));
    }
}
''', encoding="utf-8")

m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode.")
if int(m.group(1)) < 19:
    build = build[:m.start(1)] + "19" + build[m.end(1):]
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.0'", build, count=1)

NOTE.write_text(note, encoding="utf-8")
SERVICE.write_text(service, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

checks = {
    "button below speed with inactive and active visual states":
        MARKER in note and "drawPracticeControl(canvas, w, density);" in note
        and "practiceModeEnabled ? 0x994a8a72 : 0x263e5662" in note,
    "practice button triggers mode toggle": "TOUCH_PRACTICE" in note and "onTogglePracticeMode()" in note,
    "practice status is restored and rendered": "practice_mode_enabled" in service
        and "noteRollView.setPracticeModeEnabled(practiceModeEnabled);" in service,
    "playback waits at each note group": "awaitPracticeBatch(batch, transpose, at, observedSeekVersion)" in service,
    "correct key tap is forwarded to game": "dispatchGesture(builder.build()" in service
        and "forwardPracticeKeyTap(this)" in service,
    "only pending keys receive guide overlays": "practiceAwaitingInput && playbackActive" in service
        and "practiceExpectedPitches" in service,
    "toggle off, stop, seek and playback exit release wait": "PRACTICE_RESULT_AUTOPLAY" in service
        and "practiceAwaitingInput = false;" in service,
    "single note and chord gates are tested": "chordRequiresEveryDistinctPitch" in tests.read_text(encoding="utf-8")
        and "singleNoteWaitsForItsExactPitch" in tests.read_text(encoding="utf-8"),
    "v1.9.0 version set": "versionCode 19" in build and "versionName '1.9.0'" in build,
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("Practice mode V10 audit failed: " + "; ".join(failed))
print("Practice mode V10 applied.")
print("AUDIT OK: " + "; ".join(checks.keys()))
