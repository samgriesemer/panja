#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import absolute_import

import os

import staticjinja

if __name__ == "__main__":
    searchpaths = [os.path.join(os.getcwd(), 'templates')]
    site = staticjinja.make_site(searchpaths=searchpaths)
    site.render(use_reloader=True)
