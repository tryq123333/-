from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
MAIN = ROOT / "app/src/main/java/com/luoke/autopiano/MainActivity.java"
KEYS = ROOT / "app/src/main/java/com/luoke/autopiano/SongAbRangeKeys.java"
POLICY = ROOT / "app/src/main/java/com/luoke/autopiano/SongRangeCheckPolicy.java"
KEYS_TEST = ROOT / "app/src/test/java/com/luoke/autopiano/SongAbRangeKeysTest.java"
POLICY_TEST = ROOT / "app/src/test/java/com/luoke/autopiano/SongRangeCheckPolicyTest.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "SONG_RANGE_CHECK_TOGGLE_V18"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)


service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")
keys = KEYS.read_text(encoding="utf-8")

# Store the toggle by a stable digest of each song path, so songs do not share a switch.
if "static String rangeCheckEnabledKey(" not in keys:
    keys = replace_once(
        keys,
        "    static String endKey(String songPath) {\n"
        "        return \"practice_end_ms_song_\" + pathDigest(songPath);\n"
        "    }\n",
        "    static String endKey(String songPath) {\n"
        "        return \"practice_end_ms_song_\" + pathDigest(songPath);\n"
        "    }\n\n"
        "    static String rangeCheckEnabledKey(String songPath) {\n"
        "        return \"song_range_check_enabled_\" + pathDigest(songPath);\n"
        "    }\n",
        "add stable per-song range-check preference key",
    )

policy_source = r'''package com.luoke.autopiano;

/** Keeps out-of-range notes from blocking playback only when the user enables checking. */
final class SongRangeCheckPolicy {
    private SongRangeCheckPolicy() { }

    static boolean shouldBlockPlayback(boolean rangeCheckEnabled, boolean hasUnsupportedPitches) {
        return rangeCheckEnabled && hasUnsupportedPitches;
    }
}
'''

keys_test = KEYS_TEST.read_text(encoding="utf-8")
new_keys_test = """    @Test public void rangeCheckPreferenceKeyIsStableAndSongSpecific() {
        String first = "/data/user/0/app/files/imported_songs/song-a.mid";
        String second = "/data/user/0/app/files/imported_songs/song-b.mid";
        assertEquals(SongAbRangeKeys.rangeCheckEnabledKey(first), SongAbRangeKeys.rangeCheckEnabledKey(first));
        assertNotEquals(SongAbRangeKeys.rangeCheckEnabledKey(first), SongAbRangeKeys.rangeCheckEnabledKey(second));
        assertNotEquals(SongAbRangeKeys.rangeCheckEnabledKey(first), SongAbRangeKeys.startKey(first));
    }

"""
if "rangeCheckPreferenceKeyIsStableAndSongSpecific" not in keys_test:
    keys_test = replace_once(
        keys_test,
        "    @Test public void startAndEndKeysDoNotOverlap() {",
        new_keys_test + "    @Test public void startAndEndKeysDoNotOverlap() {",
        "add song-specific range-check key test",
    )

policy_test_source = r'''package com.luoke.autopiano;

import org.junit.Test;
import static org.junit.Assert.*;

public class SongRangeCheckPolicyTest {
    @Test public void enabledCheckBlocksWhenUnsupportedNotesExist() {
        assertTrue(SongRangeCheckPolicy.shouldBlockPlayback(true, true));
    }

    @Test public void enabledCheckAllowsFullySupportedSong() {
        assertFalse(SongRangeCheckPolicy.shouldBlockPlayback(true, false));
    }

    @Test public void disabledCheckDoesNotBlockForUnsupportedNotes() {
        assertFalse(SongRangeCheckPolicy.shouldBlockPlayback(false, true));
    }

    @Test public void disabledCheckStillAllowsSupportedSong() {
        assertFalse(SongRangeCheckPolicy.shouldBlockPlayback(false, false));
    }
}
'''

