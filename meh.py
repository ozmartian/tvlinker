#!/usr/bin/env python3

import time
from functools import wraps

from PyQt5.QtCore import QThread


class Runner(QThread):
    def __init__(self, target, *args, **kwargs):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.target(*self.args, **self.kwargs)
        print('ThreadID: %s' % self.currentThread())


def run(func):
    @wraps(func)
    def async_func(*args, **kwargs):
        runner = Runner(func, *args, **kwargs)
        func.__runner = runner
        runner.start()

    return async_func


if __name__ == '__main__':
    @run
    def another_test():
        time.sleep(3)
        print('TEST2')

    @run
    def test():
        time.sleep(1)
        print('TEST1')

    test()
    another_test()
    time.sleep(2)
    print('END')
