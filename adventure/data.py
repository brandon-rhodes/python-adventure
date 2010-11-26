"""Parse the original PDP ``advent.dat`` file."""

import os
import random
from .model import Move, Object, Room

ADVENT_DAT = os.path.join(os.path.dirname(__file__), 'advent.dat')

class Data(object):
    def __init__(self):
        self.rooms = {}
        self.objects = {}
        self.messages = {}
        self.class_messages = []
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

def section3(data, x, y, *verbs):
    m, n = divmod(y, 1000)
    mh, mm = divmod(m, 100)

    if m == 0:
        condition = lambda(state): True
    elif 0 < m < 100:
        condition = lambda(state): random.randint(0, 100) < m
    elif m == 100:
        condition = lambda(state): not state.is_dwarf()
    elif 100 < m <= 200:
        condition = lambda(state): state.is_carrying(mm)
    elif 200 < m <= 300:
        condition = lambda(s): (s.is_carrying(mm) or s.in_room_with(mm))
    elif 300 < m:
        condition = lambda(state): state.prop[mm] != mh - 3

    if n <= 300:
        action = lambda(state): state.move_to(n)
    elif 300 < n <= 500:
        action = lambda(state): state.goto(n - 300)
    else:
        action = lambda(state): state.print_message(n - 500)

    move = Move(verbs)
    move.condition = condition
    move.action = action
    data.rooms[x].travel_table.append(move)

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

def section10(data, score, line, *etc):
    data.class_messages.append((score, line))

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
