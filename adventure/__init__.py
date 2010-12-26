"""The Adventure game."""

import sys

def play():
    """Turn the Python prompt into an Adventure game."""
    from .game import Game
    from .interpret import read_data_from_nearby_file
    data = read_data_from_nearby_file()
    game = Game(data, sys.stdout.write, None)
    game.start()
