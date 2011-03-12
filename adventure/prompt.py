"""Routines that install Adventure commands for the Python prompt."""

import inspect

class ReprTriggeredPhrase(object):
    """Command that happens when Python calls repr() to print them."""

    def __init__(self, game, words):
        self.game = game
        self.words = tuple(words)  # protect against caller changing list

    def __repr__(self):
        """Run this command and return the message that results."""
        output = self.game.do_command(self.words)
        return output.rstrip('\n') + '\n'

    def __call__(self, arg=None):
        """Return a compound command of several words, like `get(keys)`."""
        if arg is None:
            return self
        words = arg.words if isinstance(arg, ReprTriggeredPhrase) else (arg,)
        return ReprTriggeredPhrase(self.game, self.words + words)

    def __getattr__(self, name):
        return ReprTriggeredPhrase(self.game, self.words + (name,))


def install_words(game):
    # stack()[0] is this; stack()[1] is adventure.play(); so, stack()[2]
    namespace = inspect.stack()[2][0].f_globals
    words = [ k for k in game.vocabulary if isinstance(k, str) ]
    words.append('yes')
    words.append('no')
    for word in words:
        identifier = ReprTriggeredPhrase(game, [ word ])
        namespace[word] = identifier
        if len(word) > 5:
            namespace[word[:5]] = identifier
