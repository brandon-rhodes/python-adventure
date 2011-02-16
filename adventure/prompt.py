"""Routines that install Adventure commands for the Python prompt."""


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


def install_builtins(game):
    import sys
    module = sys.modules['builtins']
    words = [ k for k in game.vocabulary if isinstance(k, str) ]
    words.append('yes')
    words.append('no')
    for word in words:
        if word in ('exit', 'open'):
            continue
        identifier = ReprTriggeredPhrase(game, [ word ])
        setattr(module, word, identifier)
        if len(word) > 5:
            setattr(module, word[:5], identifier)
