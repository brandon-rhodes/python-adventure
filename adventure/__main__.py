"""Offer Adventure at a custom command prompt."""

import argparse
import os
import re
from sys import executable, stdout
from time import sleep
from . import load_advent_dat
from .game import Game

BAUD = 1200

def baudout(s):
    for c in s:
        sleep(9. / BAUD)  # 8 bits + 1 stop bit @ the given baud rate
        stdout.write(c)
        stdout.flush()

def loop():
    parser = argparse.ArgumentParser(
        description='Adventure into the Colossal Caves.',
        prog='{} -m adventure'.format(os.path.basename(executable)))
    parser.add_argument(
        'savefile', nargs='?', help='The filename of game you have saved.')
    args = parser.parse_args()

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

try:
    loop()
except EOFError:
    pass
