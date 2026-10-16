from pathlib import Path
import re

SERVICE = Path("LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java")
MARKER = "PRACTICE_GESTURE_WINDOW_HANDOFF_V11"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)


source = SERVICE.read_text(encoding="utf-8")

# V12 replaces the V11 tap handler and uses a map/FIFO queue; do not try to reapply the older patch.
if "PRACTICE_VISUAL_MAPPING_WAIT_QUEUE_V12" in source:
    print("Practice touch V12 supersedes V11; skipping the older patch on the updated source archive.")
    raise SystemExit(0)

if MARKER not in source:
    source = replace_once(
        source,
        "    private final Map<Integer, WindowManager.LayoutParams> practiceKeyTargetParams = new LinkedHashMap<>();\n",
        "    private final Map<Integer, WindowManager.LayoutParams> practiceKeyTargetParams = new LinkedHashMap<>();\n"
        "    // Touched guide is temporarily absent during the relay; other guide windows remain visible.\n"
        "    private final Set<Integer> practiceTapInFlightPitches = new LinkedHashSet<>();\n"
        "    private volatile long practiceGestureGeneration; // " + MARKER + "\n",
        "practice tap handoff state",
    )

    source = replace_once(
        source,
        "            practiceNoteGate.begin(expected);\n",
        "            practiceGestureGeneration++;\n"
        "            practiceNoteGate.begin(expected);\n",
        "generation each note group",
    )

    start = source.find("    private void forwardPracticeKeyTap(PracticeKeyTargetView target) {")
    end = source.find("    private void removePracticeKeyTargetWindow(", start)
    if start < 0 or end < 0:
        raise SystemExit("Missing source anchor: practice tap forwarding method")
    methods = r'''    private void forwardPracticeKeyTap(PracticeKeyTargetView target) {
        if (target == null || practiceKeyTargetViews.get(target.pitch) != target) return;

        final long tapGeneration;
        synchronized (playbackLock) {
            if (!practiceModeEnabled || !practiceAwaitingInput || stopRequested
                    || !practiceExpectedPitches.contains(target.pitch)) return;
            tapGeneration = practiceGestureGeneration;
        }

        // Remove only the tapped guide. Keep the other chord guides on screen.
        // Window removal reaches the system asynchronously; wait briefly before injecting
        // the replacement touch so hit-testing can fall through to the game surface.
        removePracticeKeyTargetWindow(target.pitch);
        practiceTapInFlightPitches.add(target.pitch);
        mainHandler.postDelayed(
                () -> dispatchPracticeKeyTapAfterWindowSettles(target, tapGeneration), 50L);
    }

    private void dispatchPracticeKeyTapAfterWindowSettles(
            PracticeKeyTargetView target, long tapGeneration) {
        synchronized (playbackLock) {
            if (tapGeneration != practiceGestureGeneration
                    || !practiceModeEnabled || !practiceAwaitingInput || stopRequested
                    || !practiceExpectedPitches.contains(target.pitch)) {
                practiceTapInFlightPitches.remove(target.pitch);
                updatePracticeKeyTargetOverlays();
                return;
            }
        }

        Path path = new Path();
        path.moveTo(target.point.x, target.point.y);
        path.lineTo(target.point.x + 1f, target.point.y + 1f);
        GestureDescription.Builder builder = new GestureDescription.Builder();
        builder.addStroke(new GestureDescription.StrokeDescription(path, 0, TAP_DURATION_MS));
        boolean accepted;
        try {
            accepted = dispatchGesture(builder.build(), new GestureResultCallback() {
                @Override public void onCompleted(GestureDescription gestureDescription) {
                    practiceTapInFlightPitches.remove(target.pitch);
                    synchronized (playbackLock) {
                        if (tapGeneration == practiceGestureGeneration
                                && practiceModeEnabled && practiceAwaitingInput
                                && practiceExpectedPitches.contains(target.pitch)
                                && practiceNoteGate.accept(target.pitch)) {
                            practiceExpectedPitches = practiceNoteGate.remaining();
                            if (practiceNoteGate.isComplete()) playbackLock.notifyAll();
                        }
                    }
                    updatePracticeKeyTargetOverlays();
                }

                @Override public void onCancelled(GestureDescription gestureDescription) {
                    practiceTapInFlightPitches.remove(target.pitch);
                    boolean stillExpected;
                    synchronized (playbackLock) {
                        stillExpected = tapGeneration == practiceGestureGeneration
                                && practiceModeEnabled && practiceAwaitingInput
                                && practiceExpectedPitches.contains(target.pitch);
                    }
                    updatePracticeKeyTargetOverlays();
                    if (stillExpected) toast("游戏键位触控未送达，请再点一次对应键。");
                }
            }, mainHandler);
        } catch (Exception e) {
            accepted = false;
        }

        if (!accepted) {
            practiceTapInFlightPitches.remove(target.pitch);
            boolean stillExpected;
            synchronized (playbackLock) {
                stillExpected = tapGeneration == practiceGestureGeneration
                        && practiceModeEnabled && practiceAwaitingInput
                        && practiceExpectedPitches.contains(target.pitch);
            }
            updatePracticeKeyTargetOverlays();
            if (stillExpected) toast("游戏键位触控未送达，请再点一次对应键。");
        }
    }

'''
    source = source[:start] + methods + source[end:]

    source = replace_once(
        source,
        "        Set<Integer> desired = practiceModeEnabled && practiceAwaitingInput && playbackActive && noteRollView != null\n"
        "                ? practiceExpectedPitches : Collections.emptySet();\n",
        "        Set<Integer> desired = new LinkedHashSet<>();\n"
        "        if (practiceModeEnabled && practiceAwaitingInput && playbackActive && noteRollView != null) {\n"
        "            desired.addAll(practiceExpectedPitches);\n"
        "            desired.removeAll(practiceTapInFlightPitches);\n"
        "        }\n",
        "do not redraw the in-flight guide while the game touch is being injected",
    )

    source = replace_once(
        source,
        "        for (Integer pitch : new ArrayList<>(practiceKeyTargetViews.keySet())) removePracticeKeyTargetWindow(pitch);\n",
        "        synchronized (playbackLock) { practiceGestureGeneration++; }\n"
        "        practiceTapInFlightPitches.clear();\n"
        "        for (Integer pitch : new ArrayList<>(practiceKeyTargetViews.keySet())) removePracticeKeyTargetWindow(pitch);\n",
        "invalidate any queued touch when clearing guides",
    )

    SERVICE.write_text(source, encoding="utf-8")

