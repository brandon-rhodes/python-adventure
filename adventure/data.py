"""Parse the original PDP ``advent.dat`` file."""

import os
from functools import partial

ADVENT_DAT = os.path.join(os.path.dirname(__file__), 'advent.dat')

class Data(object):
    def __init__(self):
        self.long_descriptions = {}
        self.short_descriptions = {}
        self.object_descriptions = {}
        self.raw_messages = {}
        self.class_messages = {}
        self.magic_messages = {}

def store_message(messages, n, line, *comments):
    """Accumulate a numbered message from one or more lines of data."""
    messages[n] = messages.get(n, '') + line + '\n'

def store_functions(data):
    """Return a dictionary mapping section numbers to storage routines."""
    return {
        1: partial(store_message, data.long_descriptions),
        2: partial(store_message, data.short_descriptions),
        5: partial(store_message, data.object_descriptions),
        6: partial(store_message, data.raw_messages),
        10: partial(store_message, data.class_messages),
        12: partial(store_message, data.magic_messages),
        }

def skip(*args):
    pass

def parse():
    """Read the Adventure data file and return a ``Data`` object."""
    data = Data()
    functions = store_functions(data)
    f = open(ADVENT_DAT, 'r')
    while True:
        section_number = int(f.readline())
        if not section_number:  # no further sections
            break
        store = functions.get(section_number, skip)
        while True:
            fields = [ (int(field) if field.isdigit() else field)
                       for field in f.readline().strip().split('\t') ]
            if fields[0] == '-1':  # end-of-section marker
                break
            store(*fields)
    return data
