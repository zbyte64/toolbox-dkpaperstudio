from os.path import exists, expanduser, join, abspath, split
from functools import lru_cache
import os
import json
import shutil
from typing import Any

from dotenv import load_dotenv


load_dotenv()


class NOT_SET:
    pass


def src_dir() -> str:
    return split(abspath(__file__))[0]


def root_dir() -> str:
    return split(src_dir())[0]


def storage_dir() -> str:
    home = root_dir()
    return os.environ.get("SHOP_STORAGE_DIR", join(home, "dkstudio-toolbox-storage"))


def storage_path() -> str:
    home = root_dir()
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
    dest = os.path.join(storage_dir(), namespace, f"{id}.json")
    dest_dir = os.path.split(dest)[0]
    os.makedirs(dest_dir, exist_ok=True)
    json.dump(obj, open(dest, "w"), indent=2)


def select_keys(namespace: str):
    dest_dir = os.path.join(storage_dir(), namespace)
    if not os.path.exists(dest_dir):
        return []
    return list(
        map(
            lambda x: x[: -len(".json")],
            filter(lambda x: x.endswith(".json"), os.listdir(dest_dir)),
        )
    )


def select(namespace: str, id: str):
    dest = os.path.join(storage_dir(), namespace, f"{id}.json")
    if not os.path.exists(dest):
        return None
    return json.load(open(dest, "r"))


def write_file_metadata(path: str, data: Any):
    cp = path + ".dkps.json"
    json.dump(data, open(cp, "w"), indent=2)


def read_file_metadata(path: str, default=None) -> Any:
    cp = path + ".dkps.json"
    if not os.path.exists(cp):
        return default
    return json.load(open(cp, "r"))
