from pathlib import Path

patch_path = Path("/tmp/ab-loop-fixes-v3.patch")
patch_text = patch_path.read_text(encoding="utf-8")
unfinished = "@@ -1433,6 +1507,20 @@"
if unfinished in patch_text:
    patch_text = patch_text.split(unfinished, 1)[0].rstrip() + "\n"
patch_path.write_text(patch_text, encoding="utf-8")

if not patch_text.startswith("--- a/LuokeAutoPiano/app/src/main/java/com/luoke/autopiano/MusicAccessibilityService.java"):
    raise SystemExit("A/B patch header is missing.")
if "@@ -1433,6 +1507,20 @@" in patch_path.read_text(encoding="utf-8"):
    raise SystemExit("Incomplete live-worker hunk is still present.")
if not patch_path.read_text(encoding="utf-8").endswith("\n"):
    raise SystemExit("A/B patch must end on a complete line.")
print("Trimmed the known incomplete live-worker tail; the remaining A/B range and reset hunks are complete.")
