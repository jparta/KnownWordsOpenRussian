from pynput.keyboard import Key, KeyCode
import grequests

from abc import ABC, abstractmethod
from typing import Optional, Callable, final
from enum import Enum, auto
import math
from time import sleep

from utils import State, Screen, total_from_response, words_from_response, save_words
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
        self.INFO_STR = strings.instructions(super(), self)
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
    TIME_TO_SIT_ON_LAST_RESPONSE = 1.0

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
        self.fetched_words = []
        self.requests_sent = False
        self.words_index = 0
        self.saved_words = []
        self.response_callback = self.response_received
        self.give_proficiency_prompt()

    def _activate(self):
        pass

    def send_first_request(self):
        params = {'level': self.selected_proficiency,
                  'lang': self.config.LANG}
        req = grequests.get(self.config.API_URL_BASE, params=params, callback=self.response_callback)
        prompt = strings.words_fetch_info(self.selected_proficiency)
        self.screen.replace(prompt)
        req.send()

    def send_request_batch(self, total_length, page_size, offset=None):
        offset = 0 if offset is None else offset
        num_requests = math.ceil((total_length - offset) / page_size)
        requests_to_send = []
        for i in range(num_requests):
            params = {'start': offset + i * page_size,
                      'level': self.selected_proficiency,
                      'lang': self.config.LANG}
            req = grequests.get(self.config.API_URL_BASE, params=params, callback=self.response_callback)
            requests_to_send.append(req)
        grequests.map(requests_to_send)

    def response_received(self, resp, *args, **kwargs):
        if self.substate is not self.SubState.FETCH:
            return
        new_words = words_from_response(resp)
        self.fetched_words.extend(new_words)

        total_length = total_from_response(resp)
        prompt = strings.words_fetch_info(self.selected_proficiency,
                                          num_fetched=len(self.fetched_words),
                                          total_num=total_length)
        self.screen.replace(prompt, slow_down=True)
        if not self.requests_sent:
            self.requests_sent = True
            # First response, to find out pagination variables
            # Send the rest of the requests
            page_size = len(new_words)
            offset = len(new_words)
            if len(new_words) < total_length:
                # We need more requests
                self.send_request_batch(total_length=total_length,
                                        page_size=page_size,
                                        offset=offset)
        # State check prevents a kind of race condition where this function is being executed by two instances
        # at the same time. The second instance to enter the function would cause the word count condition
        # to be fulfilled, and both instances would enter the if-statement's body.
        if self.substate is self.SubState.FETCH and \
                len(self.fetched_words) == total_from_response(resp):
            self.substate = self.SubState.DECIDE
            prompt = strings.words_fetch_info(self.selected_proficiency,
                                              num_fetched=len(self.fetched_words),
                                              total_num=total_length)
            self.screen.replace(prompt, slow_down=False)
            sleep(self.TIME_TO_SIT_ON_LAST_RESPONSE)
            self.give_word_prompt()

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
            self.substate = self.SubState.FETCH
            self.send_first_request()
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
