"""Parse the original PDP ``advent.dat`` file."""

import os
from .model import Message, Move, Object, Room

ADVENT_DAT = os.path.join(os.path.dirname(__file__), 'advent.dat')

class Data(object):
    def __init__(self):
        self.rooms = {}
        self.vocabulary = {}
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

_last_travel = [0, [0]]  # x and verbs

def section3(data, x, y, *verbs):
    global _last_travel
    if _last_travel[0] == x and _last_travel[1][0] == verbs[0]:
        verbs = _last_travel[1]  # same first verb implies use whole list
    else:
        _last_travel = [x, verbs]

    m, n = divmod(y, 1000)
    mh, mm = divmod(m, 100)

    if m == 0:
        condition = None
    elif 0 < m < 100:
        condition = ('%', m)
    elif m == 100:
        condition = ('not_dwarf')
    elif 100 < m <= 200:
        condition = ('carrying', mm)
    elif 200 < m <= 300:
        condition = ('carrying_or_in_room_with', mm)
    elif 300 < m:
        condition = ('prop!=', mm, mh - 3)

    if n <= 300:
        action = make_object(data.rooms, Room, n)
    elif 300 < n <= 500:
        action = n - 300  # special computed goto?
    else:
        action = make_object(data.messages, Message, n - 500)

    move = Move(verbs, data.vocabulary)
    move.condition = condition
    move.action = action
    data.rooms[x].travel_table.append(move)

def section4(data, n, word, *etc):
    m = n // 1000
    if m == 0:
        data.vocabulary[n] = word

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
    message = make_object(data.messages, Message, n)
    message.text = line

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
