import unittest

class DataTest(unittest.TestCase):

    def setUp(self):
        from adventure.data import Data
        from adventure import load_advent_dat
        self.data = Data()
        load_advent_dat(self.data)

    def test_long_description(self):
        self.assertEqual(self.data.rooms[4].long_description, """\
YOU ARE IN A VALLEY IN THE FOREST BESIDE A STREAM TUMBLING ALONG A
ROCKY BED.
""")

    def test_long_description_expands_tabs(self):
        self.assertIn("ALMOST AS IF ALIVE.  A COLD WIND BLOWS",
                      self.data.rooms[15].long_description)

    def test_short_description(self):
        self.assertEqual(self.data.rooms[4].short_description,
                         "YOU'RE IN VALLEY.\n")

    def test_object_message_expands_tabs(self):
        self.assertEqual(self.data.objects[24].messages[5], """\
YOU'VE OVER-WATERED THE PLANT!  IT'S SHRIVELING UP!  IT'S, IT'S...
""")

    def test_hint(self):
        hint = self.data.hints[4]
        self.assertEqual(hint.turns_needed, 4)
        self.assertEqual(hint.penalty, 2)
        self.assertEqual(hint.question.text,
                         "ARE YOU TRYING TO GET INTO THE CAVE?\n")
        self.assertEqual(hint.message.text, """\
THE GRATE IS VERY SOLID AND HAS A HARDENED STEEL LOCK.  YOU CANNOT
ENTER WITHOUT A KEY, AND THERE ARE NO KEYS NEARBY.  I WOULD RECOMMEND
LOOKING ELSEWHERE FOR THE KEYS.
""")

class ReprTest(unittest.TestCase):

    def setUp(self):
        from adventure.data import Data
        from adventure import load_advent_dat
        self.data = Data()
        load_advent_dat(self.data)

    def assertMove(self, room_i, entry_i, s):
        r = repr(self.data.rooms[room_i].travel_table[entry_i]).strip()
        self.assertEqual(r, s)

    def test_move_repr_look_good(self):
        m = self.assertMove
        m(1, 0, '<road|west|upward moves to "YOU\'RE AT HILL IN ROAD.">')
        m(108, 0, '<east|north|south|ne|se|sw|nw|upward|d 95% of the time'
          ' prints \'YOU HAVE CRAWLED AROUND IN SOME LITTLE HOLES AND WOUND'
          ' UP BACK IN THE\\nMAIN PASSAGE.\\n\'>')
        m(61, 2, '<south if not a dwarf moves to \'YOU ARE IN A MAZE OF\'>')
        m(15, 3, '<upward|pit|steps|dome|passage|east if carrying 50 moves'
          ' to \'THE DOME IS UNCLIMBA\'>')
        m(19, 6, '<sw if carrying or in room with 11 moves to '
          '"YOU CAN\'T GET BY THE">')
        m(17, 2, '<forward if prop 12 != 1 moves to "YOU DIDN\'T MAKE IT.">')

    def test_move_repr_works_on_all_moves(self):
        for room in self.data.rooms.values():
            for i, move in enumerate(room.travel_table):
                try:
                    repr(move)
                except:  # pragma: no cover
                    print(room, i)
                    raise

    def test_room_repr(self):
        self.assertRegex(repr(self.data.rooms[64]), '<room 64 at .*>')

    def test_object_repr(self):
        self.assertRegex(repr(self.data.objects['chest']),
                         r'<Object 55 chest/box/treasure .*>')

    def test_word_repr(self):
        self.assertEqual(repr(self.data.vocabulary['eat']), '<Word eat>')
