"""How we keep track of the state of the game."""

import random
from operator import attrgetter
from .data import Data
from .model import Room, Message, Dwarf, Pirate

YESNO_ANSWERS = {'y': True, 'yes': True, 'n': False, 'no': False}

class Game(Data):

    look_complaints = 3  # how many times to "SORRY, BUT I AM NOT ALLOWED..."
    full_description_period = 5  # how often we use a room's full description
    full_wests = 0  # how many times they have typed "west" instead of "w"
    dwarf_stage = 0  # how active the dwarves are
    dwarves_killed = 0
    gave_up = False
    treasures_not_found = 0  # how many treasures have not yet been seen
    impossible_treasures = 0  # how many treasures can never be retrieved
    lamp_turns = 330
    warned_about_dim_lamp = False
    bonus = 0  # how they exited the final bonus round
    deaths = 0  # how many times the player has died
    max_deaths = 4  # how many times the player can die
    turns = 0

    def __init__(self, writer, end_game, seed=None):
        Data.__init__(self)
        self.writer = writer
        self.end_game = end_game  # function to call to end us
        self.yesno_callback = False
        self.yesno_casual = False       # whether to insist they answer

        self.is_closing = False         # is the cave closing?
        self.panic = False              # they tried to leave during closing?
        self.is_closed = False          # is the cave closed?
        self.could_fall_in_pit = False  # could the player fall into a pit?

        self.random_instance = random.Random()
        if seed is not None:
            self.random_instance.seed(seed)

        self.random = self.random_instance.random
        self.randint = self.random_instance.randint
        self.choice = self.random_instance.choice

    def write(self, s):
        """Output the Unicode representation of `s`."""
        s = str(s).upper()
        if s:
            self.writer(s)
            self.writer('\n')

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
        return [ obj for obj in self.object_list if obj.n >= 50 ]

    @property
    def objects_here(self):
        return self.objects_at(self.loc)

    def objects_at(self, room):
        return [ obj for obj in self.object_list if room in obj.rooms ]

    def is_here(self, obj):
        return obj.is_toting or (self.loc in obj.rooms)

    # Game startup

    def start(self):
        """Start the game."""
        self.chest_room = self.rooms[114]
        self.yesno(self.messages[65], self.start2)  # want instructions?

    def start2(self, yes):
        """Print out instructions if the user wants them."""
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
                    del self.dwarves[self.randint(0, len(self.dwarves) - 1)]
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
                    #knfloc here
                    if self.random() < .095 * (self.dwarf_stage - 2):
                        knife_wounds += 1

            else:  # the pirate
                pirate = dwarf

                if self.loc is self.chest_room or self.chest.prop >= 0:
                    continue  # decide that the pirate is not really here

                treasures = [ t for t in self.treasures if t.is_toting ]
                if (self.platinum in treasures and self.loc.n in (100, 101)):
                    treasures.remove(self.pyramid)

                if not treasures:
                    h = any( t for t in self.treasures if self.is_here(t) )
                    one_treasure_left = (self.treasures_not_found ==
                                         self.impossible_treasures + 1)
                    shiver_me_timbers = (
                        one_treasure_left and not h and self.chest.room.n == 0
                        and self.is_here(self.lamp) and self.lamp.prop == 1
                        )

                    if not shiver_me_timbers:
                        if (pirate.old_room != pirate.room
                            and self.random() < .2):
                            self.write_message(127)
                        continue  # proceed to the next character? aren't any!

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
            self.write('There are %d threatening little dwarves in the'
                       ' room with you.\n' % dwarf_count)

        if dwarf_attacks and self.dwarf_stage == 2:
            self.dwarf_stage = 3

        if dwarf_attacks == 1:
            self.write_message(5)
            k = 52
        elif dwarf_attacks:
            self.write('%d of them throw knives at you!\n' % dwarf_attacks)
            k = 6

        if not dwarf_attacks:
            pass
        elif not knife_wounds:
            self.write_message(k)
        else:
            if knife_wounds == 1:
                self.write_message(k + 1)
            else:
                self.write('%d of them get you!\n' % knife_wounds)
            self.oldloc2 = self.loc
            self.die()
            return

        self.describe_location()

    def describe_location(self):  #2000

        # check for whether they already have died? or do as sep func?

        loc = self.loc

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

    def say_okay_and_finish(self):  #2009
        self.write_message(54)
        self.finish_turn()

    #2009 sets SPK="OK" then...
    #2011 speaks SPK then...
    #2012 blanks VERB and OBJ and calls:
    def finish_turn(self, obj=None):  #2600

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
                            else:
                                self.write_message(54)

                        self.yesno(hint.question, callback)
                        return
            else:
                hint.turn_counter = 0

        if self.is_closed:
            if self.oyste.prop < 0: # and toting it
                self.write(self.oyste.messages[1])
            # put closing-time "prop" special case here

        self.could_fall_in_pit = self.is_dark  #2605

        # remove knife from cave if they moved away from it

        # Advance random number generator so each input affects future.
        self.random()

    # The central do_command() method, that should be called over and
    # over again with words supplied by the user.

    def do_command(self, words):  #2608
        """Parse and act upon the command in the list of strings `words`."""

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

        self.turns += 1

        if self.lamp.prop:
            self.lamp_turns -= 1

        if self.lamp_turns <= 30 and self.is_here(self.battery) \
                and self.battery.prop == 0 and self.is_here(self.lamp):
            self.write_message(188)
            self.battery.prop = 1
            if self.battery.is_toting:
                self.battery.drop(self.loc)
            self.lamp_turns += 2500
            self.warned_about_dim_lamp = False

        if self.lamp_turns == 0:
            self.lamp_turns = -1
            self.lamp.prop = 0
            if self.is_here(self.lamp):
                self.write_message(184)
        elif self.lamp_turns < 0 and self.loc.is_aboveground:
            self.write_message(185)
            self.gave_up = True
            self.score_and_exit()
            return
        elif self.lamp_turns <= 30 and not self.warned_about_dim_lamp \
                and self.is_here(self.lamp):
            self.warned_about_dim_lamp = True
            if self.battery.prop == 1:
                self.write_message(189)
            elif not self.battery.rooms:
                self.write_message(183)
            else:
                self.write_message(187)

        if words[0] not in self.vocabulary:
            n = self.randint(1, 5)
            if n == 1:
                self.write_message(61)
            elif n == 2:
                self.write_message(13)
            else:
                self.write_message(60)
            self.finish_turn()
            return

        word = self.vocabulary[words[0]]

        if word.kind == 'motion':
            if words[0] == 'west':
                self.full_wests += 1
                if self.full_wests == 10:
                    self.write_message(17)
            self.do_motion(word)

        elif word.kind == 'verb':
            prefix = 't_' if len(words) == 2 else 'i_'  # (in)transitive
            if len(words) == 2:
                word2 = self.vocabulary[words[1]]
                obj = self.objects[word2.n % 1000]
                #5000
                if not self.is_here(obj):
                    self.write('I see no %s here.\n' % obj.names[0])
                    self.finish_turn(obj)
                    return
                args = (word, obj)
            else:
                args = (word,)
            getattr(self, prefix + word.names[0])(*args)

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
            self.write(self.messages[57 if self.loc.is_aboveground else 58])
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

                else:
                    raise NotImplementedError(move.action)

        #50
        n = word.n
        if 29 <= n <= 30 or 43 <= n <= 50:
            self.write_message(9)
        elif n in (7, 36, 37):
            self.write_message(10)
        elif n in (11, 19):
            self.write_message(11)
        elif word == 'find' or word == 'invent':  # ? this might be wrong
            self.write_message(59)
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

        if self.is_closing:
            self.write_message(131)
            self.score_and_exit()
            return

        def callback(yes):
            if yes:
                self.write_message(80 + self.deaths * 2)
                if self.deaths < self.max_deaths:
                    # do water and oil thing
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

    def print_do_what(self, verb, *args):  #8000
        self.write('%s What?\n' % verb.names[0])
        self.finish_turn()

    i_drop = print_do_what
    i_say = print_do_what
    i_wave = print_do_what
    i_calm = print_do_what
    i_rub = print_do_what
    i_toss = print_do_what
    i_find = print_do_what
    i_feed = print_do_what
    i_break = print_do_what
    i_wake = print_do_what

    def t_carry(self, verb, obj):  #9010
        if obj.is_toting:
            self.write_message(verb.default_message or 54)
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
        # do liquids here
        if len(self.inventory) >= 7:
            self.write_message(92)
            self.finish_turn()
            return
        if obj is self.bird and obj.prop == 0:
            if self.rod.is_toting:
                self.write_message(26)
                self.finish_turn()
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
        # one last liquid thing
        self.say_okay_and_finish()

    def t_drop(self, verb, obj):  #9020
        if obj is self.rod and not self.rod.is_toting and self.rod2.is_toting:
            obj = self.rod2
        if not obj.is_toting:
            self.write_message(verb.default_message)
            self.finish_turn()
            return

        bird, snake, dragon, bear, troll = self.bird, self.snake, self.dragon, \
            self.bear, self.troll

        if obj is bird and self.is_here(snake):
            self.write_message(30)
            if self.is_closed:
                self.write_message(136)
                self.score_and_exit()
            snake.prop = 1
            snake.destroy()
            bird.prop = 0
            bird.drop(self.loc)

        elif obj is self.coins and self.is_here(self.machine):
            obj.destroy()
            self.battery.drop(self.loc)
            self.write(self.battery.messages[0])

        elif obj is bird and self.is_here(dragon) and dragon.prop == 0:
            self.write_message(154)
            bird.destroy()
            bird.prop = 0
            if snake.rooms:
                self.impossible_treasures += 1

        elif obj is bear and troll.is_at(self.loc):
            self.write_message(163)
            troll.destroy()  # and something about fixed?
            # something else about fixed and troll2
            # juggle?
            troll.prop = 2
            bear.drop(self.loc)

        elif obj is self.vase and self.loc is not self.rooms[96]:
            if self.pillow.is_at(self.loc):
                self.vase.prop = 0
            else:
                self.vase.prop = 2
                self.vase.is_fixed = True
            self.write(self.vase.messages[self.vase.prop + 1])

        else:
            if obj is self.cage and self.bird.prop != 0:
                bird.drop(self.loc)
            elif obj is self.bird:
                obj.prop = 0
            self.write_message(54)
            obj.drop(self.loc)

        self.finish_turn()
        return

    def t_unlock(self, verb, obj):  #9040
        if obj is self.clam or obj is self.oyster:
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
            # if keys are not here, write message 31 and give up
            if obj is self.chain:
                raise NotImplementedError()  #9048
            else:
                if self.is_closing:
                    raise NotImplementedError()  # set panic clock etc
                else:
                    oldprop = obj.prop
                    obj.prop = 0 if verb == 'lock' else 1
                    self.write_message(34 + oldprop + 2 * obj.prop)
        else:
            self.write(verb.names)
            self.write(obj.names)
            self.write(verb.default_message)
        self.finish_turn()

    def t_light(self, verb, obj):  #9070
        # if not here lamp: 2011
        # if lamp out: 2011
        self.objects['lamp'].prop = 1
        self.write_message(39)
        if self.loc.is_dark:
            self.describe_location()
        else:
            self.finish_turn()

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

    def t_attack(self, verb, obj):  #9120
        if obj is None:
            raise NotImplementedError()
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
                die
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
            self.troll2.rooms = self.troll.rooms
            self.troll.destroy()
            self.finish_turn()
            return

        if obj is self.food and self.is_here(self.bear):
            self.t_feed(self.bear)
            return

        if obj is not self.axe:
            self.t_drop(verb, obj)
            return

        dwarves_here = [ d for d in self.dwarves if d.room is self.loc ]
        if dwarves_here:
            if self.randint(0, 2):  # 1/3rd chance of killing a dwarf
                self.write_message(48)  # Miss
            else:
                self.dwarves.remove(dwarves_here[0])
                self.dwarves_killed += 1
                if self.dwarves_killed == 1:
                    self.write_message(149)
                else:
                    self.write_message(47)
            self.axe.drop(self.loc)
            self.do_motion(self.vocabulary['null'])
            return

        if self.is_here(self.dragon) and self.dragon.prop == 0:
            self.write_message(152)
            self.axe.drop(self.loc)
            self.do_motion(self.vocabulary['null'])
            return

        if self.is_here(self.troll):
            self.write_message(156)
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

    def i_score(self, verb):  #8240
        score, max_score = self.compute_score(for_score_command=True)
        self.write('If you were to quit now, you would score %d'
                   ' out of a possible %d.\n' % (score, max_score))
        def callback(yes):
            self.write_message(54)
            if yes:
                self.score_and_exit()
                return
        self.yesno(self.messages[143], callback)

    def should_offer_hint(self, hint, obj): #40000
        if hint == 4:  # cave
            return self.grate.prop == 0 and not self.is_here(self.keys)

        elif hint == 5:  # bird
            bird = self.bird
            return self.is_here(bird) and self.rod.is_toting and obj is bird

        elif hint == 6:  # snake
            return self.is_here(self.snake) and not self.is_here(bird)

        elif hint == 7:  # maze
            return (not len(self.objects_here) and
                    not len(self.objects_at(self.oldloc)) and
                    not len(self.objects_at(self.oldloc2)) and
                    len(self.inventory) > 1)

        elif hint == 8:  # dark
            return self.emerald.prop != 1 and self.pyramid.prop != 1

        elif hint == 9:  # witt
            return True

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
            maxscore += 25

        maxscore += 45
        if self.is_closed:
            score += {0: 10, 135: 25, 134: 30, 133: 45}[self.bonus]

        maxscore += 1
        if self.magazine.rooms[0].n == 108:
            score += 1

        for hint in list(self.hints.values()):
            if hint.used:
                score -= hint.penalty

        return score, maxscore

    def score_and_exit(self):
        score, maxscore = self.compute_score()
        self.write('\nYou scored %d out of a possible %d using %d turns.'
                   % (score, maxscore, self.turns))
        for i, (minimum, text) in enumerate(self.class_messages):
            if minimum >= score:
                break
        self.write('\n%s\n' % text)
        if i < len(self.class_messages) - 1:
            d = self.class_messages[i+1][0] + 1 - score
            self.write('To achieve the next higher rating, you need'
                       ' %s more point%s\n' % (d, 's' if d > 1 else ''))
        else:
            self.write('To achieve the next higher rating '
                       'would be a neat trick!\n\nCongratulations!!\n')
        self.end_game()
