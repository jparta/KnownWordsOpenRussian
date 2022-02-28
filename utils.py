from enum import Enum, auto
import os
import json
from pathlib import Path
import time


class Status(Enum):
    ACTIVE = auto()
    INACTIVE = auto()


class State(Enum):
    INFO = auto()
    MENU = auto()
    WORDS = auto()
    SAVE = auto()
    EXIT = auto()


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


class Screen:
    def __init__(self, in_focus):
        self.in_focus = in_focus
        self.contents = ""
        self.slow_down_interval = 0.1
        self.last_updated = None

    def can_update(self, slow_down):
        if not self.in_focus():
            return False
        elif not slow_down or self.last_updated is None:
            return True
        elif slow_down:
            elapsed = time.time() - self.last_updated
            return elapsed >= self.slow_down_interval

    def clear(self, slow_down=False):
        self.contents = ""
        self.show(slow_down)

    def replace(self, new_contents, slow_down=False):
        self.contents = new_contents
        self.show(slow_down)

    def show(self, slow_down=False):
        if self.can_update(slow_down):
            clear_screen()
            print(self.contents)
            self.last_updated = time.time()


def save_words(save_file, words):
    new_file = not Path(save_file).is_file()
    with open(save_file, 'w+') as f:
        existing_words = [] if new_file else json.load(f)
        new_wordset = set(existing_words).union(set(words))
        json.dump(list(new_wordset), f)


def total_from_response(resp):
    data = resp.json()
    total = data['result']['total']
    return total


def words_from_response(resp):
    data = resp.json()
    entries = data['result']['entries']
    words = [e['bare'] for e in entries]
    return words
