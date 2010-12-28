"""Parse the original PDP ``advent.dat`` file."""

from .model import Hint, Message, Move, Object, Room, Word

class Data(object):
    def __init__(self):
        self.rooms = {}
        self.vocabulary = {}
        self.objects = {}
        self.messages = {}
        self.class_messages = []
        self.hints = {}
        self.magic_messages = {}

    def put_object(self, obj, location):
        room = make_object(self.rooms, Room, location)
        room.objects.append(obj)
        obj.rooms.append(room)

# Helper functions.

def make_object(dictionary, klass, n):
    if n not in dictionary:
        dictionary[n] = obj = klass()
        obj.n = n
    return dictionary[n]

def expand_tabs(segments):
    it = iter(segments)
    line = it.next()
    for segment in it:
        spaces = 8 - len(line) % 8
        line += ' ' * spaces + segment
    return line

def accumulate_message(dictionary, n, line):
    dictionary[n] = dictionary.get(n, '') + line + '\n'

# Knowledge of what each section contains.

def section1(data, n, *etc):
    room = make_object(data.rooms, Room, n)
    room.long_description += expand_tabs(etc) + '\n'

def section2(data, n, line):
    make_object(data.rooms, Room, n).short_description += line + '\n'

def section3(data, x, y, *verbs):
    last_travel = data._last_travel
    if last_travel[0] == x and last_travel[1][0] == verbs[0]:
        verbs = last_travel[1]  # same first verb implies use whole list
    else:
        last_travel = [x, verbs]

    m, n = divmod(y, 1000)
    mh, mm = divmod(m, 100)

    if m == 0:
        condition = (None,)
    elif 0 < m < 100:
        condition = ('%', m)
    elif m == 100:
        condition = ('not_dwarf',)
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

    move = Move()
    if len(verbs) == 1 and verbs[0] == 1:
        move.forced = True
    else:
        move.verbs = [ make_object(data.vocabulary, Word, verb_n)
                       for verb_n in verbs ]
    move.condition = condition
    move.action = action
    data.rooms[x].travel_table.append(move)

def section4(data, n, text, *etc):
    text = text.lower()
    word = make_object(data.vocabulary, Word, n)
    word.texts.append(text)
    word.kind = ['motion', 'object', 'verb', 'random_message'][n // 1000]
    data.vocabulary[text] = word

def section5(data, n, *etc):
    if 1 <= n <= 99:
        data._object = make_object(data.objects, Object, n)
        data._object.inventory_message = expand_tabs(etc)
    else:
        n /= 100
        messages = data._object.messages
        messages[n] = messages.get(n, '') + expand_tabs(etc) + '\n'

def section6(data, n, *etc):
    message = make_object(data.messages, Message, n)
    message.text += expand_tabs(etc) + '\n'

def section7(data, n, room_n, *etc):
    if not room_n:
        return
    obj = make_object(data.objects, Object, n)
    data.put_object(obj, room_n)
    if len(etc):
        obj.immovable = True
        if etc[0] != -1:
            data.put_object(obj, etc[0])  # exists two places, like grate

def section8(data, word_n, message_n):
    if not message_n:
        return
    word = make_object(data.vocabulary, Word, word_n)
    message = make_object(data.messages, Message, message_n)
    word.default_message = message

def section9(data, bit, *nlist):
    name = ['is_light', 'has_water', 'has_oil', 'is_avoided_by_pirate',
            'trying_to_get_into_cave', 'trying_to_catch_bird',
            'trying_to_deal_with_snake', 'lost_in_maze',
            'pondering_dark_room', 'at_witts_end'][bit]
    for n in nlist:
        obj = make_object(data.rooms, Room, n)
        setattr(obj, name, True)

def section10(data, score, line, *etc):
    data.class_messages.append((score, line))

def section11(data, n, turns, penalty, question_n, message_n):
    hint = make_object(data.hints, Hint, n)
    hint.turns = turns
    hint.penalty = penalty
    hint.question = make_object(data.messages, Message, question_n)
    hint.message = make_object(data.messages, Message, message_n)

def section12(data, n, line):
    accumulate_message(data.magic_messages, n, line)

# Process every section of the file in turn.

def parse(data, datafile):
    """Read the Adventure data file and return a ``Data`` object."""
    data._last_travel = [0, [0]]  # x and verbs used by section 3

    while True:
        section_number = int(datafile.readline())
        if not section_number:  # no further sections
            break
        store = globals().get('section%d' % section_number)
        while True:
            fields = [ (int(field) if field.isdigit() else field)
                       for field in datafile.readline().strip().split('\t') ]
            if fields[0] == '-1':  # end-of-section marker
                break
            store(data, *fields)

    del data._last_travel  # state used by section 3
    del data._object       # state used by section 5
    return data
