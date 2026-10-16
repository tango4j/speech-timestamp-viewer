# Speech Timestamp Viewer

A portable Python + HTML viewer for inspecting model-generated word timestamps alongside
audio, a waveform, a spectrogram, and per-speaker diarization segments. No NeMo, GPU,
model checkpoint, web server, or JavaScript build tool is required.

## Preview

![LSM 2mix viewer at 2x zoom showing audio controls, a draggable overview window, waveform, spectrogram, speaker words, diarization and selected start/end times](docs/images/lsm-2mix-viewer.png)

LSM 2mix example: clicking a word or diarization segment plays that interval and displays
its start/end times to two decimal places. This is a static screenshot; build the player
below for synchronized playback and interactive inspection.

## What it shows

- Audio controls with a synchronized timeline cursor and simultaneous speaker-word highlighting.
- Waveform, spectrogram (0–8 kHz, −70…0 dB relative), per-speaker words and VAD lanes.
- Speaker-colored words; click a word, word interval, or diarization interval to play from its start to its end, then stop automatically.
- A persistent **Start XX.YY s / End XX.YY s** readout. Playback does not overwrite the selection.
- Horizontal zoom keeps waveform, spectrogram, words, diarization and cursor on one shared time scale.
- A full-recording overview with a draggable visible-window indicator that shrinks as you zoom in.
- Full recordings or excerpts; excerpt selections also display source-recording times.
- An expandable original model hypothesis. Reference text is **never** substituted for predictions.
- Self-contained browser output and size-bounded fragments for Codex inline visualization.

The viewer displays supplied timestamps unchanged, except for clipping to a requested excerpt.
It does **not** run ASR, forced alignment, interpolation, language normalization, or accuracy evaluation.
Two-decimal display formatting does not imply 10 ms acoustic accuracy. `<ev:...>` and `<sty:...>`
tokens are preserved as text. Diarization segments are supplied by you; the viewer does not threshold logits.

## Playback and navigation

- Click a word in the transcript or a word/VAD bar to play only that segment. Clicking another segment cancels the previous stop point.
- Native audio controls play continuously after a segment finishes. Seeking in the main plot cancels the segment limit; pausing/resuming within a selected segment retains its endpoint.
- **Zoom in + / Zoom out −** change the visible time span by a factor of two. The current playhead anchors zoom when visible; otherwise the viewport center is used. The minimum view span is 250 ms (or the full duration for shorter recordings).
- Drag the overview's highlighted window to pan, or click elsewhere in the overview to center it there. This moves the view without changing playback position.
- Focus the overview window and use **Left/Right** to pan, **Page Up/Down** for a full-window jump, or **Home/End** to reach either edge.
- All four tracks use the same clipped time transform; off-screen bars cannot intercept clicks. Zoom magnifies the stored waveform/spectrogram preview; it does not recompute higher-resolution acoustic features.
- Playback endpoints use browser media timing, not sample-accurate audio editing. The displayed start/end values remain the supplied timestamps.

## Install

Python 3.10+ and FFmpeg are required. FFmpeg must include the `libmp3lame` encoder.

```bash
git clone https://github.com/tango4j/speech-timestamp-viewer.git
cd speech-timestamp-viewer
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
# Ubuntu: sudo apt-get install ffmpeg
# macOS: brew install ffmpeg
# Conda alternative: conda install -c conda-forge ffmpeg
```

The Python dependencies are also listed in `requirements.txt`.

## Try without private data

```bash
python examples/make_demo.py --output demo-data
speech-timestamp-viewer \
  --predictions demo-data/predictions.jsonl \
  --title 'Synthetic two-speaker demo' \
  --output output/demo
```

Open `output/demo/index.html` in a browser. This example is **synthetic tones with illustrative
labels**, not recognized speech. No proprietary datasets, checkpoints, or recordings are included.

## Your timestamp data

### Generic JSONL (one recording per line)

```json
{"sample_id":"clip-1","audio_filepath":"audio/clip-1.wav","hypothesis":"hello there","words":[{"word":"hello","speaker":"alice","start":0.4,"end":0.8},{"word":"there","speaker":"alice","start":0.8,"end":1.2}],"diarization_timestamps":[{"speaker":"alice","start":0.35,"end":1.25}]}
```

