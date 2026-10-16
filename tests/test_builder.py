import json
from pathlib import Path
import tempfile
import unittest

from speech_timestamp_viewer.cli import (
    audio_path,
    clip_rows,
    fragment,
    normalized_timestamps,
    read_jsonl,
    write_players,
)


class BuilderTests(unittest.TestCase):
    def test_generic_speakers(self):
        words, diar, mapping = normalized_timestamps(
            dict(words=[dict(word='hello', speaker='alice', start=0.1, end=0.2)])
        )
        self.assertEqual(mapping, {'alice': 'alice'})
        self.assertEqual(words[0]['speaker'], 'alice')

    def test_nemo_mapping_and_special_tokens(self):
        words, _, mapping = normalized_timestamps(
            {
                'timestamps': {
                    'speaker_word_timestamps': {'0': [dict(word='<ev:laughter>', start=0, end=0.2)]},
                    'speaker_tag_to_sortformer_column': {'0': 2},
                }
            }
        )
        self.assertEqual(words[0]['word'], '<ev:laughter>')
        self.assertEqual(mapping, {'0': '2'})

    def test_invalid_interval(self):
        for start, end in [(2, 1), (-1, 1), (0, float('nan'))]:
            with self.assertRaises(ValueError):
                normalized_timestamps({'words': [dict(word='bad', start=start, end=end)]})

    def test_excerpt(self):
        source = [dict(word='hello', start=9, end=12)]
        self.assertEqual(clip_rows(source, 10, 1), [dict(word='hello', start=0.0, end=1, clipped=True)])
        self.assertEqual(source[0]['start'], 9)

    def test_safe_script_embedding(self):
        output = fragment([{'word': '</script><script>alert(1)</script>'}], '<b>Title</b>')
        self.assertNotIn('</script><script>alert', output)
        self.assertIn('&lt;b&gt;Title&lt;/b&gt;', output)
        self.assertNotIn('__EXAMPLES__', output)

    def test_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'input.jsonl'
            p.write_text('{"sample_id":"a"}\n{"sample_id":"a"}\n')
            with self.assertRaises(ValueError):
                read_jsonl(p)

    def test_audio_remap(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'audio.wav'
            p.touch()
            self.assertEqual(audio_path({'audio_filepath': '/remote/audio.wav'}, {}, Path('.'), Path(d), '/remote'), p)

    def test_split_size_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            records = [dict(id=str(i), offset=0, duration=1, group='demo', audio='x' * 5000) for i in range(3)]
            limit = len(fragment(records[:1], 'demo').encode()) + 100
            paths = write_players(records, Path(d), 'demo', limit)
            self.assertEqual(len(paths), 3)
            self.assertTrue(all(p.stat().st_size < limit for p in paths))
            with self.assertRaises(FileExistsError):
                write_players(records, Path(d), 'demo', limit)


if __name__ == '__main__':
    unittest.main()
