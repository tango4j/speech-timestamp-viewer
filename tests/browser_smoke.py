"""Check a generated synthetic demo in a real browser (optional test dependency)."""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('page', type=Path)
parser.add_argument('--browser', help='Optional installed Chrome/Chromium executable')
args = parser.parse_args()
with sync_playwright() as p:
    options = dict(headless=True)
    if args.browser:
        options['executable_path'] = args.browser
    browser = p.chromium.launch(**options)
    page = browser.new_page(viewport={'width': 800, 'height': 1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.page.resolve().as_uri())
    for i in range(page.locator('#ctc-sample option').count()):
        page.locator('#ctc-sample').select_option(str(i))
        page.wait_for_function('document.querySelector("audio").readyState >= 2')
        assert page.locator('#ctc-chart polygon').count() == 1
        for kind in ('Word', 'Diarization'):
            target = page.locator(f'button[data-segment-type="{kind}"]').first
            target.click()
            assert kind in page.locator('#ctc-detail').inner_text()
    page.locator('#ctc-sample').select_option('0')
    page.wait_for_function('document.querySelector("audio").readyState >= 2')
    assert page.locator('#ctc-chart polygon').count() == 1
    assert page.locator('#ctc-chart image').count() == 1
    for kind in ('Word', 'Diarization'):
        target = page.locator(f'button[data-segment-type="{kind}"]').first
        expected = target.evaluate(
            '(e)=>`Start ${Number(e.dataset.start).toFixed(2)} s · End ${Number(e.dataset.end).toFixed(2)} s`'
        )
        target.click()
        assert expected in page.locator('#ctc-detail').inner_text()
        page.evaluate('document.querySelector("audio").play()')
        page.wait_for_timeout(200)
        assert expected in page.locator('#ctc-detail').inner_text()
        page.evaluate('document.querySelector("audio").pause()')
    page.locator('#ctc-transcript button').first.focus()
    page.keyboard.press('Enter')
    assert 'Word · Spk' in page.locator('#ctc-detail').inner_text()
    for width in (390, 320):
        page.set_viewport_size({'width': width, 'height': 1000})
        page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    browser.close()
    print(
        'PASS: audio playback, waveform, spectrogram, word/VAD clicks, keyboard, persistent two-decimal readout, mobile widths'
    )
