from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
ACTIVITY = ROOT / "app/src/main/java/com/luoke/autopiano/MainActivity.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "BATCH_MIDI_IMPORT_V1"

source = ACTIVITY.read_text(encoding="utf-8")

def once(text, old, new, label):
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit("Cannot patch " + label + ": source anchor missing.")

if MARKER not in source:
    source = once(
        source,
        'Button importButton = button("2. 导入已下载的 MIDI 曲谱");',
        'Button importButton = button("2. 批量导入 MIDI 曲谱（支持多选）");',
        "batch import button label"
    )

    start = source.find("    private void openMidiPicker() {")
    end = source.find("    private String getDisplayName(", start)
    if start < 0 or end < 0:
        raise SystemExit("Cannot locate MIDI picker and result handler.")
    new_methods = r'''    private void openMidiPicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        // Let Android's document picker select many downloaded MIDI files in one pass.
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        startActivityForResult(intent, REQUEST_MIDI);
    }

    private static final class ImportedMidiResult {
        final File file;
        final String displayName;
        final int noteCount;
        ImportedMidiResult(File file, String displayName, int noteCount) {
            this.file = file;
            this.displayName = displayName;
            this.noteCount = noteCount;
        }
    }

    private ImportedMidiResult copyAndValidateMidi(Uri uri, File songsDir) throws Exception {
        String displayName = getDisplayName(uri);
        if (displayName == null || displayName.trim().isEmpty()) displayName = "imported.mid";
        String safeName = displayName.replaceAll("[^a-zA-Z0-9._\\u4e00-\\u9fa5-]", "_");
        if (safeName.trim().isEmpty()) safeName = "imported.mid";
        String lowerSafeName = safeName.toLowerCase(java.util.Locale.ROOT);
        if (!lowerSafeName.endsWith(".mid") && !lowerSafeName.endsWith(".midi")) safeName += ".mid";

        File out = new File(songsDir, System.currentTimeMillis() + "_" + safeName);
        while (out.exists()) out = new File(songsDir, System.currentTimeMillis() + "_" + safeName);
        try {
            try (InputStream in = getContentResolver().openInputStream(uri);
                 FileOutputStream stream = new FileOutputStream(out, false)) {
                if (in == null) throw new IllegalStateException("无法打开文件：" + displayName);
                byte[] buffer = new byte[32 * 1024];
                int count;
                long total = 0;
                while ((count = in.read(buffer)) != -1) {
                    total += count;
                    if (total > 32L * 1024L * 1024L) {
                        throw new IllegalArgumentException("文件超过 32 MB：" + displayName);
                    }
                    stream.write(buffer, 0, count);
                }
            }
            MidiParser.MidiSong song = MidiParser.parse(out);
            if (song == null) throw new IllegalArgumentException("无法识别 MIDI：" + displayName);
            prefs.edit()
                    .putString("song_label_" + out.getName(), displayName)
                    .putInt(songTransposePreferenceKey(out.getAbsolutePath()), 0)
                    .apply();
            return new ImportedMidiResult(out, displayName, song.notes == null ? 0 : song.notes.size());
        } catch (Exception ex) {
            if (out.exists()) out.delete();
            throw ex;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_MIDI || resultCode != RESULT_OK || data == null) return;

        java.util.ArrayList<Uri> selectedUris = new java.util.ArrayList<>();
        android.content.ClipData clipData = data.getClipData();
        if (clipData != null && clipData.getItemCount() > 0) {
            for (int i = 0; i < clipData.getItemCount(); i++) {
                Uri uri = clipData.getItemAt(i).getUri();
                if (uri != null && !selectedUris.contains(uri)) selectedUris.add(uri);
            }
        } else if (data.getData() != null) {
            selectedUris.add(data.getData());
        }
        if (selectedUris.isEmpty()) return;

        File songsDir = new File(getFilesDir(), "imported_songs");
        if (!songsDir.exists() && !songsDir.mkdirs()) {
            Toast.makeText(this, "无法创建曲库目录", Toast.LENGTH_LONG).show();
            return;
        }

        String existingPath = prefs.getString(KEY_SONG_PATH, "");
        boolean activeSongExists = existingPath != null && !existingPath.isEmpty()
                && new File(existingPath).isFile();
        boolean keepCurrentSelection = selectedUris.size() > 1 && activeSongExists;
        int succeeded = 0;
        int failed = 0;
        String firstError = null;
        ImportedMidiResult firstImported = null;
        ImportedMidiResult singleImported = null;

        for (Uri uri : selectedUris) {
            try {
                ImportedMidiResult imported = copyAndValidateMidi(uri, songsDir);
                succeeded++;
                if (firstImported == null) firstImported = imported;
                singleImported = imported;
            } catch (Exception ex) {
                failed++;
                if (firstError == null) firstError = ex.getMessage();
            }
        }

        if (succeeded > 0) {
            // A single import retains the previous behavior of selecting that song.
            // Batch import keeps the currently selected song; if there isn't one yet,
            // the first successful file becomes the initial selection.
            ImportedMidiResult activate = null;
            if (selectedUris.size() == 1) {
                activate = singleImported;
            } else if (!activeSongExists) {
                activate = firstImported;
            }
            if (activate != null) {
                prefs.edit()
                        .putString(KEY_SONG_PATH, activate.file.getAbsolutePath())
                        .putString(KEY_SONG_NAME, activate.displayName)
                        .putInt(songTransposePreferenceKey(activate.file.getAbsolutePath()), 0)
                        .putInt(KEY_TRANSPOSE, 0)
                        .apply();
            }
            refreshSongInfo();
        }

        if (selectedUris.size() == 1 && succeeded == 1) {
            Toast.makeText(this,
                    "曲谱读取成功：" + (singleImported == null ? 0 : singleImported.noteCount) + " 个音符",
                    Toast.LENGTH_SHORT).show();
        } else if (succeeded > 0) {
            String summary = "批量导入完成：成功 " + succeeded + " 首";
            if (failed > 0) summary += "，失败 " + failed + " 首";
            summary += "。可在曲目列表中搜索歌曲。";
            Toast.makeText(this, summary, Toast.LENGTH_LONG).show();
        } else if (firstError != null) {
            Toast.makeText(this, "导入失败：" + firstError, Toast.LENGTH_LONG).show();
        } else {
            Toast.makeText(this, "没有成功导入曲目。", Toast.LENGTH_LONG).show();
        }
        if (succeeded == 0 || failed > 0) refreshSongInfo();
    }

'''
    source = source[:start] + new_methods + source[end:]
    # A persistent marker makes this a repeat-safe workflow patch.
    source = source.replace(
        "    private void openMidiPicker() {",
        "    private void openMidiPicker() { // " + MARKER,
        1
    )
    ACTIVITY.write_text(source, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 5", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.5.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

source = ACTIVITY.read_text(encoding="utf-8")
start = source.find("    private void openMidiPicker()")
end = source.find("    private String getDisplayName(", start)
methods = source[start:end]
if "Intent.EXTRA_ALLOW_MULTIPLE, true" not in methods:
    raise SystemExit("The document picker does not allow multi-select.")
if "data.getClipData()" not in methods or "getItemAt(i).getUri()" not in methods:
    raise SystemExit("ClipData multi-selection handling is missing.")
if "copyAndValidateMidi(Uri uri, File songsDir)" not in methods:
    raise SystemExit("Per-file copy/validation helper is missing.")
if "批量导入完成：成功 " not in methods:
    raise SystemExit("Batch import summary is missing.")
if "BATCH_MIDI_IMPORT_V1" not in source:
    raise SystemExit("Batch import marker is missing.")
if "versionCode 5" not in BUILD.read_text(encoding="utf-8") or "versionName '0.5.0'" not in BUILD.read_text(encoding="utf-8"):
    raise SystemExit("Application version was not bumped.")
print("Added multi-select MIDI import with per-file validation, partial-failure summary, and preserved existing selection on bulk imports.")
