"""How we keep track of the state of the game."""

class Game(object):

    def __init__(self, data, write, asker):
        self.data = data
        self.write = write
        self.asker = asker

    def start(self):
        self.write(self.data.messages[65].text)
