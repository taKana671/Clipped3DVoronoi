import time

import yaml


CONFIG_FILE = 'clipping_config.yaml'


def read_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

    except FileNotFoundError:
        print(f'No such file: {CONFIG_FILE}')
    else:
        return config


class clock:

    def __init__(self):
        self.fmt = 'Elapsed time: {elapsed:0.8f}s'

    def __call__(self, func):
        def clocked(*args, **kwargs):
            start = time.perf_counter()
            func(*args, **kwargs)
            print(self.fmt.format(elapsed=time.perf_counter() - start))

        return clocked