Times are seconds relative to the original audio. Speaker IDs may be strings or numbers.
Absent an explicit mapping, generic word and diarization speaker IDs are assumed to agree.

### NeMo / SALM predictions

Supported fields:

```json
{"sample_id":"clip-1","generation":"<spk:0> hello","timestamps":{"speaker_word_timestamps":{"0":[{"word":"hello","speaker":0,"start":0.4,"end":0.8}]},"diarization_timestamps":[{"speaker":2,"start":0.35,"end":0.85}],"speaker_tag_to_sortformer_column":{"0":2}}}
```

Provide `audio_filepath` in each prediction or use `--references reference.jsonl` to join audio
paths by `sample_id`. Only audio metadata is read from references, not their transcript.
Raw hypothesis priority is `hypothesis`, then `pred_text`, then `generation`. Word highlighting
always uses the supplied aligned word entries. A missing raw hypothesis stays empty.

```bash
speech-timestamp-viewer \
  --predictions /path/to/predictions.jsonl \
  --references /path/to/reference.jsonl \
  --subset 2mix --count 10 --seed 42 \
  --title 'LSM 2mix' --output output/lsm-2mix
```

Relative audio paths resolve against their manifest directory. To remap cluster/container paths:

```bash
speech-timestamp-viewer \
  --predictions /path/to/predictions.jsonl \
  --references /path/to/reference.jsonl \
  --audio-prefix /data/dataset --audio-root /mounted/dataset \
  --output output/remapped
```

For a specific 30-second conversation excerpt:

```bash
speech-timestamp-viewer \
  --predictions /path/to/predictions.jsonl \
  --references /path/to/reference.jsonl \
  --sample-id conversation-1 --start 120 --duration 30 \
  --title 'Conversation excerpt' --output output/excerpt
```

Repeat `--sample-id` to select several recordings. `--start`/`--duration` apply to each selected
recording. Choose a new output directory each run; existing viewers are never silently overwritten.
Model speaker IDs are displayed as supplied, with the mapping used for consistent word/VAD colors.

## Open inline in Codex

Copy or clone this repository on the machine where Codex can read your audio and predictions.
Ask Codex:

> Read this repository's AGENTS.md and README.md. Build the timestamp player from these
> prediction/reference files, select ten 2mix samples, and show it inline in this conversation.

The builder emits:

- `index.html`: a standalone offline player containing all selected samples.
- `inline-001.html`, etc.: HTML fragments, automatically split below 950,000 bytes.
- `selection.json`: reproducible sample IDs and excerpt ranges.

For inline display, build into a **durable directory explicitly writable and readable by the
current Codex conversation**, not a hardcoded directory from another workstation. The CLI prints
the exact content references. Codex should include each desired reference in its final response:

```text
visualize{"path":"/absolute/path/to/inline-001.html"}
```

This requires a Codex client with inline visualization support; plain CLI/other clients can open
`index.html` in a browser instead. Copying the repository cannot enable a missing host feature.
No host-provided wrapper or skill is needed to generate the files. If a visualization skill is
available to the agent, it should follow that skill's current rendering instructions.

If one recording alone exceeds the fragment size limit, the builder fails with a suggestion to
use a shorter excerpt (e.g. `--duration 30`). It never silently drops the recording.

## Tests

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m pip install -e '.[test]'
python -m playwright install chromium
python tests/browser_smoke.py output/demo/index.html
python tests/browser_navigation.py output/demo/index.html
# Or use installed Chrome:
python tests/browser_smoke.py output/demo/index.html --browser /path/to/chrome
```

The browser checks verify actual bounded playback, cancellation/resume, word/VAD clicks,
two-decimal readouts, synchronized zoom, overview drag/keyboard navigation, waveform/spectrogram
rendering and small-screen layout. `browser_navigation.py` uses the generated four-second synthetic demo.

## Maintenance and privacy

`speech_timestamp_viewer/cli.py` handles input/media generation; `templates/viewer.html` owns
the reusable player; `templates/standalone.html` supplies browser styling. Keep HTML markup in
these literal templates, not in Python strings. Changes to interactions should extend the browser test.

Generated players embed audio and hypothesis text. **Treat them as sensitive as the original data.**
They make no network requests and require no CDNs. Do not commit generated output or private data;
the default `.gitignore` excludes these artifacts and model files. No license is granted by this
repository unless its owner adds one; preserve applicable upstream notices when importing code.
