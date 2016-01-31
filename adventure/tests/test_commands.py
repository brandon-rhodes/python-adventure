"""Test suite.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""
from unittest import TestCase
from adventure import load_advent_dat
from adventure.game import Game

class CommandTest(TestCase):

    def setUp(self):
        game = Game()
        load_advent_dat(game)
        self.words = set(w.synonyms[0].text for w in game.vocabulary.values())
        self.words.remove('suspend')

    def test_intransitive_commands_should_not_throw_exceptions(self):
        for word in self.words:
            game = Game()
            load_advent_dat(game)
            game.start()
            game.do_command(['no'])  # WOULD YOU LIKE INSTRUCTIONS?
            game.do_command([word])

    def test_transitive_commands_should_not_throw_exceptions(self):
        for word in self.words:
            game = Game()
            load_advent_dat(game)
            game.start()
            game.do_command(['no'])  # WOULD YOU LIKE INSTRUCTIONS?
            game.do_command(['enter'])  # so we are next to lamp
            game.do_command([word, 'lamp'])