if MARKER not in service:
    service = replace_once(
        service,
        "            TextView rangeInfo = new TextView(this);\n"
        "            rangeInfo.setText(describeSongRange(imported.file, shift));\n"
        "            rangeInfo.setTextColor(0xff617583);\n"
        "            rangeInfo.setTextSize(10);\n"
        "            rangeInfo.setPadding(dp(3), 0, dp(3), 0);\n"
        "            songCard.addView(rangeInfo, new LinearLayout.LayoutParams(-1, -2));\n\n"
        "            SeekBar shiftBar = new SeekBar(this);\n",
        "            TextView rangeInfo = new TextView(this);\n"
        "            boolean initialRangeCheckEnabled = prefs.getBoolean(\n"
        "                    SongAbRangeKeys.rangeCheckEnabledKey(songPath), true);\n"
        "            rangeInfo.setText(describeSongRange(imported.file, shift, initialRangeCheckEnabled));\n"
        "            rangeInfo.setTextColor(0xff617583);\n"
        "            rangeInfo.setTextSize(10);\n"
        "            rangeInfo.setPadding(dp(3), 0, dp(3), 0);\n"
        "            songCard.addView(rangeInfo, new LinearLayout.LayoutParams(-1, -2));\n\n"
        "            Button rangeCheckButton = dialogButton(\n"
        "                    initialRangeCheckEnabled ? \"音域检测：开启\" : \"音域检测：关闭\",\n"
        "                    initialRangeCheckEnabled ? 0xff317f63 : 0xff677783);\n"
        "            LinearLayout.LayoutParams rangeCheckParams = new LinearLayout.LayoutParams(-1, dp(29));\n"
        "            rangeCheckParams.setMargins(0, dp(3), 0, dp(3));\n"
        "            songCard.addView(rangeCheckButton, rangeCheckParams);\n"
        "            rangeCheckButton.setOnClickListener(v -> {\n"
        "                String preferenceKey = SongAbRangeKeys.rangeCheckEnabledKey(songPath);\n"
        "                boolean enabledNow = !prefs.getBoolean(preferenceKey, true);\n"
        "                prefs.edit().putBoolean(preferenceKey, enabledNow).apply();\n"
        "                rangeCheckButton.setText(enabledNow ? \"音域检测：开启\" : \"音域检测：关闭\");\n"
        "                rangeCheckButton.setBackground(rounded(enabledNow ? 0xff317f63 : 0xff677783, dp(8)));\n"
        "                int currentShift = MainActivity.songTranspose(prefs, songPath);\n"
        "                rangeInfo.setText(describeSongRange(imported.file, currentShift, enabledNow));\n"
        "                if (songPath.equals(prefs.getString(MainActivity.KEY_SONG_PATH, \"\"))) {\n"
        "                    toast(enabledNow\n"
        "                            ? \"本曲音域检测已开启；超出映射音域会阻止演奏。\"\n"
        "                            : \"本曲音域检测已关闭；音域外音符将跳过，其余音符照常演奏。\"\n"
        "                              + (playbackThread != null && playbackThread.isAlive() ? \"下次开始演奏时生效。\" : \"\"));\n"
        "                }\n"
        "            });\n\n"
        "            SeekBar shiftBar = new SeekBar(this);\n",
        "add per-song audio range toggle in song card",
    )

    service = replace_once(
        service,
        "                    rangeInfo.setText(describeSongRange(imported.file, nextShift));",
        "                    boolean checkEnabled = prefs.getBoolean(SongAbRangeKeys.rangeCheckEnabledKey(songPath), true);\n"
        "                    rangeInfo.setText(describeSongRange(imported.file, nextShift, checkEnabled));",
        "refresh row range report after transpose",
    )

    service = replace_once(
        service,
        "    private String describeSongRange(File file, int transpose) {\n"
        "        String shift = (transpose > 0 ? \"+\" : \"\") + transpose;\n"
        "        try {\n"
        "            MidiParser.MidiSong song = MidiParser.parse(file);\n"
        "            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);\n",
        "    private String describeSongRange(File file, int transpose, boolean rangeCheckEnabled) {\n"
        "        String shift = (transpose > 0 ? \"+\" : \"\") + transpose;\n"
        "        if (!rangeCheckEnabled) return \"移调 \" + shift + \" 半音 · 音域检测已关闭，超出映射音符将跳过\";\n"
        "        try {\n"
        "            MidiParser.MidiSong song = MidiParser.parse(file);\n"
        "            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);\n",
        "describe range report when check is turned off",
    )

    service = replace_once(
        service,
        "        int transpose = MainActivity.songTranspose(prefs, prefs.getString(MainActivity.KEY_SONG_PATH, \"\"));\n"
        "        java.util.Set<Integer> missingSet = new java.util.TreeSet<>();\n"
        "        for (MidiParser.NoteEvent note : song.notes) {\n"
        "            if (note.startMicros >= chosenStartMicros && note.startMicros < chosenEndMicros\n"
        "                    && !InstrumentLayout.supportsPitch(prefs, note.pitch + transpose)) {\n"
        "                missingSet.add(note.pitch + transpose);\n"
        "            }\n"
        "        }\n",
        "        int transpose = MainActivity.songTranspose(prefs, path);\n"
        "        boolean rangeCheckEnabled = prefs.getBoolean(SongAbRangeKeys.rangeCheckEnabledKey(path), true);\n"
        "        java.util.Set<Integer> missingSet = new java.util.TreeSet<>();\n"
        "        if (rangeCheckEnabled) {\n"
        "            for (MidiParser.NoteEvent note : song.notes) {\n"
        "                if (note.startMicros >= chosenStartMicros && note.startMicros < chosenEndMicros\n"
        "                        && !InstrumentLayout.supportsPitch(prefs, note.pitch + transpose)) {\n"
        "                    missingSet.add(note.pitch + transpose);\n"
        "                }\n"
        "            }\n"
        "        }\n",
        "make early out-of-range scan conditional",
    )

    service = replace_once(
        service,
        "        if (!missing.isEmpty()) {\n"
        "            StringBuilder msg = new StringBuilder(\"有 \").append(missing.size()).append(\" 种音高超出当前乐器音域：\");\n",
        "        if (SongRangeCheckPolicy.shouldBlockPlayback(rangeCheckEnabled, !missing.isEmpty())) {\n"
        "            StringBuilder msg = new StringBuilder(\"有 \").append(missing.size()).append(\" 种音高超出当前乐器音域：\");\n",
        "apply range-check policy to playback blocking",
    )

    service = replace_once(
        service,
        "        for (MidiParser.NoteEvent note : song.notes) {\n"
        "            if (note.startMicros >= chosenStartMicros && note.startMicros < chosenEndMicros\n"
        "                    && InstrumentLayout.pointForPitch(prefs, note.pitch + transpose) == null) {\n"
        "                toast(\"所选片段中有音符尚未映射到触控位置，已阻止演奏。\");\n"
        "                return;\n"
        "            }\n"
        "        }\n"
        "        stopRequested = false;\n",
        "        if (rangeCheckEnabled) {\n"
        "            for (MidiParser.NoteEvent note : song.notes) {\n"
        "                if (note.startMicros >= chosenStartMicros && note.startMicros < chosenEndMicros\n"
        "                        && InstrumentLayout.pointForPitch(prefs, note.pitch + transpose) == null) {\n"
        "                    toast(\"所选片段中有音符尚未映射到触控位置，已阻止演奏。\");\n"
        "                    return;\n"
        "                }\n"
        "            }\n"
        "        }\n"
        "        stopRequested = false;\n",
        "allow unmapped/out-of-range notes through when the toggle is off",
    )

    service = replace_once(
        service,
        "                points.addAll(unique.values());\n"
        "                boolean dispatchOk = true;\n",
        "                points.addAll(unique.values());\n"
        "                // With range checking disabled, an all-out-of-range chord has no calibrated points.\n"
        "                // Skip just that chord and preserve the timing of the remaining song.\n"
        "                if (points.isEmpty()) {\n"
        "                    sentBatches++;\n"
        "                    continue;\n"
        "                }\n"
        "                boolean dispatchOk = true;\n",
        "skip empty batches instead of attempting a gesture with zero strokes",
    )

    service = service.replace(
        "SONG_AB_RANGE_PERSISTENCE_V17",
        "SONG_AB_RANGE_PERSISTENCE_V17 " + MARKER,
        1,
    )

