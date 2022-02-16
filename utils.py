from enum import Enum, auto
import os
import json
from pathlib import Path


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

    def clear(self):
        self.contents = ""
        self.show()

    def replace(self, new_contents):
        self.contents = new_contents
        self.show()

    def show(self):
        if self.in_focus():
            clear_screen()
            print(self.contents)


def save_words(save_file, words):
    new_file = not Path(save_file).is_file()
    with open(save_file, 'w+') as f:
        existing_words = [] if new_file else json.load(f)
        new_wordset = set(existing_words).union(set(words))
        json.dump(list(new_wordset), f)