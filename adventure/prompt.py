"""Routines that install Adventure commands for the Python prompt."""

import __builtin__
from StringIO import StringIO

class ReprTriggeredIdentifier(object):
    def __init__(self, game, word):
        self.game = game
        self.word = word

    def __repr__(self):
        """The word was typed by itself; interpret as a single-word command."""
        s = StringIO()
        old_writer = self.game.writer
        self.game.writer = s.write
        self.game.do_command([ self.word ])
        self.game.writer = old_writer
        v = s.getvalue()
        if v[-1] == '\n':
            v = v[:-1]  # since Python eval loop will add its own newline
        return v

    def __call__(self, arg):
        """Two words were provided like `get(keys)`."""
        self.game.do_command([ self.word, arg.word ])

def install_builtins(game):
    words = [ k for k in game.vocabulary if isinstance(k, unicode) ]
    words.append('yes')
    words.append('no')
    for word in words:
        if word in ('exit', 'help', 'open', 'quit'):
            continue
        identifier = ReprTriggeredIdentifier(game, word)
        setattr(__builtin__, word, identifier)