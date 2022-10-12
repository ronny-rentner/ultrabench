import pathlib

# It is recommended to make a copy of your Google Chrome config directory.
# On Linux, this is usually located in '~/.config/google-chrome'.
chrome_user_data_dir = pathlib.Path(__file__).parent / 'runtime' / 'google-chrome'

# We will use these configuration parameters for all test scenarios below.
chrome_default_config = {
    'driver_path': '/home/ronny/.chromedriver-helper/106.0.5249.61/linux64/chromedriver',
    # 'driver_options' are the webdriver capabilities with a better name.
    # See https://sites.google.com/a/chromium.org/chromedriver/capabilities and
    #     https://www.w3.org/TR/webdriver/#capabilities
    'driver_options': [
        "--verbose", "--log-path=chromedriver.log"
    ],
    # This allows us to connect to an existing, running Chrome browser instance
    'experimental_options': {
        # This address and port must match the Chrome '--remote-debugging-port=9222' setting
        'debuggerAddress': '127.0.0.1:9222',
    },
    'browser_path': '/usr/bin/google-chrome',
}

# Useful default browser options for running performance tests for all test scenarios below.
chrome_default_browser_options = [
    # Disable the special first run actions in a browser when you create
    # a fresh user profile
    '--no-first-run',
    # Disable ending up in an a/b field test for new browser features
    '--remote-debugging-port=9222',
    # Do not ask to make it the default browser
    '--no-default-browser-check',

    f'--user-data-dir={chrome_user_data_dir}',
]


chrome = {
    'empty': {
        **chrome_default_config,
        'browser_options': [
            *chrome_default_browser_options,
        ],
    },

    'default': {
        **chrome_default_config,
        'browser_options': [
            *chrome_default_browser_options,
            '--enable-accelerated-video-decode',
            '--enable-accelerated-compositing',
            # These features are the same as browser flags which can be changed via chrome://flags
            '--enable-features=VaapiVideoDecoder,VaapiVideoEncoder,RawDraw',
            '--disable-features=UseChromeOSDirectVideoDecoder,UseChromeOSDirectVideoEncoder,UseOzonePlatform',
            '--ignore-gpu-blocklist',
            '--use-gl=desktop',
            '--disable-gpu-driver-bug-workarounds',
        ],
    },

    'no-gpu': {
        **chrome_default_config,
        'browser_options': [
            *chrome_default_browser_options,
            '--disable-gpu',
            '--disable-software-rasterizer',
        ]
    }
}

for i in range(0, 10):
    for k in list(chrome.keys()).copy():
        chrome[f"{k}{i}"] = chrome[k]

