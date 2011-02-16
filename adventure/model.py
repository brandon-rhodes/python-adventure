"""Classes representing Adventure game components."""

class Move(object):
    """An entry in the travel table."""

    is_forced = False
    verbs = []
    condition = None
    action = None

    def __repr__(self):
        verblist = [ verb.text for verb in self.verbs ]

        c = self.condition[0]
        if c is None:
            condition = ''
        elif c == '%':
            condition = ' %d%% of the time' % self.condition[1]
        elif c == 'not_dwarf':
            condition = ' if not a dwarf'
        elif c == 'carrying':
            condition = ' if carrying %s' % self.condition[1]
        elif c == 'carrying_or_in_room_with':
            condition = ' if carrying or in room with %s' % self.condition[1]
        elif c == 'prop!=':
            condition = ' if prop %d != %d' % self.condition[1:]

        if isinstance(self.action, Room):
            action = 'moves to %r' % (self.action.short_description
                or self.action.long_description[:20]).strip()
        elif isinstance(self.action, Message):
            action = 'prints %r' % self.action.text
        else:
            action = 'special %d' % self.action

        return '<{}{} {}>'.format('|'.join(verblist), condition, action)

class Room(object):
    """A location in the game."""

    long_description = ''
    short_description = ''
    times_described = 0
    visited = False

    is_light = False
    is_forbidden_to_pirate = False
    liquid = None
    trying_to_get_into_cave = False
    trying_to_catch_bird = False
    trying_to_deal_with_snake = False
    lost_in_maze = False
    pondering_dark_room = False
    at_witts_end = False

    def __init__(self):
        self.travel_table = []

    def __repr__(self):
        return '<room {} at {}>'.format(self.n, hex(id(self)))

    @property
    def is_forced(self):
        return self.travel_table and self.travel_table[0].is_forced

    @property
    def is_aboveground(self):
        return 1 <= self.n <= 8

    @property
    def is_before_hall_of_mists(self):
        return self.n < 15

    @property
    def is_after_hall_of_mists(self):
        return self.n >= 15

    @property
    def is_dark(self):
        return not self.is_light

class Word(object):
    """A word that can be used as part of a command."""

    text = None
    kind = None
    default_message = None

    def __init__(self):
        self.synonyms = [ self ]

    def __repr__(self):
        return '<Word {}>'.format(self.text)

    def __eq__(self, text):
        return any( word.text == text for word in self.synonyms )

    def add_synonym(self, other):
        """Every word in a group of synonyms shares the same list."""
        self.synonyms.extend(other.synonyms)
        other.synonyms = self.synonyms

class Object(object):
    """An object in the game, like a grate, or a rod with a rusty star."""

    def __init__(self):
        self.is_fixed = False
        self.is_treasure = False
        self.inventory_message = ''
        self.messages = {}
        self.names = []
        self.prop = 0
        self.rooms = []
        self.starting_rooms = []
        self.is_toting = False
        self.contents = None  # so the bottle can hold things

    def __repr__(self):
        return '<Object %d %s %x>' % (self.n, '/'.join(self.names), id(self))

    def __hash__(self):
        return self.n

    def __eq__(self, other):
        return any( text == other for text in self.names )

    def is_at(self, room):
        return room in self.rooms

    def carry(self):
        self.rooms[:] = []
        self.is_toting = True

    def drop(self, room):
        self.rooms[:] = [ room ]
        self.is_toting = False

    def hide(self):
        self.rooms[:] = []
        self.is_toting = False

    def destroy(self):
        self.hide()

class Message(object):
    """A message for printing."""
    text = ''

    def __str__(self):
        return self.text

class Hint(object):
    """A hint offered if the player loiters in one area too long."""

    turns_needed = 0
    turn_counter = 0
    penalty = 0
    question = None
    message = None
    used = False

    def __init__(self):
        self.rooms = []

class Dwarf(object):
    is_dwarf = True
    is_pirate = False

    def __init__(self, room):
        self.start_at(room)
        self.has_seen_adventurer = False

    def start_at(self, room):
        self.room = room
        self.old_room = room

    def can_move(self, move):
        if not isinstance(move.action, Room):
            return False
        room = move.action
        return (room.is_after_hall_of_mists
                and not room.is_forced
                and not move.condition == ('%', 100))

class Pirate(Dwarf):
    is_dwarf = False
    is_pirate = True
