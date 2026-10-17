from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
HELPER = ROOT / "app/src/main/java/com/luoke/autopiano/SongAbRangeKeys.java"
TEST = ROOT / "app/src/test/java/com/luoke/autopiano/SongAbRangeKeysTest.java"
MARKER = "SONG_AB_RANGE_PERSISTENCE_V17"


def replace_once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Missing source anchor: " + label)


helper_source = r'''package com.luoke.autopiano;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/** Stable, collision-resistant preference keys for each imported MIDI path. */
final class SongAbRangeKeys {
    private SongAbRangeKeys() { }

    static String startKey(String songPath) {
        return "practice_start_ms_song_" + pathDigest(songPath);
    }

    static String endKey(String songPath) {
        return "practice_end_ms_song_" + pathDigest(songPath);
    }

    private static String pathDigest(String songPath) {
        String normalized = songPath == null ? "" : songPath;
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(normalized.getBytes(StandardCharsets.UTF_8));
            char[] hex = "0123456789abcdef".toCharArray();
            char[] result = new char[digest.length * 2];
            for (int i = 0; i < digest.length; i++) {
                int value = digest[i] & 0xff;
                result[i * 2] = hex[value >>> 4];
                result[i * 2 + 1] = hex[value & 0x0f];
            }
            return new String(result);
        } catch (NoSuchAlgorithmException impossible) {
            throw new IllegalStateException("SHA-256 is required by Android.", impossible);
        }
    }
}
'''

test_source = r'''package com.luoke.autopiano;

import org.junit.Test;
import static org.junit.Assert.*;

public class SongAbRangeKeysTest {
    @Test public void keysAreStableForTheSameSongPath() {
        String path = "/data/user/0/app/files/imported_songs/song-a.mid";
        assertEquals(SongAbRangeKeys.startKey(path), SongAbRangeKeys.startKey(path));
        assertEquals(SongAbRangeKeys.endKey(path), SongAbRangeKeys.endKey(path));
    }

    @Test public void differentSongsKeepIndependentRangeKeys() {
        String first = "/data/user/0/app/files/imported_songs/song-a.mid";
        String second = "/data/user/0/app/files/imported_songs/song-b.mid";
        assertNotEquals(SongAbRangeKeys.startKey(first), SongAbRangeKeys.startKey(second));
        assertNotEquals(SongAbRangeKeys.endKey(first), SongAbRangeKeys.endKey(second));
    }

    @Test public void startAndEndKeysDoNotOverlap() {
        String path = "/data/user/0/app/files/imported_songs/song-a.mid";
        assertNotEquals(SongAbRangeKeys.startKey(path), SongAbRangeKeys.endKey(path));
    }
}
'''

