"""Classes representing Adventure game components."""

class Move(object):
    """An entry in the travel table."""

    def __init__(self, verbs):
        self.verbs = verbs

class Room(object):
    """A location in the game."""

    def __init__(self):
        self.long_description = ''
        self.short_description = ''
        self.travel_table = []

class Object(object):
    """An object in the game, like a grate, or a rod with a rusty star."""

    def __init__(self):
        self.inventory_message = ''
        self.prop = 0
        self.prop_messages = {}
