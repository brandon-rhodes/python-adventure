"""Offer Adventure at a custom command prompt.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""
import argparse
import os
import re
import readline
import sys
from time import sleep
from . import load_advent_dat
from .game import Game

BAUD = 1200

def baudout(s):
    out = sys.stdout
    for c in s:
        sleep(9. / BAUD)  # 8 bits + 1 stop bit @ the given baud rate
        out.write(c)
        out.flush()

def loop(args):
    parser = argparse.ArgumentParser(
        description='Adventure into the Colossal Caves.',
        prog='{} -m adventure'.format(os.path.basename(sys.executable)))
    parser.add_argument(
        'savefile', nargs='?', help='The filename of game you have saved.')
    args = parser.parse_args(args)

    if args.savefile is None:
        game = Game()
        load_advent_dat(game)
        game.start()
        baudout(game.output)
    else:
        game = Game.resume(args.savefile)
        baudout('GAME RESTORED\n')

    while not game.is_finished:
        line = input('> ').lower()
        words = re.findall(r'\w+', line)
        if words:
            baudout(game.do_command(words))

if __name__ == '__main__':
    try:
        loop(sys.argv[1:])
    except EOFError:
        pass
