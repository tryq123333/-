from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
LAYOUT = ROOT / "app/src/main/java/com/luoke/autopiano/InstrumentLayout.java"
LAYOUT_TEST = ROOT / "app/src/test/java/com/luoke/autopiano/InstrumentLayoutTest.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12"


def rep(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)


service = SERVICE.read_text(encoding="utf-8")
note = NOTE.read_text(encoding="utf-8")
layout = LAYOUT.read_text(encoding="utf-8")
layout_test = LAYOUT_TEST.read_text(encoding="utf-8")

if MARKER not in service:
    service = rep(service, "import java.io.File;\nimport java.util.ArrayList;\n",
                  "import java.io.File;\nimport java.util.ArrayDeque;\nimport java.util.ArrayList;\n",
                  "queue import")
    service = rep(service,
        "    private final Map<Integer, WindowManager.LayoutParams> practiceKeyTargetParams = new LinkedHashMap<>();\n"
        "    // Touched guide is temporarily absent during the relay; other guide windows remain visible.\n"
        "    private final Set<Integer> practiceTapInFlightPitches = new LinkedHashSet<>();\n"
        "    private volatile long practiceGestureGeneration; // PRACTICE_GESTURE_WINDOW_HANDOFF_V11\n",
        "    private final Map<Integer, WindowManager.LayoutParams> practiceKeyTargetParams = new LinkedHashMap<>();\n"
        "    private volatile Set<Integer> practiceGroupPitches = Collections.emptySet();\n"
        "    // V12 serializes injected key taps because Android cancels a running accessibility gesture when another begins.\n"
        "    private final ArrayDeque<PracticeTapRequest> practiceTapQueue = new ArrayDeque<>();\n"
        "    private final Map<Integer, Long> practiceTapInFlightPitches = new LinkedHashMap<>();\n"
        "    private boolean practiceTapGestureInFlight;\n"
        "    private volatile long practiceGestureGeneration; // PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12\n",
        "queue and group state")

    service = rep(service,
        "                    practiceNoteGate.clear();\n"
        "                    practiceAwaitingInput = false;\n"
        "                    practiceExpectedPitches = Collections.emptySet();\n"
        "                    mainHandler.post(this::updatePracticeKeyTargetOverlays);\n"
        "                    return PRACTICE_RESULT_ABORTED;",
        "                    practiceNoteGate.clear();\n"
        "                    practiceAwaitingInput = false;\n"
        "                    practiceExpectedPitches = Collections.emptySet();\n"
        "                    practiceGroupPitches = Collections.emptySet();\n"
        "                    mainHandler.post(this::updatePracticeKeyTargetOverlays);\n"
        "                    return PRACTICE_RESULT_ABORTED;",
        "clear group when interrupted")
    service = rep(service,
        "            practiceNoteGate.begin(expected);\n"
        "            practiceAwaitingInput = !practiceNoteGate.isComplete();\n"
        "            practiceExpectedPitches = practiceNoteGate.remaining();\n",
        "            practiceNoteGate.begin(expected);\n"
        "            practiceGroupPitches = Collections.unmodifiableSet(new LinkedHashSet<>(expected));\n"
        "            practiceAwaitingInput = !practiceNoteGate.isComplete();\n"
        "            practiceExpectedPitches = practiceNoteGate.remaining();\n",
        "preserve active chord group for visual alignment")
    service = rep(service,
        "            practiceNoteGate.clear();\n"
        "            practiceAwaitingInput = false;\n"
        "            practiceExpectedPitches = Collections.emptySet();\n"
        "            mainHandler.post(this::updatePracticeKeyTargetOverlays);\n"
        "            return result;",
        "            practiceNoteGate.clear();\n"
        "            practiceAwaitingInput = false;\n"
        "            practiceExpectedPitches = Collections.emptySet();\n"
        "            practiceGroupPitches = Collections.emptySet();\n"
        "            mainHandler.post(this::updatePracticeKeyTargetOverlays);\n"
        "            return result;",
        "clear group after answer")
    service = rep(service,
        "        if (!enabled) clearPracticeKeyTargetWindows();\n"
        "        else updatePracticeKeyTargetOverlays();\n",
        "        if (!enabled) clearPracticeKeyTargetWindows();\n"
        "        updatePracticeKeyTargetOverlays();\n",
        "refresh roll after mode toggle")
    service = rep(service,
        "        Set<Integer> desired = new LinkedHashSet<>();\n"
        "        if (practiceModeEnabled && practiceAwaitingInput && playbackActive && noteRollView != null) {\n"
        "            desired.addAll(practiceExpectedPitches);\n"
        "            desired.removeAll(practiceTapInFlightPitches);\n"
        "        }\n",
        "        boolean waitingForPracticeTap = practiceModeEnabled && practiceAwaitingInput && playbackActive && noteRollView != null;\n"
        "        if (noteRollView != null) {\n"
        "            noteRollView.setPracticeWaitState(practiceGroupPitches, practiceExpectedPitches, waitingForPracticeTap);\n"
        "        }\n"
        "        Set<Integer> desired = new LinkedHashSet<>();\n"
        "        if (waitingForPracticeTap) {\n"
        "            desired.addAll(practiceExpectedPitches);\n"
        "            desired.removeAll(practiceTapInFlightPitches.keySet());\n"
        "        }\n",
        "bind current wait state and active tap map")

    service = rep(service,
        "        int size = dp(32);\n"
        "        if (nearest != Double.MAX_VALUE) size = Math.min(size, (int) Math.floor(nearest * 0.62d));\n"
        "        return Math.max(22, size);",
        "        int size = dp(46);\n"
        "        if (nearest != Double.MAX_VALUE) size = Math.min(size, (int) Math.floor(nearest * 0.78d));\n"
        "        return Math.max(30, size);",
        "increase practice guide tap target")

    start = service.find("    private void forwardPracticeKeyTap(PracticeKeyTargetView target) {")
    end = service.find("    private void removePracticeKeyTargetWindow(", start)
    if start < 0 or end < 0:
        raise SystemExit("Missing practice tap forwarding method")
    methods = r'''    private final class PracticeTapRequest {
        final int pitch;
        final Point point;
        final long generation;
        PracticeTapRequest(int pitch, Point point, long generation) {
            this.pitch = pitch;
            this.point = new Point(point.x, point.y);
            this.generation = generation;
        }
    }

    private void forwardPracticeKeyTap(PracticeKeyTargetView target) {
        if (target == null || practiceKeyTargetViews.get(target.pitch) != target) return;

        final long tapGeneration;
        synchronized (playbackLock) {
            if (!practiceModeEnabled || !practiceAwaitingInput || stopRequested
                    || !practiceExpectedPitches.contains(target.pitch)) return;
            tapGeneration = practiceGestureGeneration;
        }
        if (practiceTapInFlightPitches.containsKey(target.pitch)) return;

        // Remove only the tapped guide. Other chord guides remain visible.
        removePracticeKeyTargetWindow(target.pitch);
        practiceTapInFlightPitches.put(target.pitch, tapGeneration);
        PracticeTapRequest request = new PracticeTapRequest(target.pitch, target.point, tapGeneration);
        // Allow TYPE_ACCESSIBILITY_OVERLAY hit testing to settle before the real game touch.
        mainHandler.postDelayed(() -> enqueuePracticeKeyTapAfterWindowSettles(request), 50L);
    }

    private boolean isPracticeTapRequestCurrent(PracticeTapRequest request) {
        synchronized (playbackLock) {
            return request.generation == practiceGestureGeneration
                    && practiceModeEnabled && practiceAwaitingInput && !stopRequested
                    && practiceExpectedPitches.contains(request.pitch);
        }
    }

    private void finishPracticeTapRequest(PracticeTapRequest request) {
        Long generation = practiceTapInFlightPitches.get(request.pitch);
        if (generation != null && generation.longValue() == request.generation) {
            practiceTapInFlightPitches.remove(request.pitch);
        }
    }

    private void enqueuePracticeKeyTapAfterWindowSettles(PracticeTapRequest request) {
        if (!isPracticeTapRequestCurrent(request)) {
            finishPracticeTapRequest(request);
            updatePracticeKeyTargetOverlays();
            pumpPracticeKeyTapQueue();
            return;
        }
        practiceTapQueue.addLast(request);
        pumpPracticeKeyTapQueue();
    }

    /** Starts exactly one injected gesture at a time; dispatchGesture cancels an in-flight gesture if overlapped. */
    private void pumpPracticeKeyTapQueue() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            mainHandler.post(this::pumpPracticeKeyTapQueue);
            return;
        }
        if (practiceTapGestureInFlight) return;
        while (!practiceTapQueue.isEmpty()) {
            PracticeTapRequest request = practiceTapQueue.removeFirst();
            if (!isPracticeTapRequestCurrent(request)) {
                finishPracticeTapRequest(request);
                updatePracticeKeyTargetOverlays();
                continue;
            }

            Path path = new Path();
            path.moveTo(request.point.x, request.point.y);
            path.lineTo(request.point.x + 1f, request.point.y + 1f);
            GestureDescription.Builder builder = new GestureDescription.Builder();
            builder.addStroke(new GestureDescription.StrokeDescription(path, 0, TAP_DURATION_MS));
            practiceTapGestureInFlight = true;
            boolean accepted;
            try {
                accepted = dispatchGesture(builder.build(), new GestureResultCallback() {
                    @Override public void onCompleted(GestureDescription gestureDescription) {
                        practiceTapGestureInFlight = false;
                        finishPracticeTapRequest(request);
                        synchronized (playbackLock) {
                            if (request.generation == practiceGestureGeneration
                                    && practiceModeEnabled && practiceAwaitingInput
                                    && practiceExpectedPitches.contains(request.pitch)
                                    && practiceNoteGate.accept(request.pitch)) {
                                practiceExpectedPitches = practiceNoteGate.remaining();
                                if (practiceNoteGate.isComplete()) playbackLock.notifyAll();
                            }
                        }
                        updatePracticeKeyTargetOverlays();
                        pumpPracticeKeyTapQueue();
                    }

                    @Override public void onCancelled(GestureDescription gestureDescription) {
                        practiceTapGestureInFlight = false;
                        boolean stillExpected = isPracticeTapRequestCurrent(request);
                        finishPracticeTapRequest(request);
                        updatePracticeKeyTargetOverlays();
                        if (stillExpected) toast("游戏键位触控未送达，请再点一次对应键。");
                        pumpPracticeKeyTapQueue();
                    }
                }, mainHandler);
            } catch (Exception e) {
                accepted = false;
            }

            if (!accepted) {
                practiceTapGestureInFlight = false;
                boolean stillExpected = isPracticeTapRequestCurrent(request);
                finishPracticeTapRequest(request);
                updatePracticeKeyTargetOverlays();
                if (stillExpected) toast("游戏键位触控未送达，请再点一次对应键。");
                continue;
            }
            return;
        }
    }

'''
    service = service[:start] + methods + service[end:]

    service = rep(service,
        "        synchronized (playbackLock) { practiceGestureGeneration++; }\n"
        "        practiceTapInFlightPitches.clear();\n"
        "        for (Integer pitch : new ArrayList<>(practiceKeyTargetViews.keySet())) removePracticeKeyTargetWindow(pitch);",
        "        synchronized (playbackLock) { practiceGestureGeneration++; }\n"
        "        practiceTapQueue.clear();\n"
        "        practiceTapInFlightPitches.entrySet().removeIf(entry -> entry.getValue() != practiceGestureGeneration);\n"
        "        for (Integer pitch : new ArrayList<>(practiceKeyTargetViews.keySet())) removePracticeKeyTargetWindow(pitch);",
        "clear queued stale taps")
    service = service.replace("ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10",
                               "ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10 " + MARKER, 1)

