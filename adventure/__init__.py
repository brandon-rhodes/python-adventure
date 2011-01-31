"""The Adventure game."""

import os
from .data import parse
from .game import Game
from .prompt import install_builtins

def load_advent_dat(data):
    datapath = os.path.join(os.path.dirname(__file__), 'advent.dat')
    with open(datapath, 'r', encoding='ascii') as datafile:
        parse(data, datafile)

def play(seed=None):
    """Turn the Python prompt into an Adventure game.

    With `seed` the caller can supply an integer to start the random
    number generator at a known state.  When `quiet` is true, no output
    is printed as the game is played; the caller of a command has to
    manually check `_game.output` for the result, which makes it
    possible to write very quiet tests.

    """
    global _game

    _game = Game(seed)
    load_advent_dat(_game)
    install_builtins(_game)
    _game.start()
    print(_game.output[:-1])
