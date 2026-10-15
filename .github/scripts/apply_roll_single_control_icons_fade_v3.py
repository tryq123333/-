from pathlib import Path
import base64

ROOT = Path("LuokeAutoPiano")
NOTE = ROOT / "app/src/main/java/com/luoke/autopiano/NoteRollView.java"
SERVICE = ROOT / "app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"
ASSET = ROOT / "app/src/main/res/drawable-nodpi/note_key_atlas.webp"
MARKER = "ROLL_SINGLE_PERFORMANCE_REAL_ICONS_FADE_V3"

ATLAS_B64 = """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"""
ASSET.parent.mkdir(parents=True, exist_ok=True)
ASSET.write_bytes(base64.b64decode(ATLAS_B64))

def once(source, old, new, label):
    if old in source:
        return source.replace(old, new, 1)
    if new in source:
        return source
    raise SystemExit("Cannot apply " + label + ": source anchor missing.")

note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")

# Use actual key images cropped from the user's game screenshot (A2, E3, F3, G3, A3, B3, C4, D4, E4).
for line in [
    "import android.graphics.Bitmap;",
    "import android.graphics.BitmapFactory;",
    "import android.graphics.Rect;",
]:
    if line not in note:
        note = note.replace("import android.graphics.Canvas;", "import android.graphics.Canvas;\n" + line, 1)
note = once(note,
    "    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);\n    private final int touchSlop;",
    "    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);\n    private final Bitmap gameKeyAtlas;\n    private final int touchSlop;",
    "original key atlas field")
if "gameKeyAtlas = BitmapFactory.decodeResource(getResources(), R.drawable.note_key_atlas);" not in note:
    note = once(note,
        "        touchSlop = ViewConfiguration.get(context).getScaledTouchSlop();",
        "        touchSlop = ViewConfiguration.get(context).getScaledTouchSlop();\n        gameKeyAtlas = BitmapFactory.decodeResource(getResources(), R.drawable.note_key_atlas);",
        "load original key icons")
old_icon_call = """                        drawGameKeyIcon(canvas, badge.centerX(), badge.centerY(),
                                Math.min(badge.width(), badge.height()) * .5f, keyIconIndex, noteAlpha);"""
new_icon_call = """                        drawOriginalGameKeyIcon(canvas, badge.centerX(), badge.centerY(),
                                Math.min(badge.width(), badge.height()), keyIconIndex, noteAlpha);"""
if old_icon_call in note:
    note = note.replace(old_icon_call, new_icon_call, 1)
elif "drawOriginalGameKeyIcon(canvas" not in note:
    raise SystemExit("Neither old hand-drawn nor current original-key icon call exists.")

draw_original = """    private void drawOriginalGameKeyIcon(Canvas canvas, float cx, float cy,
                                         float size, int index, int alpha) {
        if (gameKeyAtlas == null || index < 0 || index >= 9 || size <= 0f) return;
        // The atlas is ordered exactly like InstrumentLayout.PITCHES: A2, E3, F3,
        // G3, A3, B3, C4, D4, E4. Each cell is a downscaled crop of the game key.
        Rect src = new Rect((index % 3) * 64, (index / 3) * 64,
                (index % 3 + 1) * 64, (index / 3 + 1) * 64);
        RectF dst = new RectF(cx - size / 2f, cy - size / 2f,
                cx + size / 2f, cy + size / 2f);
        paint.setStyle(Paint.Style.FILL);
        paint.setAlpha(alpha);
        paint.setFilterBitmap(true);
        paint.setDither(true);
        canvas.drawBitmap(gameKeyAtlas, src, dst, paint);
        paint.setAlpha(255);
        paint.setDither(false);
    }

"""
if "private void drawOriginalGameKeyIcon(" not in note:
    note = once(note, "    private void drawGameKeyIcon(Canvas canvas, float cx, float cy, float radius,",
                     draw_original + "    private void drawGameKeyIcon(Canvas canvas, float cx, float cy, float radius,",
                     "original game icon renderer")

note = once(note, "        paint.setColor(0x66ffffff);\n        paint.setStrokeWidth(1.15f * density);",
                 "        paint.setColor(0x26ffffff);\n        paint.setStrokeWidth(0.85f * density);",
                 "fade playhead line")
note = once(note, "        paint.setColor(0xfff2f5f4);",
                 "        paint.setColor(0x99f2f5f4);",
                 "fade song title")
note = once(note, "        paint.setColor(0xccebf0f0);",
                 "        paint.setColor(0x88ebf0f0);",
                 "fade song time")
if MARKER not in note:
    note = note.replace("NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2",
                        "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 " + MARKER, 1)
NOTE.write_text(note, encoding="utf-8")

# A single "演奏" action in the floating panel as well as in the note roll: tap to start,
# pause or continue. Keep the green highlight only while music is actually playing.
old_buttons = """        Button play = smallButton("开始");
        startPlaybackButton = play;
        pauseButton = new TextView(this);
        pauseButton.setText(paused ? "继续" : "暂停");
        pauseButton.setTextColor(Color.WHITE);
        pauseButton.setTextSize(12);
        pauseButton.setGravity(Gravity.CENTER);
        pauseButton.setPadding(dp(8), dp(7), dp(8), dp(7));
        pauseButton.setBackground(rounded(0xff4b6279, dp(8)));
        Button stop = smallButton("⏮︎");
        Button songs = smallButton("曲目");
        Button segment = smallButton("A/B循环");
        Button roll = smallButton("谱面");
        Button calibrate = smallButton("校准");"""
