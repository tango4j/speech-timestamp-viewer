"""Build offline players and size-bounded Codex fragments from timestamp JSONL."""

import argparse
import base64
from collections import defaultdict
import hashlib
import html
from importlib.resources import files
import io
import json
import math
from pathlib import Path
import random
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.signal import stft


def read_jsonl(path: Path) -> dict:
    """Load unique sample IDs; reject accidental duplicate or missing IDs."""
    records = {}
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        key = record.get('sample_id', record.get('id'))
        if key is None or str(key) in records:
            raise ValueError(f'{path}:{number}: missing or duplicate sample_id')
        records[str(key)] = record
    return records


def normalized_timestamps(record: dict) -> tuple[list, list, dict]:
    """Accept NeMo speaker-grouped timestamps or a generic flat word list."""
    ts = record.get('timestamps') or record
    grouped = ts.get('speaker_word_timestamps')
    if grouped is None:
        grouped = defaultdict(list)
        for word in ts.get('words', []):
            grouped[str(word.get('speaker', 0))].append(word)
    words = []
    for tag, items in grouped.items():
        for item in items:
            words.append(
                dict(
                    word=str(item['word']),
                    speaker=str(item.get('speaker', tag)),
                    start=float(item['start']),
                    end=float(item['end']),
                )
            )
    diar = [
        dict(speaker=str(s['speaker']), start=float(s['start']), end=float(s['end']))
        for s in ts.get('diarization_timestamps', [])
    ]
    for row in words + diar:
        if not all(math.isfinite(row[k]) for k in ('start', 'end')) or not 0 <= row['start'] <= row['end']:
            raise ValueError(f'Invalid timestamp interval: {row}')
    mapping = {str(k): str(v) for k, v in ts.get('speaker_tag_to_sortformer_column', {}).items() if v is not None}
    # Generic inputs default to matching speaker identities, without inference.
    if 'speaker_tag_to_sortformer_column' not in ts:
        mapping = {w['speaker']: w['speaker'] for w in words}
    return words, diar, mapping


def audio_path(record: dict, reference: dict, origin: Path, root: Path | None, prefix: str | None) -> Path:
    """Resolve audio metadata, optionally remapping a dataset-root prefix."""
    value = record.get('audio_filepath') or reference.get('audio_filepath')
    if not value:
        raise ValueError('Missing audio_filepath; provide a reference manifest or add it to predictions')
    path = Path(value)
    if prefix:
        if root is None:
            raise ValueError('--audio-prefix requires --audio-root')
        path = root / path.relative_to(prefix)
    elif not path.is_absolute():
        path = (root or origin) / path
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def media(path: Path, start: float, duration: float | None) -> dict:
    """Decode one excerpt and embed mono MP3, peak waveform and STFT spectrogram."""
    command = ['ffmpeg', '-v', 'error', '-ss', str(start), '-i', str(path)]
    if duration is not None:
        command += ['-t', str(duration)]
    command += ['-ac', '1', '-ar', '16000', '-f', 'f32le', 'pipe:1']
    raw = subprocess.run(command, capture_output=True, check=True).stdout
    samples = np.frombuffer(raw, dtype=np.float32)
    if len(samples) < 2:
        raise ValueError(f'Empty or too-short audio excerpt: {path} at {start}s')
    mp3 = subprocess.run(
        [
            'ffmpeg',
            '-v',
            'error',
            '-f',
            'f32le',
            '-ar',
            '16000',
            '-ac',
            '1',
            '-i',
            'pipe:0',
            '-codec:a',
            'libmp3lame',
            '-b:a',
            '24k',
            '-f',
            'mp3',
            'pipe:1',
        ],
        input=raw,
        capture_output=True,
        check=True,
    ).stdout
    wave = [
        [round(float(v.min()), 4), round(float(v.max()), 4)] for v in np.array_split(samples, min(600, len(samples)))
    ]
    size = min(512, len(samples))
    _, _, z = stft(samples, 16000, nperseg=size, noverlap=size // 2)
    magnitude = np.abs(z)
    db = 20 * np.log10(np.maximum(magnitude, 1e-7) / max(float(magnitude.max()), 1e-7))
    gray = np.uint8(np.clip((db + 70) / 70, 0, 1) * 255)[::-1]
    image = Image.fromarray(gray).resize((650, 100)).quantize(colors=24)
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True)
    return dict(
        duration=len(samples) / 16000,
        wave=wave,
        audio='data:audio/mpeg;base64,' + base64.b64encode(mp3).decode(),
        spectrogram='data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode(),
    )


def clip_rows(rows: list, start: float, duration: float) -> list:
    """Clip intersecting intervals into excerpt time without modifying original records."""
    result = []
    for row in rows:
        if row['end'] > start and row['start'] < start + duration:
            result.append(
                dict(
                    row,
                    start=max(0.0, row['start'] - start),
                    end=min(duration, row['end'] - start),
                    clipped=row['start'] < start or row['end'] > start + duration,
                )
            )
    return result