if MARKER not in note:
    note = rep(note, "import java.util.List;\n",
        "import java.util.Collections;\nimport java.util.HashSet;\nimport java.util.List;\nimport java.util.Set;\n",
        "practice wait state imports")
    note = rep(note, "    private boolean practiceModeEnabled;\n",
        "    private boolean practiceModeEnabled;\n"
        "    private boolean practiceWaiting;\n"
        "    private Set<Integer> practiceGroupPitches = Collections.emptySet();\n"
        "    private Set<Integer> practiceWaitingPitches = Collections.emptySet();\n",
        "practice waiting display state")
    note = rep(note, "    public boolean isPracticeModeEnabled() { return practiceModeEnabled; }\n",
        "    public boolean isPracticeModeEnabled() { return practiceModeEnabled; }\n\n"
        "    public void setPracticeWaitState(Set<Integer> groupPitches, Set<Integer> waitingPitches, boolean waiting) {\n"
        "        practiceWaiting = waiting;\n"
        "        practiceGroupPitches = groupPitches == null || groupPitches.isEmpty()\n"
        "                ? Collections.emptySet() : new HashSet<>(groupPitches);\n"
        "        practiceWaitingPitches = waitingPitches == null || waitingPitches.isEmpty()\n"
        "                ? Collections.emptySet() : new HashSet<>(waitingPitches);\n"
        "        invalidate();\n"
        "    }\n",
        "wait-state setter")

    note = rep(note,
        "                int keyIconIndex = InstrumentLayout.indexOfPitch(pitch);\n",
        "                int keyIconIndex = InstrumentLayout.indexOfPitch(pitch);\n"
        "                int keyIconCell = InstrumentLayout.gameKeyAtlasCellForPitch(pitch);\n"
        "                boolean practiceGroupNote = practiceWaiting && practiceGroupPitches.contains(pitch)\n"
        "                        && Math.abs(noteStart - positionMicros) <= 10_000L;\n"
        "                boolean practiceNeedsTap = practiceWaitingPitches.contains(pitch);\n",
        "pitch to atlas cell and current waiting-note state")
    note = rep(note,
        "                float minBlockWidth = Math.max(25 * density, badgeWidth + 4 * density);\n",
        "                float minBlockWidth = Math.max(25 * density, badgeWidth + 4 * density);\n"
        "                if (practiceModeEnabled && useGameKeyIcons && keyIconIndex >= 0) {\n"
        "                    minBlockWidth = Math.max(minBlockWidth, 36 * density);\n"
        "                }\n",
        "room for note name labels")
    note = rep(note,
        "                int noteAlpha = Math.max(0, Math.min(255,\n"
        "                        Math.round(255f * fadeOut * fadeIn)));\n",
        "                int noteAlpha = Math.max(0, Math.min(255,\n"
        "                        Math.round(255f * fadeOut * fadeIn)));\n"
        "                if (practiceGroupNote && !practiceNeedsTap) noteAlpha = Math.round(noteAlpha * 0.42f);\n",
        "dim notes already answered within a held chord")
    note = rep(note,
        "                        float iconSize = Math.min(16 * density,\n"
        "                                Math.max(0f, Math.min(bar.height() - 4 * density, badgeHeight - density)));\n",
        "                        float iconSize = practiceGroupNote ? 18 * density : Math.min(16 * density,\n"
        "                                Math.max(0f, Math.min(bar.height() - 4 * density, badgeHeight - density)));\n",
        "highlight waiting note icon size")
    note = rep(note,
        "                        boolean blockReady = iconSize >= 8 * density\n"
        "                                && bar.width() >= iconSize + 2 * iconInset + density\n"
        "                                && bar.left <= right - iconSize - 2 * iconInset;\n",
        "                        boolean blockReady = practiceGroupNote\n"
        "                                || (iconSize >= 8 * density\n"
        "                                && bar.width() >= iconSize + 2 * iconInset + density\n"
        "                                && bar.left <= right - iconSize - 2 * iconInset);\n",
        "allow wait-note medallion to center on playhead")
    note = rep(note,
        "                            float iconCx = bar.left + iconInset + iconSize / 2f;\n"
        "                            iconCx = Math.min(bar.right - iconInset - iconSize / 2f, iconCx);\n"
        "                            int revealAlpha = Math.round(noteAlpha * Math.min(1f, reveal));\n"
        "                            if (revealAlpha > 0) {\n"
        "                                drawOriginalGameKeyIcon(canvas, iconCx, badge.centerY(),\n"
        "                                        iconSize, keyIconIndex, revealAlpha);\n"
        "                            }\n",
        "                            float iconCx = practiceGroupNote ? playheadX : bar.left + iconInset + iconSize / 2f;\n"
        "                            if (!practiceGroupNote) iconCx = Math.min(bar.right - iconInset - iconSize / 2f, iconCx);\n"
        "                            int revealAlpha = practiceGroupNote ? noteAlpha\n"
        "                                    : Math.round(noteAlpha * Math.min(1f, reveal));\n"
        "                            if (revealAlpha > 0) {\n"
        "                                if (practiceGroupNote) {\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                    paint.setColor(practiceNeedsTap ? 0x9f48e69e : 0x6048e69e);\n"
        "                                    canvas.drawCircle(playheadX, badge.centerY(), iconSize * 0.68f, paint);\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                }\n"
        "                                drawOriginalGameKeyIcon(canvas, iconCx, badge.centerY(),\n"
        "                                        iconSize, keyIconCell, revealAlpha);\n"
        "                                if (practiceModeEnabled) {\n"
        "                                    paint.setStyle(Paint.Style.FILL);\n"
        "                                    paint.setAlpha(Math.min(245, noteAlpha));\n"
        "                                    paint.setColor(practiceGroupNote && practiceNeedsTap ? 0xfff0fff5\n"
        "                                            : 0xffc5f2d8);\n"
        "                                    paint.setTextSize(Math.max(6.2f * density, Math.min(7.4f * density, laneHeight * 0.42f)));\n"
        "                                    paint.setFakeBoldText(true);\n"
        "                                    float noteNameX = iconCx + iconSize / 2f + 1.5f * density;\n"
        "                                    float noteNameY = badge.centerY() - (paint.ascent() + paint.descent()) / 2f;\n"
        "                                    if (noteNameX + paint.measureText(noteLabel) <= bar.right - density) {\n"
        "                                        canvas.drawText(noteLabel, noteNameX, noteNameY, paint);\n"
        "                                    }\n"
        "                                    paint.setFakeBoldText(false);\n"
        "                                    paint.setAlpha(255);\n"
        "                                }\n"
        "                            }\n",
        "align correct icon and label at playhead while waiting")
    note = rep(note,
        "        paint.setColor(0x26ffffff);\n"
        "        paint.setStrokeWidth(0.85f * density);\n"
        "        canvas.drawLine(playheadX, top, playheadX, bottom, paint);\n"
        "        paint.setStrokeWidth(1f * density);\n",
        "        paint.setColor(practiceWaiting ? 0xd5a4ffce : 0x26ffffff);\n"
        "        paint.setStrokeWidth((practiceWaiting ? 1.8f : 0.85f) * density);\n"
        "        canvas.drawLine(playheadX, top, playheadX, bottom, paint);\n"
        "        paint.setStrokeWidth(1f * density);\n",
        "make waiting line visibly hold its position")
    note = note.replace("ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10 */",
                        "ROLL_PRACTICE_GATE_AND_KEY_GUIDE_V10 " + MARKER + " */", 1)

