"""Classes representing Adventure game components."""

class Room(object):
    """A location in the game."""

    long_description = ''
    short_description = ''

class Object(object):
    """An object in the game, like a grate, or a rod with a rusty star."""

    prop = 0
    inventory_message = ''

    def __init__(self):
        self.prop_messages = {}
