from pynput.keyboard import Key, KeyCode

from abc import ABC, abstractmethod
from typing import Optional, Callable, final
from enum import Enum, auto

from utils import State, Screen, save_words
import strings


class StateEventsManager(ABC):
    MENU_KEY = Key.space
    EXIT_KEY = Key.esc

    def __init__(self):
        self._in_focus = False
        self.screen = Screen(self.in_focus)
        self.key_handlers: dict[Key, Callable[[Key], Optional[State]]] = {
            self.MENU_KEY: self.handle_menu_key,
            self.EXIT_KEY: self.handle_exit_key
        }

    def in_focus(self):
        return self._in_focus

    @final
    def activate(self):
        # Update screen contents before activating
        self._activate()
        self._in_focus = True
        self.screen.show()

    @abstractmethod
    def _activate(self):
        ...

    @final
    def deactivate(self):
        self._in_focus = False

    @staticmethod
    def handle_menu_key(_):
        return State.MENU

    @staticmethod
    def handle_exit_key(_):
        return State.EXIT

    def handle_key(self, key: Key) -> Optional[State]:
        if key in self.key_handlers:
            return self.key_handlers[key](key)


class Info(StateEventsManager):
    PROCEED_KEY: Key = Key.enter

    def __init__(self, config):
        super().__init__()
        self.key_handlers[self.PROCEED_KEY] = self.handle_proceed_key
        self.INFO_STR = strings.instructions(Words, super(), self)
        self.screen.replace(self.INFO_STR)

    @staticmethod
    def handle_proceed_key(_):
        return State.WORDS

    def _activate(self):
        pass


class Words(StateEventsManager):
    SAVE_WORD_KEY: Key = Key.up
    DISCARD_WORD_KEY: Key = Key.down
    NEXT_KEY: Key = Key.right
    PREVIOUS_KEY: Key = Key.left
    SELECT_KEY: Key = Key.enter
    SAVE_WORDSET_KEY: KeyCode = KeyCode(char='y')
    DISCARD_WORDSET_KEY: KeyCode = KeyCode(char='n')

    class SubState(Enum):
        PARAMS = auto()
        FETCH = auto()
        DECIDE = auto()
        SAVE = auto()

    INITIAL_SUB_STATE = SubState.PARAMS
    PROFICIENCIES = "A1 A2 B1 B2 C1 C2".split()

    def __init__(self, config):
        super().__init__()
        self.key_handlers[self.SAVE_WORD_KEY] = self.handle_word_saving_key
        self.key_handlers[self.DISCARD_WORD_KEY] = self.handle_word_saving_key
        self.key_handlers[self.NEXT_KEY] = self.handle_proficiency_selection_key
        self.key_handlers[self.PREVIOUS_KEY] = self.handle_proficiency_selection_key
        self.key_handlers[self.SELECT_KEY] = self.handle_proficiency_selection_key
        self.key_handlers[self.SAVE_WORDSET_KEY] = self.handle_wordset_saving_key
        self.key_handlers[self.DISCARD_WORDSET_KEY] = self.handle_wordset_saving_key
        self.config = config
        self.substate = self.INITIAL_SUB_STATE
        self.proficiencies_index = 0
        self.selected_proficiency = ''
        self.fetched_words = ['не', 'что', 'с', 'это', 'у', 'из', 'мочь', 'человек', 'носок', 'изменить']
        self.words_index = 0
        self.saved_words = []

    def _activate(self):
        self.give_proficiency_prompt()

    def send_request(self, proficiency):
        self.substate = self.SubState.FETCH
        self.screen.replace(proficiency)
        self.give_word_prompt()

    def response_received(self, response):
        self.substate = self.SubState.DECIDE

    def give_proficiency_prompt(self, long=True):
        idx = self.proficiencies_index
        if long:
            prompt = strings.language_proficiency_prompt_long(self) + '\n\n\t' + self.PROFICIENCIES[idx]
        else:
            prompt = strings.language_proficiency_prompt_short(self) + '\n\n\t' + self.PROFICIENCIES[idx]
        self.screen.replace(prompt)

    def handle_proficiency_selection_key(self, key):
        if self.substate is not self.SubState.PARAMS:
            return None
        if key == self.SELECT_KEY:
            idx = self.proficiencies_index
            self.selected_proficiency = self.PROFICIENCIES[idx]
            self.substate = self.SubState.DECIDE
            self.give_word_prompt()
            return None
        if key == self.NEXT_KEY:
            self.proficiencies_index += 1
            if self.proficiencies_index >= len(self.PROFICIENCIES):
                self.proficiencies_index = 0
        elif key == self.PREVIOUS_KEY:
            self.proficiencies_index -= 1
            if self.proficiencies_index < 0:
                self.proficiencies_index = len(self.PROFICIENCIES) - 1
        self.give_proficiency_prompt()
        return None

    def give_word_prompt(self):
        next_word = self.fetched_words[self.words_index]
        words_left = len(self.fetched_words) - self.words_index
        prompt = strings.word_decision_prompt(self, words_left) + '\n\n\t' + next_word
        self.screen.replace(prompt)
        self.words_index += 1

    def handle_word_saving_key(self, key):
        words_head_len = 10
        if self.substate is not self.SubState.DECIDE:
            return None
        if self.words_index >= len(self.fetched_words):
            self.substate = self.SubState.SAVE
            prompt = strings.save_wordset_prompt(self, len(self.saved_words), self.saved_words[:words_head_len])
            self.screen.replace(prompt)
            return None
        current_word = self.fetched_words[self.words_index]
        if key == self.SAVE_WORD_KEY:
            self.saved_words.append(current_word)
        self.give_word_prompt()
        return None

    def handle_wordset_saving_key(self, key):
        if self.substate is not self.SubState.SAVE:
            return None
        if key == self.SAVE_WORDSET_KEY:
            save_words(self.config.SAVE_FILE, self.saved_words)
        return State.EXIT