def fragment(examples: list, title: str) -> str:
    """Insert safely escaped data into the literal, version-controlled HTML template."""
    template = files('speech_timestamp_viewer').joinpath('templates/viewer.html').read_text()
    payload = json.dumps(examples, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
    uid = 'timestamps-' + hashlib.sha256((title + payload).encode()).hexdigest()[:16]
    return (
        template.replace('__ROOT_ID__', uid).replace('__TITLE__', html.escape(title)).replace('__EXAMPLES__', payload)
    )


def write_players(examples: list, output: Path, title: str, limit: int) -> list[Path]:
    """Split inline fragments below the byte ceiling; also save one offline standalone page."""
    batches, batch = [], []
    for example in examples:
        if len(fragment([example], title).encode()) >= limit:
            raise ValueError(f"Sample {example['id']} exceeds the inline size limit; use --duration 30")
        if batch and len(fragment(batch + [example], title).encode()) >= limit:
            batches.append(batch)
            batch = []
        batch.append(example)
    if batch:
        batches.append(batch)
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / f'inline-{i:03}.html' for i in range(1, len(batches) + 1)]
    targets = [*paths, output / 'index.html', output / 'selection.json']
    if any(path.exists() for path in targets) or list(output.glob('inline-*.html')):
        raise FileExistsError('Output contains an existing viewer; choose a new --output directory')
    for path, group in zip(paths, batches):
        path.write_text(fragment(group, title))
    wrapper = files('speech_timestamp_viewer').joinpath('templates/standalone.html').read_text()
    (output / 'index.html').write_text(wrapper.replace('__FRAGMENT__', fragment(examples, title)))
    (output / 'selection.json').write_text(
        json.dumps([{k: e[k] for k in ('id', 'offset', 'duration', 'group')} for e in examples], indent=2) + '\n'
    )
    return paths


def main() -> None:
    """Select predictions, resolve audio and create portable timestamp players."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--references', type=Path)
    parser.add_argument('--audio-root', type=Path)
    parser.add_argument('--audio-prefix', help='Prefix in manifest paths to replace with --audio-root')
    parser.add_argument('--sample-id', action='append', help='Repeat to select exact IDs in this order')
    parser.add_argument('--subset', default='', help='Substring filter on sample_id')
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--start', type=float, default=0.0, help='Excerpt offset in seconds')
    parser.add_argument('--duration', type=float, help='Excerpt length; omitted means full recording')
    parser.add_argument('--title', default='Speech timestamps')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-inline-bytes', type=int, default=950000)
    args = parser.parse_args()
    if not shutil.which('ffmpeg'):
        parser.error('ffmpeg is required; install it with apt, brew, or conda')
    if (
        args.count < 1
        or not math.isfinite(args.start)
        or args.start < 0
        or (args.duration is not None and (not math.isfinite(args.duration) or args.duration <= 0))
    ):
        parser.error('count/duration must be positive and start must be finite and nonnegative')
    if not 20000 <= args.max_inline_bytes <= 1000000:
        parser.error('max-inline-bytes must be between 20000 and 1000000')
    predictions = read_jsonl(args.predictions)
    refs = read_jsonl(args.references) if args.references else {}
    if args.sample_id:
        selected = list(dict.fromkeys(args.sample_id))
        missing = set(selected) - predictions.keys()
        if missing:
            parser.error(f'Unknown sample IDs: {sorted(missing)}')
    else:
        candidates = sorted(k for k in predictions if args.subset in k)
        selected = random.Random(args.seed).sample(candidates, min(args.count, len(candidates)))
    if not selected:
        parser.error('No matching samples')
    examples = []
    for number, key in enumerate(selected, 1):
        record, ref = predictions[key], refs.get(key, {})
        origin = (
            args.predictions.parent
            if record.get('audio_filepath')
            else args.references.parent if args.references else args.predictions.parent
        )
        path = audio_path(record, ref, origin, args.audio_root, args.audio_prefix)
        words, diar, mapping = normalized_timestamps(record)
        data = media(path, args.start, args.duration)
        # Never substitute reference text for a missing hypothesis.
        hypothesis = next(
            (record[k] for k in ('hypothesis', 'pred_text', 'generation') if isinstance(record.get(k), str)), ''
        )
        examples.append(
            dict(
                data,
                id=key,
                number=number,
                group=args.title,
                offset=args.start,
                words=sorted(clip_rows(words, args.start, data['duration']), key=lambda w: (w['start'], w['speaker'])),
                diar=clip_rows(diar, args.start, data['duration']),
                mapping=mapping,
                hypothesis=hypothesis,
            )
        )
        print(f'Prepared {number}/{len(selected)}: {key}', file=sys.stderr)
    paths = write_players(examples, args.output, args.title, args.max_inline_bytes)
    print(f'Offline browser player: {(args.output / "index.html").resolve()}')
    for path in paths:
        print('visualize' + json.dumps({'path': str(path.resolve())}) + '')


if __name__ == '__main__':
    main()
