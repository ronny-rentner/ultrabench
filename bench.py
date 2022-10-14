#!/usr/bin/env python

__version__ = 0.1

import rich
print = rich.print
import rich_click
import ultraimport

# local, relative imports
config = ultraimport('__dir__/config.py')
log = ultraimport('__dir__/utils/OneLogger.py', 'OneLogger')()
BrowserBench = ultraimport('__dir__/browserbench.py', 'BrowserBench')


def run_for_browser(name, config):
    if name not in config:
        raise Exception(f"No config found for browser '{name}'. Make sure to have it set up in config.py.")

    config = config[name]

    cli_options = config.get('always_set', '')

    for variant_name, variant_options in config.get('variants', {}).items():
        print(f"{name} {cli_options} {variant_options}")

    #log.info("Running {} with {}", name, config)

def main():
    log.info('Running browser benchmark v{}', __version__)

    print(rich.panel.Panel(f'ultrabench v{__version__}', expand=False, highlight=True, ))
    print(config.chrome)


if __name__ == '__main__':
    main()
