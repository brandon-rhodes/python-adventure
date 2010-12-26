"""Interpret Adventure commands."""

import os
from .data import parse

def read_data_from_nearby_file():
    datapath = os.path.join(os.path.dirname(__file__), 'advent.dat')
    datafile = open(datapath, 'r')
    return parse(datafile)

def interpret(data, words):
    if words == ['?']:
        print data.room.travel_table
        return
    if len(words):
        word = data.vocabulary_words.get(words[0])
        if word is None:
            return
        for move in data.room.travel_table:
            if word in move.verbs: # and check the condition!
                move.take_action(data)
                break

def loop(data):
    print data.room.description
    while True:
        data.room.visited = True
        line = raw_input('>')
        words = line.strip().upper().split()
        interpret(data, words)

def play():
    data = read_data_from_nearby_file()
    data.room = data.rooms[1]
    try:
        loop(data)
    except (KeyboardInterrupt, EOFError):
        pass
