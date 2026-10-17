"""Verify ignored text never enters playback controls and event words remain interactive."""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('page', type=Path)
parser.add_argument('--browser')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, **({'executable_path': args.browser} if args.browser else {}))
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.page.resolve().as_uri())
    page.wait_for_function('document.querySelector("audio").readyState >= 2')
    passive = page.locator('#ctc-transcript .ctc-passive')
    assert passive.all_text_contents() == ['<spk:0>', '<sty:stt:flat>', '<sty:end:flat>']
    for node in passive.all():
        assert node.evaluate('(e)=>e.tagName') == 'SPAN'
        assert node.get_attribute('aria-pressed') is None
        assert node.evaluate('(e)=>getComputedStyle(e).borderWidth') == '0px'
        assert node.evaluate('(e)=>getComputedStyle(e).backgroundColor') == 'rgba(0, 0, 0, 0)'
        node.click()
        assert page.evaluate('document.querySelector("audio").paused')
    assert page.locator('[data-track="word"]').count() == 2
    assert page.locator('#ctc-transcript button').all_text_contents() == ['hello', '<ev:laughter>']
    page.locator('#ctc-transcript button').filter(has_text='<ev:laughter>').click()
    page.wait_for_function('!document.querySelector("audio").paused')
    page.wait_for_function('document.querySelector("audio").paused', timeout=4000)
    assert abs(page.evaluate('document.querySelector("audio").currentTime') - 1.3) < 0.03
    assert not errors, errors
    browser.close()
    print('PASS: ignored tags are unboxed, passive and bar-free; events retain bounded playback')
