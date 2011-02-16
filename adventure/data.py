"""Parse the original PDP ``advent.dat`` file."""

from operator import attrgetter
from .model import Hint, Message, Move, Object, Room, Word

# The Adventure data file knows only the first five characters of each
# word in the game, so we have to know the full verion of each word.

long_words = { w[:5]: w for w in """upstream downstream forest
forward continue onward return retreat valley staircase outside building stream
cobble inward inside surface nowhere passage tunnel canyon awkward
upward ascend downward descend outdoors barren across debris broken
examine describe slabroom depression entrance secret bedquilt plover
oriental cavern reservoir office headlamp lantern pillow velvet fissure tablet
oyster magazine spelunker dwarves knives rations bottle mirror beanstalk
stalactite shadow figure drawings pirate dragon message volcano geyser
machine vending batteries carpet nuggets diamonds silver jewelry treasure
trident shards pottery emerald platinum pyramid pearl persian spices capture
release discard mumble unlock nothing extinguish placate travel proceed
continue explore follow attack strike devour inventory detonate ignite
blowup peruse shatter disturb suspend sesame opensesame abracadabra
shazam excavate information""".split() }

class Data(object):
    def __init__(self):
        self.rooms = {}
        self.vocabulary = {}
        self.objects = {}
        self.messages = {}
        self.class_messages = []
        self.hints = {}
        self.magic_messages = {}

    def referent(self, word):
        if word.kind == 'noun':
            return self.objects[word.n % 1000]

# Helper functions.

def make_object(dictionary, klass, n):
    if n not in dictionary:
        dictionary[n] = obj = klass()
        obj.n = n
    return dictionary[n]

def expand_tabs(segments):
    it = iter(segments)
    line = next(it)
    for segment in it:
        spaces = 8 - len(line) % 8
        line += ' ' * spaces + segment
    return line

def accumulate_message(dictionary, n, line):
    dictionary[n] = dictionary.get(n, '') + line + '\n'

# Knowledge of what each section contains.

def section1(data, n, *etc):
    room = make_object(data.rooms, Room, n)
    if not etc[0].startswith('>$<'):
        room.long_description += expand_tabs(etc) + '\n'

def section2(data, n, line):
    make_object(data.rooms, Room, n).short_description += line + '\n'

def section3(data, x, y, *verbs):
    last_travel = data._last_travel
    if last_travel[0] == x and last_travel[1][0] == verbs[0]:
        verbs = last_travel[1]  # same first verb implies use whole list
    else:
        data._last_travel = [x, verbs]

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
        action = n  # special computed goto
    else:
        action = make_object(data.messages, Message, n - 500)

    move = Move()
    if len(verbs) == 1 and verbs[0] == 1:
        move.is_forced = True
    else:
        move.verbs = [ make_object(data.vocabulary, Word, verb_n)
                       for verb_n in verbs if verb_n < 100 ] # skip bad "109"
    move.condition = condition
    move.action = action
    data.rooms[x].travel_table.append(move)

def section4(data, n, text, *etc):
    text = text.lower()
    text = long_words.get(text, text)
    word = make_object(data.vocabulary, Word, n)
    if word.text is None:  # this is the first word with index "n"
        word.text = text
    else:  # there is already a word sitting at "n", so create a synonym
        original = word
        word = Word()
        word.n = n
        word.text = text
        original.add_synonym(word)
    word.kind = ['travel', 'noun', 'verb', 'snappy_comeback'][n // 1000]
    if word.kind == 'noun':
        n %= 1000
        obj = make_object(data.objects, Object, n)
        obj.names.append(text)
        obj.is_treasure = (n >= 50)
        data.objects[text] = obj
    if text not in data.vocabulary:  # since duplicate names exist
        data.vocabulary[text] = word

def section5(data, n, *etc):
    if 1 <= n <= 99:
        data._object = make_object(data.objects, Object, n)
        data._object.inventory_message = expand_tabs(etc)
    else:
        n /= 100
        messages = data._object.messages
        if etc[0].startswith('>$<'):
            more = ''
        else:
            more = expand_tabs(etc) + '\n'
        messages[n] = messages.get(n, '') + more

def section6(data, n, *etc):
    message = make_object(data.messages, Message, n)
    message.text += expand_tabs(etc) + '\n'

def section7(data, n, room_n, *etc):
    if not room_n:
        return
    obj = make_object(data.objects, Object, n)
    room = make_object(data.rooms, Room, room_n)
    obj.drop(room)
    if len(etc):
        if etc[0] == -1:
            obj.is_fixed = True
        else:
            room2 = make_object(data.rooms, Room, etc[0])
            obj.rooms.append(room2)  # exists two places, like grate
    obj.starting_rooms = list(obj.rooms)  # remember where things started

def section8(data, word_n, message_n):
    if not message_n:
        return
    word = make_object(data.vocabulary, Word, word_n + 2000)
    message = make_object(data.messages, Message, message_n)
    for word2 in word.synonyms:
        word2.default_message = message

def section9(data, bit, *nlist):
    for n in nlist:
        room = make_object(data.rooms, Room, n)
        if bit == 0:
            room.is_light = True
        elif bit == 1:
            room.liquid = make_object(data.objects, Object, 22) #oil
        elif bit == 2:
            room.liquid = make_object(data.objects, Object, 21) #water
        elif bit == 3:
            room.is_forbidden_to_pirate = True
        else:
            hint = make_object(data.hints, Hint, bit)
            hint.rooms.append(room)

def section10(data, score, line, *etc):
    data.class_messages.append((score, line))

def section11(data, n, turns_needed, penalty, question_n, message_n):
    hint = make_object(data.hints, Hint, n)
    hint.turns_needed = turns_needed
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
            fields = [ (int(field) if field.lstrip('-').isdigit() else field)
                       for field in datafile.readline().strip().split('\t') ]
            if fields[0] == -1:  # end-of-section marker
                break
            store(data, *fields)

    del data._last_travel  # state used by section 3
    del data._object       # state used by section 5

    data.object_list = sorted(set(data.objects.values()), key=attrgetter('n'))
    #data.room_list = sorted(set(data.rooms.values()), key=attrgetter('n'))
    for obj in data.object_list:
        name = obj.names[0]
        if hasattr(data, name):
            name = name + '2'  # create identifiers like ROD2, PLANT2
        setattr(data, name, obj)

    return data
