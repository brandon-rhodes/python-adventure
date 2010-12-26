"""Routines that install Adventure commands for the Python prompt."""

import __builtin__

class ReprTriggeredIdentifier(object):
    def __init__(self, function, *args, **kw):
        self.function = function
        self.args = args
        self.kw = kw

    def __repr__(self):
        self.function(*self.args, **self.kw)
        return u''

def install_builtins(game):
    for word in ('yes', 'no'):
        identifier = ReprTriggeredIdentifier(game.do_command, [ word ])
        setattr(__builtin__, word, identifier)
