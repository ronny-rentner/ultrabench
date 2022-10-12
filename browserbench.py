# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import argparse
from selenium import webdriver

import json
import platform
import selenium
import subprocess
import sys
import time
import traceback

import config
import drivers.chrome

from rich import print

DEFAULT_STP_DRIVER_PATH = '/Applications/Safari Technology Preview.app/Contents/MacOS/safaridriver'

# Maximum number of times the benchmark will be run before giving up.
MAX_ATTEMPTS = 6


class BrowserBench(object):
    def __init__(self, name, version):
        self._name = name
        self._version = version
        self._output = None
        self._githash = None
        self._browser = None
        self._driver = None

    @staticmethod
    def _CreateChromeDriver(optargs):
        options = webdriver.ChromeOptions()
        #options.add_argument('enable-benchmarking')
        print('ARGS: ', optargs.arguments)
        caps = webdriver.DesiredCapabilities.CHROME.copy()

        if optargs.arguments:
            for arg in optargs.arguments:
                options.add_argument(arg if arg.startswith('--') else f"--{arg}")

        options.add_argument('--no-first-run')
        options.add_argument('--disable-field-trial-config')
        options.add_argument('--no-default-browser-check')

        #options.add_argument('window-size=2920,1080')
        #options.add_argument('--disable-infobars')
        #options.add_argument("start-maximized");
        #options.add_experimental_option('excludeSwitches', [
        #         'disable-hang-monitor',
        #         'disable-prompt-on-repost',
        #         'disable-background-networking',
        #         'disable-sync',
        #         'disable-translate',
        #         'disable-web-resources',
        #         'disable-client-side-phishing-detection',
        #         'disable-component-update',
        #         'disable-default-apps',
        #         'disable-zero-browsers-open-for-tests'
        #])

        print("OPT", repr(options))
        #caps['acceptInsecureCerts'] = True
        #caps['noWebsiteTestingDefaults'] = True
        #caps['disable-inforbars'] = True
        #caps['disableInforbars'] = True
        #caps['disableInforBars'] = True
        #caps['start-maximized'] = True
        #caps['startMaximized'] = True
        #options.add_argument("start-maximized=True");

        #caps.update(options)

        print('CAPS: ', caps)
        service_args=["--verbose", "--log-path=chromedriver.log"]

        if optargs.driver_path:
            options.binary_location = optargs.driver_path
        #service = webdriver.chrome.service.Service(executable_path=optargs.executable)
        chrome = webdriver.Chrome(service_args=service_args, options=options, executable_path=optargs.executable, desired_capabilities=caps)
        size = chrome.get_window_size()
        print("Window size: width = {}px, height = {}px".format(size["width"], size["height"]))
        return chrome

    @staticmethod
    def _CreateSafariDriver(optargs):
        params = {}
        if optargs.executable:
            params['exexutable_path'] = optargs.executable
        if optargs.browser == 'stp':
            safari_options = webdriver.safari.options.Options()
            safari_options.use_technology_preview = 1
            params['desired_capabilities'] = {
                    'browserName': safari_options.capabilities['browserName']
            }
            # Stp requires executable_path. If the path is not supplied use the
            # typical location.
            if not optargs.executable:
                params['executable_path'] = DEFAULT_STP_DRIVER_PATH
        return webdriver.Safari(**params)

    def get_browser_vesion(self, optargs):
        '''
        Returns the version of the browser.
        '''
        if optargs.browser == 'safari' or optargs.browser == 'stp':
            return BrowserBench._GetSafariVersion(optargs)
        # Selenium provides the full version for chrome.
        return self._driver.capabilities['browserVersion']

    @staticmethod
    def _GetSafariVersion(optargs):
        # selenium does not report the build id of stp (e.g. 149), so this uses safaridriver,
        # which is able to report the version.
        safaridriver_executable = 'safaridriver'
        if optargs.executable:
            safaridriver_executable = optargs.executable
        if optargs.browser == 'stp' and not optargs.executable:
            safaridriver_executable = DEFAULT_STP_DRIVER_PATH
        results = subprocess.run([safaridriver_executable, '--version'],
                                                         capture_output=True).stdout.decode('utf-8')
        start_index = results.find('Safari')
        version = results[start_index:] if start_index != -1 else results
        return version.strip()

    @staticmethod
    def _CreateDriver(optargs, current_config):
        if optargs.browser == 'chrome':
            #return BrowserBench._CreateChromeDriver(optargs)
            #config.chrome['browser_options'] = config.chrome['browser_options']['default']

            return drivers.chrome.Chrome(**current_config, extra_arguments=optargs.arguments)
        elif optargs.browser == 'safari' or optargs.browser == 'stp':
            for i in range(0, 10):
                try:
                    return BrowserBench._CreateSafariDriver(optargs)
                except selenium.common.exceptions.SessionNotCreatedException as e:
                    traceback.print_exc(e)
                    print('Connecting to Safari failed, will try again')
                    time.sleep(5)
            print('Failed to connect to Safari, this likely means Safari '
                                            'is running something else')
            return None
        else:
            return None

    @staticmethod
    def _KillBrowser(optargs):
        if optargs.browser == 'safari' or optargs.browser == 'stp':
            browser_process_name = ('Safari' if optargs.browser == 'safari' else
                                                    'Safari Technology Preview')
            print('Killing Safari')
            subprocess.run(['killall', '-9', browser_process_name])
            # Sleep for a little bit to ensure the kill happened.
            time.sleep(5)

            # safaridriver may be wedged, kill it too.
            print('Killing safaridriver')
            subprocess.run(['killall', '-9', 'safaridriver'])
            # Sleep for a little bit to ensure the kill happened.
            time.sleep(5)

            print('Continuing after kill')
            return
        # This logic is primarily for Safari, which seems to occasionally hang. Will
        # implement for Chrome if necessary.
        print('Not handling kill of chrome, if this is hit and test '
                                        'fails, implement it')

    def _CreateDriverAndRun(self, optargs):
        print('Creating Driver')
        results = {}
        for name, current_config in config.chrome.items():
            with BrowserBench._CreateDriver(optargs, current_config) as driver:
                self._driver = driver
                if not self._driver:
                    raise Exception('failed to create driver')

                #self._driver.set_window_size(900, 780)

                print(f'About to run test scenario "{name}"')
                print(f'Using: {driver}')
                results[name] = self.RunAndExtractMeasurements(driver, optargs)
                print(f'Results for "{name}": {results[name]}')

        return results

    def _ConvertMeasurementsToSkiaFormat(self, measurements):
        '''
        Processes the results from RunAndExtractMeasurements() into the format used
        by skia, which is:
        An array of dictionaries. Each dictionary contains a single result.
        Expected values in the dictionary are:
            'key': a dictionary that contains the following entries:
                'sub-test': the sub test. For the final score, this is not present.
                'value': the type of measurement: 'score', 'max'...
            'measurement': the measured value.
        The format for this is documented at
        https://skia.googlesource.com/buildbot/+/refs/heads/main/perf/FORMAT.md
        '''
        all_results = []
        for suite, results in measurements.items():
            for result in results if isinstance(results, list) else [results]:
                converted_result = {
                        'key': {
                                'value': result['value']
                        },
                        'measurement': result['measurement']
                }
                if suite != 'score':
                    converted_result['key']['sub-test'] = suite
                    converted_result['key']['type'] = 'sub-test'
                else:
                    converted_result['key']['type'] = 'rollup'
                all_results.append(converted_result)
        return all_results

    def _ProduceOutput(self, measurements, extra_key_values, optargs):
        '''
        extra_key_values is a dictionary of arbitrary key/value pairs added to the
        results.
        '''
        data = {
                'version': 1,
                'git_hash': self._githash,
                'key': {
                        'test': self._name,
                        'version': self._version,
                        'browser': self._browser,
                        'browser_details': {
                                'version': self.get_browser_vesion(optargs),
                                'options': self.browser_options,
                        }
                },
                'results': self._ConvertMeasurementsToSkiaFormat(measurements),
                'results_orig': measurements,
                'links': {
                        # Links is used for metadata that is not interpreted by skia. Skia
                        # expects key value pairs with the value a link. As there is no a
                        # good place to link the version to, about:blank is used.
                        self.get_browser_vesion(optargs):
                        'about:blank',
                }
        }
        data['key'].update(extra_key_values)
        print(json.dumps(data, sort_keys=True, indent=2, separators=(',', ': ')))
        if self._output:
            with open(self._output, 'w') as file:
                file.write(json.dumps(data))

    def Run(self):
        '''Runs the benchmark.

        Runs the benchmark end-to-end, starting from parsing the command line
        arguments (see README.md for details), and ending with producing the output
        to the standard output, as well as any output file specified in the command
        line arguments.
        '''

        print('Script starting')

        caffeinate_process = None
        if platform.system() == 'Darwin':
            print('Starting caffeinate')
            # Caffeinate ensures the machine is not sleeping/idle.
            caffeinate_process = subprocess.Popen(
                    ['/usr/bin/caffeinate', '-uims', '-t', '300'])

        parser = argparse.ArgumentParser()
        parser.add_argument('-b',
                                            '--browser',
                                            dest='browser',
                                            help="""The browser to use. One of chrome, safari, or stp
                                                            (Safari Technology Preview).""")
        parser.add_argument('-e',
                                            '--executable-path',
                                            dest='executable',
                                            help="""Path to the executable to the driver binary. For
                                                            safari this is the path to safaridriver.""")

        parser.add_argument('-a', '--arguments', dest='arguments', action='append',
                help='Extra command line arguments to pass to the browser')

        parser.add_argument('-g', '--githash', dest='githash',
                                            help='A git-hash associated with this run.')
        parser.add_argument('-o',
                                            '--output',
                                            dest='output',
                                            help='Path to the output json file.')
        parser.add_argument('--extra-keys',
                                            dest='extra_key_value_pairs',
                                            help='Comma separated key/value pairs added to output.')

        parser.add_argument('--browser-path', dest='browser_path',
            help='Path of the browser executable. If not specified, the default is picked up from the driver.')

        self.AddExtraParserOptions(parser)

        optargs = parser.parse_args()
        self._githash = optargs.githash or 'deadbeef'
        self._output = optargs.output
        self._browser = optargs.browser
        self._browser = optargs.browser
        self.browser_options = optargs.arguments

        extra_key_values = {}
        if optargs.extra_key_value_pairs:
            pairs = optargs.extra_key_value_pairs.split(',')
            assert len(pairs) % 2 == 0
            for i in range(0, len(pairs), 2):
                extra_key_values[pairs[i]] = pairs[i + 1]

        self.UpdateParseArgs(optargs)

        run_count = 0
        measurements = False
        # Try running the benchmark a number of times. For whatever reason either
        # Safari or safaridriver does not always complete (based on exceptions it
        # seems the http connection to safari is prematurely closing).
        while not measurements and run_count < MAX_ATTEMPTS:
            run_count += 1
            try:
                measurements = self._CreateDriverAndRun(optargs)
                break
            except Exception as e:
                if run_count < MAX_ATTEMPTS:
                    print('Got exception running, will try again', e)
                else:
                    print('Got exception running, retried too many times, giving up')
                    if caffeinate_process:
                        caffeinate_process.kill()
                    raise e
            # When rerunning, first try killing the browser in hopes of state
            # resetting.
            BrowserBench._KillBrowser(optargs)

        print('Test completed')
        print(measurements)
        #self._ProduceOutput(measurements, extra_key_values, optargs)
        if caffeinate_process:
            caffeinate_process.kill()

    def AddExtraParserOptions(self, parser):
        pass

    def UpdateParseArgs(self, optargs):
        pass

    def RunAndExtractMeasurements(self, driver, optargs):
        '''Runs the benchmark and returns the result.

        The result is a dictionary with an entry per suite as well as an entry for
        the overall score. The value of each entry is a list of dictionaries, with
        the key 'value' denoting the type of value. For example:
        {
            'score': [{ 'value': 'score',
                                    'measurement': 10 }],
            'Suite1': [{ 'value': 'score',
                                     'measurement': 11 }],
        }
        The has an overall score of 10, and the suite 'Suite1' has an overall
        score of 11. Additional values types are 'min' and 'max', these are
        optional as not all tests provide them.
        '''
        return {'error': 'Benchmark has not been set up correctly.'}

