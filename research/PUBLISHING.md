# Add this research to GitHub

Use this `research/` folder as the repository contents, or keep it as a
subfolder in an existing repository. It includes generated audio, exact
scripts, measurements, raw telemetry, reproduction scripts and local patches.

Do not upload the parent workspace's `models/`, `setup/`, or `outputs/`:
those contain large model/runtime downloads and the original voice recording.
A parent `.gitignore` excludes them. The source reference recording is not in
this research folder; the generated audio does contain Jivraj's cloned voice.

To add your listening observations:

1. Open `index.html` in a browser (or serve this folder locally).
2. Listen to each clip, choose ratings and write comments.
3. Click **Export my reviews** and add `jivraj-listening-reviews.json` to the repo.
4. Update the pending comments in README.md with your actual observations.

Browser draft storage is local to that browser/origin. Export before switching
browsers or moving the worksheet. The recorded initial comment applies to the
previous short clone; no ratings have been assigned to the stress tests yet.

This research is published at https://github.com/Jivraj-18/voice-cloning-research.
The listening hub is hosted at https://jivraj-18.github.io/voice-cloning-research/.
