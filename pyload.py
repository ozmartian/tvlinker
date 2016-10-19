#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from urllib.parse import urljoin, urlencode
from urllib.request import urlopen


class PyloadConfig:
    host = None
    username = None
    password = None


class PyloadConnection:
    def __init__(self, config: PyloadConfig):
        self.url_base = urljoin('http://%s' % config.host, 'api/')
        username, password = config.username, config.password
        self.session = self._call('login', {'username': username, 'password': password}, False)

    def _call(self, name, args={}, encode=True):
        url = urljoin(self.url_base, name)
        if encode:
            data = {}
            for key, value in args.items():
                data[key] = json.dumps(value)
        else:
            data = args
        if hasattr(self, 'session'):
            data['session'] = self.session
        post = urlencode(data).encode('utf-8')
        return json.loads(urlopen(url, post).read().decode('utf-8'))

    def __getattr__(self, name):
        def wrapper(**kargs):
            return self._call(name, kargs)
        return wrapper
