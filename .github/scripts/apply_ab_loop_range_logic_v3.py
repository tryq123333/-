from pathlib import Path

SERVICE = Path("LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java")
MARKER = "AB_LOOP_FIXES_V2"


def replace_once(source, old, new, label):
    if old not in source:
        raise SystemExit("Cannot apply " + label + ": source anchor not found.")
    return source.replace(old, new, 1)


source = SERVICE.read_text(encoding="utf-8")
if MARKER not in source:
    source = source.replace("AB_LOOP_SETTINGS_V1 */", "AB_LOOP_SETTINGS_V1 AB_LOOP_FIXES_V2 */", 1)

    toggle_start = source.find("    private void toggleAbLoopEnabled() {")
    toggle_end = source.find("    private boolean saveAbLoopSettings(", toggle_start)
    if toggle_start < 0 or toggle_end < 0:
        raise SystemExit("Cannot find A/B toggle/save method boundaries.")
    toggle_method = """    private void toggleAbLoopEnabled() {
        boolean enabled = !prefs.getBoolean(KEY_AB_LOOP_ENABLED, false);
        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, enabled).apply();
        if (currentSong == null) currentSong = readCurrentSong();
        if (currentSong != null) {
            long duration = Math.max(1L, currentSong.durationMicros);
            long activeStart = 0L;
            long activeEnd = duration;
            if (enabled) {
                long start = Math.max(0L, prefs.getLong(KEY_RANGE_START_MS, 0L)) * 1000L;
                long rawEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
                long end = (rawEndMs <= 0L || rawEndMs * 1000L > duration)
                        ? duration : rawEndMs * 1000L;
                if (end <= start) { start = 0L; end = duration; }
                activeStart = Math.min(start, duration);
                activeEnd = Math.max(activeStart + 1L, Math.min(duration, end));
                if (playbackPositionMicros < activeStart || playbackPositionMicros >= activeEnd) {
                    playbackPositionMicros = activeStart;
                    playbackBaseMicros = activeStart;
                    if (playbackThread != null && playbackThread.isAlive() && playbackActive) {
                        seekRequestMicros = activeStart;
                        seekRequestVersion++;
                        synchronized (playbackLock) { playbackLock.notifyAll(); }
                    }
                }
            }
            long previousStart = playbackRangeStartMicros;
            long previousEnd = playbackRangeEndMicros;
            playbackRangeStartMicros = activeStart;
            playbackRangeEndMicros = activeEnd;
            if ((previousStart != activeStart || previousEnd != activeEnd)
                    && playbackThread != null && playbackThread.isAlive() && playbackActive) {
                // Stop the old worker so the next start uses the new active scope.
                stopPlayback();
            }
        }
        if (noteRollView != null) {
            noteRollView.setAbLoopEnabled(enabled);
            refreshNoteRollData();
        }
        toast(enabled ? "A/B循环已开启；长按谱面上的 A/B循环 可编辑起止点。"
                : "A/B循环已关闭，播放范围已恢复整首歌。起止点设置会保留。");
    }

"""
    source = source[:toggle_start] + toggle_method + source[toggle_end:]

    old_save = """        long endMicros = endMs * 1000L;
        boolean rangeChanged = startMicros != playbackRangeStartMicros || endMicros != playbackRangeEndMicros;
        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, enabled.isChecked())
                .putLong(KEY_RANGE_START_MS, startMs).putLong(KEY_RANGE_END_MS, endMs).apply();
        playbackRangeStartMicros = startMicros;
        playbackRangeEndMicros = endMicros;
        if (rangeChanged && playbackThread != null && playbackThread.isAlive()) {
            // Playback worker captured the previous A/B boundaries. Stop it cleanly;
            // the edited range will be used the next time Start is pressed.
            stopPlayback();
        }
        if (playbackPositionMicros < startMicros || playbackPositionMicros >= endMicros) {
            playbackPositionMicros = startMicros;
            playbackBaseMicros = startMicros;
        }
"""
    new_save = """        long endMicros = endMs * 1000L;
        boolean loopEnabled = enabled.isChecked();
        long effectiveStart = loopEnabled ? startMicros : 0L;
        long effectiveEnd = loopEnabled ? endMicros : durationMs * 1000L;
        boolean rangeChanged = effectiveStart != playbackRangeStartMicros
                || effectiveEnd != playbackRangeEndMicros;
        prefs.edit().putBoolean(KEY_AB_LOOP_ENABLED, loopEnabled)
                .putLong(KEY_RANGE_START_MS, startMs).putLong(KEY_RANGE_END_MS, endMs).apply();
        playbackRangeStartMicros = effectiveStart;
        playbackRangeEndMicros = effectiveEnd;
        if (rangeChanged && playbackThread != null && playbackThread.isAlive()) {
            // The running worker captured the old scope. Stop cleanly; the next start uses the new scope.
            stopPlayback();
        }
        if (loopEnabled && (playbackPositionMicros < effectiveStart || playbackPositionMicros >= effectiveEnd)) {
            playbackPositionMicros = effectiveStart;
            playbackBaseMicros = effectiveStart;
        }
"""
    source = replace_once(source, old_save, new_save, "A/B settings save range behavior")

    # Add reset action beside Done in the existing A/B settings dialog.
    old_footer = """        Button done = dialogButton("完成", 0xff547c68);
        done.setTextColor(Color.WHITE);
        LinearLayout.LayoutParams doneParams = new LinearLayout.LayoutParams(-1, dp(42));
        doneParams.setMargins(0, dp(12), 0, 0);
        card.addView(done, doneParams);
"""
    new_footer = """        LinearLayout footerButtons = new LinearLayout(this);
        footerButtons.setOrientation(LinearLayout.HORIZONTAL);
        Button reset = dialogButton("重置 A/B", 0xfff8fbf8);
        reset.setTextColor(0xff304b3e);
        reset.setBackground(roundedBorder(0xfff8fbf8, 0xffdce5de, dp(12)));
        Button done = dialogButton("完成", 0xff547c68);
        done.setTextColor(Color.WHITE);
        LinearLayout.LayoutParams resetParams = new LinearLayout.LayoutParams(0, dp(42), 1f);
        resetParams.setMargins(0, dp(12), dp(6), 0);
        LinearLayout.LayoutParams doneParams = new LinearLayout.LayoutParams(0, dp(42), 1f);
        doneParams.setMargins(dp(6), dp(12), 0, 0);
        footerButtons.addView(reset, resetParams);
        footerButtons.addView(done, doneParams);
        card.addView(footerButtons);
        reset.setOnClickListener(v -> {
            long resetDurationMs = Math.max(1L, (currentSong.durationMicros + 999L) / 1000L);
            aField.setText("0");
            bField.setText(formatSecondsField(resetDurationMs));
            prefs.edit().putLong(KEY_RANGE_START_MS, 0L)
                    .putLong(KEY_RANGE_END_MS, resetDurationMs).apply();
            playbackRangeStartMicros = 0L;
            playbackRangeEndMicros = currentSong.durationMicros;
            if (playbackPositionMicros < 0L || playbackPositionMicros > currentSong.durationMicros) {
                playbackPositionMicros = 0L;
                playbackBaseMicros = 0L;
            }
            if (noteRollView != null) refreshNoteRollData();
            toast("A/B起止点已重置：A=0，B=整首歌时长。");
        });
"""
    source = replace_once(source, old_footer, new_footer, "A/B settings reset button")

    # Make range edits update the active scope only while looping is on.
    old_range = """        prefs.edit().putLong(KEY_RANGE_START_MS, start / 1000L)
                .putLong(KEY_RANGE_END_MS, end / 1000L).apply();
        playbackRangeStartMicros = start;
        playbackRangeEndMicros = end;
        if (playbackPositionMicros < start || playbackPositionMicros >= end) {
"""
    new_range = """        prefs.edit().putLong(KEY_RANGE_START_MS, start / 1000L)
                .putLong(KEY_RANGE_END_MS, end / 1000L).apply();
        boolean loopEnabled = prefs.getBoolean(KEY_AB_LOOP_ENABLED, false);
        playbackRangeStartMicros = loopEnabled ? start : 0L;
        playbackRangeEndMicros = loopEnabled ? end : duration;
        if (loopEnabled && (playbackPositionMicros < start || playbackPositionMicros >= end)) {
"""
    source = replace_once(source, old_range, new_range, "active range update when moving A/B handles")

    # Refresh the roll and active playback scope using saved A/B points only when the loop is enabled.
    refresh_start = source.find("    private void refreshNoteRollData() {")
    refresh_end = source.find("    private void seekPlaybackTo(", refresh_start)
    if refresh_start < 0 or refresh_end < 0:
        raise SystemExit("Cannot find note-roll data refresh method boundaries.")
    refresh_method = """    private void refreshNoteRollData() {
        if (noteRollView == null) return;
        if (currentSong == null) currentSong = readCurrentSong();
        if (currentSong == null) return;
        long duration = Math.max(1L, currentSong.durationMicros);
        long startMs = Math.max(0L, prefs.getLong(KEY_RANGE_START_MS, 0L));
        long savedEnd = prefs.getLong(KEY_RANGE_END_MS, -1L);
        long endMs = (savedEnd <= 0L || savedEnd > duration / 1000L)
                ? duration / 1000L : savedEnd;
        long pointStart = Math.min(duration, startMs * 1000L);
        long pointEnd = Math.min(duration, endMs * 1000L);
        if (pointEnd <= pointStart) { pointStart = 0L; pointEnd = duration; }
        boolean loopEnabled = prefs.getBoolean(KEY_AB_LOOP_ENABLED, false);
        long activeStart = loopEnabled ? pointStart : 0L;
        long activeEnd = loopEnabled ? pointEnd : duration;
        playbackRangeStartMicros = activeStart;
        playbackRangeEndMicros = activeEnd;
        if (playbackPositionMicros < activeStart || playbackPositionMicros > activeEnd) {
            playbackPositionMicros = activeStart;
            playbackBaseMicros = activeStart;
            if (loopEnabled && playbackThread != null && playbackThread.isAlive() && playbackActive) {
                seekRequestMicros = activeStart;
                seekRequestVersion++;
                synchronized (playbackLock) { playbackLock.notifyAll(); }
            }
        }
        if (!playbackActive) playbackBaseMicros = playbackPositionMicros;
        int speed = Math.max(50, Math.min(200, prefs.getInt(MainActivity.KEY_SPEED, 100)));
        noteRollView.setAbLoopEnabled(loopEnabled);
        noteRollView.setData(currentSong,
                prefs.getString(MainActivity.KEY_SONG_NAME, currentSong.name),
                prefs.getInt(MainActivity.KEY_TRANSPOSE, 0), playbackPositionMicros,
                duration, pointStart, pointEnd, speed, playbackActive && !paused);
    }

"""
    source = source[:refresh_start] + refresh_method + source[refresh_end:]

    # Starting a song must ignore saved A/B points whenever A/B is off.
    old_start_range = """        long rangeStartMs = Math.max(0L, Math.min(durationMs, prefs.getLong(KEY_RANGE_START_MS, 0L)));
        long storedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
        long rangeEndMs = (storedEndMs <= 0L || storedEndMs > durationMs) ? durationMs : storedEndMs;
"""
    new_start_range = """        boolean abLoopEnabled = prefs.getBoolean(KEY_AB_LOOP_ENABLED, false);
        long rangeStartMs = abLoopEnabled
                ? Math.max(0L, Math.min(durationMs, prefs.getLong(KEY_RANGE_START_MS, 0L))) : 0L;
        long storedEndMs = prefs.getLong(KEY_RANGE_END_MS, -1L);
        long rangeEndMs = !abLoopEnabled ? durationMs
                : ((storedEndMs <= 0L || storedEndMs > durationMs) ? durationMs : storedEndMs);
"""
    source = replace_once(source, old_start_range, new_start_range, "full-song start range when A/B is off")
    source = source.replace("洛克自动琴", "洛克乐器演奏")
    SERVICE.write_text(source, encoding="utf-8")

# Validate the service edits before later steps change manifest/icon/NoteRollView.
source = SERVICE.read_text(encoding="utf-8")
if MARKER not in source or "重置 A/B" not in source:
    raise SystemExit("A/B fixes or reset button marker missing.")
if "A/B循环已关闭，播放范围已恢复整首歌" not in source:
    raise SystemExit("The A/B-disabled full-song message is missing.")
if "boolean abLoopEnabled = prefs.getBoolean(KEY_AB_LOOP_ENABLED, false);" not in source:
    raise SystemExit("The start-playback full-song range guard is missing.")
print("Applied A/B on/off active-range handling, A/B reset button, and full-song startup scope.")