service = SERVICE.read_text(encoding="utf-8")
if MARKER not in service:
    service = replace_once(
        service,
        '    private static final String KEY_RANGE_END_MS = "practice_end_ms";\n',
        '    private static final String KEY_RANGE_END_MS = "practice_end_ms";\n'
        '    private static final String KEY_RANGE_ACTIVE_SONG_PATH = "practice_range_active_song_path"; // ' + MARKER + '\n',
        "track which song owns the live A/B values",
    )

    helper_method = r'''    /**
     * The existing KEY_RANGE_START_MS/END_MS entries remain the active UI cache.
     * Before switching songs, persist that cache to its owning path; then load the
     * destination song's saved A/B values or use the full-song defaults.
     *
     * If this is an upgrade from an older build with no owner marker, the current
     * selected path is treated as the owner of the legacy range values.
     */
    private void ensureSongRangeContext(String requestedPath) {
        if (prefs == null) return;
        String targetPath = requestedPath == null ? "" : requestedPath;
        String activePath = prefs.getString(KEY_RANGE_ACTIVE_SONG_PATH, null);
        if (activePath == null) {
            activePath = prefs.getString(MainActivity.KEY_SONG_PATH, "");
            if (activePath == null) activePath = "";
            prefs.edit().putString(KEY_RANGE_ACTIVE_SONG_PATH, activePath).apply();
        }
        if (targetPath.equals(activePath)) return;

        SharedPreferences.Editor editor = prefs.edit();
        if (!activePath.isEmpty()) {
            editor.putLong(SongAbRangeKeys.startKey(activePath),
                            prefs.getLong(KEY_RANGE_START_MS, 0L))
                    .putLong(SongAbRangeKeys.endKey(activePath),
                            prefs.getLong(KEY_RANGE_END_MS, -1L));
        }

        long targetStartMs = 0L;
        long targetEndMs = -1L;
        if (!targetPath.isEmpty()) {
            String startKey = SongAbRangeKeys.startKey(targetPath);
            String endKey = SongAbRangeKeys.endKey(targetPath);
            if (prefs.contains(startKey)) targetStartMs = Math.max(0L, prefs.getLong(startKey, 0L));
            if (prefs.contains(endKey)) targetEndMs = prefs.getLong(endKey, -1L);
        }

        editor.putLong(KEY_RANGE_START_MS, targetStartMs)
                .putLong(KEY_RANGE_END_MS, targetEndMs)
                .putString(KEY_RANGE_ACTIVE_SONG_PATH, targetPath)
                .apply();
    }

'''
    service = replace_once(
        service,
        "    private MidiParser.MidiSong readCurrentSong() {\n",
        helper_method + "    private MidiParser.MidiSong readCurrentSong() {\n",
        "add per-song range cache-switching helper",
    )

    service = replace_once(
        service,
        '        String path = prefs.getString(MainActivity.KEY_SONG_PATH, "");\n'
        '        if (path == null || path.isEmpty() || !new File(path).isFile()) return null;\n'
        '        try { return MidiParser.parse(new File(path)); }\n',
        '        String path = prefs.getString(MainActivity.KEY_SONG_PATH, "");\n'
        '        if (path == null || path.isEmpty() || !new File(path).isFile()) return null;\n'
        '        ensureSongRangeContext(path);\n'
        '        try { return MidiParser.parse(new File(path)); }\n',
        "align active range with path when loading the current song",
    )

    service = replace_once(
        service,
        '        String previousPath = prefs.getString(MainActivity.KEY_SONG_PATH, "");\n'
        '        String transposeKey = MainActivity.songTransposePreferenceKey(file.getAbsolutePath());\n',
        '        ensureSongRangeContext(path);\n'
        '        String previousPath = prefs.getString(MainActivity.KEY_SONG_PATH, "");\n'
        '        String transposeKey = MainActivity.songTransposePreferenceKey(file.getAbsolutePath());\n',
        "save previous song and load chosen song range before changing selection",
    )

    service = replace_once(
        service,
        '                .putInt(transposeKey, selectedTranspose).putInt(MainActivity.KEY_TRANSPOSE, selectedTranspose)\n'
        '                .putLong(KEY_RANGE_START_MS, 0L).putLong(KEY_RANGE_END_MS, -1L).apply();\n',
        '                .putInt(transposeKey, selectedTranspose).putInt(MainActivity.KEY_TRANSPOSE, selectedTranspose).apply();\n',
        "stop resetting A/B values on every song selection",
    )

    service = replace_once(
        service,
        '        if (path == null || path.isEmpty() || !new File(path).isFile()) {\n'
        '            toast("请先在奏乐主界面导入 MIDI 曲谱。");\n'
        '            return;\n'
        '        }\n'
        '        final MidiParser.MidiSong song;\n',
        '        if (path == null || path.isEmpty() || !new File(path).isFile()) {\n'
        '            toast("请先在奏乐主界面导入 MIDI 曲谱。");\n'
        '            return;\n'
        '        }\n'
        '        ensureSongRangeContext(path);\n'
        '        final MidiParser.MidiSong song;\n',
        "align range state before starting a song from its path",
    )

    service = replace_once(
        service,
        '        boolean selected = path.equals(selectedPath);\n'
        '        songPickerRevealSelectedOnNextOpen = false;\n',
        '        boolean selected = path.equals(selectedPath);\n'
        '        if (selected) ensureSongRangeContext(path);\n'
        '        songPickerRevealSelectedOnNextOpen = false;\n',
        "ensure correct owner before deleting active song",
    )

    service = replace_once(
        service,
        '        SharedPreferences.Editor editor = prefs.edit()\n'
        '                .remove("song_label_" + imported.file.getName())\n'
        '                .remove(MainActivity.songTransposePreferenceKey(path));\n',
        '        SharedPreferences.Editor editor = prefs.edit()\n'
        '                .remove("song_label_" + imported.file.getName())\n'
        '                .remove(MainActivity.songTransposePreferenceKey(path))\n'
        '                .remove(SongAbRangeKeys.startKey(path))\n'
        '                .remove(SongAbRangeKeys.endKey(path));\n',
        "remove a deleted song's saved range",
    )

    service = replace_once(
        service,
        '                    .remove(KEY_RANGE_START_MS)\n'
        '                    .remove(KEY_RANGE_END_MS)\n'
        '                    .putBoolean("note_roll_enabled", false);\n',
        '                    .remove(KEY_RANGE_START_MS)\n'
        '                    .remove(KEY_RANGE_END_MS)\n'
        '                    .remove(KEY_RANGE_ACTIVE_SONG_PATH)\n'
        '                    .putBoolean("note_roll_enabled", false);\n',
        "clear active range owner when deleting current song",
    )

