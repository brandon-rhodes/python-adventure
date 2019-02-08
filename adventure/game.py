"""How we keep track of the state of the game.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""
# Numeric comments scattered through this file refer to FORTRAN line
# numbers, for those comparing this file and `advent.for`; so "#2012"
# refers to FORTRAN line number 2012 (which you can find easily in the
# FORTRAN using Emacs with an interactive search for newline-2012-tab,
# that is typed C-s C-q C-j 2 0 1 2 C-i).

import os
import pickle
import random
import zlib
from operator import attrgetter
from .data import Data
from .model import Room, Message, Dwarf, Pirate

YESNO_ANSWERS = {'y': True, 'yes': True, 'n': False, 'no': False}

class Game(Data):

    look_complaints = 3  # how many times to "SORRY, BUT I AM NOT ALLOWED..."
    full_description_period = 5  # how often we use a room's full description
    full_wests = 0  # how many times they have typed "west" instead of "w"
    dwarf_stage = 0  # DFLAG how active the dwarves are
    dwarves_killed = 0  # DKILL
    knife_location = None  # KNFLOC
    foobar = -1  # FOOBAR turn number of most recent still-valid "fee"
    gave_up = False
    treasures_not_found = 0  # TALLY how many treasures have not yet been seen
    impossible_treasures = 0  # TALLY2 how many treasures can never be retrieved
    lamp_turns = 330
    warned_about_dim_lamp = False
    bonus = 0  # how they exited the final bonus round
    is_dead = False  # whether we are currently dead
    deaths = 0  # how many times the player has died
    max_deaths = 3  # how many times the player can die
    turns = 0

    def __init__(self, seed=None):
        Data.__init__(self)
        self.output = ''
        self.yesno_callback = False
        self.yesno_casual = False       # whether to insist they answer

        self.clock1 = 30                # counts down from finding last treasure
        self.clock2 = 50                # counts down until cave closes
        self.is_closing = False         # is the cave closing?
        self.panic = False              # they tried to leave during closing?
        self.is_closed = False          # is the cave closed?
        self.is_done = False            # caller can check for "game over"
        self.could_fall_in_pit = False  # could the player fall into a pit?

        self.random_generator = random.Random()
        if seed is not None:
            self.random_generator.seed(seed)

    def random(self):
        return self.random_generator.random()

    def choice(self, seq):
        return self.random_generator.choice(seq)

    def write(self, more):
        """Append the Unicode representation of `s` to our output."""
        if more:
            self.output += str(more).upper()
            self.output += '\n'

    def write_message(self, n):
        self.write(self.messages[n])

    def yesno(self, s, yesno_callback, casual=False):
        """Ask a question and prepare to receive a yes-or-no answer."""
        self.write(s)
        self.yesno_callback = yesno_callback
        self.yesno_casual = casual

    # Properties of the cave.

    @property
    def is_dark(self):
        lamp = self.objects['lamp']
        if self.is_here(lamp) and lamp.prop:
            return False
        return self.loc.is_dark

    @property
    def inventory(self):
        return [ obj for obj in self.object_list if obj.is_toting ]

    @property
    def treasures(self):
        return [ obj for obj in self.object_list if obj.is_treasure ]

    @property
    def objects_here(self):
        return self.objects_at(self.loc)

    def objects_at(self, room):
        return [ obj for obj in self.object_list if room in obj.rooms ]

    def is_here(self, obj):
        if isinstance(obj, Dwarf):
            return self.loc is obj.room
        else:
            return obj.is_toting or (self.loc in obj.rooms)

    @property
    def is_finished(self):
        return (self.is_dead or self.is_done) and not self.yesno_callback

    # Game startup

    def start(self):
        """Start the game."""

        # For old-fashioned players, accept five-letter truncations like
        # "inven" instead of insisting on full words like "inventory".

        for key, value in list(self.vocabulary.items()):
            if isinstance(key, str) and len(key) > 5:
                self.vocabulary[key[:5]] = value

        # Set things going.

        self.chest_room = self.rooms[114]
        self.bottle.contents = self.water
        self.yesno(self.messages[65], self.start2)  # want instructions?

    def start2(self, yes):
        """Display instructions if the user wants them."""
        if yes:
            self.write_message(1)
            self.hints[3].used = True
            self.lamp_turns = 1000

        self.oldloc2 = self.oldloc = self.loc = self.rooms[1]
        self.dwarves = [ Dwarf(self.rooms[n]) for n in (19, 27, 33, 44, 64) ]
        self.pirate = Pirate(self.chest_room)

        treasures = self.treasures
        self.treasures_not_found = len(treasures)
        for treasure in treasures:
            treasure.prop = -1

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
            newloc = loc  # cancel move and put him back underground
            if not self.panic:
                self.clock2 = 15
                self.panic = True

        must_allow_move = ((newloc is loc) or (loc.is_forced)
                           or (loc.is_forbidden_to_pirate))

        dwarf_blocking_the_way = any(
            dwarf.old_room is newloc and dwarf.has_seen_adventurer
            for dwarf in self.dwarves
            )

        if not must_allow_move and dwarf_blocking_the_way:
            newloc = loc  # cancel move they were going to make
            self.write_message(2)  # dwarf is blocking the way

        self.loc = loc = newloc  #74

        # IF LOC.EQ.0 ?
        is_dwarf_area = not (loc.is_forced or loc.is_forbidden_to_pirate)
        if is_dwarf_area and self.dwarf_stage > 0:
            self.move_dwarves()
        else:
            if is_dwarf_area and loc.is_after_hall_of_mists:
                self.dwarf_stage = 1
            self.describe_location()

    def move_dwarves(self):

        #6000
        if self.dwarf_stage == 1:

            # 5% chance per turn of meeting first dwarf
            if self.loc.is_before_hall_of_mists or self.random() < .95:
                self.describe_location()
                return
            self.dwarf_stage = 2
            for i in range(2):  # randomly remove 0, 1, or 2 dwarves
                if self.random() < .5:
                    self.dwarves.remove(self.choice(self.dwarves))
            for dwarf in self.dwarves:
                if dwarf.room is self.loc:  # move dwarf away from our loc
                    dwarf.start_at(self.rooms[18])
            self.write_message(3)  # dwarf throws axe and curses
            self.axe.drop(self.loc)
            self.describe_location()
            return

        #6010
        dwarf_count = dwarf_attacks = knife_wounds = 0

        for dwarf in self.dwarves + [ self.pirate ]:

            locations = { move.action for move in dwarf.room.travel_table 
                          if dwarf.can_move(move)
                          and move.action is not dwarf.old_room
                          and move.action is not dwarf.room }
            # Without stabilizing the order with a sort, the room chosen
            # would depend on how the Room addresses in memory happen to
            # order the rooms in the set() - and make it impossible to
            # test the game by setting the random number generator seed
            # and then playing through the game.
            locations = sorted(locations, key=attrgetter('n'))
            if locations:
                new_room = self.choice(locations)
            else:
                new_room = dwarf.old_room
            dwarf.old_room, dwarf.room = dwarf.room, new_room
            if self.loc in (dwarf.room, dwarf.old_room):
                dwarf.has_seen_adventurer = True
            elif self.loc.is_before_hall_of_mists:
                dwarf.has_seen_adventurer = False

            if not dwarf.has_seen_adventurer:
                continue

            dwarf.room = self.loc

            if dwarf.is_dwarf:
                dwarf_count += 1
                # A dwarf cannot walk and attack at the same time.
                if dwarf.room is dwarf.old_room:
                    dwarf_attacks += 1
                    self.knife_location = self.loc
                    if self.random() < .095 * (self.dwarf_stage - 2):
                        knife_wounds += 1

            else:  # the pirate
                pirate = dwarf

                if self.loc is self.chest_room or self.chest.prop >= 0:
                    continue  # decide that the pirate is not really here

                treasures = [ t for t in self.treasures if t.is_toting ]
                if (self.platinum in treasures and self.loc.n in (100, 101)):
                    treasures.remove(self.platinum)

                if not treasures:
                    h = any( t for t in self.treasures if self.is_here(t) )
                    one_treasure_left = (self.treasures_not_found ==
                                         self.impossible_treasures + 1)
                    shiver_me_timbers = (
                        one_treasure_left and not h and not(self.chest.rooms)
                        and self.is_here(self.lamp) and self.lamp.prop == 1
                        )

                    if not shiver_me_timbers:
                        if (pirate.old_room != pirate.room
                            and self.random() < .2):
                            self.write_message(127)
                        continue  # pragma: no cover

                    self.write_message(186)
                    self.chest.drop(self.chest_room)
                    self.message.drop(self.rooms[140])

                else:
                    #6022  I'll just take all this booty
                    self.write_message(128)
                    if not self.message.rooms:
                        self.chest.drop(self.chest_room)
                    self.message.drop(self.rooms[140])
                    for treasure in treasures:
                        treasure.drop(self.chest_room)

                #6024
                pirate.old_room = pirate.room = self.chest_room
                pirate.has_seen_adventurer = False  # free to move

        # Report what has happened.

        if dwarf_count == 1:
            self.write_message(4)
        elif dwarf_count:
            self.write('There are {} threatening little dwarves in the'
                       ' room with you.\n'.format(dwarf_count))

        if dwarf_attacks and self.dwarf_stage == 2:
            self.dwarf_stage = 3

        if dwarf_attacks == 1:
            self.write_message(5)
            k = 52
        elif dwarf_attacks:
            self.write('{} of them throw knives at you!\n'.format(dwarf_attacks))
            k = 6

        if not dwarf_attacks:
            pass
        elif not knife_wounds:
            self.write_message(k)
        else:
            if knife_wounds == 1:
                self.write_message(k + 1)
            else:
                self.write('{} of them get you!\n'.format(knife_wounds))
            self.oldloc2 = self.loc
            self.die()
            return

        self.describe_location()

    def describe_location(self):  #2000

        loc = self.loc

        if loc.n == 0:
            self.die()

        could_fall = self.is_dark and self.could_fall_in_pit
        if could_fall and not loc.is_forced and self.random() < .35:
            self.die_here()
            return

        if self.bear.is_toting:
            self.write_message(141)

        if self.is_dark and not loc.is_forced:
            self.write_message(16)
        else:
            do_short = loc.times_described % self.full_description_period
            loc.times_described += 1
            if do_short and loc.short_description:
                self.write(loc.short_description)
            else:
                self.write(loc.long_description)

        if loc.is_forced:
            self.do_motion(self.vocabulary[2])  # dummy motion verb
            return

        if loc.n == 33 and self.random() < .25 and not self.is_closing:
            self.write_message(8)

        if not self.is_dark:
            for obj in self.objects_here:

                if obj is self.steps and self.gold.is_toting:
                    continue

                if obj.prop < 0:  # finding a treasure the first time
                    if self.is_closed:
                        continue
                    obj.prop = 1 if obj in (self.rug, self.chain) else 0
                    self.treasures_not_found -= 1
                    if (self.treasures_not_found > 0 and
                        self.treasures_not_found == self.impossible_treasures):
                        self.lamp_turns = min(35, self.lamp_turns)

                if obj is self.steps and self.loc is self.steps.rooms[1]:
                    prop = 1
                else:
                    prop = obj.prop

                self.write(obj.messages[prop])

        self.finish_turn()

    def say_okay_and_finish(self, *ignored):  #2009
        self.write_message(54)
        self.finish_turn()

    #2009 sets SPK="OK" then...
    #2010 sets SPK to K
    #2011 speaks SPK then...
    #2012 blanks VERB and OBJ and calls:
    def finish_turn(self, obj=None):  #2600

        # Advance random number generator so each input affects future.
        self.random()

        # Check whether we should offer a hint.
        for hint in self.hints.values():
            if hint.turns_needed == 9999 or hint.used:
                continue
            if self.loc in hint.rooms:
                hint.turn_counter += 1
                if hint.turn_counter >= hint.turns_needed:
                    if hint.n != 5:  # hint 5 counter does not get reset
                        hint.turn_counter = 0
                    if self.should_offer_hint(hint, obj):
                        hint.turn_counter = 0

                        def callback(yes):
                            if yes:
                                self.write(hint.message)
                                hint.used = True
                            else:
                                self.write_message(54)

                        self.yesno(hint.question, callback)
                        return
            else:
                hint.turn_counter = 0

        if self.is_closed:
            if self.oyster.prop < 0 and self.oyster.is_toting:
                self.write(self.oyster.messages[1])
            for obj in self.inventory:
                if obj.prop < 0:
                    obj.prop = - 1 - obj.prop

        self.could_fall_in_pit = self.is_dark  #2605
        if self.knife_location and self.knife_location is not self.loc:
            self.knife_location = None

    # The central do_command() method, that should be called over and
    # over again with words supplied by the user.

    def do_command(self, words):
        """Parse and act upon the command in the list of strings `words`."""
        self.output = ''
        self._do_command(words)
        return self.output

    def _do_command(self, words):
        if self.yesno_callback is not None:
            answer = YESNO_ANSWERS.get(words[0], None)
            if answer is None:
                if self.yesno_casual:
                    self.yesno_callback = None
                else:
                    self.write('Please answer the question.')
                    return
            else:
                callback = self.yesno_callback
                self.yesno_callback = None
                callback(answer)
                return

        if self.is_dead:
            self.write('You have gotten yourself killed.')
            return

        #2608
        self.turns += 1
        if (self.treasures_not_found == 0
            and self.loc.n >= 15 and self.loc.n != 33):
            self.clock1 -= 1
            if self.clock1 == 0:
                self.start_closing_cave()  # no "return", to do their command
        if self.clock1 < 0:
            self.clock2 -= 1
            if self.clock2 == 0:
                return self.close_cave()  # "return", to cancel their command

        if self.lamp.prop == 1:
            self.lamp_turns -= 1

        if self.lamp_turns <= 30 and self.is_here(self.batteries) \
                and self.batteries.prop == 0 and self.is_here(self.lamp):
            #12000
            self.write_message(188)
            self.batteries.prop = 1
            if self.batteries.is_toting:
                self.batteries.drop(self.loc)
            self.lamp_turns += 2500
            self.warned_about_dim_lamp = False
        elif self.lamp_turns == 0:
            #12400
            self.lamp_turns = -1
            self.lamp.prop = 0
            if self.is_here(self.lamp):
                self.write_message(184)
        elif self.lamp_turns < 0 and self.loc.is_aboveground:
            #12600
            self.write_message(185)
            self.gave_up = True
            self.score_and_exit()
            return
        elif self.lamp_turns <= 30 and not self.warned_about_dim_lamp \
                and self.is_here(self.lamp):
            #12200
            self.warned_about_dim_lamp = True
            if self.batteries.prop == 1:
                self.write_message(189)
            elif not self.batteries.rooms:
                self.write_message(183)
            else:
                self.write_message(187)

        self.dispatch_command(words)

    def dispatch_command(self, words):  #19999

        if not 1 <= len(words) <= 2:
            return self.dont_understand()

        if words[0] == 'save' and len(words) > 1:
            # Handle suspend separately, since filename can be anything,
            # and is not restricted to being a vocabulary word (and, in
            # fact, it can be an open file).
            return self.t_suspend(words[0], words[1])

        words = [ self.vocabulary.get(word) for word in words ]
        if None in words:
            return self.dont_understand()

        word1 = words[0]
        word2 = words[1] if len(words) == 2 else None

        if word1 == 'enter' and (word2 == 'stream' or word2 == 'water'):
            if self.loc.liquid is self.water:
                self.write_message(70)
            else:
                self.write_message(43)
            return self.finish_turn()

        if (word1 == 'enter' or word1 == 'walk') and word2:
            #2800  'enter house' becomes simply 'house' and so forth
            word1, word2 = word2, None

        if ((word1 == 'water' or word1 == 'oil') and
            (word2 == 'plant' or word2 == 'door') and
            self.is_here(self.referent(word2))):
            word1, word2 = self.vocabulary['pour'], word1

        if word1 == 'say':
            return self.t_say(word1, word2) if word2 else self.i_say(word1)

        kinds = (word1.kind, word2.kind if word2 else None)

        #2630
        if kinds == ('travel', None):
            if word1.text == 'west':  #2610
                self.full_wests += 1
                if self.full_wests == 10:
                    self.write_message(17)
            return self.do_motion(word1)

        if kinds == ('snappy_comeback', None):
            self.write_message(word1.n % 1000)
            return self.finish_turn()

        if kinds == ('noun', None):
            verb, noun = None, word1
        elif kinds == ('verb', None):
            verb, noun = word1, None
        elif kinds == ('verb', 'noun'):
            verb, noun = word1, word2
        elif kinds == ('noun', 'verb'):
            noun, verb = word1, word2
        else:
            return self.dont_understand()

        if not noun:
            obj = None
        else:
            obj = self.referent(noun)
            obj_here = self.is_here(obj)
            if not obj_here:
                if obj is self.grate:
                    if self.loc.n in (1, 4, 7):
                        return self.dispatch_command([ 'depression' ])
                    elif 9 < self.loc.n < 15:
                        return self.dispatch_command([ 'entrance' ])
                elif noun == 'dwarf':
                    obj_here = any( d.room is self.loc for d in self.dwarves )
                elif obj is self.bottle.contents and self.is_here(self.bottle):
                    obj_here = True
                elif obj is self.loc.liquid:
                    obj_here = True
                elif (obj is self.plant and self.is_here(self.plant2)
                      and self.plant2.prop != 0):
                    obj = self.plant2
                    obj_here = True
                elif obj is self.knife and self.knife_location is self.loc:
                    self.knife_location = None
                    self.write_message(116)
                    return self.finish_turn()
                elif obj is self.rod and self.is_here(self.rod2):
                    obj = self.rod2
                    obj_here = True
                elif verb and (verb == 'find' or verb == 'inventory'):
                    obj_here = True  # lie; these verbs work for absent objects

            if not obj_here:
                return self.i_see_no(noun)

            if not verb:
                self.write('What do you want to do with the {}?\n'.format(
                        noun.text))
                return self.finish_turn()

        verb_name = verb.synonyms[0].text
        if obj:
            method_name = 't_' + verb_name
            args = (verb, obj)
        else:
            method_name = 'i_' + verb_name
            args = (verb,)
        method = getattr(self, method_name)
        method(*args)

    def dont_understand(self):
        #3000  (a bit earlier than in the Fortran code)
        n = self.random()
        if n < 0.20:    # 20% of the entire 1.0 range of random()
            self.write_message(61)
        elif n < 0.36:  # 20% of the remaining 0.8 left
            self.write_message(13)
        else:
            self.write_message(60)
        self.finish_turn()

    def i_see_no(self, thing):
        self.write('I see no {} here.\n'.format(getattr(thing, 'text', thing)))
        self.finish_turn()

    # Motion.

    def do_motion(self, word):  #8

        if word == 'null': #2
            self.move_to()
            return

        elif word == 'back':  #20
            dest = self.oldloc2 if self.oldloc.is_forced else self.oldloc
            self.oldloc2, self.oldloc = self.oldloc, self.loc
            if dest is self.loc:
                self.write_message(91)
                self.move_to()
                return
            alt = None
            for move in self.loc.travel_table:
                if move.action is dest:
                    word = move.verbs[0]  # arbitrary verb going to `dest`
                    break # Fall through, to attempt the move.
                elif (isinstance(move.action, Room)
                      and move.action.is_forced
                      and move.action.travel_table[0].action is dest):
                    alt = move.verbs[0]
            else:  # no direct route is available
                if alt is not None:
                    word = alt  # take a forced move if it's the only option
                else:
                    self.write_message(140)
                    self.move_to()
                    return

        elif word == 'look':  #30
            if self.look_complaints > 0:
                self.write_message(15)
                self.look_complaints -= 1
            self.loc.times_described = 0
            self.move_to()
            self.could_fall_in_pit = False
            return

        elif word == 'cave':  #40
            self.write_message(57 if self.loc.is_aboveground else 58)
            self.move_to()
            return

        self.oldloc2, self.oldloc = self.oldloc, self.loc

        for move in self.loc.travel_table:
            if move.is_forced or word in move.verbs:
                c = move.condition

                if c[0] is None or c[0] == 'not_dwarf':
                    allowed = True
                elif c[0] == '%':
                    allowed = 100 * self.random() < c[1]
                elif c[0] == 'carrying':
                    allowed = self.objects[c[1]].is_toting
                elif c[0] == 'carrying_or_in_room_with':
                    allowed = self.is_here(self.objects[c[1]])
                elif c[0] == 'prop!=':
                    allowed = self.objects[c[1]].prop != c[2]

                if not allowed:
                    continue

                if isinstance(move.action, Room):
                    self.move_to(move.action)
                    return

                elif isinstance(move.action, Message):
                    self.write(move.action)
                    self.move_to()
                    return

                elif move.action == 301:  #30100
                    inv = self.inventory
                    if len(inv) != 0 and inv != [ self.emerald ]:
                        self.write_message(117)
                        self.move_to()
                    elif self.loc.n == 100:
                        self.move_to(self.rooms[99])
                    else:
                        self.move_to(self.rooms[100])
                    return

                elif move.action == 302:  #30200
                    self.emerald.drop(self.loc)
                    self.do_motion(word)
                    return

                elif move.action == 303:  #30300
                    troll, troll2 = self.troll, self.troll2
                    if troll.prop == 1:
                        self.write(troll.messages[1])
                        troll.prop = 0
                        troll.rooms = list(troll.starting_rooms)
                        troll2.destroy()
                        self.move_to()
                        return
                    else:
                        places = list(troll.starting_rooms)
                        places.remove(self.loc)
                        self.loc = places[0]  # "the other side of the bridge"
                        if troll.prop == 0:
                            troll.prop = 1
                        if not self.bear.is_toting:
                            self.move_to()
                            return
                        self.write_message(162)
                        self.chasm.prop = 1
                        troll.prop = 2
                        self.bear.drop(self.loc)
                        self.bear.is_fixed = True
                        self.bear.prop = 3
                        if self.spices.prop < 0:
                            self.impossible_treasures += 1
                        self.oldloc2 = self.loc  # refuse to strand belongings
                        self.die()
                        return

        #50
        n = word.n
        if 29 <= n <= 30 or 43 <= n <= 50:
            self.write_message(9)
        elif n in (7, 36, 37):
            self.write_message(10)
        elif n in (11, 19):
            self.write_message(11)
        elif n in (62, 65):
            self.write_message(42)
        elif n == 17:
            self.write_message(80)
        else:
            self.write_message(12)
        self.move_to()
        return

    # Death and reincarnation.

    def die_here(self):  #90
        self.write_message(23)
        self.oldloc2 = self.loc
        self.die()

    def die(self):  #99
        self.deaths += 1
        self.is_dead = True

        if self.is_closing:
            self.write_message(131)
            self.score_and_exit()
            return

        def callback(yes):
            if yes:
                self.write_message(80 + self.deaths * 2)
                if self.deaths < self.max_deaths:
                    # do water and oil thing
                    self.is_dead = False
                    if self.lamp.is_toting:
                        self.lamp.prop = 0
                    for obj in self.inventory:
                        if obj is self.lamp:
                            obj.drop(self.rooms[1])
                        else:
                            obj.drop(self.oldloc2)
                    self.loc = self.rooms[3]
                    self.describe_location()
                    return
            else:
                self.write_message(54)
            self.score_and_exit()

        self.yesno(self.messages[79 + self.deaths * 2], callback)

    # Verbs.

    def ask_verb_what(self, verb, *args):  #8000
        self.write('{} What?\n'.format(verb.text))
        self.finish_turn()

    i_walk = ask_verb_what
    i_drop = ask_verb_what
    i_say = ask_verb_what
    i_nothing = say_okay_and_finish
    i_wave = ask_verb_what
    i_calm = ask_verb_what
    i_rub = ask_verb_what
    i_throw = ask_verb_what
    i_find = ask_verb_what
    i_feed = ask_verb_what
    i_break = ask_verb_what
    i_wake = ask_verb_what

    def write_default_message(self, verb, *args):
        self.write(verb.default_message)
        self.finish_turn()

    t_nothing = say_okay_and_finish
    t_calm = write_default_message
    t_quit = write_default_message
    t_score = write_default_message
    t_fee = write_default_message
    t_brief = write_default_message
    t_hours = write_default_message

    def i_carry(self, verb):  #8010
        is_dwarf_here = any( dwarf.room == self.loc for dwarf in self.dwarves )
        objs = self.objects_here
        if len(objs) != 1 or is_dwarf_here:
            self.ask_verb_what(verb)
        else:
            self.t_carry(verb, objs[0])

    def t_carry(self, verb, obj):  #9010
        if obj.is_toting:
            self.write(verb.default_message)
            self.finish_turn()
            return
        if obj.is_fixed or len(obj.rooms) > 1:
            if obj is self.plant and obj.prop <= 0:
                self.write_message(115)
            elif obj is self.bear and obj.prop == 1:
                self.write_message(169)
            elif obj is self.chain and self.chain.prop != 0:
                self.write_message(170)
            else:
                self.write_message(25)
            self.finish_turn()
            return
        if obj is self.water or obj is self.oil:
            if self.is_here(self.bottle) and self.bottle.contents is obj:
                # They want to carry the filled bottle.
                obj = self.bottle
            else:
                # They must mean they want to fill the bottle.
                if not self.bottle.is_toting:
                    self.write_message(104)
                elif self.bottle.contents is not None:
                    self.write_message(105)
                else:
                    self.t_fill(verb, self.bottle)  # hand off control to "fill"
                    return
                self.finish_turn()
                return
        if len(self.inventory) >= 7:
            self.write_message(92)
            self.finish_turn()
            return
        if obj is self.bird and obj.prop == 0:
            if self.rod.is_toting:
                self.write_message(26)
                self.finish_turn(obj)  # needs obj to decide to give hint
                return
            if not self.cage.is_toting:
                self.write_message(27)
                self.finish_turn()
                return
            self.bird.prop = 1
        if (obj is self.bird or obj is self.cage) and self.bird.prop != 0:
            self.bird.carry()
            self.cage.carry()
        else:
            obj.carry()
            if obj is self.bottle and self.bottle.contents is not None:
                self.bottle.contents.carry()
        self.say_okay_and_finish()

    def t_drop(self, verb, obj):  #9020
        if obj is self.rod and not self.rod.is_toting and self.rod2.is_toting:
            obj = self.rod2

        if not obj.is_toting:
            self.write(verb.default_message)
            self.finish_turn()
            return

        bird, snake, dragon, bear, troll = self.bird, self.snake, self.dragon, \
            self.bear, self.troll

        if obj is bird and self.is_here(snake):
            self.write_message(30)
            if self.is_closed:
                self.wake_repository_dwarves()
                return
            snake.prop = 1
            snake.destroy()

        elif obj is self.coins and self.is_here(self.machine):
            obj.destroy()
            self.batteries.drop(self.loc)
            self.write(self.batteries.messages[0])
            self.finish_turn()
            return

        elif obj is bird and self.is_here(dragon) and dragon.prop == 0:
            self.write_message(154)
            bird.destroy()
            bird.prop = 0
            if snake.rooms:
                self.impossible_treasures += 1
            self.finish_turn()
            return

        elif obj is bear and self.is_here(troll):
            self.write_message(163)
            troll.destroy()
            self.troll2.rooms = list(self.troll.starting_rooms)
            troll.prop = 2

        elif obj is self.vase and self.loc is not self.rooms[96]:
            if self.pillow.is_at(self.loc):
                self.vase.prop = 0
            else:
                self.vase.prop = 2
                self.vase.is_fixed = True
            self.write(self.vase.messages[self.vase.prop + 1])

        else:
            self.write_message(54)

        #9021
        if obj is self.bottle.contents:
            obj = self.bottle
        if obj is self.bottle and self.bottle.contents:
            self.bottle.contents.hide()
        if obj is self.cage and self.bird.prop != 0:
            bird.drop(self.loc)
        elif obj is self.bird:
            obj.prop = 0
        obj.drop(self.loc)
        self.finish_turn()
        return

    def t_say(self, verb, word):  #9030
        if word.n in (62, 65, 71, 2025):
            self.dispatch_command([ word.text ])
        else:
            self.write('Okay, "{}".'.format(word.text))
            self.finish_turn()

    def i_unlock(self, verb):  #8040  Handles "unlock" case as well
        objs = (self.grate, self.door, self.oyster, self.clam, self.chain)
        objs = list(filter(self.is_here, objs))
        if len(objs) > 1:
            self.ask_verb_what(verb)
        elif len(objs) == 1:
            self.t_unlock(verb, objs[0])
        else:
            self.write_message(28)
            self.finish_turn()

    i_lock = i_unlock

    def t_unlock(self, verb, obj):  #9040  Handles "lock" case as well
        if obj is self.clam or obj is self.oyster:
            #9046
            oy = 1 if (obj is self.oyster) else 0
            if verb == 'lock':
                self.write_message(61)
            elif not self.trident.is_toting:
                self.write_message(122 + oy)
            elif obj.is_toting:
                self.write_message(120 + oy)
            elif obj is self.oyster:
                self.write_message(125)
            else:
                self.write_message(124)
                self.clam.destroy()
                self.oyster.drop(self.loc)
                self.pearl.drop(self.rooms[105])
        elif obj is self.door:
            if obj.prop == 1:
                self.write_message(54)
            else:
                self.write_message(111)
        elif obj is self.cage:
            self.write_message(32)
        elif obj is self.keys:
            self.write_message(55)
        elif obj is self.grate or obj is self.chain:
            if not self.is_here(self.keys):
                self.write_message(31)
            elif obj is self.chain:
                #9048
                if verb == 'unlock':
                    if self.chain.prop == 0:
                        self.write_message(37)
                    elif self.bear.prop == 0:
                        self.write_message(41)
                    else:
                        self.chain.prop = 0
                        self.chain.is_fixed = False
                        if self.bear.prop != 3:
                            self.bear.prop = 2
                        self.bear.is_fixed = 2 - self.bear.prop
                        self.write_message(171)
                else:
                    #9049
                    if self.loc not in self.chain.starting_rooms:
                        self.write_message(173)
                    elif self.chain.prop != 0:
                        self.write_message(34)
                    else:
                        self.chain.prop = 2
                        if self.chain.is_toting:
                            self.chain.drop(self.loc)
                        self.chain.is_fixed = True
                        self.write_message(172)
            elif self.is_closing:
                if not self.panic:
                    self.clock2 = 15
                    self.panic = True
                self.write_message(130)
            else:
                #9043
                oldprop = obj.prop
                obj.prop = 0 if verb == 'lock' else 1
                self.write_message(34 + oldprop + 2 * obj.prop)
        else:
            self.write(verb.default_message)
        self.finish_turn()

    t_lock = t_unlock

    def t_light(self, verb, obj=None):  #9070
        if not self.is_here(self.lamp):
            self.write(verb.default_message)
        elif self.lamp_turns <= 0:
            self.write_message(184)
        else:
            self.lamp.prop = 1
            self.write_message(39)
            if self.loc.is_dark:
                return self.describe_location()
        self.finish_turn()

    i_light = t_light

    def t_extinguish(self, verb, obj=None):  #9080
        if not self.is_here(self.lamp):
            self.write(verb.default_message)
        else:
            self.lamp.prop = 0
            self.write_message(40)
            if self.loc.is_dark:
                self.write_message(16)
        self.finish_turn()

    i_extinguish = t_extinguish

    def t_wave(self, verb, obj):  #9090
        fissure = self.fissure

        if (obj is self.rod and obj.is_toting and self.is_here(fissure)
            and not self.is_closing):
            fissure.prop = 0 if fissure.prop else 1
            self.write(fissure.messages[2 - fissure.prop])
        else:
            if obj.is_toting or (obj is self.rod and self.rod2.is_toting):
                self.write(verb.default_message)
            else:
                self.write_message(29)

        self.finish_turn()

    def i_attack(self, verb):  #9120
        enemies = [ self.snake, self.dragon, self.troll, self.bear ]
        if self.dwarf_stage >= 2:
            enemies.extend(self.dwarves)
        dangers = list(filter(self.is_here, enemies))
        if len(dangers) > 1:
            return self.ask_verb_what(verb)
        if len(dangers) == 1:
            return self.t_attack(verb, dangers[0])
        targets = []
        if self.is_here(self.bird) and verb != 'throw':
            targets.append(self.bird)
        if self.is_here(self.clam) or self.is_here(self.oyster):
            targets.append(self.clam)
        if len(targets) > 1:
            return self.ask_verb_what(verb)
        elif len(targets) == 1:
            return self.t_attack(verb, targets[0])
        else:
            return self.t_attack(verb, None)

    def t_attack(self, verb, obj):  #9124  (but control goes to 9120 first)
        if obj is self.bird:
            if self.is_closed:
                self.write_message(137)
            else:
                obj.destroy()
                obj.prop = 0
                if self.snake.rooms:
                    self.impossible_treasures += 1
                self.write_message(45)
        elif obj is self.clam or obj is self.oyster:
            self.write_message(150)
        elif obj is self.snake:
            self.write_message(46)
        elif obj is self.dwarf:
            if self.is_closed:
                self.wake_repository_dwarves()
                return
            self.write_message(49)
        elif obj is self.dragon:
            if self.dragon.prop != 0:
                self.write_message(167)
            else:
                def callback(yes):
                    self.write(obj.messages[1])
                    obj.prop = 2
                    obj.is_fixed = True
                    oldroom1 = obj.rooms[0]
                    oldroom2 = obj.rooms[1]
                    newroom = self.rooms[ (oldroom1.n + oldroom2.n) // 2 ]
                    obj.drop(newroom)
                    self.rug.prop = 0
                    self.rug.is_fixed = False
                    self.rug.drop(newroom)
                    for oldroom in (oldroom1, oldroom2):
                        for o in self.objects_at(oldroom):
                            o.drop(newroom)
                    self.move_to(newroom)
                self.yesno(self.messages[49], callback, casual=True)
                return
        elif obj is self.troll:
            self.write_message(157)
        elif obj is self.bear:
            self.write_message(165 + (self.bear.prop + 1) // 2)
        else:
            self.write_message(44)
        self.finish_turn()

    def i_pour(self, verb):  #9130
        if self.bottle.contents is None:
            self.ask_verb_what(verb)
        else:
            self.t_pour(verb, self.bottle.contents)

    def t_pour(self, verb, obj):
        if obj is self.bottle:
            return self.i_pour(verb)
        if not obj.is_toting:
            self.write(verb.default_message)
        elif obj is not self.oil and obj is not self.water:
            self.write_message(78)
        else:
            self.bottle.prop = 1
            self.bottle.contents = None
            obj.hide()
            if self.is_here(self.plant):
                if obj is not self.water:
                    self.write_message(112)
                else:
                    self.write(self.plant.messages[self.plant.prop + 1])
                    self.plant.prop = (self.plant.prop + 2) % 6
                    self.plant2.prop = self.plant.prop // 2
                    return self.move_to()
            elif self.is_here(self.door):
                #9132
                self.door.prop = 1 if obj is self.oil else 0
                self.write_message(113 + self.door.prop)
            else:
                self.write_message(77)
        return self.finish_turn()

    def i_eat(self, verb):  #8140
        if self.is_here(self.food):
            self.t_eat(verb, self.food)
        else:
            self.ask_verb_what(verb)

    def t_eat(self, verb, obj):  #9140
        if obj is self.food:
            #8142
            self.food.destroy()
            self.write_message(72)
        elif obj in (self.bird, self.snake, self.clam, self.oyster,
                     self.dwarf, self.dragon, self.troll, self.bear):
            self.write_message(71)
        else:
            self.write(verb.default_message)
        self.finish_turn()

    def i_drink(self, verb):  #9150
        if self.is_here(self.water) or self.loc.liquid is self.water:
            self.t_drink(verb, self.water)
        else:
            self.ask_verb_what(verb)

    def t_drink(self, verb, obj):  #9150
        if obj is not self.water:
            self.write_message(110)
        elif self.is_here(self.water):
            self.bottle.prop = 1
            self.bottle.contents = None
            self.water.destroy()
            self.write_message(74)
        elif self.loc.liquid is self.water:
            self.write(verb.default_message)
        self.finish_turn()

    def t_rub(self, verb, obj):  #9160
        if obj is self.lamp:
            self.write(verb.default_message)
        else:
            self.write_message(71)
        self.finish_turn()

    def t_throw(self, verb, obj):  #9170
        if obj is self.rod and not self.rod.is_toting and self.rod2.is_toting:
            obj = self.rod2

        if not obj.is_toting:
            self.write(verb.default_message)
            self.finish_turn()
            return

        if obj.is_treasure and self.is_here(self.troll):
            # Pay the troll toll
            self.write_message(159)
            obj.destroy()
            self.troll.destroy()
            self.troll2.rooms = list(self.troll.starting_rooms)
            self.finish_turn()
            return

        if obj is self.food and self.is_here(self.bear):
            self.t_feed(verb, self.bear)
            return

        if obj is not self.axe:
            self.t_drop(verb, obj)
            return

        dwarves_here = [ d for d in self.dwarves if d.room is self.loc ]
        if dwarves_here:
            # 1/3rd chance that throwing the axe kills a dwarf
            if self.choice((True, False, False)):
                self.dwarves.remove(dwarves_here[0])
                self.dwarves_killed += 1
                if self.dwarves_killed == 1:
                    self.write_message(149)
                else:
                    self.write_message(47)
            else:
                self.write_message(48)  # Miss
            self.axe.drop(self.loc)
            self.do_motion(self.vocabulary['null'])
            return

        if self.is_here(self.dragon) and self.dragon.prop == 0:
            self.write_message(152)
            self.axe.drop(self.loc)
            self.do_motion(self.vocabulary['null'])
            return

        if self.is_here(self.troll):
            self.write_message(158)
            self.axe.drop(self.loc)
            self.do_motion(self.vocabulary['null'])
            return

        if self.is_here(self.bear) and self.bear.prop == 0:
            self.write_message(164)
            self.axe.drop(self.loc)
            self.axe.is_fixed = True
            self.axe.prop = 1
            self.finish_turn()
            return

        self.t_attack(verb, None)

    def i_quit(self, verb):  #8180
        def callback(yes):
            self.write_message(54)
            if yes:
                self.score_and_exit()
        self.yesno(self.messages[22], callback)

    def t_find(self, verb, obj):  #9190
        if obj.is_toting:
            self.write_message(24)
        elif self.is_closed:
            self.write_message(138)
        elif (self.is_here(obj) or
            obj is self.loc.liquid or
            obj is self.dwarf and any(d.room is self.loc for d in self.dwarves)):
            self.write_message(94)
        else:
            self.write(verb.default_message)
        self.finish_turn()

    t_inventory = t_find

    def i_inventory(self, verb):  #8200
        first = True
        objs = [ obj for obj in self.inventory if obj is not self.bear ]
        for obj in objs:
            if first:
                self.write_message(99)
                first = False
            self.write(obj.inventory_message)
        if self.bear.is_toting:
            self.write_message(141)
        if not objs:
            self.write_message(98)
        self.finish_turn()

    def t_feed(self, verb, obj):  #9210
        if obj is self.bird:
            self.write_message(100)
        elif obj is self.troll:
            self.write_message(182)
        elif obj is self.dragon:
            if self.dragon.prop != 0:
                self.write_message(110)
            else:
                self.write_message(102)
        elif obj is self.snake:
            if self.is_closed or not self.is_here(self.bird):
                self.write_message(102)
            else:
                self.write_message(101)
                self.bird.destroy()
                self.bird.prop = 0
                self.impossible_treasures += 1
        elif obj is self.dwarf:
            if self.is_here(self.food):
                self.write_message(103)
                self.dwarf_stage += 1
            else:
                self.write(verb.default_message)
        elif obj is self.bear:
            if not self.is_here(self.food):
                if self.bear.prop == 0:
                    self.write_message(102)
                elif self.bear.prop == 3:
                    self.write_message(110)
                else:
                    self.write(verb.default_message)
            else:
                self.food.destroy()
                self.bear.prop = 1
                self.axe.is_fixed = False
                self.axe.prop = 0
                self.write_message(168)
        else:
            self.write_message(14)
        self.finish_turn()

    def i_fill(self, verb):  #9220
        if self.is_here(self.bottle):
            return self.t_fill(verb, self.bottle)
        self.ask_verb_what(verb)

    def t_fill(self, verb, obj):
        if obj is self.bottle:
            liquid = self.loc.liquid
            if liquid is None:
                self.write_message(106)
            elif self.bottle.contents:
                self.write_message(105)
            else:
                self.bottle.contents = liquid
                if self.bottle.is_toting:
                    liquid.is_toting = True
                if liquid is self.oil:
                    self.write_message(108)
                else:
                    self.write_message(107)
        elif obj is self.vase:
            #9222
            if self.vase.is_toting:
                if self.loc.liquid is None:
                    self.write_message(144)
                else:
                    self.write_message(145)
                    self.vase.drop(self.loc)
                    self.vase.prop = 2
                    self.vase.is_fixed = True
            else:
                self.write(verb.default_message)
        else:
            self.write(verb.default_message)
        self.finish_turn()

    def t_blast(self, verb, obj=None):  #9230
        if self.rod2.prop < 0 or not self.is_closed:
            self.write(verb.default_message)
            self.finish_turn()
            return
        if self.is_here(self.rod2):
            self.bonus = 135
        elif self.loc.n == 115:
            self.bonus = 134
        else:
            self.bonus = 133
        self.write_message(self.bonus)
        self.score_and_exit()

    i_blast = t_blast

    def i_score(self, verb):  #8240
        score, max_score = self.compute_score(for_score_command=True)
        self.write('If you were to quit now, you would score {}'
                   ' out of a possible {}.\n'.format(score, max_score))
        def callback(yes):
            self.write_message(54)
            if yes:
                self.score_and_exit()
        self.yesno(self.messages[143], callback)

    def i_fee(self, verb):  #8250
        for n in range(5):
            if verb.synonyms[n].text == verb.text:
                break  # so that 0=fee, 1=fie, 2=foe, 3=foo, 4=fum
        if n == 0:
            self.foobar = self.turns
            self.write_message(54)
        elif n != self.turns - self.foobar:
            self.write_message(151)
        elif n < 3:
            self.write_message(54)
        else:
            self.foobar = -1
            eggs = self.eggs
            start = eggs.starting_rooms[0]
            if (eggs.is_at(start) or eggs.is_toting and self.loc is start):
                self.write_message(54)
            else:
                troll = self.troll
                if not eggs.rooms and not troll.rooms and not troll.prop:
                    self.troll.prop = 1
                if self.loc is start:
                    self.write(eggs.messages[0])
                elif self.is_here(eggs):
                    self.write(eggs.messages[1])
                else:
                    self.write(eggs.messages[2])
                eggs.rooms = list(eggs.starting_rooms)
                eggs.is_toting = False
        self.finish_turn()

    def i_brief(self, verb):  #8260
        self.write_message(156)
        self.full_description_period = 10000
        self.look_complaints = 0
        self.finish_turn()

    def i_read(self, verb):  #8270
        if self.is_closed and self.oyster.is_toting:
            return self.t_read(verb, self.oyster)
        objs = (self.magazine, self.tablet, self.message)
        objs = list(filter(self.is_here, objs))
        if len(objs) != 1 or self.is_dark:
            self.ask_verb_what(verb)
        else:
            self.t_read(verb, objs[0])

    def t_read(self, verb, obj):  #9270
        if self.is_dark:
            return self.i_see_no(obj.names[0])
        elif (obj is self.oyster and not self.hints[2].used and
              self.oyster.is_toting):
            def callback(yes):
                if yes:
                    self.hints[2].used = True
                    self.write_message(193)
                else:
                    self.write_message(54)
            self.yesno(self.messages[192], callback)
        elif obj is self.oyster and self.hints[2].used:
            self.write_message(194)
        elif obj is self.message:
            self.write_message(191)
        elif obj is self.tablet:
            self.write_message(196)
        elif obj is self.magazine:
            self.write_message(190)
        else:
            self.write(verb.default_message)
        self.finish_turn()

    def t_break(self, verb, obj):  #9280
        if obj is self.vase and self.vase.prop == 0:
            self.write_message(198)
            if self.vase.is_toting:
                self.vase.drop(self.loc)
            self.vase.prop = 2
            self.vase.is_fixed = True
        elif obj is self.mirror and self.is_closed:
            self.write_message(197)
            self.wake_repository_dwarves()
            return
        elif obj is self.mirror:
            self.write_message(148)
        else:
            self.write(verb.default_message)
        self.finish_turn()

    def t_wake(self, verb, obj):  #9290
        if obj is self.dwarf and self.is_closed:
            self.write_message(199)
            self.wake_repository_dwarves()
        else:
            self.write(verb.default_message)
            self.finish_turn()

    def i_suspend(self, verb):
        self.write('Provide "{}" with a filename or open file'.format(
                verb.text))
        self.finish_turn()

    def t_suspend(self, verb, obj):
        if isinstance(obj, str):
            if os.path.exists(obj):  # pragma: no cover
                self.write('I refuse to overwrite an existing file.')
                return
            savefile = open(obj, 'wb')
        else:
            savefile = obj
        r = self.random_generator  # must replace live object with static state
        self.random_state = r.getstate()
        try:
            del self.random_generator
            savefile.write(zlib.compress(pickle.dumps(self), 9))
        finally:
            self.random_generator = r
            if savefile is not obj:
                savefile.close()
        self.write('Game saved')

    def i_hours(self, verb):
        self.write('Open all day')

    @classmethod
    def resume(self, obj):
        """Returns an Adventure game saved to the given file."""
        if isinstance(obj, str):
            savefile = open(obj, 'rb')
        else:
            savefile = obj
        game = pickle.loads(zlib.decompress(savefile.read()))
        if savefile is not obj:
            savefile.close()
        # Reinstate the random number generator.
        game.random_generator = random.Random()
        game.random_generator.setstate(game.random_state)
        del game.random_state
        return game

    def should_offer_hint(self, hint, obj): #40000
        if hint.n == 4:  # cave
            return self.grate.prop == 0 and not self.is_here(self.keys)

        elif hint.n == 5:  # bird
            bird = self.bird
            return self.is_here(bird) and self.rod.is_toting and obj is bird

        elif hint.n == 6:  # snake
            return self.is_here(self.snake) and not self.is_here(self.bird)

        elif hint.n == 7:  # maze
            return (not len(self.objects_here) and
                    not len(self.objects_at(self.oldloc)) and
                    not len(self.objects_at(self.oldloc2)) and
                    len(self.inventory) > 1)

        elif hint.n == 8:  # dark
            return self.emerald.prop != 1 and self.platinum.prop != 1

        elif hint.n == 9:  # witt
            return True

    def start_closing_cave(self):  #10000
        self.grate.prop = 0
        self.fissure.prop = 0
        del self.dwarves[:]
        self.troll.destroy()
        self.troll2.rooms = list(self.troll.starting_rooms)
        if self.bear.prop != 3:
            self.bear.destroy()
        for obj in self.chain, self.axe:
            obj.prop = 0
            obj.is_fixed = False
        self.write_message(129)
        self.clock1 = -1
        self.is_closing = True

    def close_cave(self):  #11000
        ne = self.rooms[115]  # ne end of repository
        sw = self.rooms[116]
        for obj in (self.bottle, self.plant, self.oyster, self.lamp,
                    self.rod, self.dwarf):
            obj.prop = -2 if obj is self.bottle else -1
            obj.drop(ne)
        self.loc = self.oldloc = self.oldloc2 = ne
        for obj in (self.grate, self.snake, self.bird, self.cage,
                    self.rod2, self.pillow):
            obj.prop = -2 if (obj is self.bird or obj is self.snake) else -1
            obj.drop(sw)
        self.mirror.rooms = [ne, sw]
        self.mirror.is_fixed = 1
        self.is_closed = True
        for obj in self.inventory:
            obj.is_toting = False
        self.write_message(132)
        self.move_to()

    # TODO: 12000
    # TODO: 12200
    # TODO: 12400
    # TODO: 12600

    def wake_repository_dwarves(self):  #19000
        self.write_message(136)
        self.score_and_exit()

    def compute_score(self, for_score_command=False):  #20000
        score = maxscore = 2

        for treasure in self.treasures:
            # if ptext(0) is zero?
            if treasure.n > self.chest.n:
                value = 16
            elif treasure is self.chest:
                value = 14
            else:
                value = 12

            maxscore += value

            if treasure.prop >= 0:
                score += 2
            if treasure.rooms and treasure.rooms[0].n == 3 \
                    and treasure.prop == 0:
                score += value - 2

        maxscore += self.max_deaths * 10
        score += (self.max_deaths - self.deaths) * 10

        maxscore += 4
        if not for_score_command and not self.gave_up:
            score += 4

        maxscore += 25
        if self.dwarf_stage:
            score += 25

        maxscore += 25
        if self.is_closing:
            score += 25

        maxscore += 45
        if self.is_closed:
            score += {0: 10, 135: 25, 134: 30, 133: 45}[self.bonus]

        maxscore += 1
        if 108 in (room.n for room in self.magazine.rooms):
            score += 1

        for hint in list(self.hints.values()):
            if hint.used:
                score -= hint.penalty

        return score, maxscore

    def score_and_exit(self):
        score, maxscore = self.compute_score()
        self.write('\nYou scored {} out of a possible {} using {} turns.'
                   .format(score, maxscore, self.turns))
        for i, (minimum, text) in enumerate(self.class_messages):
            if minimum >= score:
                break
        self.write('\n{}\n'.format(text))
        if i < len(self.class_messages) - 1:
            d = self.class_messages[i+1][0] + 1 - score
            self.write('To achieve the next higher rating, you need'
                       ' {} more point{}\n'.format(d, 's' if d > 1 else ''))
        else:
            self.write('To achieve the next higher rating '
                       'would be a neat trick!\n\nCongratulations!!\n')
        self.is_done = True
