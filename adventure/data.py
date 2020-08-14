# -*- coding: utf-8 -*-

"""Parse the original PDP ``advent.dat`` file.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""
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
    """Handle record from “Section 1: long form descriptions”.

    Section 1: long form descriptions. Each line contains a location
    number, a TAB, and a line of text. The set of (necessarily adjacent)
    lines whose numbers are X form the long description of location X.

    """
    room = make_object(data.rooms, Room, n)
    if not etc[0].startswith('>$<'):
        room.long_description += expand_tabs(etc) + '\n'

def section2(data, n, line):
    """Handle record from “Section 2: short form descriptions”.

    Section 2: short form descriptions. Same format as long form.  Not
    all places have short descriptions.

    """
    make_object(data.rooms, Room, n).short_description += line + '\n'

def section3(data, x, y, *verbs):
    """Handle record from “Section 3: travel table”.

    Section 3: travel table. Each line contains a location number (X), a
    second location number (Y), and a list of motion numbers (see
    section 4).

    Each motion represents a verb which will go to Y if currently at
    X. Y, in turn, is interpreted as follows. Let M=Y/1000, N=Y MOD
    1000.

        If N<=300: it is the location to go to.

        If 300<N<=500: N-300 is used in a computed GOTO to a
        section of special code.

        If N>500: message N-500 from section 6 is printed, and he
        stays wherever he is.

    Meanwhile, M specifies the conditions on the motion.

        If M=0: it's unconditional.
        If 0<M<100: it is done with M% probability.
        If M=100: unconditional, but forbidden to dwarves.
        If 100<M<=200: he must be carrying object M-100.
        If 200<M<=300: must be carrying or in same room as M-200.
        If 300<M<=400: PROP(M MOD 100) must *not* be 0.
        If 400<M<=500: PROP(M MOD 100) must *not* be 1.
        If 500<M<=600: PROP(M MOD 100) must *not* be 2, etc.

    If the condition (if any) is not met, then the next *different*
    "destination" value is used (unless it fails to meet *its*
    conditions, in which case the next is found, etc.).  Typically, the
    next dest will be for one of the same verbs, so that its only use is
    as the alternate destination for those verbs. For instance:

        15	110022	29	31	34	35	23	43
        15	14	29

    This says that, from LOC 15, any of the verbs 29, 31, etc., will
    take him to 22 if he's carrying object 10, and otherwise will go to
    14.

        11	303008	49
        11	9	50

    This says that, from 11, 49 takes him to 8 unless PROP(3)=0, in
    which case he goes to 9. Verb 50 takes him to 9 regardless of
    PROP(3).

    """
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
    """Handle record from “Section 4: vocabulary”.

    Section 4: vocabulary. Each line contains a number (N), a TAB, and a
    five-letter word. Call M=N/1000. If M=0, then the word is a motion
    verb for use in travelling (see section 3). Else, if M=1, the word
    is an object. Else, if M=2, the word is an action verb (such as
    "CARRY" or "ATTACK"). Else, if M=3, the word is a special case verb
    (such as "DIG") and N MOD 1000 is an index into section 6. Objects
    from 50 to (currently, anyway) 79 are considered treasures (for
    pirate, closeout).

    """
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
    """Handle record from “Section 5: object descriptions”.

    Section 5: object descriptions. Each line contains a number (N), a
    TAB, and a message. If N is from 1 to 100, the message is the
    "inventory" message for object N. Otherwise, N should be 000, 100,
    200, etc., and the message should be the description of the
    preceding object when its PROP value is N/100. The N/100 is used
    only to distinguish multiple messages from multi-line messages; the
    PROP info actually requires all messages for an object to be present
    and consecutive.  Properties which produce no message should be
    given the message ">$<".

    """
    if 1 <= n <= 99:
        data._object = make_object(data.objects, Object, n)
        data._object.inventory_message = expand_tabs(etc)
    else:
        n //= 100
        messages = data._object.messages
        if etc[0].startswith('>$<'):
            more = ''
        else:
            more = expand_tabs(etc) + '\n'
        messages[n] = messages.get(n, '') + more

def section6(data, n, *etc):
    """Handle record from “Section 6: arbitrary messages”.

    Section 6: arbitrary messages. Same format as sections 1, 2, and 5,
    except the numbers bear no relation to anything (except for special
    verbs in section 4).

    """
    message = make_object(data.messages, Message, n)
    message.text += expand_tabs(etc) + '\n'

def section7(data, n, room_n, fixed=None):
    """Handle record from “Section 7: object locations”.

    Section 7: object locations. Each line contains an object number and
    its initial location (zero (or omitted) if none).  If the object is
    immovable, the location is followed by a "-1". If it has two
    locations (e.g. the grate) the first location is followed with the
    second, and the object is assumed to be immovable.

    """
    obj = make_object(data.objects, Object, n)
    if room_n:
        room = make_object(data.rooms, Room, room_n)
        obj.drop(room)
    if fixed is not None:
        if fixed == -1:
            obj.is_fixed = True
        else:
            room2 = make_object(data.rooms, Room, fixed)
            obj.rooms.append(room2)  # exists two places, like grate
    obj.starting_rooms = list(obj.rooms)  # remember where things started

def section8(data, word_n, message_n):
    """Handle record from “Section 8: action defaults”.

    Section 8: action defaults. Each line contains an "action-verb"
    number and the index (in section 6) of the default message for the
    verb.

    """
    if not message_n:
        return
    word = make_object(data.vocabulary, Word, word_n + 2000)
    message = make_object(data.messages, Message, message_n)
    for word2 in word.synonyms:
        word2.default_message = message

def section9(data, bit, *nlist):
    """Handle record from “Section 9: liquid assets, etc.”.

    Section 9: liquid assets, etc. Each line contains a number (N) and
    up to 20 location numbers. Bit N (where 0 is the units bit) is set
    in COND(LOC) for each LOC given. The COND bits currently assigned
    are:

        0: light
        1: if bit 2 is on: on for oil, off for water
        2: liquid asset, see bit 1
        3: pirate doesn't go here unless following player

    Other bits are used to indicate areas of interest to "hint"
    routines:

        4: trying to get into cave
        5: trying to catch bird
        6: trying to deal with snake
        7: lost in maze
        8: pondering dark room
        9: at Witt's End

    COND(LOC) is set to 2, overriding all other bits, if LOC has forced
    motion.

    """
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
    """Handle record from “Section 10: class messages”.

    Section 10: class messages. Each line contains a number (N), a TAB,
    and a message describing a classification of player. The scoring
    section selects the appropriate message, where each message is
    considered to apply to players whose scores are higher than the
    previous N but not higher than this N. Note that these scores
    probably change with every modification (and particularly expansion)
    of the program.

    """
    data.class_messages.append((score, line))

def section11(data, n, turns_needed, penalty, question_n, message_n):
    """Handle record from “Section 11: hints”.

    Section 11: hints. Each line contains a hint number (corresponding
    to a COND bit, see section 9), the number of turns he must be at the
    right LOC(s) before triggering the hint, the points deducted for
    taking the hint, the message number (section 6) of the question, and
    the message number of the hint. These values are stashed in the
    "HINTS" array.

    HNTMAX is set to the max hint number (<= HNTSIZ). Numbers 1-3 are
    unusable since COND bits are otherwise assigned, so 2 is used to
    remember if he's read the clue in the repository, and 3 is used to
    remember whether he asked for instructions (gets more turns, but
    loses points).

    """
    hint = make_object(data.hints, Hint, n)
    hint.turns_needed = turns_needed
    hint.penalty = penalty
    hint.question = make_object(data.messages, Message, question_n)
    hint.message = make_object(data.messages, Message, message_n)

def section12(data, n, line):
    """Handle record from “Section 12: magic messages”.

    Section 12: magic messages. Identical to section 6 except put in a
    separate section for easier reference. Magic messages are used by
    the startup, maintenance mode, and related routines.

    """
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
