"""Offer Adventure at a custom command prompt."""

import re
from sys import stdout
from time import sleep
from . import load_advent_dat
from .game import Game

BAUD = 1200

def baudout(s):
    for c in s:
        sleep(9. / BAUD)  # 8 bits + 1 stop bit @ the given baud rate
        stdout.write(c)
        stdout.flush()

game = Game()
load_advent_dat(game)
game.start()
baudout(game.output)
while not game.is_finished:
    line = input('> ')
    words = re.findall(r'\w+', line)
    if words:
        baudout(game.do_command(words))
