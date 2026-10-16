"""Regression coverage for bounded playback, zoom, shared scales and overview navigation."""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('page', type=Path, help='Generated four-second synthetic demo index.html')
parser.add_argument('--browser')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, **({'executable_path': args.browser} if args.browser else {}))
    page = browser.new_page(viewport={'width': 800, 'height': 1100})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.page.resolve().as_uri())
    page.wait_for_function('document.querySelector("audio").readyState >= 2')
    for selector in (
        'button[data-segment-type="Word"]',
        'button[data-segment-type="Diarization"]',
        '#ctc-transcript button',
    ):
        target = page.locator(selector).first
        target.click()
        page.wait_for_function('!document.querySelector("audio").paused', timeout=2000)
        page.wait_for_function('document.querySelector("audio").paused', timeout=4000)
        expected = 1.3 if 'Diarization' in selector else 0.8
        assert abs(page.evaluate('document.querySelector("audio").currentTime') - expected) < 0.03
    # Switching segments must cancel the old endpoint timer.
    page.locator('button[data-segment-type="Word"]').first.click()
    page.wait_for_timeout(50)
    page.locator('button[data-segment-type="Diarization"]').first.click()
    page.wait_for_function('document.querySelector("audio").paused', timeout=4000)
    assert abs(page.evaluate('document.querySelector("audio").currentTime') - 1.3) < 0.03
    # Resuming native playback after a segment finishes must not remain capped.
    page.evaluate('document.querySelector("audio").play()')
    page.wait_for_function('document.querySelector("audio").currentTime > 1.4')
    page.evaluate('document.querySelector("audio").pause();document.querySelector("audio").currentTime=1')
    page.wait_for_timeout(100)
    image_width = page.locator('[data-track="spectrogram"]').evaluate('(e)=>Number(e.getAttribute("width"))')
    word_width = page.locator('[data-track="word"]').first.evaluate('(e)=>Number(e.getAttribute("width"))')
    page.locator('#ctc-zoom-in').click()
    assert (
        abs(
            page.locator('[data-track="spectrogram"]').evaluate('(e)=>Number(e.getAttribute("width"))') / image_width
            - 2
        )
        < 0.001
    )
    assert (
        abs(
            page.locator('[data-track="word"]').first.evaluate('(e)=>Number(e.getAttribute("width"))') / word_width - 2
        )
        < 0.001
    )
    assert page.locator('#ctc-nav-window').evaluate('(e)=>e.style.width') == '50%'
    # Keyboard panning and pointer drag move the viewport, not the audio clock.
    page.locator('#ctc-nav-window').focus()
    page.keyboard.press('End')
    assert float(page.locator('#ctc-chart').get_attribute('data-view-start')) == 2
    assert abs(page.evaluate('document.querySelector("audio").currentTime') - 1) < 0.03
    page.keyboard.press('Home')
    box = page.locator('#ctc-nav-window').bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.mouse.down()
    page.mouse.move(box['x'] + box['width'], box['y'] + box['height'] / 2, steps=5)
    page.mouse.up()
    assert float(page.locator('#ctc-chart').get_attribute('data-view-start')) > 0.5
    # All timeline layers share exactly the same coordinate transform.
    page.locator('#ctc-nav-window').focus()
    page.keyboard.press('Home')
    for track in ('waveform', 'spectrogram', 'word', 'diarization'):
        assert page.locator(f'[data-track="{track}"]').count() > 0
    assert page.locator('[data-track="word"]').first.get_attribute('x') == page.locator(
        '[data-track="diarization"]'
    ).first.get_attribute('x')
    page.locator('#ctc-zoom-out').click()
    assert page.locator('#ctc-nav-window').evaluate('(e)=>e.style.width') == '100%'
    for width in (390, 320):
        page.set_viewport_size({'width': width, 'height': 1100})
        page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    browser.close()
    print(
        'PASS: automatic bounded playback, cancellation/resume, shared zoom, overview resize/drag/keyboard, mobile layout'
    )
