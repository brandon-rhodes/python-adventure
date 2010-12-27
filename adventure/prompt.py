"""Routines that install Adventure commands for the Python prompt."""

import __builtin__
from StringIO import StringIO

class ReprTriggeredIdentifier(object):
    def __init__(self, game, *args, **kw):
        self.game = game
        self.args = args
        self.kw = kw

    def __repr__(self):
        s = StringIO()
        self.game.writer = s.write
        self.game.do_command(*self.args, **self.kw)
        v = s.getvalue()
        if v[-1] == '\n':
            v = v[:-1]  # since Python eval loop will add its own newline
        return v

def install_builtins(game):
    for word in ('yes', 'no'):
        identifier = ReprTriggeredIdentifier(game, [ word ])
        setattr(__builtin__, word, identifier)
