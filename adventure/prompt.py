"""Routines that install Adventure commands for the Python prompt."""

class ReprTriggeredIdentifier(object):
    def __init__(self, game, word):
        self.game = game
        self.word = word

    def __repr__(self):
        """The word was typed by itself; interpret as a single-word command."""
        output = self.game.do_command([ self.word ])
        return output.rstrip('\n') + '\n'

    def __call__(self, arg):
        """Two words were provided like `get(keys)`."""
        output = self.game.do_command([ self.word, arg.word ])
        print(output.rstrip('\n') + '\n')

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
