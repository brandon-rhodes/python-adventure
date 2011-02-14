"""Routines that install Adventure commands for the Python prompt."""

class ReprString(object):
    """An object whose __repr__() can be specified explicitly."""

    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return self.value

class ReprTriggeredIdentifier(object):
    """A command word that activates simply by being typed at the prompt."""

    def __init__(self, game, word):
        self.game = game
        self.word = word

    def __repr__(self):
        """The word was typed by itself; interpret as a single-word command."""
        output = self.game.do_command([ self.word ])
        return output.rstrip('\n') + '\n'

    def __call__(self, arg=None):
        """One word `get()` or two words like `get(keys)` were provided."""
        words = [ self.word ]
        if arg is not None:
            if isinstance(arg, ReprTriggeredIdentifier):
                arg = arg.word
            words.append(arg)
        output = self.game.do_command(words)
        return ReprString(output.rstrip('\n') + '\n')

def install_builtins(game):
    import sys
    module = sys.modules['builtins']
    words = [ k for k in game.vocabulary if isinstance(k, str) ]
    words.append('yes')
    words.append('no')
    for word in words:
        if word in ('exit', 'help', 'open', 'quit'):
            continue
        identifier = ReprTriggeredIdentifier(game, word)
        setattr(module, word, identifier)
        if len(word) > 5:
            setattr(module, word[:5], identifier)
