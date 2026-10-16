# Maintaining and showing the speech timestamp player

Read README.md first. This repository is a viewer, not an ASR/alignment implementation.

## Rendering for a user

1. Find the requested prediction JSONL and audio. References may supply audio paths only.
2. Use `python -m speech_timestamp_viewer` (or the installed command). Never hardcode a user's
   workstation path into repository files. Use `--audio-prefix`/`--audio-root` for path remapping.
3. Choose an explicitly authorized durable visualization output directory for this conversation.
   Use `--duration 30` for requested 30-second excerpts; retain full recordings otherwise if they fit.
4. Use `inline-*.html` for Codex, not the standalone `index.html`. Emit the printed absolute-path
   visualization references in the final response. If the client lacks inline support, provide the
   standalone browser file. Follow the installed visualization skill when available.
5. Verify actual browser playback and word/VAD click details before claiming the viewer works.

## Invariants

- Display hypothesis words, never substitute ground-truth text. Preserve event/style tokens.
- Keep all simultaneous active speakers highlighted. A single cursor follows the audio clock.
- Clicking a word or diarization segment plays only its start/end interval and shows exactly two decimals.
- All tracks share one zoom/pan transform; the overview window width represents the visible duration.
- Segment switches and sample switches cancel stale playback timers. Native continuous playback remains usable.
- Keep selected details persistent during playback. Source times must be explicit for excerpts.
- Do not distort chart dimensions. Support 320px layouts and keyboard-operated segment buttons.
- Inline fragments stay below 1 MB; split at sample boundaries and reject oversized single samples.
- Escape embedded text/JSON; do not fetch local paths from the browser or add network dependencies.
- Never publish private audio, transcripts, generated viewers, checkpoints, or local paths.

## Development

Use Python 3.10+, NumPy, SciPy, Pillow and system FFmpeg. Run unit tests and the synthetic demo
browser smoke test after changes. Keep markup in HTML templates and behavior in that template's JS.
Preserve unrelated local edits. Do not change visibility or publish artifacts without authorization.
Use signed-off commits (`git commit -s`). Do not push directly to main; initialize/publish via a
feature branch and set the repository's default branch explicitly when bootstrapping.