# Persist service modifications before writing helper/test files.
SERVICE.write_text(service, encoding="utf-8")

# Always write helper and tests, so the patch can repair a partially materialized archive.
HELPER.parent.mkdir(parents=True, exist_ok=True)
TEST.parent.mkdir(parents=True, exist_ok=True)
HELPER.write_text(helper_source, encoding="utf-8")
TEST.write_text(test_source, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
m = re.search(r"versionCode\s+(\d+)", build)
if not m:
    raise SystemExit("Cannot find versionCode")
if int(m.group(1)) < 26:
    build = build[:m.start(1)] + "26" + build[m.end(1):]
if not re.search(r"versionName\s+['\"][^'\"]*['\"]", build):
    raise SystemExit("Cannot find versionName")
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '1.9.7'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
helper = HELPER.read_text(encoding="utf-8")
tests = TEST.read_text(encoding="utf-8")
build = BUILD.read_text(encoding="utf-8")
selection_start = service.find("    private void selectImportedSong(String path, String displayName) {")
selection_end = service.find("    private Button dialogButton(", selection_start)
selection = service[selection_start:selection_end] if selection_start >= 0 and selection_end >= 0 else ""
checks = {
    "V17 marker and active owner path are present": MARKER in service and "KEY_RANGE_ACTIVE_SONG_PATH" in service,
    "switch saves the previously active song's A/B values": "SongAbRangeKeys.startKey(activePath)" in service and "SongAbRangeKeys.endKey(activePath)" in service,
    "switch loads each song's own A/B values": "SongAbRangeKeys.startKey(targetPath)" in service and "SongAbRangeKeys.endKey(targetPath)" in service,
    "song selection no longer resets A/B to defaults": "putLong(KEY_RANGE_START_MS, 0L).putLong(KEY_RANGE_END_MS, -1L)" not in selection,
    "new selected song is loaded through range-context helper": "ensureSongRangeContext(path);" in selection,
    "current-song reads and direct playback starts align range context": service.count("ensureSongRangeContext(path);") >= 3,
    "deleted song's range is removed": "remove(SongAbRangeKeys.startKey(path))" in service and "remove(SongAbRangeKeys.endKey(path))" in service,
    "SHA-256 key helper and unit tests exist": "MessageDigest.getInstance(\"SHA-256\")" in helper and "differentSongsKeepIndependentRangeKeys" in tests,
    "version bumped to 1.9.7": "versionCode 26" in build and "versionName '1.9.7'" in build,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise SystemExit("Per-song A/B persistence V17 audit failed: " + "; ".join(failed))
print("Per-song A/B persistence V17 applied.")
print("AUDIT OK: " + "; ".join(checks))