if MARKER not in layout:
    layout = rep(layout,
        "    public static int indexOfPitch(int pitch) {\n"
        "        for (int i = 0; i < PITCHES.length; i++) if (PITCHES[i] == pitch) return i;\n"
        "        return -1;\n"
        "    }\n",
        "    public static int indexOfPitch(int pitch) {\n"
        "        for (int i = 0; i < PITCHES.length; i++) if (PITCHES[i] == pitch) return i;\n"
        "        return -1;\n"
        "    }\n\n"
        "    // The 3x3 atlas follows the photographed game's screen order, not MIDI pitch order.\n"
        "    private static final int[] GAME_KEY_ATLAS_CELL_BY_PITCH_INDEX = {8, 3, 4, 5, 6, 7, 0, 1, 2};\n\n"
        "    public static int gameKeyAtlasCellForPitch(int pitch) {\n"
        "        int index = indexOfPitch(pitch);\n"
        "        return index < 0 ? -1 : GAME_KEY_ATLAS_CELL_BY_PITCH_INDEX[index];\n"
        "    }\n",
        "explicit atlas-to-pitch mapping")
    layout = rep(layout, "public final class InstrumentLayout {",
                 "public final class InstrumentLayout { // " + MARKER, "layout patch marker")

if MARKER not in layout_test:
    layout_test = rep(layout_test,
        "    @Test public void piano88ModeCoversStandardRangeAndClassifiesBlackKeys() {",
        "    @Test public void nineKeyPitchIconsMapToCorrectGameAtlasCells() {\n"
        "        assertEquals(8, InstrumentLayout.gameKeyAtlasCellForPitch(45)); // A2\n"
        "        assertEquals(3, InstrumentLayout.gameKeyAtlasCellForPitch(52)); // E3\n"
        "        assertEquals(4, InstrumentLayout.gameKeyAtlasCellForPitch(53)); // F3\n"
        "        assertEquals(5, InstrumentLayout.gameKeyAtlasCellForPitch(55)); // G3\n"
        "        assertEquals(6, InstrumentLayout.gameKeyAtlasCellForPitch(57)); // A3\n"
        "        assertEquals(7, InstrumentLayout.gameKeyAtlasCellForPitch(59)); // B3\n"
        "        assertEquals(0, InstrumentLayout.gameKeyAtlasCellForPitch(60)); // C4\n"
        "        assertEquals(1, InstrumentLayout.gameKeyAtlasCellForPitch(62)); // D4\n"
        "        assertEquals(2, InstrumentLayout.gameKeyAtlasCellForPitch(64)); // E4\n"
        "        assertEquals(-1, InstrumentLayout.gameKeyAtlasCellForPitch(61));\n"
        "    }\n\n"
        "    @Test public void piano88ModeCoversStandardRangeAndClassifiesBlackKeys() {",
        "assert atlas mapping regression tests")
    layout_test = layout_test.replace("public class InstrumentLayoutTest {",
        "public class InstrumentLayoutTest { // " + MARKER, 1)

