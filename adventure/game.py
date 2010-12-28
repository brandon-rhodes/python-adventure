"""How we keep track of the state of the game."""

from random import random
from .data import Data
from .model import Message, Room

YESNO_ANSWERS = {'y': True, 'yes': True, 'n': False, 'no': False}

class Game(Data):

    look_complaints = 3  # how many times to "SORRY, BUT I AM NOT ALLOWED..."
    full_description_period = 5  # how often we use a room's full description

    def __init__(self, writer):
        Data.__init__(self)
        self.writer = writer
        self.yesno_callback = False

        self.is_closing = False         # is the cave closing?
        self.is_closed = False          # is the cave closed?
        self.could_fall_in_pit = False  # could the player fall into a pit?

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

    @property
    def is_dark(self):
        return self.loc.is_dark  # and also check for lamp!

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

    # Routines that handle the aftermath of "big" actions like movement.
    # Although these are called at the end of each `do_command()` cycle,
    # we place here at the top of `game.py` to mirror the order in the
    # advent.for file.

    def move_to(self, newloc=None):  #2
        loc = self.loc
        if newloc is None:
            newloc = loc

        if self.is_closing and newloc.is_aboveground:
            self.write_message(130)
            newloc = loc
            if not self.panic:
                self.clock2 = 15
                self.panic = True

        # put dwarf stuff here

        self.loc = newloc
        self.describe_location()

    def describe_location(self):  #2000

        # check for whether they already have died? or do as sep func?

        loc = self.loc

        if self.could_fall_in_pit and not loc.forced_move and random() < .35:
            self.die()
            return

        # if self.toting(bear):
        #     self.write_message(141)

        if self.is_dark and not loc.forced_move:
            self.write_message(16)
        else:
            do_short = loc.times_described % self.full_description_period
            loc.times_described += 1
            if do_short and loc.short_description:
                self.write(loc.short_description)
            else:
                self.write(loc.long_description)

        if loc.forced_move:
            self.do_motion(self.vocabulary[2])
            return

        if loc.n == 33 and random() < .25 and not self.is_closing:
            self.speak_message(8)

        if not self.is_dark:
            for obj in self.objects.values():

                if loc not in obj.rooms:
                    continue

                #IF(OBJ.GT.100)OBJ=OBJ-100
                if obj == u'steps': #...and toting nugget
                    continue

                if obj.prop < 0:  # finding a treasure the first time
                    if self.is_closing:
                        continue
                    obj.prop = 1 if (obj == u'rug' or obj == u'chain') else 0
                    #IF(TALLY.EQ.TALLY2.AND.TALLY.NE.0)LIMIT=MIN0(35,LIMIT)

                #if obj == u'steps' and AND.LOC.EQ.FIXED(STEPS))prop=1
                self.write(obj.messages[obj.prop])

        self.finish_turn()

    def say_okay(self):  #2012
        self.write_message(54)
        self.finish_turn()

    def finish_turn(self):  #2600
        # put hints here
        if self.is_closed:
            if self.oyste.prop < 0: # and toting it
                self.write(self.oyste.messages[1])
            # put closing-time "prop" special case here

        self.could_fall_in_pit = self.loc.is_dark  #2605
        # remove knife from cave if they moved away from it

    # The central do_command() method, that should be called over and
    # over again with words supplied by the user.

    def do_command(self, words):  #2608
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

        if word.kind == 'motion':
            self.do_motion(word)
            return

        elif word == u'inven':
            first = True
            for obj in self.objects.values():
                if obj.toting: # ...and is not bear
                    if first:
                        self.write_message(99)
                        first = False
                    self.write(obj.inventory_message)
            # ... and do bear too
            self.finish_turn()
            return

        elif word == u'get':
            # if toting obj: goto 2011 and actspeak thing
            word2 = self.vocabulary[words[1]]
            obj = self.objects[word2.n % 1000]
            obj.toting = True
            del obj.rooms[:]
            return

        elif word == u'unloc':
            word2 = self.vocabulary[words[1]]
            # TODO
            return

        raise NotImplementedError('cannot do word: %r' % word)

    #

    def do_motion(self, word):  #8

        if word == u'null':
            self.move_to()
            return

        elif word == u'back':  #20
            #todo
            return

        elif word == u'look':  #30
            if self.look_complaints > 0:
                self.write_message(15)
                self.look_complaints -= 1
            self.loc.times_described = 0
            self.move_to()
            self.could_fall_in_pit = False
            return

        elif word == u'cave':  #40
            self.write(self.messages[57 if self.loc.is_aboveground else 58])
            self.move_to()
            return

        for move in self.loc.travel_table:
            if move.forced or word in move.verbs:
                c = move.condition

                if c[0] is None:
                    go = True
                elif c[0] == '%':
                    go = 100 * random() < c[1]
                elif c[0] == 'carrying':
                    go = True # TODO: test if carrying object c[1]
                elif c[0] == 'carrying_or_in_room_with':
                    go = True # TODO: test this too
                elif c[0] == 'prop!=':
                    go = self.objects[c[1]].prop != c[2]

                if not go:
                    continue

                if isinstance(move.action, Room):
                    self.move_to(move.action)
                    return
                elif isinstance(move.action, Message):
                    self.write(move.action)
                    self.move_to()
                    return
                else:
                    raise NotImplemented

        #50
        n = word.n
        if 29 <= n <= 30 or 43 <= n <= 50:
            self.write_message(9)
        elif n in (7, 36, 37):
            self.write_message(10)
        elif n in (11, 19):
            self.write_message(11)
        elif word == u'find' or word == u'invent':  # ? this might be wrong
            self.write_message(59)
        elif n in (62, 65):
            self.write_message(42)
        elif n == 17:
            self.write_message(80)
        else:
            self.write_message(12)
        self.move_to()
        return

    def die(self):  #90
        self.write_message(23)
