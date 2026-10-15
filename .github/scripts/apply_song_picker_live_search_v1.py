from pathlib import Path
import re

ROOT = Path("LuokeAutoPiano")
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
BUILD = ROOT / "app/build.gradle"
MARKER = "SONG_PICKER_LIVE_SEARCH_V1"

service = SERVICE.read_text(encoding="utf-8")
picker_start = service.find("    private void showSongPickerDialog() {")
picker_end = service.find("    private String describeSongRange(", picker_start)
if picker_start < 0 or picker_end < 0:
    raise SystemExit("Cannot locate song picker method.")
picker = service[picker_start:picker_end]

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot patch " + label + ": anchor missing.")

if MARKER not in picker:
    picker = once(picker,
        """        card.addView(hint);
        ScrollView scroll = new ScrollView(this);""",
        """        card.addView(hint);

        EditText searchField = new EditText(this);
        searchField.setSingleLine(true);
        searchField.setTextSize(13);
        searchField.setTextColor(0xff192a35);
        searchField.setHintTextColor(0xff82919a);
        searchField.setHint("搜索已导入的歌曲名");
        searchField.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_AUTO_CORRECT);
        searchField.setFocusable(true);
        searchField.setFocusableInTouchMode(true);
        searchField.setPadding(dp(11), 0, dp(11), 0);
        searchField.setBackground(rounded(0xffe7edf3, dp(10)));
        LinearLayout.LayoutParams searchParams = new LinearLayout.LayoutParams(-1, dp(42));
        searchParams.setMargins(0, 0, 0, dp(8));
        card.addView(searchField, searchParams);

        ScrollView scroll = new ScrollView(this);""",
        "insert song-name search input")

    picker = once(picker,
        """            ip.setMargins(0, 0, 0, dp(6));
            rows.addView(songCard, ip);
            item.setOnClickListener(v -> selectImportedSong(songPath, imported.name));""",
        """            ip.setMargins(0, 0, 0, dp(6));
            songCard.setTag(imported.name);
            rows.addView(songCard, ip);
            item.setOnClickListener(v -> selectImportedSong(songPath, imported.name));""",
        "tag cards with track names for filtering")

    picker = once(picker,
        """        scroll.addView(rows);
        card.addView(scroll, new LinearLayout.LayoutParams(-1, Math.min(dp(330), Math.max(dp(100), getResources().getDisplayMetrics().heightPixels * 2 / 5))));""",
        """        TextView noResults = new TextView(this);
        noResults.setText("没有找到匹配的曲目");
        noResults.setTextColor(0xff71808a);
        noResults.setTextSize(12);
        noResults.setGravity(Gravity.CENTER);
        noResults.setPadding(dp(8), dp(14), dp(8), dp(14));
        noResults.setVisibility(View.GONE);
        rows.addView(noResults, new LinearLayout.LayoutParams(-1, -2));

        searchField.addTextChangedListener(new android.text.TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                String query = s == null ? "" : s.toString().trim().toLowerCase(java.util.Locale.ROOT);
                int matches = 0;
                for (int i = 0; i < rows.getChildCount(); i++) {
                    View child = rows.getChildAt(i);
                    if (child == noResults) continue;
                    Object tag = child.getTag();
                    if (!(tag instanceof String)) continue;
                    boolean visible = query.isEmpty()
                            || ((String) tag).toLowerCase(java.util.Locale.ROOT).contains(query);
                    child.setVisibility(visible ? View.VISIBLE : View.GONE);
                    if (visible) matches++;
                }
                noResults.setVisibility(matches == 0 ? View.VISIBLE : View.GONE);
            }
            @Override public void afterTextChanged(android.text.Editable s) { }
        });

        scroll.addView(rows);
        card.addView(scroll, new LinearLayout.LayoutParams(-1, Math.min(dp(330), Math.max(dp(100), getResources().getDisplayMetrics().heightPixels * 2 / 5))));""",
        "filter song cards and show empty state")

    picker = once(picker,
        """                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT);
        overlayParams.gravity = Gravity.TOP | Gravity.LEFT;
        segmentOverlay = root;""",
        """                WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN
                        | WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                PixelFormat.TRANSLUCENT);
        overlayParams.gravity = Gravity.TOP | Gravity.LEFT;
        overlayParams.softInputMode = WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE
                | WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN;
        segmentOverlay = root;""",
        "allow keyboard focus in song picker")

    if MARKER not in picker:
        picker = picker.replace(
            "    private void showSongPickerDialog() {",
            "    private void showSongPickerDialog() { // " + MARKER,
            1)
    service = service[:picker_start] + picker + service[picker_end:]
    SERVICE.write_text(service, encoding="utf-8")

build = BUILD.read_text(encoding="utf-8")
build = re.sub(r"versionCode\s+\d+", "versionCode 4", build, count=1)
build = re.sub(r"versionName\s+['\"][^'\"]*['\"]", "versionName '0.4.0'", build, count=1)
BUILD.write_text(build, encoding="utf-8")

service = SERVICE.read_text(encoding="utf-8")
picker_start = service.find("    private void showSongPickerDialog() {")
picker_end = service.find("    private String describeSongRange(", picker_start)
picker = service[picker_start:picker_end]
if "搜索已导入的歌曲名" not in picker or "android.text.TextWatcher" not in picker:
    raise SystemExit("Live song search was not installed.")
if "child.setVisibility(visible ? View.VISIBLE : View.GONE);" not in picker:
    raise SystemExit("Song card filter is missing.")
if "没有找到匹配的曲目" not in picker:
    raise SystemExit("Empty search state is missing.")
if "FLAG_NOT_FOCUSABLE" in picker:
    raise SystemExit("Song picker is still marked not-focusable; keyboard input may fail.")
if "versionCode 4" not in BUILD.read_text(encoding="utf-8") or "versionName '0.4.0'" not in BUILD.read_text(encoding="utf-8"):
    raise SystemExit("App version bump missing.")
print("Added live song-name filtering, no-results text and keyboard focus; bumped app version to 0.4.0.")
