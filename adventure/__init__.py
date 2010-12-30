"""The Adventure game."""

import sys

def end_game():
    pass

def play(seed=None):
    """Turn the Python prompt into an Adventure game."""

    global _game

    from .game import Game
    from .interpret import read_data_from_nearby_file
    from .prompt import install_builtins

    _game = Game(sys.stdout.write, end_game, seed)
    read_data_from_nearby_file(_game)
    install_builtins(_game)
    _game.start()
