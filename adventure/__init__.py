"""The Adventure game."""

import sys

def end_game():
    pass

def play(seed=None):
    """Turn the Python prompt into an Adventure game."""

    from .game import Game
    from .interpret import read_data_from_nearby_file
    from .prompt import install_builtins

    game = Game(sys.stdout.write, end_game, seed)
    read_data_from_nearby_file(game)
    install_builtins(game)
    game.start()