if "private static int pitchLane(int pitch, int laneCount) {\n        int instrumentIndex" not in note:
    note = rep(note,
        "    private static int pitchLane(int pitch, int laneCount) {\n"
        "        return Math.min(laneCount - 1, Math.floorMod(pitch, 12) * laneCount / 12);\n"
        "    }\n",
        "    private static int pitchLane(int pitch, int laneCount) {\n"
        "        int instrumentIndex = InstrumentLayout.indexOfPitch(pitch);\n"
        "        if (instrumentIndex >= 0) {\n"
        "            int highToLowIndex = InstrumentLayout.PITCHES.length - 1 - instrumentIndex;\n"
        "            return Math.min(laneCount - 1, highToLowIndex * laneCount / InstrumentLayout.PITCHES.length);\n"
        "        }\n"
        "        return Math.min(laneCount - 1, Math.floorMod(pitch, 12) * laneCount / 12);\n"
        "    }\n",
        "stable pitch lane ordering")

build_path = BUILD
build = build_path.read_text(encoding="utf-8")
match = re.search(r"versionCode\s+(\d+)", build)
if not match:
    raise SystemExit("Cannot find versionCode")
if int(match.group(1)) < 21:
    build = build[:match.start(1)] + "21" + build[match.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.2'", build, count=1)

SERVICE.write_text(service, encoding="utf-8")
NOTE.write_text(note, encoding="utf-8")
LAYOUT.write_text(layout, encoding="utf-8")
LAYOUT_TEST.write_text(layout_test, encoding="utf-8")
BUILD.write_text(build, encoding="utf-8")

checks = {
    "patch marker applied": MARKER in service and MARKER in note and MARKER in layout,
    "all touch injections queued serially": "ArrayDeque<PracticeTapRequest> practiceTapQueue" in service
        and "private boolean practiceTapGestureInFlight;" in service
        and "pumpPracticeKeyTapQueue();" in service,
    "other chord guides are preserved": "Remove only the tapped guide. Other chord guides remain visible." in service,
    "tap target enlarged": "int size = dp(46);" in service and "nearest * 0.78d" in service,
    "actual waiting chord holds current notes on playhead": "setPracticeWaitState(practiceGroupPitches, practiceExpectedPitches, waitingForPracticeTap)" in service
        and "float iconCx = practiceGroupNote ? playheadX" in note,
    "waiting playhead visibly highlighted": "practiceWaiting ? 0xd5a4ffce : 0x26ffffff" in note,
    "pitch name shown with icon during practice": "canvas.drawText(noteLabel, noteNameX, noteNameY, paint);" in note,
    "logical pitch maps to true atlas cell": ("GAME_KEY_ATLAS_CELL_BY_PITCH_INDEX = {8, 0, 1, 3, 2, 4, 5, 6, 7}" in layout
        or "GAME_KEY_ATLAS_CELL_BY_PITCH_INDEX = {8, 3, 4, 5, 6, 7, 0, 1, 2}" in layout)
        and "gameKeyAtlasCellForPitch(pitch)" in note,
    "all nine icon cell mappings tested": all(f"gameKeyAtlasCellForPitch({pitch})" in layout_test for pitch in [45, 52, 53, 55, 57, 59, 60, 62, 64]),
    "installable app version bumped": "versionCode 21" in build and "versionName '1.9.2'" in build,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Practice visual/queue V12 audit failed: " + "; ".join(failed))
print("Practice visual/queue V12 applied.")
print("AUDIT OK: " + "; ".join(checks))
