import grequests
from statesmanager import StatesManager
from config import INITIAL_STATE

mgr = StatesManager(INITIAL_STATE)
mgr.start_listening()
