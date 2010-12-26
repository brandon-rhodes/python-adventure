"""How we keep track of the state of the game."""

YESNO_ANSWERS = {'y': True, 'yes': True, 'n': False, 'no': False}

from .data import Data

class Game(Data):

    def __init__(self, writer):
        Data.__init__(self)
        self.writer = writer
        self.yesno_callback = False

    def write(self, s):
        """Output the Unicode representation of `s`."""
        self.writer(unicode(s))

    def yesno(self, s, yesno_callback):
        """Ask a question and prepare to receive a yes-or-no answer."""
        self.write(s)
        self.yesno_callback = yesno_callback

    # Game startup

    def start(self):
        """Start the game."""
        self.yesno(self.messages[65], self.instruct)  # like instructions?

    def instruct(self, yes):
        """Print out instructions if the user wants them."""
        if yes:
            self.write(self.messages[1])
            self.hints[3].used = True

    # The central do_command() method, that should be called over and
    # over again with words supplied by the user.

    def do_command(self, words):
        """Parse and act upon the command in the list of strings `words`."""
        if self.yesno_callback is not None:
            answer = YESNO_ANSWERS.get(words[0], None)
            if answer is None:
                self.write('Please answer the question.')
            else:
                self.yesno_callback(answer)
            return
