# Development


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

