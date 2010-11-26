"""Classes representing Adventure game components."""

class Move(object):
    """An entry in the travel table."""

    def __init__(self, verbs, vocabulary):
        self.verbs = verbs
        self.vocabulary = vocabulary

    def __repr__(self):
        verblist = [ self.vocabulary[i] for i in self.verbs ]
        if isinstance(self.action, Room):
            action = 'moves to %r' % self.action.description
        elif isinstance(self.action, Message):
            action = 'prints %r' % self.action.text
        else:
            action = 'special %d' % self.action
        return '<%s %s>' % ('|'.join(verblist), action)

class Room(object):
    """A location in the game."""

    def __init__(self):
        self.long_description = ''
        self.short_description = ''
        self.travel_table = []

    @property
    def description(self):
        return self.short_description or self.long_description

class Object(object):
    """An object in the game, like a grate, or a rod with a rusty star."""

    def __init__(self):
        self.inventory_message = ''
        self.prop = 0
        self.prop_messages = {}

class Message(object):
    """A message for printing."""
    text = ''
