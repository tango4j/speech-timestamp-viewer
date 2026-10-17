"""Generate synthetic two-speaker tones and illustrative timestamps, not speech recognition."""

import argparse
import json
from pathlib import Path
import wave

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('demo-data'))
    parser.add_argument('--special-tokens', action='store_true', help='Include illustrative speaker/style/event tags')
    args = parser.parse_args()
    if (args.output / 'tones.wav').exists() or (args.output / 'predictions.jsonl').exists():
        parser.error('Demo files already exist; choose a new directory')
    args.output.mkdir(parents=True, exist_ok=True)
    sr = 16000
    t = np.arange(4 * sr) / sr
    signal = np.zeros_like(t)
    for start, end, hz in [(0.4, 1.3, 330), (1.0, 2.2, 550), (2.5, 3.4, 330)]:
        select = (t >= start) & (t < end)
        signal[select] += (
            0.15 * np.sin(2 * np.pi * hz * t[select]) * np.sin(np.pi * (t[select] - start) / (end - start)) ** 2
        )
    with wave.open(str(args.output / 'tones.wav'), 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes((signal * 32767).astype('<i2').tobytes())
    record = dict(
        sample_id='synthetic-two-speakers',
        audio_filepath='tones.wav',
        hypothesis='low tone high tone low again',
        words=[
            dict(word=w, speaker=s, start=a, end=b)
            for w, s, a, b in [
                ('low', 0, 0.4, 0.8),
                ('tone', 0, 0.8, 1.3),
                ('high', 1, 1.0, 1.5),
                ('tone', 1, 1.5, 2.2),
                ('low', 0, 2.5, 2.9),
                ('again', 0, 2.9, 3.4),
            ]
        ],
        diarization_timestamps=[
            dict(speaker=s, start=a, end=b) for s, a, b in [(0, 0.4, 1.3), (1, 1.0, 2.2), (0, 2.5, 3.4)]
        ],
    )
    if args.special_tokens:
        record['hypothesis'] = '<spk:0><sty:stt:flat> hello <ev:laughter><sty:end:flat>'
        record['words'] = [
            dict(word=w, speaker=0, start=a, end=b)
            for w, a, b in [
                ('<sty:stt:flat>', 0, 0.4),
                ('hello', 0.4, 0.8),
                ('<ev:laughter>', 0.8, 1.3),
                ('<sty:end:flat>', 1.3, 1.5),
            ]
        ]
    (args.output / 'predictions.jsonl').write_text(json.dumps(record) + '\n')
    print(args.output / 'predictions.jsonl')


if __name__ == '__main__':
    main()
