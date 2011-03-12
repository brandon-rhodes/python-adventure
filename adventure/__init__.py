"""The Adventure game."""

def load_advent_dat(data):
    import os
    from .data import parse

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

    from .game import Game
    from .prompt import install_words

    _game = Game(seed)
    load_advent_dat(_game)
    install_words(_game)
    _game.start()
    print(_game.output[:-1])

def resume(savefile, quiet=False):
    global _game

    from .game import Game
    from .prompt import install_words

    _game = Game.resume(savefile)
    install_words(_game)
    if not quiet:
        print('GAME RESTORED\n')
