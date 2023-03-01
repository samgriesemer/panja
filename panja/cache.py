import os
import dill as pickle
from pathlib import Path
from datetime import datetime

# can elect to only update backlink pages (based on modified times) when the user requests
# the backlink buffer i.e. not doing it automatically as they write to files in the wiki.
# Or you could do this, trying to always keep everything up to date at the earliest
# possible moment. Will probably stick to the former approach for now

# IMPLEMENTATION:

## starting with native Panja objects, will likely replace with tighter score Vim-roam
## objects later. Don't think it's worth trying to global these efforts despite the
## similarity between what I'll do here and with the site _beyond_ the caching system,
## which should be able to overlap fine.

## wiki.vim treats cahce as interface for getting items out of the underlying dict. That
## is, if I want a key out of the cached dict, I could call cache.get(key), instead of
## getting the raw dict first after loading the cache and then manually grabbing the key.
## Note also that the cache object only does anything when read or load is called when
## there is a noticeable change on disk (which makes sense). Otherwise in my case here
## calling load() should do nothing if we already have the current state loaded (i.e.
## start with mod_time of -1, load and change to current time. Then only reload when
## mod_time on disk is different from that stored; will always be different if not yet
## loaded).


class Cache:
    def __init__(self, name, path, default=None):
        self.name = name
        self.path = path
        self.default = default

        self.obj = None
        self.file = Path(path, name)
        self.file = self.file.with_suffix(self.file.suffix + ".pkl")
        self.rtime = -1

        Path(path).mkdir(parents=True, exist_ok=True)
        self.file.touch()

        # if not self.file.exists():
        # raise FileNotFoundError('Cache "{}" not found at cache path {}'.format(self.name, self.path))

    def load(self):
        if self.rtime < self.file.stat().st_mtime:
            if self.file.stat().st_size == 0:
                if self.default is not None:
                    self.obj = self.default()
                    return self.obj
                else:
                    return None
            with self.file.open("rb") as f:
                self.obj = pickle.load(f)
            self.rtime = datetime.now().timestamp()
        return self.obj

    def write(self, obj=None):
        if obj is None:
            obj = self.obj
        with self.file.open("wb") as f:
            pickle.dump(obj, f)
