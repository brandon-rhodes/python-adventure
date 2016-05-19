"""The Adventure game.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""

import argparse
import os
import re
import readline
from sys import executable, stdout
from time import sleep
from game import Game

def loop():
    """Main Game Loop"""
    if args.savefile is None:
        game = Game()
        load_advent_dat(game)
        game.start()
        baudout(game.output)
    else:
        game = Game.resume(args.savefile)
        baudout('GAME RESTORED\n')

    while not game.is_finished:
        line = input('> ')
        words = re.findall(r'\w+', line)
        if words:
            baudout(game.do_command(words))

def load_advent_dat(data):
    import os
    from .data import parse

    datapath = os.path.join(os.path.dirname(__file__), 'advent.dat')
    with open(datapath, 'r', encoding='ascii') as datafile:
        parse(data, datafile)

def play(seed=None):
    """Turn the Python prompt into an Adventure game.

    With optional the `seed` argument the caller can supply an integer
    to start the Python random number generator at a known state.

    """
    global _game

    from game import Game

    _game = Game(seed)
    load_advent_dat(_game)
    _game.start()
    print(_game.output[:-1])

def resume(savefile, quiet=False):
    global _game

    from game import Game

    _game = Game.resume(savefile)
    if not quiet:
        print('GAME RESTORED\n')
