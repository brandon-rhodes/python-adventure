"""Classes representing Adventure game components."""

class Move(object):
    """An entry in the travel table."""

    def __init__(self, verbs):
        self.verbs = verbs

    def __repr__(self):
        verblist = [ verb.text for verb in self.verbs ]

        if not self.condition:
            condition = ''
        elif self.condition[0] == '%':
            condition = ' %d%% of the time' % self.condition[1]
        elif self.condition[0] == 'not_dwarf':
            condition = ' if not a dwarf'
        elif self.condition[0] == 'carrying':
            condition = ' if carrying %s'
        elif self.condition[0] == 'carrying_or_in_room_with':
            condition = ' if carrying or in room with %s'
        elif self.condition[0] == 'prop!=':
            condition = ' if prop %d != %d' % self.condition[1:]
        else:
            condition = ' if X'

        if isinstance(self.action, Room):
            action = 'moves to %r' % self.action.description
        elif isinstance(self.action, Message):
            action = 'prints %r' % self.action.text
        else:
            action = 'special %d' % self.action

        return '<%s%s %s>' % ('|'.join(verblist), condition, action)

    def test_condition(self, data):
        pass

    def take_action(self, data):
        if isinstance(self.action, Room):
            data.room = self.action
            print data.room.description
        elif isinstance(self.action, Message):
            print self.action.text
        else:
            print 'special %d' % self.action

class Room(object):
    """A location in the game."""

    long_description = u''
    short_description = u''
    times_described = 0
    visited = False

    is_light = False
    has_water = False
    has_oil = False
    is_avoided_by_pirate = False
    trying_to_get_into_cave = False
    trying_to_catch_bird = False
    trying_to_deal_with_snake = False
    lost_in_maze = False
    pondering_dark_room = False
    at_witts_end = False

    def __init__(self):
        self.travel_table = []
        self.objects = []

    @property
    def is_aboveground(self):
        return 1 <= self.n <= 8

    @property
    def is_dark(self):
        return not self.is_light

    @property
    def description(self):
        return self.visited and self.short_description or self.long_description

class Word(object):
    """A word that can be used as part of a command."""

    kind = None
    text = u''
    default_message = None

    def __eq__(self, other):
        return self.text == other

class Object(object):
    """An object in the game, like a grate, or a rod with a rusty star."""

    def __init__(self):
        self.immovable = False
        self.inventory_message = u''
        self.rooms = []
        self.prop = 0
        self.messages = {}

class Message(object):
    """A message for printing."""
    text = u''

    def __unicode__(self):
        return self.text

class Hint(object):
    """A hint offered if the player loiters in one area too long."""

    turns = 0
    penalty = 0
    question = None
    message = None
    used = False

    def write(self, writer):
        writer(self.message)
        self.used = True
