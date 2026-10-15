from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "SONG_LIST_SCROLL_RESTORE_V2"

service = SERVICE.read_text(encoding="utf-8")

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": source anchor missing.")

# Keep the scrolling-note window independently controlled. Remove any coupled-collapse
# code that may have been included by an earlier interrupted build of this patch.
service = re.sub(r"(?m)^\s*private boolean noteRollTemporarilyHiddenByCollapse;\s*\n", "", service)
service = re.sub(r"(?ms)^\s*private void restoreNoteRollAfterPanelExpand\(\) \{.*?^\s*\}\s*\n", "", service)
service = re.sub(r"(?m)^\s*if \(controlOverlay != null\) restoreNoteRollAfterPanelExpand\(\);\s*\n", "", service)
service = re.sub(r"(?ms)^\s*if \(noteRollView != null && noteRollParams != null\s*&& !noteRollTemporarilyHiddenByCollapse\) \{\s*removeOverlay\(noteRollView\);\s*noteRollTemporarilyHiddenByCollapse = true;\s*\}\s*\n", "", service)
service = service.replace("            noteRollTemporarilyHiddenByCollapse = false;\n", "")
service = service.replace("                    noteRollTemporarilyHiddenByCollapse = false;\n", "")

if "private int songPickerScrollY;" not in service:
    service = once(service,
        "    private void showSongPickerDialog() {",
        "    private int songPickerScrollY;\n    private boolean songPickerRevealSelectedOnNextOpen;\n\n    private void showSongPickerDialog() {",
        "remember song list scroll state")

# Song picker: remember scroll position, identify each card by its absolute path separately from
# its name tag (the name tag remains dedicated to live search).
picker_start = service.find("    private void showSongPickerDialog()")
picker_end = service.find("    private void confirmRemoveImportedSong(", picker_start)
if picker_start < 0 or picker_end < 0:
    raise SystemExit("Cannot locate song picker method and removal handlers.")
picker = service[picker_start:picker_end]

if "SONG_LIST_SCROLL_RESTORE_V2" not in picker:
    picker = once(picker,
        """        ScrollView scroll = new ScrollView(this);
        LinearLayout rows = new LinearLayout(this);""",
        """        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        scroll.setOnScrollChangeListener((View v, int scrollX, int scrollY, int oldScrollX, int oldScrollY) -> {
            songPickerScrollY = scrollY;
        });
        LinearLayout rows = new LinearLayout(this);""",
        "track song list scroll position")

    picker = once(picker,
        """            songCard.setTag(imported.name);
            rows.addView(songCard, ip);
            item.setOnClickListener(v -> selectImportedSong(songPath, imported.name));""",
        """            songCard.setTag(imported.name);
            songCard.setContentDescription(songPath);
            rows.addView(songCard, ip);
            item.setOnClickListener(v -> {
                songPickerRevealSelectedOnNextOpen = true;
                selectImportedSong(songPath, imported.name);
            });""",
        "remember selected song card path and reveal it on next open")

    picker = once(picker,
        """        scroll.addView(rows);
        card.addView(scroll, new LinearLayout.LayoutParams(-1, Math.min(dp(330), Math.max(dp(100), getResources().getDisplayMetrics().heightPixels * 2 / 5))));""",
        """        scroll.addView(rows);
        scroll.post(() -> {
            int maxScrollY = Math.max(0, rows.getHeight() - scroll.getHeight());
            scroll.scrollTo(0, Math.max(0, Math.min(songPickerScrollY, maxScrollY)));
            if (songPickerRevealSelectedOnNextOpen) {
                String selectedPath = prefs.getString(MainActivity.KEY_SONG_PATH, "");
                for (int i = 0; i < rows.getChildCount(); i++) {
                    View child = rows.getChildAt(i);
                    if (selectedPath.equals(child.getContentDescription())) {
                        int visibleTop = scroll.getScrollY();
                        int visibleBottom = visibleTop + scroll.getHeight();
                        if (child.getTop() < visibleTop) {
                            scroll.scrollTo(0, child.getTop());
                        } else if (child.getBottom() > visibleBottom) {
                            scroll.scrollTo(0, Math.max(0, child.getBottom() - scroll.getHeight()));
                        }
                        break;
                    }
                }
                songPickerRevealSelectedOnNextOpen = false;
            }
            songPickerScrollY = scroll.getScrollY();
        });
        card.addView(scroll, new LinearLayout.LayoutParams(-1, Math.min(dp(330), Math.max(dp(100), getResources().getDisplayMetrics().heightPixels * 2 / 5))));""",
        "restore scroll and reveal selected song after layout")

    picker = picker.replace(
        "    private void showSongPickerDialog() {",
        "    private void showSongPickerDialog() { // " + MARKER,
        1)
    service = service[:picker_start] + picker + service[picker_end:]

# Removing a track must preserve the list's current scroll, not auto-jump to the selected track.
remove_start = service.find("    private void removeImportedSongNow(ImportedSong imported) {")
remove_end = service.find("    private String describeSongRange(", remove_start)
if remove_start < 0 or remove_end < 0:
    raise SystemExit("Cannot locate track-removal method.")
remove_method = service[remove_start:remove_end]
if "songPickerRevealSelectedOnNextOpen = false;" not in remove_method:
    remove_method = once(remove_method,
        """        boolean selected = path.equals(selectedPath);

        if (selected && playbackThread != null""",
        """        boolean selected = path.equals(selectedPath);
        songPickerRevealSelectedOnNextOpen = false;

        if (selected && playbackThread != null""",
        "preserve deletion scroll instead of selected-song auto reveal")
    service = service[:remove_start] + remove_method + service[remove_end:]

# Make sure the correct anchor gets a durable source marker and bump the build identity.
build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 7", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.7.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")
SERVICE.write_text(service, encoding="utf-8")

# Postconditions: no false "sync" if either behavior did not reach the build source.
service = SERVICE.read_text(encoding="utf-8")
picker_start = service.find("    private void showSongPickerDialog()")
picker_end = service.find("    private void confirmRemoveImportedSong(", picker_start)
picker = service[picker_start:picker_end]
if "noteRollTemporarilyHiddenByCollapse" in service or "restoreNoteRollAfterPanelExpand()" in service:
    raise SystemExit("Scrolling-note window must remain independently controllable.")
if "songPickerScrollY = scrollY;" not in picker or "scroll.scrollTo(0, Math.max(0, Math.min(songPickerScrollY, maxScrollY)));" not in picker:
    raise SystemExit("Song-list scroll restoration is missing.")
if "songCard.setContentDescription(songPath);" not in picker or "songPickerRevealSelectedOnNextOpen = true;" not in picker:
    raise SystemExit("Selected-song reveal is missing.")
if "songPickerRevealSelectedOnNextOpen = false;" not in service[service.find("private void removeImportedSongNow"):service.find("private String describeSongRange")]:
    raise SystemExit("Removal doesn't preserve the current scroll position.")
if "versionCode 7" not in BUILD.read_text(encoding="utf-8") or "versionName '0.7.0'" not in BUILD.read_text(encoding="utf-8"):
    raise SystemExit("Application version bump missing.")
print("Applied independent note-roll controls, selected-song scroll restoration and stable scroll after removals; version 0.7.0.")
