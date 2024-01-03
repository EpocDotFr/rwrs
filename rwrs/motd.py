from types import SimpleNamespace
from enum import Enum
import os

FILENAME = 'motd'


class Types(Enum):
    Success = 'success'
    Error = 'error'
    Info = 'info'


def remove():
    try:
        os.remove(FILENAME)

        return True
    except FileNotFoundError:
        return False


def save(type_, message):
    type_ = Types(type_).value

    with open(FILENAME, 'w', encoding='utf-8') as f:
        f.write('\n'.join((type_, message)))


def get():
    try:
        with open(FILENAME, 'r', encoding='utf-8') as f:
            ret = f.read().splitlines()
    except FileNotFoundError:
        return None

    if not ret or len(ret) <= 1:
        return None

    return SimpleNamespace(
        type=Types(ret[0]).value,
        message='\n'.join(ret[1:])
    )