new_buttons = """        Button play = smallButton("演奏");
        startPlaybackButton = calibrated ? play : null;
        pauseButton = null;
        Button stop = smallButton("⏮︎");
        Button songs = smallButton("曲目");
        Button segment = smallButton("A/B循环");
        Button roll = smallButton("谱面");
        Button calibrate = smallButton("校准");"""
if old_buttons in service:
    service = service.replace(old_buttons, new_buttons, 1)
elif 'Button play = smallButton("演奏");' not in service:
    raise SystemExit("Neither old split play/pause nor unified 演奏 button exists.")
service = once(service,
    """        if (calibrated) {
            panel.addView(play, flowButtonParams());
            panel.addView(pauseButton, flowButtonParams());
            panel.addView(stop, flowButtonParams());
            panel.addView(songs, flowButtonParams());
            panel.addView(segment, flowButtonParams());
            panel.addView(roll, flowButtonParams());
        } else {
            pauseButton = null;
        }""",
    """        if (calibrated) {
            panel.addView(play, flowButtonParams());
            panel.addView(stop, flowButtonParams());
            panel.addView(songs, flowButtonParams());
            panel.addView(segment, flowButtonParams());
            panel.addView(roll, flowButtonParams());
        }""",
    "remove separate start and pause views")
service = once(service,
    """        if (calibrated) {
            play.setOnClickListener(v -> startPlayback());
            pauseButton.setOnClickListener(v -> togglePause());
            stop.setContentDescription("回到起始点");""",
    """        if (calibrated) {
            play.setOnClickListener(v -> toggleUnifiedPlayback());
            stop.setContentDescription("回到起始点");""",
    "single floating performance click handler")

helper = """    private void toggleUnifiedPlayback() {
        if (playbackThread != null && playbackThread.isAlive() && playbackActive && !stopRequested) {
            togglePause();
        } else {
            startPlayback();
        }
        refreshUnifiedPlaybackButton();
    }

    private void refreshUnifiedPlaybackButton() {
        if (!(startPlaybackButton instanceof TextView)) return;
        TextView button = (TextView) startPlaybackButton;
        boolean active = playbackThread != null && playbackThread.isAlive()
                && playbackActive && !paused && !stopRequested;
        button.setText("演奏");
        button.setTextColor(Color.WHITE);
        button.setBackground(rounded(active ? 0xff4c8d80 : 0xff4b6279, dp(8)));
        button.setContentDescription(active ? "正在演奏，点击暂停" : "演奏，点击开始或继续");
    }

"""
if "private void toggleUnifiedPlayback()" not in service:
    service = once(service, "    private void updateControlPanelPlaybackButtons() {",
                    helper + "    private void updateControlPanelPlaybackButtons() {",
                    "unified performance state helper")
service = once(service,
    """        if (pauseButton != null) pauseButton.setVisibility(visibility);
    }""",
    """        if (pauseButton != null) pauseButton.setVisibility(visibility);
        refreshUnifiedPlaybackButton();
    }""",
    "refresh unified button visibility/state")
service = once(service,
    """        if (miniPlaybackButton != null) {
            boolean alive = playbackThread != null && playbackThread.isAlive();
            miniPlaybackButton.setText(alive && playbackActive && !paused ? "Ⅱ" : "▶");
            miniPlaybackButton.setContentDescription(alive && playbackActive && !paused ? "暂停自动演奏" : "开始或继续演奏");
        }
    }""",
    """        if (miniPlaybackButton != null) {
            boolean alive = playbackThread != null && playbackThread.isAlive();
            miniPlaybackButton.setText(alive && playbackActive && !paused ? "Ⅱ" : "▶");
            miniPlaybackButton.setContentDescription(alive && playbackActive && !paused ? "暂停自动演奏" : "开始或继续演奏");
        }
        refreshUnifiedPlaybackButton();
    }""",
    "refresh unified button highlight during playback")

if MARKER not in service:
    service = service.replace("NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2",
                              "NOTE_ROLL_PLAY_REWIND_SEEK_GUARD_V1 SONG_SPECIFIC_ROLL_UI_V2 " + MARKER, 1)
SERVICE.write_text(service, encoding="utf-8")

# Postconditions: ensure the old separated UI cannot creep back into either floating surface.
note = NOTE.read_text(encoding="utf-8")
service = SERVICE.read_text(encoding="utf-8")
if not ASSET.is_file() or len(ASSET.read_bytes()) < 1000:
    raise SystemExit("Original game key atlas was not written.")
if "drawOriginalGameKeyIcon(canvas" not in note or "R.drawable.note_key_atlas" not in note:
    raise SystemExit("Original game key pictograms are not wired into the note roll.")
if "paint.setColor(0x26ffffff)" not in note or "paint.setColor(0x99f2f5f4)" not in note:
    raise SystemExit("Playhead/title fade postconditions failed.")
if 'Button play = smallButton("演奏");' not in service or "panel.addView(pauseButton" in service:
    raise SystemExit("Floating panel still contains separated start and pause controls.")
if "private void toggleUnifiedPlayback()" not in service or "private void refreshUnifiedPlaybackButton()" not in service:
    raise SystemExit("Unified floating performance state handler is missing.")
print("Applied a single 演奏 control, authentic cropped in-game key icons, and lower-contrast playhead/title.")
