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
        self.closing = False

    def write(self, s):
        """Output the Unicode representation of `s`."""
        self.writer(unicode(s))
        self.writer('\n')

    def write_message(self, n):
        self.write(self.messages[n])

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
            self.write_message(1)
            self.hints[3].used = True
        self.loc = self.rooms[1]
        self.describe_location()

    # Routines that handle the aftermath of "big" commands like movement.

    def move_to(self, newloc=None):  #2
        loc = self.loc
        if newloc is None:
            newloc = loc

        if self.closing and newloc.is_aboveground:
            self.write_message(130)
            newloc = loc
            if not self.panic:
                self.clock2 = 15
                self.panic = True

        # put dwarf stuff here

        loc = self.loc = newloc
        self.describe_location()

    def say_okay(self):  #2012
        self.write_message(54)
        self.describe_location()

    def describe_location(self):  #2000
        loc = self.loc
        short = loc.times_described % self.full_description_period
        if short and loc.short_description:
            self.write(loc.short_description)
        else:
            self.write(loc.long_description)
        loc.times_described += 1

        # put hints here

        # put closing-time "prop" special case here

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

        loc = self.loc

        if not loc:
            raise NotImplemented('death not yet implemented')

        word = self.vocabulary[words[0]]

        if word.kind == 'motion': #8
            self.do_motion(word)

    #

    def do_motion(self, verb):

        if verb == u'back':
            #todo
            return

        elif verb == u'look':
            if self.look_complaints > 0:
                self.write_message(15)
                self.look_complaints -= 1
            self.loc.times_described = 0
            self.move_to()
            return

        elif verb == u'cave':
            self.write(self.messages[57 if self.loc.is_aboveground else 58])
            self.move_to()
            return

        for move in self.loc.travel_table:
            if verb in move.verbs: # == 1?
                # if action is a room:
                self.move_to(move.action)
                return

        # todo #50
        self.move_to()
        return
