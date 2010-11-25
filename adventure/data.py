"""Parse the original PDP ``advent.dat`` file."""

import os
from .model import Room, Object

ADVENT_DAT = os.path.join(os.path.dirname(__file__), 'advent.dat')

class Data(object):
    def __init__(self):
        self.rooms = {}
        self.objects = {}
        self.messages = {}
        self.class_messages = {}
        self.magic_messages = {}

# Helper functions.

def make_object(dictionary, klass, n):
    if n not in dictionary:
        dictionary[n] = klass()
    return dictionary[n]

def accumulate_message(dictionary, n, line):
    dictionary[n] = dictionary.get(n, '') + line + '\n'

# Knowledge of what each section contains.

def section1(data, n, line, *etc):
    make_object(data.rooms, Room, n).long_description += line + '\n'

def section2(data, n, line, *etc):
    make_object(data.rooms, Room, n).short_description += line + '\n'

def section5(data, n, line, *etc):
    global _object
    if 1 <= n <= 99:
        _object = make_object(data.objects, Object, n)
        _object.inventory_message = line
    else:
        n /= 100
        messages = _object.prop_messages
        messages[n] = messages.get(n, '') + line + '\n'

def section6(data, n, line, *etc):
    accumulate_message(data.messages, n, line)

def section10(data, n, line, *etc):
    accumulate_message(data.class_messages, n, line)

def section12(data, n, line, *etc):
    accumulate_message(data.magic_messages, n, line)

def skip(*args):
    pass

# Process every section of the file in turn.

def parse():
    """Read the Adventure data file and return a ``Data`` object."""
    data = Data()
    f = open(ADVENT_DAT, 'r')
    while True:
        section_number = int(f.readline())
        if not section_number:  # no further sections
            break
        store = globals().get('section%d' % section_number, skip)
        while True:
            fields = [ (int(field) if field.isdigit() else field)
                       for field in f.readline().strip().split('\t') ]
            if fields[0] == '-1':  # end-of-section marker
                break
            store(data, *fields)
    return data
