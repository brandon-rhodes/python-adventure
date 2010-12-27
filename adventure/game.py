"""How we keep track of the state of the game."""

YESNO_ANSWERS = {'y': True, 'yes': True, 'n': False, 'no': False}

from .data import Data

class Game(Data):

    look_complaints = 3  # how many times to "SORRY, BUT I AM NOT ALLOWED..."
    full_description_period = 5  # how often we use a room's full description

    def __init__(self, writer):
        Data.__init__(self)
        self.writer = writer
        self.yesno_callback = False

    def write(self, s):
        """Output the Unicode representation of `s`."""
        self.writer(unicode(s))
        self.writer('\n')

    def yesno(self, s, yesno_callback):
        """Ask a question and prepare to receive a yes-or-no answer."""
        self.write(s)
        self.yesno_callback = yesno_callback

    # Game startup

    def start(self):
        """Start the game."""
        self.yesno(self.messages[65], self.start2)  # want instructions?

    def start2(self, yes):
        """Print out instructions if the user wants them."""
        if yes:
            self.write(self.messages[1])
            self.hints[3].used = True
        self.here = self.rooms[1]
        self.describe_location()

    # The central do_command() method, that should be called over and
    # over again with words supplied by the user.

    def do_command(self, words):
        """Parse and act upon the command in the list of strings `words`."""

        if self.yesno_callback is not None:
            answer = YESNO_ANSWERS.get(words[0], None)
            if answer is None:
                self.write('Please answer the question.')
            else:
                callback = self.yesno_callback
                self.yesno_callback = None
                callback(answer)
            return

        here = self.here

        if not here:
            raise NotImplemented('death not yet implemented')

        word = self.vocabulary[words[0]]
        if word.kind == 'motion':
            if word.text in ('cave', 'look'):
                getattr(self, word.text)()

    # Helpful routines.

    def describe_location(self):
        here = self.here
        short = here.times_described % self.full_description_period
        if short and here.short_description:
            self.write(here.short_description)
        else:
            self.write(here.long_description)
        here.times_described += 1

    # Specific intransitive commands.

    def look(self):
        if self.look_complaints > 0:
            self.write(self.messages[15])
            self.look_complaints -= 1
        self.here.times_described = 0

    def cave(self):
        self.write(self.messages[57 if (self.here.n < 8) else 58])
