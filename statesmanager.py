from pynput.keyboard import Key, KeyCode, Listener

from typing import Optional, Union

import config
from utils import State
from stateeventsmanagers import StateEventsManager, Info, Words


class StatesManager:
    _event_managers: dict[State, StateEventsManager] = {
        State.INFO:  Info,
        State.WORDS: Words,
    }

    def __init__(self, initial_state: State):
        self.listener: Listener = None
        self.event_managers = self.instantiated_event_managers()
        self.state: State = initial_state
        self.change_state(initial_state)

    def instantiated_event_managers(self):
        return {k: m(config) for k, m in self._event_managers.items()}

    def start_listening(self):
        with Listener(on_press=self.handle_key) as listener:
            self.listener = listener
            listener.join()

    def change_state(self, new_state: State):
        if new_state == State.EXIT:
            self.listener.stop()
            return
        if new_state not in self.event_managers:
            print("The requested state has not been implemented.")
            return
        old_manager = self.event_managers[self.state]
        old_manager.deactivate()
        self.state = new_state
        new_manager = self.event_managers[self.state]
        new_manager.activate()

    def handle_key(self, key: Optional[Union[Key, KeyCode]]):
        next_state = self.event_managers[self.state].handle_key(key)
        if next_state is not None:
            self.change_state(next_state)
