# Speech Timestamp Viewer

[![Tests](https://github.com/tango4j/speech-timestamp-viewer/actions/workflows/tests.yml/badge.svg)](https://github.com/tango4j/speech-timestamp-viewer/actions/workflows/tests.yml)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
[![Version 0.2.0](https://img.shields.io/badge/version-0.2.0-blue)](pyproject.toml)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Inspect word timestamps alongside audio, waveform, spectrogram and speaker diarization in a portable, offline HTML player.
No GPU, NeMo installation, checkpoint, web server or JavaScript build tools required.

- 🎧 **Click to listen** — play a word or diarization segment and stop at its end.
- 🔎 **Synchronized zoom** — waveform, spectrogram and timestamp tracks scale together.
- 🧭 **Navigate recordings** — drag the overview window or use keyboard controls.
- 🗣️ **Inspect multiple speakers** — color-coded words, simultaneous highlighting and VAD lanes.
- 📦 **Share offline** — self-contained HTML, excerpts and Codex-compatible fragments.

## Preview

![LSM 2mix at 2× zoom with a panned overview, speaker tracks and selected start/end times](docs/images/lsm-2mix-viewer.png)

**LSM 2mix at 2× zoom.** The overview covers half the recording. Click a word or diarization
bar to play its interval and inspect start/end times to two decimal places.

## Quick start

Requires **Python 3.10+** and **FFmpeg with libmp3lame**. Install FFmpeg with
`sudo apt-get install ffmpeg` (Ubuntu), `brew install ffmpeg` (macOS), or
`conda install -c conda-forge ffmpeg`.

```bash
git clone https://github.com/tango4j/speech-timestamp-viewer.git
cd speech-timestamp-viewer
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python examples/make_demo.py --output demo-data
speech-timestamp-viewer --predictions demo-data/predictions.jsonl --output output/demo
```

Open **`output/demo/index.html`** in a browser. The example uses synthetic tones and illustrative
labels, not recognized speech. No private recordings or model downloads are needed.

### Controls in action

![Synthetic demo showing segment playback, synchronized zoom and overview navigation](docs/images/controls-demo.gif)

*Muted screen recording of the synthetic example. The generated HTML includes audio playback.*

## Controls

| Control | Action |
| --- | --- |
| Word text, word bar or VAD bar | Play that interval; show **Start / End** in seconds |
| Audio play / pause | Normal continuous playback after a segment finishes |
| Main timeline | Seek and cancel the segment playback limit |
| Zoom **+ / −** | Double / halve zoom on all tracks together |
| Overview window | Drag to pan; click outside it to recenter |
| Focused overview: **← / →** | Pan left / right |
| **Page Up / Down**, **Home / End** | Jump one window, or move to either edge |
| Original hypothesis | Expand the supplied text, including event/style tokens |

## Use your predictions

```bash
speech-timestamp-viewer --predictions /path/to/predictions.jsonl --count 10 --seed 42 --output output/my-viewer
```

Supports generic JSONL and NeMo/SALM timestamp output. References can supply audio paths,
but **ground-truth text never replaces the hypothesis**. Choose a new output directory each run.

| Guide | Contents |
| --- | --- |
| [Input formats](docs/input-formats.md) | Schemas, speaker mapping, hypothesis selection |
| [Usage and navigation](docs/usage.md) | Path remapping, sample selection, excerpts and playback details |
| [Codex integration](docs/codex.md) | Inline fragments, output files and client requirements |
| [Development](docs/development.md) | Unit tests, browser checks and project structure |

## Scope and privacy

This is a **viewer**, not an ASR or alignment engine. Supplied timestamps are unchanged except
for excerpt clipping. Two-decimal formatting does not imply 10 ms accuracy. Zoom magnifies
the stored preview rather than recomputing acoustic features. Playback is not sample-accurate editing.

Generated players embed audio and hypothesis text: **treat them as sensitive as the original data**.
They require no CDNs or network requests. Do not commit private recordings, transcripts or generated players.

## License

The viewer code is [MIT licensed](LICENSE). Input audio and transcripts remain subject to their own permissions.
