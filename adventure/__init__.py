"""The Adventure game."""

import sys

def play():
    """Turn the Python prompt into an Adventure game."""

    from .game import Game
    from .interpret import read_data_from_nearby_file
    from .prompt import install_builtins

    game = Game(sys.stdout.write)
    read_data_from_nearby_file(game)
    install_builtins(game)
    game.start()
