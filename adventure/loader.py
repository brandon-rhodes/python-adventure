"""The Adventure game.

Copyright 2010-2015 Brandon Rhodes.  Licensed as free software under the
Apache License, Version 2.0 as detailed in the accompanying README.txt.

"""

#------------------------------------------
from game import Game
from time import sleep
import os
import re
from data import parse

user_saves = {}
save_dir = "saves/"

def user_exists(user_id):
    return user_id in iser_saves.keys()

def new_game(user_id, seed=None):
    """Create new game"""
    game = Game(seed)
    user_saves[user_id] = game
    load_advent_dat(game)
    game.start()
    return game.output

def respond(user_id, user_response):
    """Gets the game response for a specific user_id and user_response"""
    game = user_saves[user_id]
    user_tupl_resp = tuple(user_response.split(" "))
    return game.do_command(user_tupl_resp)

def reset_game(user_id, seed=None):
    """Clears the game for a specific user_id, need to wipe memory and file game"""
    new_game(user_id)

def db_load(database=user_saves):
    """Set up database files"""
    for dir_name, sub_dir_list, file_list in os.walk(save_dir):
        for fname in file_list:
            user_saves[fname] = Game.resume(fname)

def db_save(database=user_saves):
    """Saves the database files to disk"""
    for user_id, save in user_saves.items():
        save.t_suspend(None, save_dir + user_id)
    pass

def load_advent_dat(data):
    """Called for each came object"""
    datapath = os.path.join(os.path.dirname(__file__), 'advent.dat')
    with open(datapath, 'r', encoding='ascii') as datafile:
        parse(data, datafile)


if __name__ == "__main__":
    print(new_game("mark12"))
    print(respond("mark12", "no"))
    print(new_game("john12"))
    print(respond("john12", "yes"))
    db_save()
    print(respond("mark12", "road"))
