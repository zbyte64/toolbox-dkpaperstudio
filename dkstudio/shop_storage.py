from os.path import exists, expanduser, join
from functools import lru_cache
import os
import json
import shutil

from dotenv import load_dotenv


load_dotenv()

class NOT_SET:
    pass

def storage_dir() -> str:
    home = expanduser("~")
    return os.environ.get("SHOP_STORAGE_DIR", join(home, "dkstudio-toolbox-storage"))


def storage_path() -> str:
    home = expanduser("~")
    return os.environ.get("SHOP_STORAGE_PATH", join(home, "dkstudio-config.json"))


@lru_cache(1)
def read() -> dict: 
    path = storage_path()
    if exists(path):
        return json.load(open(storage_path(), "r"))
    return {}


def refresh():
    read.cache_clear()


def write():
    current = read()
    json.dump(current, open(storage_path(), "w"), indent=2)


def has(key: str):
    return key in read()


def get(key: str, default=NOT_SET):
    if default is not NOT_SET and not has(key):
        # set default value
        set(key, default)
        return default
    return read().get(key)


def set(key: str, value):
    read()[key] = value
    write()


def update(params: dict):
    read().update(params)
    write()

def persist(namespace: str, id: str, obj):
    dest = os.path.join(storage_dir(), namespace, id + '.json')
    dest_dir = os.path.split(dest)[0]
    os.makedirs(dest_dir, exist_ok=True)
    json.dump(obj, open(dest, 'w'), indent=2)

def select_keys(namespace: str):
    dest_dir = os.path.join(storage_dir(), namespace)
    if not os.path.exists(dest_dir):
        return []
    return list(filter(lambda x: x.endswith('.json'), os.listdir(dest_dir)))

def select(namespace: str, id: str):
    dest = os.path.join(storage_dir(), namespace, id + '.json')
    if not os.path.exists(dest):
        return None
    return json.load(open(dest, 'r'))