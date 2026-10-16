# Usage and navigation


- Click a word in the transcript or a word/VAD bar to play only that segment. Clicking another segment cancels the previous stop point.
- Native audio controls play continuously after a segment finishes. Seeking in the main plot cancels the segment limit; pausing/resuming within a selected segment retains its endpoint.
- **Zoom in + / Zoom out −** change the visible time span by a factor of two. The current playhead anchors zoom when visible; otherwise the viewport center is used. The minimum view span is 250 ms (or the full duration for shorter recordings).
- Drag the overview's highlighted window to pan, or click elsewhere in the overview to center it there. This moves the view without changing playback position.
- Focus the overview window and use **Left/Right** to pan, **Page Up/Down** for a full-window jump, or **Home/End** to reach either edge.
- All four tracks use the same clipped time transform; off-screen bars cannot intercept clicks. Zoom magnifies the stored waveform/spectrogram preview; it does not recompute higher-resolution acoustic features.
- Playback endpoints use browser media timing, not sample-accurate audio editing. The displayed start/end values remain the supplied timestamps.


## Selection, paths and excerpts

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

