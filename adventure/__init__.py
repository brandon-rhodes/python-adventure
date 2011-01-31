"""The Adventure game."""

def end_game():
    pass

def play(seed=None):
    """Turn the Python prompt into an Adventure game.

    With `seed` the caller can supply an integer to start the random
    number generator at a known state.  When `quiet` is true, no output
    is printed as the game is played; the caller of a command has to
    manually check `_game.output` for the result, which makes it
    possible to write very quiet tests.

    """
    global _game

    from .game import Game
    from .interpret import read_data_from_nearby_file
    from .prompt import install_builtins

    _game = Game(end_game, seed)
    read_data_from_nearby_file(_game)
    install_builtins(_game)
    _game.start()
    print(_game.output[:-1])