source = SERVICE.read_text(encoding="utf-8")

# Give the fix a fresh installable app version; do this outside the source-patch
# guard so future builds keep the version stable once it reaches 1.9.1.
BUILD = Path("LuokeAutoPiano/app/build.gradle")
build = BUILD.read_text(encoding="utf-8")
version_match = re.search(r"versionCode\s+(\d+)", build)
if not version_match:
    raise SystemExit("Cannot find versionCode for the practice handoff build.")
if int(version_match.group(1)) < 20:
    build = build[:version_match.start(1)] + "20" + build[version_match.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName for the practice handoff build.")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.1'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

checks = {
    "version marker present": MARKER in source,
    "installable version bumped": "versionCode 20" in BUILD.read_text(encoding="utf-8") and "versionName '1.9.1'" in BUILD.read_text(encoding="utf-8"),
    "only tapped guide is removed": "Remove only the tapped guide. Keep the other chord guides on screen." in source,
    "window handoff delay is present": "postDelayed(\n                () -> dispatchPracticeKeyTapAfterWindowSettles(target, tapGeneration), 50L);" in source,
    "delayed touch is guarded against stale note groups": "tapGeneration != practiceGestureGeneration" in source,
    "tap-in-flight guide is not redrawn": "desired.removeAll(practiceTapInFlightPitches);" in source,
    "failure restores guide and reports retry": "if (stillExpected) toast(\"游戏键位触控未送达，请再点一次对应键。\");" in source,
    "practice tap still uses accessibility gesture injection": "dispatchGesture(builder.build()" in source,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Practice gesture handoff V11 audit failed: " + "; ".join(failed))
print("Practice gesture handoff V11 applied.")
print("AUDIT OK: " + "; ".join(checks))
