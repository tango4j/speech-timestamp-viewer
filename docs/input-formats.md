# Input formats


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

