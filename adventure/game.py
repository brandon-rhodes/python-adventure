"""How we keep track of the state of the game."""

class Game(object):

    def __init__(self, data, writer, asker):
        self.data = data
        self.writer = writer
        self.asker = asker

    def write(self, s):
        self.writer(unicode(s))

    def start(self):
        self.write(self.data.messages[65])
