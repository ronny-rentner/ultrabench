import subprocess
import selenium
from selenium import webdriver
import rich.pretty, rich.repr

class ChromeOptions(webdriver.ChromeOptions):
    def __str__(self):
        return rich.pretty.pretty_repr(self.__dict__)
        #return json.dumps(self.chrome.capabilities, sort_keys=True, indent=4)

class Chrome():
    def __init__(self, *, driver_path=None, driver_options={}, remote_debugging_port=9222,
            browser_path=None, browser_options=None, experimental_options=None, extra_arguments=None, **kwargs):

        self.driver_path = driver_path
        self.driver_options = driver_options
        self.remote_debugging_port = remote_debugging_port

        self.browser_process = None
        self.browser_path = browser_path
        self.browser_options = browser_options or []

        self.experimental_options = experimental_options or {}

        self.extra_arguments = extra_arguments or []

    def start(self):

        self.start_browser()
        self.start_driver()

        size = self.chrome.get_window_size()
        #print(self)
        print("Window size: width = {}px, height = {}px".format(size["width"], size["height"]))
        return self.chrome

    def start_browser(self):
        cmd_line = [self.browser_path] + self.browser_options + self.extra_arguments
        print("Starting Chrome with command line:", cmd_line)
        self.browser_process = subprocess.Popen(cmd_line)

    def stop_browser(self):
        if not self.browser_process:
            print("No known Chrome browser process exists, cannot stop.")
            return
        print(f"Killing Chrome browser process with PID {self.browser_process.pid}.")
        #self.browser_process.kill()

    def start_driver(self):
        self.chrome = webdriver.Chrome(service_args=self.driver_options, options=self.prepare_browser_options(), executable_path=self.driver_path)

    def stop_driver(self):
        try:
            for handle in self.chrome.window_handles:
                self.chrome.switch_to.window(handle)
                self.chrome.close()
        except selenium.common.exceptions.WebDriverException:
            pass

    def stop(self):
        self.stop_driver()
        self.stop_browser()

    def prepare_browser_options(self):
        options = ChromeOptions()
        options.binary_location = self.browser_path

        for option in self.browser_options + self.extra_arguments:
            options.add_argument(option)

        for option, value in self.experimental_options.items():
            options.add_experimental_option(option, value)

        return options

    def __getattr__(self, name):
        # Forward everything to the webdriver instance
        if name is not 'chrome' and hasattr(self, 'chrome') and self.chrome:
            return getattr(self.chrome, name)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __str__(self):
        return rich.pretty.pretty_repr(self.__dict__)
        #return json.dumps(self.chrome.capabilities, sort_keys=True, indent=4)
