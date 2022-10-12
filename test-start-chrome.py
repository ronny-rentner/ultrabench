#!/usr/bin/env python
import sys, time

import drivers.chrome
import config

from rich import print

print('Testing browser start')

try:
    chrome_config = next(iter(config.chrome.values()))
except AttributeError:
    raise Exception('Could not find Chrome config variable in config.py.')

# Allow selecting the scenario as the first command line argument
try:
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
        chrome_config = config.chrome[scenario]
except KeyError:
    raise Exception(f'Could not find scenario "{scenario}" in `chrome` config variable in config.py.')

with drivers.chrome.Chrome(**chrome_config, extra_arguments=['--window-size=1920,1080']) as driver:
    while True:
        try:
            _ = driver.window_handles
        except Exception as e:
            break
        time.sleep(1)

