from os.path import exists, expanduser, join
from functools import lru_cache
import os
import json


def storage_path():
    home = expanduser("~")
    return os.environ.get("SHOP_STORAGE_PATH", join(home, "dkstudio-config.json"))


@lru_cache(1)
def read():
    path = storage_path()
    if exists(path):
        return json.load(open(storage_path(), "r"))
    return {}


def refresh():
    read.cache_clear()


def write():
    current = read()
    json.dump(current, open(storage_path(), "w"), indent=2)


def get(key, default=None):
    if key not in read():
        # set default value
        set(key, default)
        return default
    return read().get(key, default)


def set(key, value):
    read()[key] = value
    write()


def update(params):
    read().update(params)
    write()