if "SONG_RANGE_CHECK_TOGGLE_V18" not in main:
    main = replace_once(
        main,
        "            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);\n",
        "            List<String> missing = InstrumentLayout.missingNotes(song, transpose, prefs);\n"
        "            boolean rangeCheckEnabled = prefs.getBoolean(SongAbRangeKeys.rangeCheckEnabledKey(path), true);\n",
        "show active song check state on main screen",
    )
    main = replace_once(
        main,
        "            if (missing.isEmpty()) {\n"
        "                text.append(\"音域检查：通过（全部音符都有九键映射）\");\n"
        "            }\n"
        "            else {\n",
        "            if (!rangeCheckEnabled) {\n"
        "                text.append(\"音域检测：已关闭（超出九键映射的音符会跳过，其余音符照常演奏）\");\n"
        "            } else if (missing.isEmpty()) {\n"
        "                text.append(\"音域检查：通过（全部音符都有九键映射）\");\n"
        "            }\n"
        "            else {\n",
        "reflect disabled check in main song info",
    )
    main = main.replace("public class MainActivity extends Activity {",
                        "public class MainActivity extends Activity { // " + MARKER, 1)

# Write code/test files even on a re-run to heal an incomplete archive.
SERVICE.write_text(service, encoding="utf-8")
MAIN.write_text(main, encoding="utf-8")
KEYS.write_text(keys, encoding="utf-8")
POLICY.parent.mkdir(parents=True, exist_ok=True)
POLICY.write_text(policy_source, encoding="utf-8")
KEYS_TEST.write_text(keys_test, encoding="utf-8")
POLICY_TEST.parent.mkdir(parents=True, exist_ok=True)
POLICY_TEST.write_text(policy_test_source, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
version = re.search(r"versionCode\s+(\d+)", build)
if not version:
    raise SystemExit("Cannot find versionCode")
if int(version.group(1)) < 27:
    build = build[:version.start(1)] + "27" + build[version.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.8'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

# Audit the final source, not pre-write in-memory strings.
service = SERVICE.read_text(encoding="utf-8")
main = MAIN.read_text(encoding="utf-8")
keys = KEYS.read_text(encoding="utf-8")
policy = POLICY.read_text(encoding="utf-8")
policy_test = POLICY_TEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
checks = {
    "per-song toggle is rendered in each song row": "音域检测：开启" in service and "音域检测：关闭" in service,
    "toggle defaults on and stores state by song path": "rangeCheckEnabledKey(songPath), true" in service and "putBoolean(preferenceKey, enabledNow)" in service,
    "range report describes off behavior": "音域检测已关闭，超出映射音符将跳过" in service,
    "playback out-of-range block is conditional": "SongRangeCheckPolicy.shouldBlockPlayback(rangeCheckEnabled, !missing.isEmpty())" in service,
    "unmapped-point hard block is conditional": "if (rangeCheckEnabled) {" in service and "所选片段中有音符尚未映射到触控位置，已阻止演奏。" in service,
    "empty unmapped note batches are skipped safely": "if (points.isEmpty())" in service and "Skip just that chord and preserve the timing" in service,
    "main song info reflects disabled mode": "SONG_RANGE_CHECK_TOGGLE_V18" in main and "音域检测：已关闭" in main,
    "per-song preference key helper exists": "static String rangeCheckEnabledKey(String songPath)" in keys,
    "policy tests cover on/off gating": "disabledCheckDoesNotBlockForUnsupportedNotes" in policy_test and "enabledCheckBlocksWhenUnsupportedNotesExist" in policy_test,
    "version bumped to 1.9.8": "versionCode 27" in build and "versionName '1.9.8'" in build,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Song range-check toggle V18 audit failed: " + "; ".join(failed))
print("Song range-check toggle V18 applied.")
print("AUDIT OK: " + "; ".join(checks))
